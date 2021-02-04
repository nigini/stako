import settings
import requests
import json
import logging
from data import StakoActivity

API_SO_QS = 'https://api.stackexchange.com/2.2/questions/{}?site=stackoverflow&key={}&pagesize=100'


class Question:
    def __init__(self):
        self.testing = settings.STAKO_TEST

    def get_questions(self, question_ids):
        to_return = {}
        if len(question_ids) > 0:
            for q in self._get_so_questions(question_ids):
                to_return[str(q['question_id'])] = q
        return to_return

    @staticmethod
    def get_visits_questions_keys(user_activities):
        questions = {}
        for act in user_activities:
            if act['type'] == StakoActivity.ACTIVITY_TYPE_SO_VISIT:
                url_s = act['url'].split('/')
                if url_s[2].lower() == 'stackoverflow.com' and url_s[3].lower() == 'questions' and url_s[4].isdigit():
                    questions[url_s[4]] = act
        return questions

    def _get_so_questions(self, question_ids):
        if not self.testing:
            ids_str = ''
            for q in question_ids:
                if q.isdigit():
                    ids_str += q + ';'
            r_url = API_SO_QS.format(ids_str[:-1], settings.SO_API_KEY)
            response = requests.get(r_url)
            if response.status_code == 200:
                return response.json()['items']
        else:
            return Question._test_questions(question_ids)

    @staticmethod
    def _test_questions(question_ids):
        logging.info('[SO:GetQuestions] USING MOCK DATA!')
        with open('test_stackoverflow.json') as so_data_file:
            so_data = json.load(so_data_file)['questions']
            to_return = []
            for q in so_data:
                if str(q['question_id']) in question_ids:
                    print(q['question_id'])
                    to_return.append(q)
            return to_return

