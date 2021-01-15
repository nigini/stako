import settings
from flask import Flask, request
from flask_restful import Resource, Api
from datetime import datetime
import logging
from mongo import APIMongo, ExperimentMongo, DataStructure
from random import random
from urllib.parse import urlparse


class APIBase(Resource):
    def __init__(self):
        if app.testing:
            settings.MONGODB_NAME = settings.MONGODB_NAME_TEST
        self.data_source = APIMongo(settings)
        self.auth = ExperimentMongo(settings)

    @staticmethod
    def get_tag_list(tags_string):
        tag_list = tags_string.split(';')
        tag_list.sort()
        return tag_list


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
        new_user = DataStructure.get_empty_user()
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
    ACTIVITY_TYPE_SO_VISIT = 'stackoverflow:visit'
    ACTIVITY_TYPE_SO_MOUSE = 'stackoverflow:mouse'
    ACTIVITY_TYPE_SO_CLICK = 'stackoverflow:click'

    ACTIVITY_TYPES = {}
    ACTIVITY_TYPES[ACTIVITY_TYPE_SO_VISIT] = []
    ACTIVITY_TYPES[ACTIVITY_TYPE_SO_MOUSE] = ['ELEMENT', 'DURATION']
    ACTIVITY_TYPES[ACTIVITY_TYPE_SO_CLICK] = ['ELEMENT']


    def post(self, uuid):
        user = self.data_source.get_user(uuid)
        if user:
            request_data = request.json
            logging.info('[API:PostActivity] REQUEST DATA: {}'.format(request_data))
            valid_data = self.validate_activity_data(request_data)
            if valid_data:
                new_activity = self.get_empty_activity()
                new_activity['UUID'] = uuid
                new_activity['URL'] = valid_data.pop('URL')
                new_activity['TYPE'] = valid_data.pop('TYPE')
                new_activity['DATA'] = valid_data
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
        activity_type = request_data.pop('TYPE', None)
        url = request_data.pop('URL', None)
        if activity_type and url:
            valid_url = urlparse(url)
            if url and all([valid_url.scheme, valid_url.netloc, valid_url.path]):
                if activity_type in self.ACTIVITY_TYPES:
                    activity = {'URL': url, 'TYPE': activity_type}
                    for entry in self.ACTIVITY_TYPES[activity_type]:
                        try:
                            activity[entry] = request_data.pop(entry)
                        except KeyError:
                            return None
                    return activity
        return None

    @staticmethod
    def get_empty_activity():
        return {
            'UUID': '',
            'URL': '',
            'TYPE': '',
            'TIMESTAMP': int(datetime.timestamp(datetime.utcnow())),
            'DATA': {}
        }


class TeamList(APIBase):
    def get(self, tags):
        logging.info('[API:TeamList] Tags {}'.format(tags))
        teams = self.data_source.get_teams(self.get_tag_list(tags))
        return teams


class TeamByID(APIBase):
    def get(self, id):
        logging.info('[API:GetTeam] ID {}'.format(id))
        team = self.data_source.get_team(id)
        if team is None:
            return {}
        return team


class NewTeam(APIBase):
    def post(self):
        # TODO Check tags existence
        tags = request.form.get('tags')
        name = request.form.get('name')
        # TODO Add current user as member
        logging.info('[API:PostTeam] Team {}: {}'.format(name, tags))
        team = self.get_empty_team()
        team['tags'] = self.get_tag_list(tags)
        team['name'] = name
        self.data_source.save_team(team)

    @staticmethod
    def get_empty_team():
        return {
            'name': '',
            'id': str(random())[2:],
            'tags': [],
            'participants': [],
            'facts': {
                'num_posts': 0,
            },
            'last_updated': int(datetime.timestamp(datetime.utcnow())),
        }


logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
api = Api(app)

prefix = '/v1'
api.add_resource(User, '{}/user/<uuid>/'.format(prefix))
api.add_resource(NewUser, '{}/user/'.format(prefix))
api.add_resource(UserActivity, '{}/user/<uuid>/activity/'.format(prefix))
api.add_resource(TeamList, '{}/teams/<tags>/'.format(prefix))
api.add_resource(TeamByID, '{}/team/<id>/'.format(prefix))
api.add_resource(NewTeam, '{}/team/'.format(prefix))

if __name__ == '__main__':
    app.run(debug=settings.DEBUG)
