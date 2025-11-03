from functools import wraps
from flask import session, redirect, url_for, request

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login_get", next=request.full_path or request.path))
        return view(*args, **kwargs)
    return wrapped
