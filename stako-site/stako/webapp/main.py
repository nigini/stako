import stako.webapp.settings as settings
from stako.webapp.data import user as stako_user

from flask import Flask
from flask import request
from flask import render_template
import logging

if settings.STAKO_DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
BASE_URL = settings.STAKO_API_URL
app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('hello.html')

@app.route("/user/<uuid>/activity")
def user_activities(uuid):
    logging.info('ACTIVITIES FOR {}'.format(uuid))
    r_data = request.get_json()
    if r_data and ('token' in r_data.keys()):
        logging.debug('REQUEST DATA: {}'.format(r_data))
        user = stako_user.get_user(uuid, r_data.get('token'))
        if user:
            logging.debug('ACTIVITY FOR USER: {}'.format(user))
            return render_template('user/activity.html', user={'uuid': uuid, 'nickname': user['nickname']})
    return render_template('error.html',  message='It is likely your request does not have a valid authorization token.')
