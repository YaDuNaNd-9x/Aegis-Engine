from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from backend.app.agents.graph import run_agent
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.core.config import settings

from backend.app.security.prompt_guard import validate_user_prompt
from backend.app.security.validation import (
    validate_filename,
    validate_file_extension,
    validate_file_content,
    validate_instruction,
    ValidationError,
)
from backend.app.security.permissions import (
    Role,
    require_permission,
    PermissionDenied,
)


router = APIRouter(
    prefix="/chat",
    tags=["AI Workbench"],
)


def build_chat_response(result: dict) -> ChatResponse:
    return ChatResponse(
        response=result.get("response"),
        selected_model=result.get("selected_model"),
        model_type=result.get("model_type"),
        status=result.get("status", "unknown"),
        error=result.get("error"),
        execution_steps=result.get("execution_steps", []),
        citations=result.get("citations", []),
    )


@router.post("/", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    try:
        require_permission(Role.OPERATOR, "chat")

        message = validate_user_prompt(request.message)

        result = await run_agent(
            user_query=message,
        )

        return build_chat_response(result)

    except (ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except PermissionDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {exc}",
        ) from exc


@router.post("/analyze", response_model=ChatResponse)
async def analyze_with_agent(
    instruction: str = Form(..., min_length=5, max_length=3000),
    file: UploadFile = File(...),
):
    try:
        require_permission(Role.OPERATOR, "data_analysis")

        instruction = validate_instruction(instruction)
        instruction = validate_user_prompt(instruction)

        filename = validate_file_extension(
            file.filename or "",
            {".csv"},
        )

        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        csv_bytes = await file.read(max_size + 1)

        validate_file_content(
            csv_bytes,
            max_size,
        )

        result = await run_agent(
            user_query=instruction,
            csv_bytes=csv_bytes,
            csv_filename=filename,
        )

        return build_chat_response(result)

    except HTTPException:
        raise

    except (ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except PermissionDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent CSV analysis failed: {exc}",
        ) from exc

    finally:
        await file.close()