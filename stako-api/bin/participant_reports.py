from datetime import datetime
import argparse
import sys
import pathlib
sys.path.append(pathlib.Path(__file__).parent.absolute().__str__() + '/..')
import stako.settings as settings
from stako.api.data.mongo import APIMongo, ExperimentMongo, UserSummary
from stako.api.data.data import StakoActivity

api = APIMongo(settings)
exp = ExperimentMongo(settings)
sum = UserSummary(settings)


def basic_report():
    print("===========================================================")
    print("BASIC ACT REPORT: {}".format(datetime.now()))
    print("===========================================================")
    accounts = exp.get_all()
    for a in accounts:
        acts = api.get_activities(a['uuid'])
        last_act = '0000-00-00' if len(acts) == 0 else str(datetime.fromtimestamp(acts[0]['timestamp']).date())
        print('{} : {} : {}'.format(a['email'], len(acts), last_act))


def act_listing(activity_type=StakoActivity.ACTIVITY_TYPE_SO_VISIT):
    print("===========================================================")
    print("ACTIVITY LISTING: {}".format(datetime.now()))
    print("ACTIVITY TYPE: {}".format(activity_type))
    print("===========================================================")
    accounts = exp.get_all()
    for a in accounts:
        print("===========================================================")
        print("ACCOUNT: {}".format(a['uuid']))
        print("===========================================================")
        acts = api.get_activities(a['uuid'], a_type=activity_type)
        for act in acts:
            act_date = str(datetime.fromtimestamp(act['timestamp']).date())
            act_data = act['data'] if 'data' in act.keys() else '{}'
            print("{}::{}::{}".format(act_date, act['url'], act_data))


parser = argparse.ArgumentParser(description='EXPERIMENT PARTICIPANTS MANAGEMENT SCRIPT')
subparsers = parser.add_subparsers(help='Commands', dest='command')

basic = subparsers.add_parser('basic', help='Show email : SO_visit_count : last_SO_visit.')
listing = subparsers.add_parser('listing', help='Lists all activities of an specified type.')
listing.add_argument('--type', help='An activity type: [<visit>, mouse_click, mouse_over].', default='visit')

args = parser.parse_args()
if args.command == 'basic':
    basic_report()
elif args.command == 'listing':
    if args.type == 'mouse_click':
        act_type = act_type = StakoActivity.ACTIVITY_TYPE_SO_CLICK
    elif args.type == 'mouse_over':
        act_type = act_type = StakoActivity.ACTIVITY_TYPE_SO_MOUSE
    else:
        act_type = StakoActivity.ACTIVITY_TYPE_SO_VISIT
    act_listing(act_type)
else:
    parser.print_help()
