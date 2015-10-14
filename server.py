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


class User(Resource):
    @requires_auth
    def get(self, user_id=None):
        if user_id is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            myuser_collection = app.db.myobjects
            my_user = myuser_collection.find_one({"_id": ObjectId(user_id)})
            print("Got User")
            print(my_user)
            return my_user

    def post(self):
        new_user = request.json
        password = new_user['password'].encode('utf-8')

        hashed = bcrypt.hashpw(password, bcrypt.gensalt(BCRYPT_ROUNDS)).decode('utf-8')

        new_user['password'] = hashed
        # print("Post User")
        # print(new_user)

        myuser_collection = app.db.myobjects
        result = myuser_collection.insert_one(new_user)

        myuser = myuser_collection.find_one({
            "_id": ObjectId(result.inserted_id)
        })
        # print("After got")
        # print(myuser)
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


api.add_resource(
    Trip,
    '/mytrips/',
    '/mytrips/<string:trip_id>'
)

api.add_resource(
    User,
    '/myuser/',
    '/myuser/<string:user_id>/'
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
