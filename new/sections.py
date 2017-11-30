from colorama import Fore, Back, Style
import requests
import constants

sections = []


def init():
    global sections
    print('[0%] Loading sections.\r'),  # comma lets next print overwrite.
    sections = requests.get(constants.API_SECTIONS_ENDPOINT).json()
    print('[100%] Loaded sections.')


def get_section_id(name):
    return next((
        s for s in sections
        if (s['name'].lower() == name.lower()
            or name == 'A&E' and s['name'] == "Arts & Entertainment")
    ))['id']