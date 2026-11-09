from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
)

from backend.app.core.config import settings
from backend.app.services.document_service import document_service
from backend.app.rag.retriever import retriever

from backend.app.schemas.documents import (
    DocumentResponse,
    SearchRequest,
    SearchResult,
)

from backend.app.security.validation import (
    validate_file_extension,
    validate_file_content,
    validate_prompt,
    ValidationError,
)

from backend.app.security.permissions import (
    Role,
    require_permission,
    PermissionDenied,
)


router = APIRouter(
    prefix="/documents",
    tags=["Knowledge Base"],
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
)
async def upload_document(
    file: UploadFile = File(...),
):
    try:
        require_permission(Role.OPERATOR, "document_upload")

        filename = validate_file_extension(
            file.filename or "",
            {".pdf", ".docx", ".txt"},
        )

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        file_bytes = await file.read(max_bytes + 1)

        validate_file_content(
            file_bytes,
            max_bytes,
        )

        result = await document_service.process_document(
            file_bytes,
            filename,
        )

        return DocumentResponse(**result)

    except PermissionDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {exc}",
        ) from exc

    finally:
        await file.close()


@router.post(
    "/search",
    response_model=list[SearchResult],
)
async def search_documents(
    request: SearchRequest,
):
    try:
        require_permission(Role.OPERATOR, "document_search")

        query = validate_prompt(request.query)

        if not 1 <= request.top_k <= 10:
            raise ValidationError(
                "top_k must be between 1 and 10."
            )

        results = await retriever.search(
            query=query,
            top_k=request.top_k,
        )

        return [
            SearchResult(**result)
            for result in results
        ]

    except PermissionDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document search failed: {exc}",
        ) from exc


@router.get("/stats")
async def document_stats():
    try:
        require_permission(Role.OPERATOR, "document_view")

        import asyncio

        indexed_chunks = await asyncio.to_thread(
            retriever.collection.count
        )

        return {
            "collection": "industrial_knowledge",
            "indexed_chunks": indexed_chunks,
            "retrieval_method": "hybrid",
            "reranking": "local_lexical",
        }

    except PermissionDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc