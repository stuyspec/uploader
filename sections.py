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
        section for section in sections if section['parent_id'] == section_id
    ]
    print(Fore.GREEN + Style.BRIGHT +
          'Optional subsections (choose subsections like "p/q/r")-> '
          + Style.RESET_ALL)
    for i in range(len(subsections)):
        print('  [{}] {}'.format(i, subsections[i]['name']))
    index_choices = raw_input(Fore.GREEN + Style.BRIGHT + 'subsections: '
                             + Style.RESET_ALL)
    if index_choices != '':
        return [
            subsections[int(i)]['id'] for i in index_choices.split('/')
        ]

def get_section_name_by_id(section_name):
    return next(
        (s for s in sections
         if (s['name'].lower() == section_name.lower() or
             section_name == 'A&E'
             and s['name'] == "Arts & Entertainment")
         ),
        {}
    ).get('id', -1)