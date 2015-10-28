from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder
import bcrypt
from functools import wraps
import datetime

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
        myuser_collection = app.db.users
        my_user = myuser_collection.find_one({"username": username})
        if my_user is None:
            return False
        db_password = my_user['password']
        password = str.encode(password)
        db_password = str.encode(db_password)

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
    def get(self):
        username = request.authorization.username
        if username is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            myuser_collection = app.db.users
            my_user = myuser_collection.find_one({"username": username})

            return my_user

    def post(self):
        new_user = request.json
        # new_user = request.authorization.password

        if new_user['username'] == "" or new_user['password'] == "":
            response = jsonify(data=[])
            response.status_code = 401
            return response

        password = new_user['password'].encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt(BCRYPT_ROUNDS)).decode('utf-8')
        new_user['password'] = hashed

        # Check for existing user
        existing_user = app.db.users.find_one({
            "username": new_user["username"]
        })

        print("Existing User: " + str(existing_user))

        if existing_user:
            message = {"error": "User already exists"}
            response = jsonify(message)
            response.status_code = 401

            return response
        else:
            myuser_collection = app.db.users
            result = myuser_collection.insert_one(new_user)

            myuser = myuser_collection.find_one({
                "_id": ObjectId(result.inserted_id)
            })

            return myuser

        def put(self):
            # Add implementation for updating a User
            username = request.authorization.username
            myuser_collection = app.db.users
            myuser_collection.update_one({"$set": {"username": username}})

            user = myuser_collection.find_one({"username": username})
            return user


class Trip(Resource):
    @requires_auth
    def get(self, trip_id=None):
        if trip_id is None:
            # [Ben-G] If the trip_id is none, it means that the API Endpoint '/trips/' was called
            # instead of returning a 404, you should return all trips for the current user in this case
            my_user = request.authorization.username
            mytrip_collection = app.db.trips
            my_trips = mytrip_collection.find({"username": my_user})
            # trip_list = list(my_trips)
            # import pdb; pdb.set_trace()
            return list(my_trips)
        else:
            # [Ben-G] In future you need to check if the requested trip belongs to the authenticated
            # user before returning it
            my_user = request.authorization.username
            mytrip_collection = app.db.trips
            my_trip = mytrip_collection.find_one({"_id": ObjectId(trip_id)})
            if my_trip['username'] == my_user:
                print("Trips is: " + str(my_trip))
                return my_trip
            else:
                response = jsonify(data=[])
                response.status_code = 404
                return response

    @requires_auth
    def post(self):
        # [Ben-G] In future you should associate the trip with the
        # authenticated user
        new_trip = request.json
        my_user = request.authorization.username
        print("New Trip: " + str(new_trip))
        mytrip_collection = app.db.trips

        new_trip['username'] = my_user
        new_trip['createdAt'] = datetime.datetime.utcnow()

        result = mytrip_collection.insert_one(new_trip)

        mytrip = mytrip_collection.find_one({
            "_id": ObjectId(result.inserted_id)
        })
        print("Trips is: " + str(mytrip))
        return mytrip

    # Add implementation for updating a Post
    # [Ben-G] This function shouldn't have a default argument for `trip_id`, since the client
    # always needs to pass a valid ID in order to update a trip

    @requires_auth
    def put(self, trip_id=None):
        # [Ben-G] In future you need to check if the requested trip belongs to the authenticated
        # user before updating it
        if trip_id is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            username = request.authorization.username
            new_trip = request.json

            # Find a trip and modify it
            trip_collection = app.db.trips
            trip_collection.update_one({
                "$set": {"username": username},
                "$tripDate": {"lastModified": True}
            })

            my_trip = trip_collection.find_one({"_id": ObjectId(trip_id)})

            return my_trip

# [Ben-G] No possessive determiners! ;) Should be renamed to '/trips/' and '/users/'
api.add_resource(
    Trip,
    '/trips/',
    '/trips/<string:trip_id>'
)

api.add_resource(
    User,
    '/users/',
    '/users/<string:user_id>'
)


# provide a custom JSON serializer for flaks_restful
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    # import pdb; pdb.set_trace()
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(host="0.0.0.0", debug=True)
