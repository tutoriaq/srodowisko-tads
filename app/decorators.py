# app/decorators.py
import functools
from flask import abort, request


def wymagany_parametr(nazwa):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if nazwa not in request.args:
                abort(400, description=f"Brak parametru {nazwa}")
            return f(*args, **kwargs)

        return decorated_function

    return decorator