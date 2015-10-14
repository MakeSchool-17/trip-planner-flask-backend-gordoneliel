import bcrypt
from flask import request, jsonify
from functools import wraps

BCRYPT_ROUNDS = 12


def check_auth(username, password):
    if username or password is None:
        return False
    else:
        hashed = bcrypt.hashpw(password, bcrypt.gensalt(BCRYPT_ROUNDS))
        if bcrypt.hashpw(password, hashed) == hashed:
            return True
        else:
            return False
    # return username == 'Joe' and password == 'p@ssword'


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            message = {'error': 'Basic Auth Required.'}
            resp = jsonify(message)
            resp.status_code = 401
            return resp
        return f(*args, **kwargs)
    return decorated
