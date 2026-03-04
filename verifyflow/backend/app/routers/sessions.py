from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Annotated, List
from .. import models, schemas, database
from ..core import security
from ..database import get_db
from ..models import ReferenceDocument, QuestionnaireSession
from ..services.parser import parse_reference

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=schemas.QuestionnaireSessionOut)
def create_session(
    session_in: schemas.QuestionnaireSessionCreate,
    current_user_email: Annotated[str, Depends(security.get_current_user)],
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise HTTPException(404, "User not found")

    db_session = models.QuestionnaireSession(
        user_id=user.id,
        title=session_in.title or "Untitled Assessment",
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.post("/{session_id}/references", response_model=list[schemas.ReferenceDocumentOut])
async def upload_references(
    session_id: int,
    current_user_email: Annotated[str, Depends(security.get_current_user)],
    db: Session = Depends(get_db),
    files: List[UploadFile] = File(...),
):
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise HTTPException(404, "User not found")

    session = db.query(QuestionnaireSession).filter(
        QuestionnaireSession.id == session_id,
        QuestionnaireSession.user_id == user.id
    ).first()

    if not session:
        raise HTTPException(404, "Session not found or not owned by you")

    uploaded = []
    for file in files:
        if not file.filename.lower().endswith((".pdf", ".docx", ".txt")):
            continue  # skip unsupported formats

        content = await file.read()

        try:
            parsed_text = parse_reference(content, file.filename)
        except Exception as e:
            raise HTTPException(422, f"Failed to parse {file.filename}: {str(e)}")

        doc = ReferenceDocument(
            session_id=session_id,
            filename=file.filename,
            parsed_text=parsed_text
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        uploaded.append(doc)

    return uploaded