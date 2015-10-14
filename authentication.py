import bcrypt
from flask import request, jsonify
from functools import wraps

BCRYPT_ROUNDS = 12

from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder
from authentication import requires_auth, bcrypt, BCRYPT_ROUNDS


# Basic Setup
app = Flask(__name__)
mongo = MongoClient('localhost', 27017)
app.db = mongo.develop_database
api = Api(app)


def check_auth(username, password):
    print("Username password combo \n")
    print(username, password)
    if username is None or password is None:
        return False
    else:
        myuser_collection = app.db.myusers
        my_user = myuser_collection.find_one({"_id": ObjectId(user_id)})
        
        password = str.encode(password)
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
        print("Check auth: " + str(auth))
        if not auth or not check_auth(auth.username, auth.password):
            message = {'error': 'Basic Auth Required.'}
            resp = jsonify(message)
            resp.status_code = 401
            return resp
        return f(*args, **kwargs)
    return decorated
