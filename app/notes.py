"""API REST de ejemplo: notas."""

from datetime import UTC, datetime

from flask import Blueprint, abort, jsonify, request
from sqlalchemy import select

from .extensions import db

bp = Blueprint("notes", __name__)


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "created_at": self.created_at.isoformat(),
        }


@bp.get("")
def list_notes():
    limit = min(request.args.get("limit", 50, type=int), 100)
    notes = db.session.scalars(select(Note).order_by(Note.id.desc()).limit(limit)).all()
    return jsonify([n.to_dict() for n in notes])


@bp.post("")
def create_note():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not 1 <= len(title) <= 200:
        abort(422, description="'title' es obligatorio (1-200 caracteres)")
    note = Note(title=title, body=str(data.get("body", "")))
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201


@bp.get("/<int:note_id>")
def get_note(note_id: int):
    return jsonify(db.get_or_404(Note, note_id).to_dict())


@bp.delete("/<int:note_id>")
def delete_note(note_id: int):
    note = db.get_or_404(Note, note_id)
    db.session.delete(note)
    db.session.commit()
    return "", 204
