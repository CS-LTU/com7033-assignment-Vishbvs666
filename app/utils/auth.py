from __future__ import annotations
from functools import wraps
from flask import session, redirect, url_for, request

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            nxt = request.full_path or url_for("main.dashboard")
            return redirect(url_for("auth.login_get", next=nxt))
        return view(*args, **kwargs)
    return wrapped
