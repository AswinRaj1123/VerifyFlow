from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated, List
from .. import models, schemas, database
from ..core import security
from ..database import get_db
from ..models import ReferenceDocument, QuestionnaireSession
from ..services.parser import parse_reference, parse_questionnaire
from ..services.rag_index import index_references_for_session
from ..services.rag import generate_answers
from ..services.export import build_docx

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


@router.post("/{session_id}/references")
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

    if uploaded:
        refs = [
            {"id": doc.id, "filename": doc.filename, "parsed_text": doc.parsed_text}
            for doc in uploaded
        ]
        index_result = index_references_for_session(session_id, refs)
        return {
            "uploaded": [schemas.ReferenceDocumentOut.from_orm(doc) for doc in uploaded],
            "indexing": index_result
        }

    return {"uploaded": [], "indexing": None}


@router.post("/{session_id}/index-references")
def index_session_references(
    session_id: int,
    current_user_email: Annotated[str, Depends(security.get_current_user)],
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise HTTPException(404, "User not found")

    session = db.query(QuestionnaireSession).filter(
        QuestionnaireSession.id == session_id,
        QuestionnaireSession.user_id == user.id
    ).first()

    if not session:
        raise HTTPException(404, "Session not found or access denied")

    refs_db = db.query(ReferenceDocument).filter(
        ReferenceDocument.session_id == session_id
    ).all()

    if not refs_db:
        return {"status": "no references to index"}

    references = [
        {"id": r.id, "filename": r.filename, "parsed_text": r.parsed_text}
        for r in refs_db
    ]

    result = index_references_for_session(session_id, references)
    return result


@router.post("/{session_id}/questionnaire", response_model=schemas.QuestionnaireUploadResponse)
async def upload_questionnaire(
    session_id: int,
    current_user_email: Annotated[str, Depends(security.get_current_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...)
):
    """
    Upload questionnaire file (PDF/XLSX/DOCX), parse questions, and store in DB.
    """
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise HTTPException(404, "User not found")

    session = db.query(QuestionnaireSession).filter(
        QuestionnaireSession.id == session_id,
        QuestionnaireSession.user_id == user.id
    ).first()

    if not session:
        raise HTTPException(404, "Session not found or not owned by you")

    # Validate file type
    if not file.filename.lower().endswith((".pdf", ".xlsx", ".xls", ".docx")):
        raise HTTPException(400, "Unsupported file type. Use PDF, XLSX, or DOCX.")

    content = await file.read()

    try:
        question_texts = parse_questionnaire(content, file.filename)
    except Exception as e:
        raise HTTPException(422, f"Failed to parse questionnaire: {str(e)}")

    if not question_texts:
        raise HTTPException(400, "No questions found in file")

    # Store questions in DB
    questions_created = []
    for q_text in question_texts:
        question = models.Question(
            session_id=session_id,
            original_text=q_text.strip()
        )
        db.add(question)
        questions_created.append(question)

    db.commit()
    for q in questions_created:
        db.refresh(q)

    return schemas.QuestionnaireUploadResponse(
        session_id=session_id,
        questions_created=len(questions_created),
        questions=[schemas.QuestionOut.from_orm(q) for q in questions_created]
    )


@router.post("/{session_id}/generate-answers", response_model=schemas.GenerateAnswersResponse)
def generate_all_answers(
    session_id: int,
    current_user_email: Annotated[str, Depends(security.get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Generate answers for ALL questions in the session using RAG.
    """
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise HTTPException(404, "User not found")

    session = db.query(QuestionnaireSession).filter(
        QuestionnaireSession.id == session_id,
        QuestionnaireSession.user_id == user.id
    ).first()

    if not session:
        raise HTTPException(404, "Session not found or not owned by you")

    # Get all questions for this session
    questions = db.query(models.Question).filter(
        models.Question.session_id == session_id
    ).all()

    if not questions:
        raise HTTPException(400, "No questions found in session. Upload a questionnaire first.")

    # Check if references exist
    ref_count = db.query(ReferenceDocument).filter(
        ReferenceDocument.session_id == session_id
    ).count()

    if ref_count == 0:
        raise HTTPException(400, "No reference documents found. Upload references first.")

    # Extract question texts
    question_texts = [q.original_text for q in questions]

    # Generate answers using RAG
    try:
        results = generate_answers(session_id, question_texts)
    except Exception as e:
        raise HTTPException(500, f"Answer generation failed: {str(e)}")

    # Update questions in DB
    for question, result in zip(questions, results):
        question.answer = result["answer"]
        question.citations = result["citations"]
        question.confidence = result["confidence"]

    db.commit()
    for q in questions:
        db.refresh(q)

    # Update session status
    session.status = "completed"
    db.commit()

    return schemas.GenerateAnswersResponse(
        session_id=session_id,
        questions_processed=len(questions),
        results=[schemas.QuestionOut.from_orm(q) for q in questions]
    )


@router.post("/{session_id}/questions/{question_id}/regenerate", response_model=schemas.QuestionOut)
def regenerate_single_answer(
    session_id: int,
    question_id: int,
    current_user_email: Annotated[str, Depends(security.get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Regenerate answer for a single question (useful for testing or re-answering).
    """
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise HTTPException(404, "User not found")

    session = db.query(QuestionnaireSession).filter(
        QuestionnaireSession.id == session_id,
        QuestionnaireSession.user_id == user.id
    ).first()

    if not session:
        raise HTTPException(404, "Session not found or not owned by you")

    question = db.query(models.Question).filter(
        models.Question.id == question_id,
        models.Question.session_id == session_id
    ).first()

    if not question:
        raise HTTPException(404, "Question not found in this session")

    # Generate answer for single question
    try:
        results = generate_answers(session_id, [question.original_text])
        result = results[0]
    except Exception as e:
        raise HTTPException(500, f"Answer generation failed: {str(e)}")

    # Update question
    question.answer = result["answer"]
    question.citations = result["citations"]
    question.confidence = result["confidence"]
    question.is_edited = False  # Reset edit flag on regeneration

    db.commit()
    db.refresh(question)

    return schemas.QuestionOut.from_orm(question)


@router.post("/{session_id}/regenerate", response_model=schemas.GenerateAnswersResponse)
def regenerate_selected_questions(
    session_id: int,
    request: schemas.PartialRegenerateRequest,
    current_user_email: Annotated[str, Depends(security.get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Regenerate answers for specific questions selected by the user.
    Allows partial regeneration while keeping other questions unchanged.
    """
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise HTTPException(404, "User not found")

    session = db.query(QuestionnaireSession).filter(
        QuestionnaireSession.id == session_id,
        QuestionnaireSession.user_id == user.id
    ).first()

    if not session:
        raise HTTPException(404, "Session not found or not owned by you")

    if not request.question_ids:
        raise HTTPException(400, "No question IDs provided")

    # Fetch only the specified questions
    questions = db.query(models.Question).filter(
        models.Question.id.in_(request.question_ids),
        models.Question.session_id == session_id
    ).all()

    if not questions:
        raise HTTPException(404, "No matching questions found in this session")

    if len(questions) != len(request.question_ids):
        found_ids = {q.id for q in questions}
        missing_ids = set(request.question_ids) - found_ids
        raise HTTPException(400, f"Questions not found in this session: {missing_ids}")

    # Check if references exist
    ref_count = db.query(ReferenceDocument).filter(
        ReferenceDocument.session_id == session_id
    ).count()

    if ref_count == 0:
        raise HTTPException(400, "No reference documents found. Upload references first.")

    # Extract question texts
    question_texts = [q.original_text for q in questions]

    # Generate answers using RAG
    try:
        results = generate_answers(session_id, question_texts)
    except Exception as e:
        raise HTTPException(500, f"Answer generation failed: {str(e)}")

    # Update selected questions in DB
    for question, result in zip(questions, results):
        question.answer = result["answer"]
        question.citations = result["citations"]
        question.confidence = result["confidence"]
        question.is_edited = False  # Reset edit flag since auto-regenerated

    db.commit()
    for q in questions:
        db.refresh(q)

    return schemas.GenerateAnswersResponse(
        session_id=session_id,
        questions_processed=len(questions),
        results=[schemas.QuestionOut.from_orm(q) for q in questions]
    )


@router.get("/{session_id}/export")
def export_session_docx(
    session_id: int,
    current_user_email: Annotated[str, Depends(security.get_current_user)],
    db: Session = Depends(get_db),
    format: str = "docx"
):
    """
    Export questionnaire session as a downloadable Word document (.docx).
    Includes questions, answers, confidence scores, citations, and edit flags.
    """
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise HTTPException(404, "User not found")

    session = db.query(QuestionnaireSession).filter(
        QuestionnaireSession.id == session_id,
        QuestionnaireSession.user_id == user.id
    ).first()

    if not session:
        raise HTTPException(404, "Session not found or not owned by you")

    # Only support docx format for now
    if format.lower() != "docx":
        raise HTTPException(400, "Only 'docx' format is supported")

    # Get all questions for this session (ordered by ID)
    questions = db.query(models.Question).filter(
        models.Question.session_id == session_id
    ).order_by(models.Question.id).all()

    if not questions:
        raise HTTPException(400, "No questions found in session. Upload a questionnaire first.")

    # Build the Word document
    try:
        doc_stream = build_docx(
            session_id=session_id,
            session_title=session.title,
            questions=questions,
            db=db
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to generate document: {str(e)}")

    # Generate filename
    filename = f"questionnaire-session-{session_id}.docx"

    # Return as streaming response
    return StreamingResponse(
        doc_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )