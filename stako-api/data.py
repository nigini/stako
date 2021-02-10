import uuid
from datetime import datetime, timezone
import hashlib


def get_utc_timestamp():
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    return int(now.timestamp())


class Experiment:
    ROLES = ['participant', 'researcher', 'tester']
    EXPERIMENTS = {
        "test": ['group_a', 'group_b', 'control']
    }

    def __init__(self, settings):
        Experiment.EXPERIMENTS = settings.STAKO_EXPERIMENTS

    @staticmethod
    def _hash_string(str):
        return hashlib.sha256(str.encode()).hexdigest()

    @staticmethod
    def get_experiments_hash(experiments):
        result = {}
        for exp in experiments.keys():
            exp_hash = Experiment._hash_string(exp)
            result[exp_hash] = Experiment._hash_string(experiments[exp])
        return result

    @staticmethod
    def get_empty_user():
        return {
            'uuid': str(uuid.uuid4()),
            'email': '',
            'roles': [],
            'experiments': {}
        }


class StakoUser:
    @staticmethod
    def get_empty_user():
        return {
            "nickname": "",
            "uuid": str(uuid.uuid4()),
            "motto": "",
            "start_date": get_utc_timestamp(),
            "activity": {
                "weekly_summary": StakoUser.get_empty_weekly_summary(),
                "updated": get_utc_timestamp()
            }
        }

    @staticmethod
    def get_empty_weekly_summary(year='1970', week='1'):
        return {
            year: {  # YEAR
                week: {  # ISO_WEEK
                    "top_tags": {
                        "top_tag": {
                            "pages_visited": 0
                        },
                    },
                    "pages_visited": 0
                }
            }
        }


class StakoActivity:

    ACTIVITY_TYPE_SO_VISIT = 'stackoverflow:visit'
    ACTIVITY_TYPE_SO_MOUSE = 'stackoverflow:mouse'
    ACTIVITY_TYPE_SO_CLICK = 'stackoverflow:click'

    ACTIVITY_TYPES = {}
    ACTIVITY_TYPES[ACTIVITY_TYPE_SO_VISIT] = []
    ACTIVITY_TYPES[ACTIVITY_TYPE_SO_MOUSE] = ['element', 'duration']
    ACTIVITY_TYPES[ACTIVITY_TYPE_SO_CLICK] = ['element']

    @staticmethod
    def get_empty_activity():
        return {
            'uuid': '',
            'url': '',
            'type': '',
            'timestamp': get_utc_timestamp(),
            'data': {}
        }


class StakoToken:
    TEST_KEY = 'ABCD_1234567890'

    @staticmethod
    def get_new_token():
        return {
            'uuid': '',
            'key': StakoToken.TEST_KEY,
            'expiration': get_utc_timestamp() + (1*24*60*60) #Expires in one day!
        }
