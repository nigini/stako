import settings
import requests
from data import StakoActivity

API_SO_QS = 'https://api.stackexchange.com/2.2/questions/{}?site=stackoverflow&key={}'


class Question:
    @staticmethod
    def get_questions(question_ids):
        to_return = {}
        if len(question_ids) > 0:
            ids_str = ''
            for q in question_ids:
                if q.isdigit():
                    ids_str += q+';'
            r_url = API_SO_QS.format(ids_str[:-1], settings.SO_API_KEY)
            response = requests.get(r_url)
            if response.status_code == 200:
                for q in response.json()['items']:
                    to_return[str(q['question_id'])] = q
        return to_return

    @staticmethod
    def get_visits_questions_keys(user_activities):
        questions = {}
        for act in user_activities:
            if act['TYPE'] == StakoActivity.ACTIVITY_TYPE_SO_VISIT:
                url_s = act['URL'].split('/')
                if url_s[2].lower() == 'stackoverflow.com' and url_s[3].lower() == 'questions' and url_s[4].isdigit():
                    questions[url_s[4]] = act
        return questions
