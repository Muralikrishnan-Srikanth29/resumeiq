from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.exceptions import UnsupportedFileTypeError
from app.core.rate_limit import limiter
from app.services import resume_service, session_service
from app.utils.validation import validate_file_size

router = APIRouter(prefix="/resume", tags=["resume"])

ALLOWED_EXTENSIONS = (".pdf", ".docx")


@router.post("/upload")
@limiter.limit("20/hour")
async def upload_resume(
    request: Request,
    session_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload a PDF or DOCX resume. Extracts text → parses → caches structured JSON."""
    if not file.filename or not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise UnsupportedFileTypeError()

    file_bytes = await file.read()
    validate_file_size(len(file_bytes))

    session_service.ensure_session(session_id)
    resume_id, resume_json = resume_service.ingest_resume_from_file(
        session_id, file_bytes, file.filename
    )
    return {"resume_id": resume_id, "resume": resume_json.model_dump()}


@router.post("/paste")
@limiter.limit("20/hour")
async def paste_resume(
    request: Request,
    session_id: str = Form(...),
    resume_text: str = Form(...),
):
    """Submit resume as pasted plain text instead of a file upload."""
    session_service.ensure_session(session_id)
    resume_id, resume_json = resume_service.ingest_resume_from_text(session_id, resume_text)
    return {"resume_id": resume_id, "resume": resume_json.model_dump()}


@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    resume_json = resume_service.get_resume_json(resume_id)
    return {"resume_id": resume_id, "resume": resume_json.model_dump()}
