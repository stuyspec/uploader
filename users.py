from promise import Promise
from colorama import Fore, Back, Style

import requests
import json
import constants, backups, utils

users = []
user_roles = []
roles = []

def init():
    """Initiates globals with API data"""
    global users, user_roles, roles
    users = requests.get(constants.API_USERS_ENDPOINT).json()
    user_roles = requests.get(constants.API_USER_ROLES_ENDPOINT).json()
    roles = requests.get(constants.API_ROLES_ENDPOINT).json()


# TODO: this needs you to put in default password

def update_user(user_id, data):
    update_response = requests.put(constants.API_USERS_ENDPOINT
                                   + '/{}'.format(user_id),
                                   data=json.dumps(data),
                                   headers={
                                       'Content-Type': 'application/json'
                                   })
    update_response.raise_for_status()
    return update_response.json().get('id', -1)


def make_contributor(user_id):
    contributor_role_id = next(
        (r for r in roles if r['title'] == 'Contributor'),
        -1
    )['id']
    user_role_response = requests.post(constants.API_USER_ROLES_ENDPOINT,
                                       data=json.dumps({
                                           'user_id': user_id,
                                           'role_id': contributor_role_id
                                       }),
                                       headers={
                                           'Content-Type': 'application/json'
                                       })
    user_role_response.raise_for_status()
    return user_role_response.json().get('id', -1)


def user_is_contributor(user_id):
    print(3)
    contributor_role_id = next(
        (r for r in roles if r['title'] == 'Contributor'),
        -1
    )['id']
    for u in user_roles:
        print(u)
        if u['user_id'] == user_id and u['role_id'] == contributor_role_id:
            return True
    return False


def get_contributor_id(name):
    """Checks if contributor exists."""
    contributor_role_id = next(
        (r for r in roles if r['title'] == 'Contributor'),
        -1
    )['id']
    for u in users:
        print(u)
        if ('{first_name} {last_name}'.format(**u) == name
            and next((
                user_role for user_role in user_roles
                if (user_role['user_id'] == u['id']
                    and user_role['role_id'] == contributor_role_id)
            ), None)):
            print(u)
            return u['id']
    return -1


def label_existing_contributors(contributors):
    """Returns contributors in the form [(name, contributor_id)]"""
    return [
        (c, get_contributor_id(c))
        for c in contributors
    ]


def authenticate_new_user(name_dict):
    email = backups.get_email_by_name(name_dict)
    while not email:
        email = raw_input(
            (Fore.MAGENTA + Style.BRIGHT + 'no email found for '
            + '{firstname} {lastname}. email: '.format(**name_dict)
            + Style.RESET_ALL))
    password = utils.generate_password(16)  # generates password of length 16
    auth_params = {
        'email': backups.get_email_by_name(name_dict),
        'password': password,
        'password_confirmation': password,
    }
    devise_response = requests.post(constants.API_AUTH_ENDPOINT,
                                    data=json.dumps(auth_params),
                                    headers={
                                        'Content-Type': 'application/json'
                                    })
    devise_response.raise_for_status()
    devise_json = devise_response.json().get('data', {})
    return devise_response.json().get('data', {}).get('id', -1)


def name_to_dict(name):
    name = name.split(' ')
    if len(name) < 2: name *= 2  # first and last name are the same
    return {
        'first_name': ' '.join(name[:-1]),
        'last_name': name[-1]
    }


def create_contributor(name):
    name_dict = name_to_dict(name)
    create_contributor_promise = Promise(
        lambda resolve, reject: resolve(authenticate_new_user(name_dict))
    )\
        .then(lambda user_id: update_user(user_id, name_dict))\
        .then(lambda user_id: make_contributor(user_id))
    print(Fore.YELLOW + Style.BRIGHT + 'Created new contributor {}.'
          .format(name) + Style.RESET_ALL)
    return create_contributor_promise.get()


def post_contributors(article_id, contributors):
    contributors = label_existing_contributors(contributors)
    contributor_ids = []
    for name, contributor_id in contributors:
        if contributor_id == -1:
            contributor_ids.append(create_contributor(name))
        else:
            contributor_ids.append(contributor_id)
    print(contributor_ids)
    return (
        article_id,
        contributor_ids
    )
