import uuid
from datetime import datetime

from _pytest.mark import get_empty_parameterset_mark


class StakoUser:
    @staticmethod
    def get_empty_user():
        return {
            "nickname": "",
            "uuid": str(uuid.uuid4()),
            "motto": "",
            "start_date": int(datetime.timestamp(datetime.utcnow())),
            "activity": {
                "weekly_summary": StakoUser.get_empty_weekly_summary(),
                "updated": int(datetime.timestamp(datetime.utcnow()))
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
            'timestamp': int(datetime.timestamp(datetime.utcnow())),
            'data': {}
        }
