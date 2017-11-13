from colorama import Fore, Back, Style

import requests
import constants, utils

sections = []


def init():
    """Initiates globals with API data"""
    global sections
    print('[0%] Loading sections.\r'), # comma lets next print overwrite.
    sections = requests.get(constants.API_SECTIONS_ENDPOINT).json()
    print('[100%] Loaded sections.')


def choose_subsection(section_id):
    subsections = [
        section for section in sections if section['parent_id'] == section_id
    ]
    if len(subsections) == 0 or subsections[0]['name'] == 'Staff Editorials':
        return section_id
    print(Fore.GREEN + Style.BRIGHT +
          'Optional subsection ->'
          + Style.RESET_ALL)
    for i in range(len(subsections)):
        print('  [{}] {}'.format(i, subsections[i]['name']))

    index_choice = 'default'
    while not utils.represents_int(index_choice):
        if index_choice == '':
            break
        index_choice = raw_input(Fore.GREEN + Style.BRIGHT
                                 + 'subsection (leave blank if none): '
                                 + Style.RESET_ALL)
    return section_id \
        if index_choice == '' \
        else subsections[int(index_choice)]['id']


def get_section_id_by_name(section_name):
    return next(
        (s for s in sections
         if (s['name'].lower() == section_name.lower() or
             section_name == 'A&E'
             and s['name'] == "Arts & Entertainment")
         ),
        {}
    ).get('id', -1)