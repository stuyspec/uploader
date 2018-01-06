from colorama import Fore, Back, Style
import requests
import constants
import utils

sections = []


def init():
    global sections
    print('[0%] Loading sections.\r'),  # comma lets next print overwrite.
    sections = requests.get(constants.API_SECTIONS_ENDPOINT).json()
    print('[100%] Loaded sections.')


def get_section_id(name):
    if name == 'A&E' or name == 'Arts and Entertainment':
        name = 'Arts & Entertainment'
    return next((
        s for s in sections
        if s['name'].lower() == name.lower()
    ))['id']


def choose_subsection(section_name):
    section_id = get_section_id(section_name)
    subsections = [
        section for section in sections if section['parent_id'] == section_id
    ]
    if len(subsections) == 0: # already a subsection
        return section_id
    print(Fore.GREEN + Style.BRIGHT + 'Optional subsection ->' +
          Style.RESET_ALL)
    for i in range(len(subsections)):
        print('  [{}] {}'.format(i, subsections[i]['name']))

    index_choice = 'default'
    while not utils.represents_int(index_choice):
        if index_choice == '':
            break
        index_choice = raw_input(Fore.GREEN + Style.BRIGHT +
                                 'subsection (leave blank if none): ' +
                                 Style.RESET_ALL)
    return section_id \
        if index_choice == '' \
        else subsections[int(index_choice)]['id']
