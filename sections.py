from colorama import Fore, Back, Style

import requests
import constants

sections = []

def init():
    """Initiates globals with API data"""
    global sections
    sections = requests.get(constants.API_SECTIONS_ENDPOINT).json()


def choose_subsection(section_id):
    subsections = [
        section for section in sections if section.parent_id == section_id
    ]
    print('Optional subsections (choose subsections like "p/q/r")-> ')
    for i in range(len(subsections)):
        print('  [{}] {}'.format(i, subsections[i]))
    index_choices = raw_input(Fore.GREEN + Style.BRIGHT + 'subsections:'
                             + Style.RESET_ALL)
    if index_choices != '':
        return [
            subsections[int(i)]['id'] for i in index_choices.split('/')
        ]