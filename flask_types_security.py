"""Tools for type-safe and secure flask."""

from typing import Tuple

from flask import Flask
from flask import Response as FlaskResponse
from flask import redirect as redirect_untyped
from flask_wtf.csrf import CSRFProtect  # type: ignore

Response = FlaskResponse | str | Tuple[FlaskResponse, int] | Tuple[str, int]


def redirect(url: str) -> Response:
    """Flask redirect with correct typing."""
    return redirect_untyped(url)  # type: ignore


def more_secure_flask(app: Flask, flask_secret_key: str) -> None:
    """Flask app settings more secure, setup session cookie."""
    app.secret_key = flask_secret_key
    app.config["SESSION_COOKIE_SAMESITE"] = "strict"
    CSRFProtect(app)

    @app.after_request
    def apply_caching(response: FlaskResponse) -> FlaskResponse:
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Server"] = "server"  # Clear server name
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
