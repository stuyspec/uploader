from os.path import join, dirname
from dotenv import load_dotenv
from colorama import Fore, Back, Style
import constants
import requests
import json
import os


headers = {
    'Content-Type': 'application/json'
}


def init():
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)


def sign_in():
    user_auth = requests.post(
        constants.API_AUTH_ENDPOINT + '/sign_in',
        data=json.dumps({
            'email': os.environ.get("EMAIL"),
            'password': os.environ.get("PASSWORD")
        }),
        headers=headers
    )
    user_auth.raise_for_status()
    user_auth_headers = user_auth.headers
    for key in ['access-token', 'uid', 'client', 'expiry']:
        headers[key] = user_auth_headers[key]
    print(Fore.YELLOW + Style.BRIGHT
          + 'Signed in with UID {uid}.'.format(**headers) + Style.RESET_ALL)


def update_headers(response):
    print('== Updating headers ' + '=' * 30)
    try:
        headers['access-token'] = response.headers['access-token']
        print(Fore.BLUE + '  access-token -> ' + headers['access-token'])
        headers['expiry'] = response.headers['expiry']
        print('  expiry -> ' + headers['expiry'])
    except KeyError as e:
        raise ValueError(
            'Response object {} does not have access-token or expiry'.format(
                response))