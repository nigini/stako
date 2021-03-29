import requests
from datetime import datetime, timezone
import stako.webapp.settings as settings

API_URL = settings.STAKO_API_URL
GET_USER_URL = API_URL + '/user/{}/'
GET_ACTIVITY_URL = API_URL + '/user/{}/activity?year={}&week={}'


def _request_data(url, token):
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }
    response = requests.get(url, headers=headers)
    return response.json()


def get_user(uuid, token):
    url = GET_USER_URL.format(uuid)
    return _request_data(url, token)


def get_activities(uuid, token, year=None, week=None):
    now = datetime.utcnow().replace(tzinfo=timezone.utc).isocalendar()
    if not year:
        year = now[0]
    if not week:
        week = now[1]
    url = GET_ACTIVITY_URL.format(uuid, year, week)
    return _request_data(url, token)

