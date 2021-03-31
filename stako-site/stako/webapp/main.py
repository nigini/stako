import stako.webapp.settings as settings
from stako.webapp.data import user as stako_user

from flask import Flask
from flask import request
from flask import render_template
import logging
from flask_cors import CORS

if settings.STAKO_DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
BASE_URL = settings.STAKO_API_URL
app = Flask(__name__)
CORS(app)


@app.route("/")
def hello():
    return render_template('hello.html')


@app.route("/user/<uuid>/activity")
def user_activities(uuid):
    logging.info('ACTIVITIES FOR {}'.format(uuid))
    token = request.headers.get('token')
    if token:
        user = stako_user.get_user(uuid, token)
        if user:
            act = stako_user.get_activities(uuid, token)
            history = []
            if act and ('activities' in act):
                history = act['activities']
            logging.debug('ACTIVITY FOR USER: {}'.format(user))
            return render_template('user/activity.html', user={'uuid': uuid, 'nickname': user['nickname']},
                                   activity=history)
    return render_template('error.html',
                           message='It is likely your request does not have a valid authorization token.')
