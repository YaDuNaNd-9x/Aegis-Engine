import httpx

from typing import Optional

from backend.app.core.config import settings


class OllamaError(RuntimeError):
    """Raised when an Ollama operation fails."""


class OllamaConnectionError(OllamaError):
    """Raised when the local Ollama server cannot be reached."""


class OllamaModelError(OllamaError):
    """Raised when a requested model is unavailable."""


class OllamaClient:
    """
    Async client for local Ollama inference.

    All inference and embedding requests are sent to the
    configured local Ollama server. No external LLM API is used.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")

        self.timeout = httpx.Timeout(
            settings.OLLAMA_TIMEOUT_SECONDS,
            connect=settings.OLLAMA_CONNECT_TIMEOUT_SECONDS,
        )

    async def check_connection(self) -> bool:
        """Return True if the Ollama server is reachable."""

        try:
            async with httpx.AsyncClient(
                timeout=settings.OLLAMA_HEALTH_TIMEOUT_SECONDS
            ) as client:
                response = await client.get(
                    f"{self.base_url}/api/tags"
                )

                response.raise_for_status()
                return True

        except (httpx.HTTPError, ValueError):
            return False

    async def list_models(self) -> list:
        """Return models currently installed in local Ollama."""

        try:
            async with httpx.AsyncClient(
                timeout=settings.OLLAMA_HEALTH_TIMEOUT_SECONDS
            ) as client:
                response = await client.get(
                    f"{self.base_url}/api/tags"
                )

                response.raise_for_status()

                models = response.json().get("models", [])

                return models if isinstance(models, list) else []

        except httpx.HTTPError as exc:
            raise OllamaConnectionError(
                f"Unable to retrieve local Ollama models: {exc}"
            ) from exc

        except (ValueError, TypeError) as exc:
            raise OllamaError(
                "Ollama returned an invalid model-list response."
            ) from exc

    async def get_installed_model_names(self) -> list[str]:
        """Return installed model names, including their tags."""

        models = await self.list_models()

        return [
            model.get("name")
            for model in models
            if isinstance(model, dict) and model.get("name")
        ]

    async def is_model_available(self, model_name: str) -> bool:
        """Check whether a model is installed, handling default tags."""

        if not model_name:
            return False

        installed_models = await self.get_installed_model_names()

        def normalize(name: str) -> str:
            if ":" not in name:
                return f"{name}:latest"
            return name

        target = normalize(model_name)

        return any(
            normalize(installed) == target
            for installed in installed_models
        )

    async def check_required_models(self) -> dict:
        """Check whether all configured models are installed."""

        required_models = {
            "fast_model": settings.FAST_MODEL,
            "reasoning_model": settings.REASONING_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
        }

        results = {}

        for key, model_name in required_models.items():
            results[key] = {
                "model": model_name,
                "available": await self.is_model_available(model_name),
            }

        return results

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate a response using a local Ollama chat model.

        keep_alive defaults to zero to unload models after
        each request and conserve unified memory on the Mac.
        """

        if not isinstance(messages, list) or not messages:
            raise ValueError("Messages must be a non-empty list.")

        selected_model = model or settings.FAST_MODEL
        selected_temperature = (
            settings.LLM_TEMPERATURE
            if temperature is None
            else temperature
        )

        if not 0.0 <= selected_temperature <= 2.0:
            raise ValueError("Temperature must be between 0 and 2.")

        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
            "keep_alive": settings.LLM_KEEP_ALIVE,
            "options": {
                "temperature": selected_temperature,
                "num_predict": settings.LLM_MAX_TOKENS,
            },
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                if response.status_code == 404:
                    raise OllamaModelError(
                        f"Model '{selected_model}' was not found. "
                        "Check that it is installed in Ollama."
                    )

                response.raise_for_status()

                result = response.json()

                content = (
                    result.get("message", {}).get("content")
                    if isinstance(result, dict)
                    else None
                )

                if not isinstance(content, str):
                    raise OllamaError(
                        "Ollama returned an invalid chat response."
                    )

                return content

        except OllamaError:
            raise

        except httpx.ConnectError as exc:
            raise OllamaConnectionError(
                "Cannot connect to Ollama. Make sure the local "
                "Ollama application/server is running."
            ) from exc

        except httpx.TimeoutException as exc:
            raise OllamaError(
                f"Ollama request timed out after "
                f"{settings.OLLAMA_TIMEOUT_SECONDS} seconds."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise OllamaError(
                f"Ollama chat request failed with HTTP "
                f"{exc.response.status_code}."
            ) from exc

        except (ValueError, TypeError) as exc:
            raise OllamaError(
                "Unable to parse the Ollama chat response."
            ) from exc

        except httpx.HTTPError as exc:
            raise OllamaConnectionError(
                f"Ollama communication error: {exc}"
            ) from exc

    async def embed(
        self,
        texts: str | list[str],
    ) -> list[list[float]]:
        """Generate embeddings using the configured local model."""

        if isinstance(texts, str):
            if not texts.strip():
                raise ValueError("Embedding input cannot be empty.")
        elif isinstance(texts, list):
            if not texts or any(
                not isinstance(item, str) or not item.strip()
                for item in texts
            ):
                raise ValueError(
                    "Embedding input must contain non-empty strings."
                )
        else:
            raise TypeError(
                "Embedding input must be a string or list of strings."
            )

        payload = {
            "model": settings.EMBEDDING_MODEL,
            "input": texts,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json=payload,
                )

                if response.status_code == 404:
                    raise OllamaModelError(
                        f"Embedding model '{settings.EMBEDDING_MODEL}' "
                        "was not found in Ollama."
                    )

                response.raise_for_status()

                result = response.json()
                embeddings = result.get("embeddings")

                if (
                    not isinstance(embeddings, list)
                    or not embeddings
                    or any(not isinstance(vector, list) for vector in embeddings)
                ):
                    raise OllamaError(
                        "Ollama returned an invalid embedding response."
                    )

                return embeddings

        except OllamaError:
            raise

        except httpx.ConnectError as exc:
            raise OllamaConnectionError(
                "Cannot connect to Ollama for embedding generation."
            ) from exc

        except httpx.TimeoutException as exc:
            raise OllamaError(
                "Ollama embedding request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise OllamaError(
                f"Ollama embedding request failed with HTTP "
                f"{exc.response.status_code}."
            ) from exc

        except (ValueError, TypeError) as exc:
            raise OllamaError(
                "Unable to parse the Ollama embedding response."
            ) from exc

        except httpx.HTTPError as exc:
            raise OllamaConnectionError(
                f"Ollama embedding communication error: {exc}"
            ) from exc


# Shared client instance
ollama_client = OllamaClient()