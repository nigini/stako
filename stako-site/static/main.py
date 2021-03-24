import settings

from flask import Flask
from flask import render_template

import requests
import logging

logging.basicConfig(level=logging.INFO)
BASE_URL = settings.QAW_API_URL
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"


@app.route("/teams/<tags>")
def teams(tags='python'):
    new_team_url = BASE_URL + 'team/'
    tags_list = tags.split(';')
    teams = _get_teams(tags_list)
    logging.info('[GET_TEAMS]: {}'.format(teams))
    return render_template('teams.html', tags=tags, teams=teams, newteamurl=new_team_url)


def _get_teams(tag_list, size=10):
    url = BASE_URL + 'teams/{}/'.format(';'.join(tag_list))
    teams = requests.get(url)
    result = []
    if teams.status_code == 200:
        result = teams.json()
    return result


@app.route("/team/<id>")
def team(id):
    team = _get_team(id)
    logging.info('[GET_TEAM] ID {}: {}'.format(id, team))
    if team:
        # TODO: ADD QUESTIONS!!!
        # TODO: ADD FACTS!!!
        return render_template('team.html', team=team)
    return 'OPS! NO TEAM WAS FOUND WITH ID {}. =('.format(id)

def _get_team(id):
    url = BASE_URL + 'team/{}/'.format(id)
    team = requests.get(url)
    result = None
    if team.status_code == 200:
        result = team.json()
    return result

def _get_questions(tag_list, size=10):
    url = BASE_URL + 'teams/{}/'.format(';'.join(tag_list))
    questions = requests.get(url)
    if questions.status_code == 200:
        print(questions.json())
        if len(questions.json().items()) > 0:
            return list(questions.json().items())[0][1]
    return []
