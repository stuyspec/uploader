from promise import Promise
from colorama import Fore, Back, Style
from slugify import slugify

import requests
import json
import constants, utils
import ast

users = []
user_roles = []
roles = []
backup_users = []
wp_user_dict = {}


def init():
    """Initiates globals with API data"""
    print('[0%] Loading users.\r'),  # comma lets next print overwrite.
    global users, user_roles, roles, backup_users, backup_user_dict
    users = requests.get(constants.API_USERS_ENDPOINT).json()
    user_roles = requests.get(constants.API_USER_ROLES_ENDPOINT).json()
    roles = requests.get(constants.API_ROLES_ENDPOINT).json()
    with open('backups/wp-users-backup.txt', 'r') as wp:
        backup_user_dict = ast.literal_eval(wp.read())
    with open('backups/wp-users-backup.txt', 'r') as wp, \
        open('backups/drive-features-writers-2017-2018.txt', 'r') \
                as features, \
        open('backups/drive-opinions-writers-2017-2018.txt', 'r') as opinions:
        backup_users = ast.literal_eval(wp.read()).values() \
                       + ast.literal_eval(features.read()) \
                       + ast.literal_eval(opinions.read())
    print('[100%] Loaded users.')


def get_email_by_name(name_dict):
    for user in backup_users:
        if (name_dict['first_name'] == user['firstname']
            and name_dict['last_name'] == user['lastname']):
            return user['email']
    raise LookupError('no email found')


def update_user(user_id, data):
    update_response = requests.put(constants.API_USERS_ENDPOINT
                                   + '/{}'.format(user_id),
                                   data=json.dumps(data),
                                   headers={
                                       'Content-Type': 'application/json'
                                   })
    update_response.raise_for_status()
    updated_user_json = update_response.json()
    global users
    users.append(updated_user_json)
    return updated_user_json.get('id', -1)


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
    user_role_json = user_role_response.json()
    global user_roles
    user_roles.append(user_role_json)
    return user_id


def get_contributor_id(name):
    """Checks if contributor exists."""
    contributor_role_id = next(
        (r for r in roles if r['title'] == 'Contributor'),
        -1
    )['id']
    for u in users:
        if u['last_name'] == '' and u['first_name'] == name:
            # the case for "The {section_name} Department"
            print(u)
            return u['id']
        if ('{first_name} {last_name}'.format(**u) == name
            and next((
                user_role for user_role in user_roles
                if (user_role['user_id'] == u['id']
                    and user_role['role_id'] == contributor_role_id)
                ), None)):
            return u['id']
    return -1


def label_existing_contributors(contributors):
    """Returns contributors in the form [(name, contributor_id)]"""
    return [
        (c, get_contributor_id(c))
        for c in contributors
    ]


def authenticate_new_user(name_dict):
    try:
        email = get_email_by_name(name_dict)
    except LookupError:
        email = ''
        while email == '':
            email = raw_input(
                (Fore.YELLOW + Style.BRIGHT + 'no email found for '
                + '{first_name} {last_name}. '.format(**name_dict) + Fore.GREEN
                + 'email: ' + Style.RESET_ALL))
    password = utils.generate_password(16)  # generates password of length 16
    auth_params = {
        'email': email,
        'password': password,
        'password_confirmation': password,
    }
    devise_response = requests.post(constants.API_AUTH_ENDPOINT,
                                    data=json.dumps(auth_params),
                                    headers={
                                        'Content-Type': 'application/json'
                                    })
    devise_response.raise_for_status()
    print(Fore.YELLOW + Style.BRIGHT
          + 'Authenticated new user with e-mail {}.'.format(email)
          + Style.RESET_ALL)
    return devise_response.json().get('data', {}).get('id', -1)


def name_to_dict(name):
    name = name.split(' ')
    if len(name) < 2: name *= 2  # first and last name are the same
    return {
        'first_name': ' '.join(name[:-1]),
        'last_name': name[-1]
    }


def create_contributor(name):
    name_dict = utils.merge_two_dicts(
        name_to_dict(name),
        {'slug': slugify(name)}
    )

    create_contributor_promise = Promise(
        lambda resolve, reject: resolve(authenticate_new_user(name_dict))
    )\
        .then(lambda user_id: update_user(user_id, name_dict))\
        .then(lambda user_id: make_contributor(user_id))\
        .then(lambda user_id: user_id)
    return create_contributor_promise.get()


def post_contributors(article_id, contributors):
    contributors = label_existing_contributors(contributors)
    contributor_ids = []
    for name, contributor_id in contributors:
        if contributor_id == -1:
            new_contributor_id = create_contributor(name)
            contributor_ids.append(new_contributor_id)
            print(Fore.YELLOW + Style.BRIGHT + 'Created Contributor #{}: {}.'
                    .format(new_contributor_id, name) + Style.RESET_ALL)

        else:
            contributor_ids.append(contributor_id)
            print(Fore.YELLOW + Style.BRIGHT + 'Confirmed Contributor #{}: {}.'
                  .format(contributor_id, name) + Style.RESET_ALL)
    print('\n')
    return (
        article_id,
        contributor_ids
    )


def clean_content(content):
    content = content.replace('<span style="font-weight: 400;">', "<p>")
    content = content.replace("</span>\r\n\r\n", "</p>")
    return content

def summary(content):
    content = clean_content(content).replace("<p>","").replace("</p>","")
    return " ".join(content.split()[:24]) + "... "

def contributors(authors):
    contributors_list = []
    return contributors_list

def read_article_backup(article_dict):
    info = {}
    wp_entry = article_dict.values()[0]
    info["title"] = wp_entry["title"]
    info["contributors"] = contributors(wp_entry["authors"])
    info["summary"] = summary(wp_entry["content"])
    return info
