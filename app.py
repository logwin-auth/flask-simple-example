"""Flask demo app with sqlite database."""

import os
import uuid

import werkzeug.exceptions
from flask import Flask, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.orm import Session

import database_objects
from flask_types_security import Response, more_secure_flask, redirect


def create_app() -> Flask:
    """Create and return the flask app for the demo."""
    host_db_url = os.environ.get(
        "NOTE_DATABASE", "sqlite+pysqlite:///:memory:"
    )
    note_echo = bool(os.environ.get("NOTE_ECHO", ""))
    engine = database_objects.create_engine_migrate(
        host_db_url, echo=note_echo
    )

    app = Flask(__name__)
    more_secure_flask(app, os.getenv("FLASK_SECRET", "secret"))

    @app.route("/", methods=["POST", "GET"])
    def homepage() -> Response:
        empty_error = False
        if (
            request.method == "POST"
            and request.form.get("exec_action") == "create_note"
        ):
            note_title = request.form.get("note_title")
            if note_title and isinstance(note_title, str):
                note_id = str(uuid.uuid4())
                with Session(engine) as db:
                    db.add(database_objects.Note(note_id, note_title, ""))
                    db.flush()
                    db.commit()
                return redirect(url_for("note_page", note_id=note_id))
            empty_error = True
        with Session(engine) as db:
            notes = db.execute(select(database_objects.Note)).scalars().all()
        return render_template(
            "index.html", notes=notes, empty_error=empty_error
        )

    @app.route("/note/<string:note_id>", methods=["GET", "POST"])
    def note_page(note_id: str) -> Response:
        note_title = ""
        note_text = ""
        empty_error = False
        with Session(engine) as db:
            note = (
                db.execute(
                    select(database_objects.Note).where(
                        database_objects.Note.note_id == note_id
                    )
                )
                .scalars()
                .one_or_none()
            )
            if not note:
                return render_template("404.html"), 404
            if (
                request.method == "POST"
                and request.form.get("delete_note") == "delete"
            ):
                db.delete(note)
                db.flush()
                db.commit()
                return redirect(url_for("homepage"))
            elif request.method == "POST":
                # Update the database
                if request.form.get("note_title"):
                    note.note_title = request.form.get("note_title", "")
                else:
                    empty_error = True
                note.note_text = request.form.get("note_text", "")
                db.flush()
                db.commit()
            # Extract strings from the object before it is detacthed
            note_title = note.note_title
            note_text = note.note_text
        return render_template(
            "note.html",
            note_title=note_title,
            note_text=note_text,
            empty_error=empty_error,
        )

    @app.errorhandler(werkzeug.exceptions.NotFound)
    def handle_not_found(error: werkzeug.exceptions.NotFound) -> Response:
        return render_template("404.html"), 404

    return app
