import server
import unittest
import json
from pymongo import MongoClient
import base64


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client()
        # Run app in testing mode to retrieve exceptions and stack traces
        server.app.config['TESTING'] = True

        # Inject test database into application
        mongo = MongoClient('localhost', 27017)
        db = mongo.test_database
        server.app.db = db

        # Drop collection (significantly faster than dropping entire db)
        db.drop_collection('trips')
        db.drop_collection('users')

    # def test_posting_trip(self):
    #     # [Ben-G] Posting a trip should require user authentication
    #     # You should also avoid using possesive determiners in variable names, routes, etc.
    #     # '/trips/' is better than '/trips/'
    #     response = self.app.post('/trips/', data=json.dumps(dict(
    #         tripName="A Trip"
    #     )),
    #         content_type='application/json'
    #     )
    #
    #     responseJSON = json.loads(response.data.decode())
    #
    #     self.assertEqual(response.status_code, 200)
    #     assert 'application/json' in response.content_type
    #     assert 'A Trip' in responseJSON["tripName"]

    def test_getting_trip(self):
        #  Post a user
        data = {'username': 'Joe', 'password': 'p@ssword'}
        self.app.post('/users/', data=json.dumps(
            data),
            content_type='application/json',
        )

        # [Ben-G] The association with a user should happen by passing an
        # Base64 encoded authorization header that contains username and password.
        # You should do that instead of passing a username as part of the JSON.
        # The backend should also be able to verify your password, so you need
        # to pass it along here.

        headers = {}
        headers['Authorization'] = 'Basic ' + base64.b64encode(
            (data['username'] + ':' + data['password']).encode('utf-8')
        ).decode('utf-8')

        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'

        #  Post a trip and associate it with a user
        response = self.app.post('/trips/', data=json.dumps(dict(
            tripName="A Trip"
        )), headers=headers,
            content_type='application/json'
        )

        postResponseJSON = json.loads(response.data.decode())
        print("SSSSSSS")
        print(postResponseJSON)
        postedObjectID = postResponseJSON["_id"]

        response = self.app.get('/trips/' + postedObjectID, headers=headers)
        responseJSON = json.loads(response.data.decode())
        print("Getting Trip: " + str(responseJSON))
        self.assertEqual(response.status_code, 200)
        assert 'A Trip' in responseJSON["tripName"]

    def test_getting_non_existent_trip(self):
        response = self.app.get('/mytrip/55f0cbb4236f44b7f0e3cb23')
        self.assertEqual(response.status_code, 404)

    ''' Tests that a user signed up succesfully '''
    def test_sign_up(self):
        # Login tests
        data = {'username': 'Joe', 'password': 'p@ssword'}

        response = self.app.post('/users/', data=json.dumps(
            data),
            content_type='application/json',
        )

        loginPostResponseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'Joe' in loginPostResponseJSON["username"]

    ''' Tests that you can login in and out of the service  '''

    def test_good_login(self):
        # Login tests
        data = {'username': 'Joe', 'password': 'p@ssword'}
        response = self.app.post('/users/', data=json.dumps(
            data),
            content_type='application/json'
        )

        loginPostResponseJSON = json.loads(response.data.decode())
        postedUserId = loginPostResponseJSON["_id"]

        # [Ben-G] Since these are all headers, not only 'auth headers' I would
        # reather name this dictionary 'headers'
        auth_header = {}
        auth_header['Authorization'] = 'Basic ' + base64.b64encode(
            (data['username'] + ':' + data['password']).encode('utf-8')
        ).decode('utf-8')

        auth_header['Content-Type'] = 'application/json'
        auth_header['Accept'] = 'application/json'

        response = self.app.get('/users/', headers=auth_header)

        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'Joe' in loginPostResponseJSON["username"]

    def test_bad_login(self):
        # Login tests
        data = {'username': 'sdf', 'password': 'p@sd'}
        response = self.app.post('/users/', data=json.dumps(
            dict(username='Joe', password='p@ssword')),
            content_type='application/json'
        )

        loginPostResponseJSON = json.loads(response.data.decode())
        postedUserId = loginPostResponseJSON["_id"]

        # [Ben-G] Since these are all headers, not only 'auth headers' I would
        # reather name this dictionary 'headers'
        auth_header = {}
        auth_header['Authorization'] = 'Basic ' + base64.b64encode(
            (data['username'] + ':' + data['password']).encode('utf-8')
        ).decode('utf-8')
        auth_header['Content-Type'] = 'application/json'
        response = self.app.get('/users/' + postedUserId, headers=auth_header)

        self.assertEqual(response.status_code, 401)

    def test_logout(arg):
        pass

if __name__ == '__main__':
    unittest.main()
