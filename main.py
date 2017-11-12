#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from oauth2client import tools
from promise import Promise
import io, re

import constants, users, authorships, articles, sections, outquotes, drive

args = None
try:
    import argparse
    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--local', help='post data to a specified port')
    args = parser.parse_args()
except ImportError:
    flags = None

from colorama import Fore, Back, Style
import colorama


def find_matching_folder_in(parent_id, files, name_pattern):
    parent_file = next((f for f in files if f['id'] == parent_id), None)
    if not parent_file:
        raise ValueError('No parent {} found.'.format(parent_id))
    if parent_file['mimeType'] != 'application/vnd.google-apps.folder':
        raise ValueError('File {} is not a folder.'
                         .format(parent_file['name']))
    return next((
        f for f in files if (f.get('parents', [None])[0] == parent_id
                             and re.match(name_pattern, f['name']))
    ), None)


def main():
    Issue = drive.get_file(r"Issue\s?1", 'folder')
    SBC = drive.get_file(r"SBC", 'folder', Issue['id'])
    SBC_folders = drive.get_children(SBC['id'], 'folder')

    art_folder = drive.get_file(r"(?i)art", 'folder', Issue['id'])
    photo_folder = drive.get_file(r"(?i)(photo\s?color)",
                                  'folder',
                                  Issue['id'])
    if not photo_folder:
        photo_folder = drive.get_file(r"(?i)(photo\s?b&?w)",
                                      'folder',
                                      Issue['id'])

    volume = 107  # int(raw_input('Volume (number): '))
    issue = 1  # int(raw_input('Issue: '))
    unprocessed_file_names = []

    for section in SBC_folders:

        section_id = sections.get_section_id_by_name(section['name'])
        section_articles = drive.get_children(section['id'], 'document')

        for file in section_articles:
            print('\n')
            file_unwanted = None
            for unwanted_keyword in ['worldbeat', 'survey']:
                if unwanted_keyword in file['name'].lower():
                    file_unwanted = file
                    print(Fore.RED + Style.BRIGHT + unwanted_keyword.upper()
                          + ' skipped.' + Style.RESET_ALL)
                    file_unwanted = file
            if file_unwanted:
                continue

            print(Fore.CYAN + Style.BRIGHT + section['name'].upper()
                  + Fore.BLUE + ' ' + file['name'] + Style.RESET_ALL, end=' ')
            article_text = drive.download_document(file)

            if articles.file_article_exists(article_text):
                print(Fore.RED + Style.BRIGHT + '{} already exists.'
                        .format(file['name'].encode("utf-8")) + Style.RESET_ALL)
                continue

            if article_text.count('%') > 10:  # possibly a survey
                survey_confirmation = ''
                is_survey = False
                while survey_confirmation == '':
                    survey_confirmation = raw_input((
                        Fore.RED + Style.BRIGHT +
                        'Is this article, with {} counts of "%", a survey? (y/n) '
                        + Style.RESET_ALL).format(article_text.count('%')))
                    if survey_confirmation == 'y':
                        print(Fore.RED + Style.BRIGHT + 'Survey skipped.')
                        unprocessed_file_names.append(file['name'])
                        is_survey = True
                        break
                    elif survey_confirmation == 'n':
                        break
                if is_survey:
                    continue  # continue to next file

            if re.match(r'(?i)staff\s?ed', file['name']):
                article_data = articles.read_staff_ed(article_text)
            else:
                article_data = articles.read_article(article_text)

            section_id = sections.choose_subsection(section_id) or section_id
            if type(article_data) is str:
                # read_article failed and returned file title
                unprocessed_file_names.append(file['name'])
                continue

            article_attributes = ['title', 'content', 'summary', 'content']
            article_post_data = {
                key: value for key, value in article_data.items()
                               if key in article_attributes
            }
            for attr in ('volume', 'issue', 'section_id'):
                article_post_data[attr] = int(locals()[attr])  # adds specified local variables

            print('\n')
            article_promise = Promise(
                lambda resolve, reject: resolve(articles.post_article(article_post_data))
            )\
                .then(lambda article_id:
                      users.post_contributors(article_id,
                                              article_data.get(
                                                  'contributors',
                                                  []
                                              )))\
                .then(lambda authorship_data:
                      authorships.post_authorships(authorship_data))\
                .then(lambda article_id:
                      outquotes.post_outquotes(article_id,
                                               article_data['outquotes']))\
                .then(lambda article_id:
                      print(Fore.GREEN + Style.BRIGHT
                            + '\nSuccessfully wrote Article {}: {}.'
                                .format(article_id, article_post_data['title'])
                            + Style.RESET_ALL))
    if len(unprocessed_file_names) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessed_file_names, sep='\n')


# NEEDS A BACK FUNCTION TODO
def get_folders_in_file(files, parent_folder_id):
    folders = {}
    for file in files:
        # check if parent folder is SBC and file type is folder
        if file.get('parents', [None])[0] == parent_folder_id and file.get(
                'mimeType') == 'application/vnd.google-apps.folder':
            folders[file['id']] = file['name']
    return folders


# DO NOT CHANGE THE ORDER OF THESE INIT'S
if __name__ == '__main__':
    colorama.init()
    if args.local is not None:
        constants.init('localhost:{}'.format(args.local))
    else:
        constants.init('not-deployed.yet')
    drive.init()
    sections.init()
    articles.init()
    users.init()
    print('\n')
    main()
