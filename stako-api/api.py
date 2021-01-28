import settings
import requests
from flask import Flask, request
from flask_restful import Resource, Api
import logging
from mongo import APIMongo, ExperimentMongo
from data import StakoUser, StakoActivity
from urllib.parse import urlparse


class APIBase(Resource):
    def __init__(self):
        if app.testing:
            settings.MONGODB_NAME = settings.MONGODB_NAME_TEST
            self.testing = True
        self.data_source = APIMongo(settings)
        self.auth = ExperimentMongo(settings)

    @staticmethod
    def get_tag_list(tags_string):
        tag_list = tags_string.split(';')
        tag_list.sort()
        return tag_list


class Auth(APIBase):
    GOOGLE_OAUTH_INFO = 'https://oauth2.googleapis.com/tokeninfo?access_token={}'
    TESTER_EMAIL = 'user@tester.com'
    TESTER_TOKEN = 'XPTO_1234567890'

    def get(self):
        data = request.args
        if data and ('email' in data.keys()) and ('google_id' in data.keys()) and ('token' in data.keys()):
            valid = self._validate_token(data.get('email'), data.get('google_id'), data.get('token'))
            if valid:
                pass
            else:
                return {'MESSAGE': '401: Invalid OAUTH token for provided email!'}, 401
        else:
            return {'MESSAGE': 'Malformed auth request: need "email" and "token" params.'}, 400

    def _validate_token(self, email, google_id, oauth_token):
        logging.info('[API:AUTHORIZE] EMAIL {}, GID {}, and TOKEN {}.'.format(email, google_id, oauth_token))
        if self.testing:
            return email == Auth.TESTER_EMAIL and oauth_token == Auth.TESTER_TOKEN
        else:
            r_url = Auth.GOOGLE_OAUTH_INFO.format(oauth_token)
            response = requests.get(r_url)
            if response.status_code == 200:
                data = response.json()
                logging.info('[API:AUTHORIZED?] {}'.format(data))
                if 'error' not in data.keys():
                    app = data['aud']
                    user = data['sub']
                    if app == settings.STAKO_OAUTH_ID and user == google_id:
                        return True
        return False



class User(APIBase):
    def get(self, uuid):
        logging.info('[API:GetUser] ID {}'.format(uuid))
        a_user = self.data_source.get_user(uuid)
        return a_user

    def put(self, uuid):
        user = self.data_source.get_user(uuid)
        if user:
            # TODO: Block/sort out non-json requests
            new_data = request.json
            for key in ['nickname', 'email', 'motto']:
                if key in new_data:
                    user[key] = new_data[key]
            if 'activity' in new_data:
                pass
                # TODO: Implement!
            if 'communities' in new_data:
                pass
                # TODO: Implement!
            if self.data_source.save_user(user):
                return user
            else:
                return {'MESSAGE': '500: Could not update user {}!'.format(uuid)}, 500
        else:
            return {'MESSAGE': '404: User {} not found!'.format(uuid)}, 404


class NewUser(APIBase):
    def get(self):
        search = request.args
        if search and ('key' in search.keys()) and ('value' in search.keys()):
            key = search['key']
            value = search['value']
            if key == 'email':
                email = value
                uuid = self._authorize(email)
                if uuid:
                    key = 'uuid'
                    value = uuid
                else:
                    return {'MESSAGE': 'The email "{}" is not associated to an authorized user.'.format(email)}, 403
            if key == 'uuid':
                user = self._get_user(key, value)
                if user:
                    return user
                else:
                    return {'MESSAGE': 'Could not find a user matching search {}.'.format(search)}, 404
            return {'MESSAGE': 'Malformed search request: KEY not in [uuid, email].'}, 400
        return {'MESSAGE': 'Malformed search request: need [KEY:K,VALUE:V] params.'}, 400


    def post(self):
        new_user = StakoUser.get_empty_user()
        if self.data_source.save_user(new_user):
            logging.info('[API:PostUser] UUID {}'.format(new_user['uuid']))
            return {'uuid': new_user['uuid']}
        else:
            # TODO: Should return and ERROR?
            logging.info('[API:PostUser] ERROR!')
            return {}

    def _authorize(self, email):
        auth = self.auth.get_user(email)
        if auth == {}:
            return False
        else:
            return auth['uuid']

    def _get_user(self, key, value):
        return self.data_source.get_user(value, key)


class UserActivity(APIBase):

    def post(self, uuid):
        user = self.data_source.get_user(uuid)
        if user:
            request_data = request.json
            logging.info('[API:PostActivity] REQUEST DATA: {}'.format(request_data))
            valid_data = self.validate_activity_data(request_data)
            if valid_data:
                new_activity = StakoActivity.get_empty_activity()
                new_activity['uuid'] = uuid
                new_activity['url'] = valid_data.pop('url')
                new_activity['type'] = valid_data.pop('type')
                new_activity['data'] = valid_data
                result = self.data_source.save_activity(new_activity)
                if result:
                    logging.info('[API:PostActivity] Activity {}'.format(new_activity))
                    new_activity.pop('_id', None)
                    return new_activity
                else:
                    return {'MESSAGE': '500: Could not add activity to user {}!'.format(uuid)}, 500
            else:
                return {'MESSAGE': '400: Malformed User Activity!'}, 400
        else:
            return {'MESSAGE': '404: User {} not found!'.format(uuid)}, 404

    def validate_activity_data(self, request_data):
        activity_type = request_data.pop('type', None)
        url = request_data.pop('url', None)
        if activity_type and url:
            valid_url = urlparse(url)
            if url and all([valid_url.scheme, valid_url.netloc, valid_url.path]):
                if activity_type in StakoActivity.ACTIVITY_TYPES:
                    activity = {'url': url, 'type': activity_type}
                    for entry in StakoActivity.ACTIVITY_TYPES[activity_type]:
                        try:
                            activity[entry] = request_data.pop(entry)
                        except KeyError:
                            return None
                    return activity
        return None


logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
api = Api(app)

prefix = '/v1'
api.add_resource(Auth, '{}/auth/'.format(prefix))
api.add_resource(User, '{}/user/<uuid>/'.format(prefix))
api.add_resource(NewUser, '{}/user/'.format(prefix))
api.add_resource(UserActivity, '{}/user/<uuid>/activity/'.format(prefix))

if __name__ == '__main__':
    app.run(debug=settings.STAKO_DEBUG)
