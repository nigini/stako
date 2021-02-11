import sys
import os
from datetime import datetime
import argparse

sys.path.append(os.getcwd() + '/..')
import settings
from mongo import APIMongo, ExperimentMongo, UserSummary

api = APIMongo(settings)
exp = ExperimentMongo(settings)
sum = UserSummary(settings)


def add_user(user_email, role):
    # TODO: Check invalid email format
    uuid = exp.add_participant(user_email)
    if uuid:
        print("Added participant {}.".format(user_email))
        added = exp.add_participant_role(user_email, role)
        if added:
            print("Added role {} to participant {}.".format(role, user_email))
        else:
            print("FAILED to add role {} to participant {}.".format(role, user_email))
    else:
        print("FAILED to add participant {}.".format(user_email))


def update_all(force_restart=False, timestamp=None):
    print("===========================================================")
    print("USERS UPDATE: {}".format(datetime.now()))
    print("===========================================================")
    accounts = exp.get_all()
    for a in accounts:
        user = api.get_user(a['uuid'])
        if not timestamp:
            timestamp = user['activity']['updated']
        result = sum.update_user(user['uuid'], force_restart, timestamp)
        print("Updated user {}: {}".format(user['uuid'], result))


parser = argparse.ArgumentParser(description='EXPERIMENT PARTICIPANTS MANAGEMENT SCRIPT')
subparsers = parser.add_subparsers(help='Commands', dest='command')

update_c = subparsers.add_parser('update', help='Updates weekly activities summary.')
update_c.add_argument('--uuid', help='Updates the participant weekly activities with given UUID.')
update_c.add_argument('--all', action='store_true', help='Updates all participants weekly activities.')
update_c.add_argument('--refresh', action='store_true', help='Force recreating weekly activities.')
update_c.add_argument('--timestamp',
                      help='Updates summary with activities that happened after the UTC TIMESTAMP in seconds.')

create_c = subparsers.add_parser('create', help='Create new research participant')
create_c.add_argument('email', help='Email account used to authenticate user.')
create_c.add_argument('--role', help='A user role: [<participant>, researcher, tester].', default='participant')


args = parser.parse_args()
if args.command == 'create':
    add_user(args.email, args.role)
elif args.command == 'update':
    if args.uuid:
        print('TODO: IMPLEMENT UPDATE INDIVIDUAL USER.')
    elif args.all:
        update_all(args.refresh, args.timestamp)
    else:
        print('For <UPDATE>, please provide a <UUID> or <ALL>!')
else:
    print('SOMETHING\'S WRONG WITH ARGPARSE! No command {} found!'. format(args['command']))
