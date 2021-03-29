import requests
import logging
from datetime import datetime, timezone, timedelta
import stako.webapp.settings as settings

API_URL = settings.STAKO_API_URL
GET_USER_URL = API_URL + 'user/{}/'
GET_ACTIVITY_URL = API_URL + 'user/{}/activity/?date_start={}&date_end={}'


def _request_data(url, token):
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error('[STAKO:WEBAPP] REQUEST: {}, RESPONSE: {}'.format(url, response.text))
        return {}


def get_user(uuid, token):
    url = GET_USER_URL.format(uuid)
    return _request_data(url, token)


def get_activities(uuid, token, week_start=None):
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    if not week_start:
        past_week = timedelta(days=7)
        week_start = now-past_week
    url = GET_ACTIVITY_URL.format(uuid, int(week_start.timestamp()), int(now.timestamp()))
    return _request_data(url, token)

