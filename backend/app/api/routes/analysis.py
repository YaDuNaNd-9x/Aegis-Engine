from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from backend.app.services.analysis_service import analysis_service
from backend.app.schemas.analysis import AnalysisResponse
from backend.app.core.config import settings

from backend.app.security.prompt_guard import validate_user_prompt
from backend.app.security.validation import (
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
    prefix="/analysis",
    tags=["Industrial Data Analysis"],
)


@router.post(
    "/csv",
    response_model=AnalysisResponse,
)
async def analyze_csv(
    instruction: str = Form(
        ...,
        min_length=5,
        max_length=3000,
    ),
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

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        csv_bytes = await file.read(max_bytes + 1)

        validate_file_content(
            csv_bytes,
            max_bytes,
        )

        result = await analysis_service.analyze(
            instruction=instruction,
            csv_bytes=csv_bytes,
        )

        return AnalysisResponse(**result)

    except HTTPException:
        raise

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
            detail=f"Analysis failed: {exc}",
        ) from exc

    finally:
        await file.close()