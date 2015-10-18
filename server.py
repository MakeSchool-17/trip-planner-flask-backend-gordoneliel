from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder
import bcrypt
from functools import wraps

# Basic Setup
app = Flask(__name__)
# MONGO_URL = os.environ.get('MONGOHQ_URL')
mongo = MongoClient('localhost', 27017)
app.db = mongo.develop_database
# app.db = mongo.app42721996
api = Api(app)
BCRYPT_ROUNDS = 12


def check_auth(username, password):
    if username is None or password is None:
        return False
    else:
        #  Get user from database
        myuser_collection = app.db.myusers
        my_user = myuser_collection.find_one({"username": username})
        if my_user is None:
            return False
        db_password = my_user['password']
        password = str.encode(password)
        db_password = str.encode(db_password)
        # hashed = bcrypt.hashpw(password, bcrypt.gensalt(BCRYPT_ROUNDS))
        # print(hashed, db_password)
        return bcrypt.hashpw(password, db_password) == db_password


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


class User(Resource):
    @requires_auth
    def get(self, user_id=None):
        if user_id is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            myuser_collection = app.db.myusers
            my_user = myuser_collection.find_one({"_id": ObjectId(user_id)})

            return my_user

    def post(self):
        new_user = request.json
        password = new_user['password'].encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt(BCRYPT_ROUNDS)).decode('utf-8')
        new_user['password'] = hashed

        # Check for existing user
        existing_user = app.db.myusers.find_one({
            "username": new_user["username"]
        })

        print("Existing User: " + str(existing_user))

        if existing_user:
            message = {"error": "User already exists"}
            response = jsonify(message)
            response.status_code = 401
            # print(response)
            return response
        else:
            myuser_collection = app.db.myusers
            result = myuser_collection.insert_one(new_user)

            myuser = myuser_collection.find_one({
                "_id": ObjectId(result.inserted_id)
            })

            return myuser


class Trip(Resource):
    @requires_auth
    def get(self, trip_id=None):
        if trip_id is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            mytrip_collection = app.db.myobjects
            my_trip = mytrip_collection.find_one({"_id": ObjectId(trip_id)})
            return my_trip

    def post(self):
        new_trip = request.json
        mytrip_collection = app.db.myobjects
        result = mytrip_collection.insert_one(new_trip)

        mytrip = mytrip_collection.find_one({
            "_id": ObjectId(result.inserted_id)
        })

        return mytrip

    def put(self, trip_id=None):
        if trip_id is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:

            new_trip = request.json

            # Find a trip and modify it
            trip_collection = app.db.myobjects
            my_trip = trip_collection.update_one({"_id": ObjectId(trip_id)})

            return my_trip

api.add_resource(
    Trip,
    '/mytrips/',
    '/mytrips/<string:trip_id>'
)

api.add_resource(
    User,
    '/myusers/',
    '/myusers/<string:user_id>'
)


# provide a custom JSON serializer for flaks_restful
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
