from functools import wraps
import secrets

from flask import abort, redirect, request, session, url_for
from werkzeug.security import check_password_hash

from .models import User


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_user(user):
    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["_csrf_token"] = secrets.token_urlsafe(32)


def logout_user():
    session.clear()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("main.admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def verify_password(user, password):
    return bool(user and check_password_hash(user.password_hash, password))


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def validate_csrf():
    token = session.get("_csrf_token")
    if not token or request.form.get("_csrf_token") != token:
        abort(400, description="CSRF token invalido.")
