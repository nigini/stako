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
    new_team_url = BASE_URL + 'teams/'
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


@app.route("/team/<tags>")
def team(tags='python'):
    tags_list = tags.split(';')
    #TODO define and change this to TEAM entity!!!
    questions = _get_questions(tags_list)
    if(len(questions) > 0):
        return render_template('team.html', tags=tags, questions=questions)
    return 'NO TAG TEAM WAS FOUND FOR: {}'.format(tags)


def _get_questions(tag_list, size=10):
    url = BASE_URL + 'teams/{}/'.format(';'.join(tag_list))
    questions = requests.get(url)
    if questions.status_code == 200:
        print(questions.json())
        if len(questions.json().items()) > 0:
            return list(questions.json().items())[0][1]
    return []
