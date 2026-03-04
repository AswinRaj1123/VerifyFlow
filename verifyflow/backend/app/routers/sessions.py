from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from .. import models, schemas, database
from ..core import security

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