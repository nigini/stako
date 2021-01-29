import settings
import requests
from flask import Flask, request, jsonify
import flask_restful
from flask_restful import Resource, Api
import logging
from mongo import APIMongo, ExperimentMongo
from data import StakoUser, StakoActivity, StakoToken
from urllib.parse import urlparse
from functools import wraps
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended import exceptions as jwt_exceptions


def authorize_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'uuid' in kwargs:
            try:
                verify_jwt_in_request()
                if get_jwt_identity() == kwargs['uuid']:
                    return func(*args, **kwargs)
                else:
                    flask_restful.abort(403)
            except jwt_exceptions.NoAuthorizationError:
                flask_restful.abort(401)
        else:
            flask_restful.abort(400)
    return wrapper


class APIBase(Resource):
    def __init__(self):
        self.data_source = APIMongo(settings)
        self.auth = ExperimentMongo(settings)


class Auth(APIBase):
    GOOGLE_OAUTH_INFO = 'https://oauth2.googleapis.com/tokeninfo?access_token={}'
    TESTER_EMAIL = 'user@tester.com'

    def get(self):
        data = request.args
        if data and ('email' in data.keys()) and ('google_id' in data.keys()) and ('token' in data.keys()):
            valid = self._validate_token(data.get('email'), data.get('google_id'), data.get('token'))
            if valid:
                user = self.auth.get_user(data.get('email'))
                if 'uuid' in user.keys():
                    # TODO: Should check for existing one first?
                    token = create_access_token(identity=user['uuid'])
                    return {'uuid': user['uuid'], 'access_token': token}
                else:
                    return {'MESSAGE': 'Non Authorized: User with email {} is not a registered STAKO user!'
                            .format(data.get('email'))}, 401
            else:
                return {'MESSAGE': 'Non Authorized: Invalid OAUTH token for provided email!'}, 401
        else:
            return {'MESSAGE': 'Malformed auth request: need "email" and "token" params.'}, 400

    def _validate_token(self, email, google_id, oauth_token):
        logging.info('[API:AUTHORIZE] EMAIL {}, GID {}, and TOKEN {}.'.format(email, google_id, oauth_token))
        if settings.STAKO_TEST:
            return email == Auth.TESTER_EMAIL
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
    method_decorators = [authorize_user]

    def get(self, uuid):
        logging.info('[API:GetUser] ID {}'.format(uuid))
        a_user = self.data_source.get_user(uuid)
        return a_user

    def put(self, uuid):
        user = self.data_source.get_user(uuid)
        if user:
            new_data = request.json
            for key in ['nickname', 'motto']:
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


class UserActivity(APIBase):
    method_decorators = [authorize_user]

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
                    msg = '500: Could not add activity to user {}!'.format(uuid)
                    err = 500
            else:
                msg = '400: Malformed User Activity!'
                err = 400
        else:
            msg = '404: User {} not found!'.format(uuid)
            err = 404

        logging.error('[API:PostActivity] ERROR: {}'.format(msg))
        return {'MESSAGE': msg}, err

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

app.config['JWT_SECRET_KEY'] = settings.STAKO_JWT_SECRET
jwt = JWTManager(app)

prefix = '/v1'
api.add_resource(Auth, '{}/auth/'.format(prefix))
api.add_resource(User, '{}/user/<uuid>/'.format(prefix))
api.add_resource(UserActivity, '{}/user/<uuid>/activity/'.format(prefix))

if __name__ == '__main__':
    app.run(debug=settings.STAKO_DEBUG)
