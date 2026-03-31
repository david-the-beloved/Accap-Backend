from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models import Note, User
from app.schemas import NoteResponse, NoteUpsertRequest
from app.services.book_state_service import sync_user_book_state

router = APIRouter(prefix="/notes", tags=["notes"])


def _draw_wrapped_line(pdf: canvas.Canvas, text: str, x: float, y: float, max_width: float, step: float) -> float:
    current = ""
    for word in text.split():
        candidate = word if not current else f"{current} {word}"
        if pdf.stringWidth(candidate, "Helvetica", 10) <= max_width:
            current = candidate
            continue

        pdf.drawString(x, y, current)
        y -= step
        current = word

    if current:
        pdf.drawString(x, y, current)
        y -= step

    return y


@router.put("/upsert", response_model=NoteResponse)
def upsert_note(
    payload: NoteUpsertRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> NoteResponse:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    sync_user_book_state(session, current_user, payload.book_version)

    note = session.exec(
        select(Note).where(Note.user_id == current_user.id,
                           Note.page_number == payload.page_number)
    ).first()

    if not note:
        note = Note(
            user_id=current_user.id,
            page_number=payload.page_number,
            chapter=payload.chapter,
            content=payload.content,
        )
        session.add(note)
    else:
        note.chapter = payload.chapter
        note.content = payload.content
        note.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(note)
    return NoteResponse(**note.model_dump())


@router.get("/by-page", response_model=NoteResponse | None)
def get_note_by_page(
    page_number: int = Query(...),
    book_version: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    changed = sync_user_book_state(session, current_user, book_version)
    if changed:
        session.commit()

    note = session.exec(
        select(Note).where(Note.user_id == current_user.id,
                           Note.page_number == page_number)
    ).first()
    if not note:
        return None
    return NoteResponse(**note.model_dump())


@router.get("/export/pdf")
def export_notes_pdf(
    book_version: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    changed = sync_user_book_state(session, current_user, book_version)
    if changed:
        session.commit()

    notes = session.exec(
        select(Note).where(Note.user_id == current_user.id)
    ).all()
    notes.sort(key=lambda item: item.page_number) 

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    left_margin = 54
    top_y = height - 54
    bottom_y = 54
    line_step = 14
    max_line_width = width - (left_margin * 2)

    y = top_y
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(left_margin, y, "Reading Notes Export")
    y -= 22

    pdf.setFont("Helvetica", 10)
    subtitle = f"User: {current_user.email}"
    y = _draw_wrapped_line(pdf, subtitle, left_margin,
                           y, max_line_width, line_step)
    y = _draw_wrapped_line(
        pdf,
        f"Book Version: {book_version or 'default'}",
        left_margin,
        y,
        max_line_width,
        line_step,
    )
    y = _draw_wrapped_line(
        pdf,
        f"Exported (UTC): {datetime.utcnow().isoformat(timespec='seconds')}",
        left_margin,
        y,
        max_line_width,
        line_step,
    )
    y -= 6

    if not notes:
        pdf.setFont("Helvetica", 11)
        pdf.drawString(
            left_margin, y, "No notes available for this book version.")
    else:
        for note in notes:
            if y < bottom_y + 90:
                pdf.showPage()
                y = top_y

            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(
                left_margin,
                y,
                f"Page {note.page_number} - {note.chapter or 'Unknown'}",
            )
            y -= line_step

            pdf.setFont("Helvetica", 10)
            content = (note.content or "").replace("\r\n", "\n")
            paragraphs = content.split("\n") if content else ["(empty note)"]
            for paragraph in paragraphs:
                text = paragraph.strip() or " "
                y = _draw_wrapped_line(
                    pdf, text, left_margin, y, max_line_width, line_step)
                if y < bottom_y + 40:
                    pdf.showPage()
                    y = top_y
                    pdf.setFont("Helvetica", 10)
                else:
                    y -= 3

            y -= 8

    pdf.save()
    data = buffer.getvalue()
    buffer.close()

    filename = f"notes-{datetime.utcnow().date().isoformat()}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=data, media_type="application/pdf", headers=headers)
