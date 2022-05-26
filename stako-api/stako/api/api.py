import requests
from flask import Flask, request
import flask_restful
from flask_restful import Resource, Api
import logging
from urllib.parse import urlparse
from functools import wraps
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, verify_jwt_in_request, decode_token
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import ExpiredSignatureError
import stako.settings as settings
from stako.api.data.mongo import APIMongo, ExperimentMongo
import stako.api.data.data as stako_data
from stako.api.data.data import StakoActivity, Experiment
from flask_cors import CORS


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
            except (ExpiredSignatureError, NoAuthorizationError):
                flask_restful.abort(401)
        else:
            flask_restful.abort(400)
    return wrapper


class APIBase(Resource):
    def __init__(self):
        self.data_source = APIMongo(settings)
        self.experiment = ExperimentMongo(settings)


class Auth(APIBase):
    TESTER_EMAIL = 'user@somewhere.com'

    def return_token(self, email):
        user = self.experiment.get_participant(email)
        if 'uuid' in user.keys():
            # TODO: Should check for existing one first?
            token = self._get_token(user.get('uuid'))
            if token:
                return token, 200
            else:
                return {'MESSAGE': 'Non Authorized: User with email {} is not a registered STAKO user!'
                        .format(email)}, 401

    @staticmethod
    def _get_token(uuid):
        token = create_access_token(identity=uuid)
        token_exp = decode_token(token)['exp']
        return {'uuid': uuid, 'access_token': token, 'expiration': token_exp}


class AuthStako(Auth):
    TESTER_EMAIL = 'user@stako.com'

    def get(self):
        data = request.args
        if data and ('email' in data.keys()) and ('pass_key' in data.keys()):
            if self._validate_passkey(data.get('email'), data.get('pass_key')):
                return self.return_token(data.get('email'))
            return {'MESSAGE': 'Invalid user/passkey pair.'}, 401
        else:
            return {'MESSAGE': 'Malformed auth request: need "email" and "token" params.'}, 400

    def _validate_passkey(self, email, passkey):
        if email == AuthStako.TESTER_EMAIL:
            return True
        else:
            participant = self.experiment.get_participant(email)
            if participant and participant['pass_hash'] == stako_data.string_hash(passkey):
                return True
        return False


class AuthGoogle(Auth):
    GOOGLE_OAUTH_INFO = 'https://oauth2.googleapis.com/tokeninfo?access_token={}'
    TESTER_EMAIL = 'user@google.com'

    def get(self):
        data = request.args
        if data and ('email' in data.keys()) and ('google_id' in data.keys()) and ('token' in data.keys()):
            valid = self._validate_token(data.get('email'), data.get('google_id'), data.get('token'))
            if valid:
                return self.return_token(data.get('email'))
            else:
                return {'MESSAGE': 'Non Authorized: Invalid OAUTH token for provided email!'}, 401
        else:
            return {'MESSAGE': 'Malformed auth request: need "email" and "token" params.'}, 400

    def _validate_token(self, email, google_id, oauth_token):
        logging.info('[API:AUTHORIZE] EMAIL {}, GID {}, and TOKEN {}.'.format(email, google_id, oauth_token))
        if settings.STAKO_TEST:
            return email.lower() == AuthGoogle.TESTER_EMAIL
        else:
            r_url = AuthGoogle.GOOGLE_OAUTH_INFO.format(oauth_token)
            response = requests.get(r_url)
            if response.status_code == 200:
                data = response.json()
                logging.info('[API:AUTHORIZED?] {}'.format(data))
                if 'error' not in data.keys():
                    app = data['aud']
                    user = data['sub']
                    if app in settings.STAKO_OAUTH_ID and user == google_id:
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


class UserExperiment(APIBase):
    method_decorators = [authorize_user]

    def get(self, uuid):
        participant = self.experiment.get_participant(uuid, 'uuid')
        if participant:
            p_exp = {'uuid': uuid}
            if 'experiments' in participant.keys():
                p_exp['experiments'] = Experiment.get_experiments_hash(participant['experiments'])
            else:
                p_exp['experiments'] = {}
            return p_exp
        else:
            msg = '404: User {} not found!'.format(uuid)
            err = 404

        logging.error('[API:UserExperiment] ERROR: {}'.format(msg))
        return {'MESSAGE': msg}, err


class UserActivity(APIBase):
    method_decorators = [authorize_user]

    def get(self, uuid):
        user = self.data_source.get_user(uuid)
        act = []
        if user:
            start = request.args.get('date_start', None)
            end = request.args.get('date_end', None)
            act = self.data_source.get_activities(uuid, start_date=start, end_date=end)
        to_return = {'activities': act}
        return to_return

    def post(self, uuid):
        return self.put(uuid)

    def put(self, uuid):
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


class UserNotification(APIBase):
    method_decorators = [authorize_user]

    def get(self, uuid):
        return {
            'uuid': uuid,
            'notifications': self.data_source.get_notifications(uuid)
        }


if settings.STAKO_DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
api = Api(app)
CORS(app)

app.config['JWT_SECRET_KEY'] = settings.STAKO_JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = settings.STAKO_JWT_TOKEN_EXPIRES
jwt = JWTManager(app)

prefix = '/v1'
api.add_resource(AuthGoogle, '{}/auth/google'.format(prefix))
api.add_resource(AuthStako, '{}/auth/stako'.format(prefix))
api.add_resource(User, '{}/user/<uuid>/'.format(prefix))
api.add_resource(UserActivity, '{}/user/<uuid>/activity/'.format(prefix))
api.add_resource(UserExperiment, '{}/user/<uuid>/experiment/'.format(prefix))
api.add_resource(UserNotification, '{}/user/<uuid>/notification/'.format(prefix))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=settings.STAKO_DEBUG)
