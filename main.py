#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from oauth2client import tools
from promise import Promise
import io, re

import constants, users, authorships, articles, sections, outquotes, media, drive

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

    art_folder = drive.get_file(r"(?i)art", 'folder', Issue['id'])
    photo_folder = drive.get_file(r"(?i)(photo\s?color)",
                                  'folder',
                                  Issue['id'])
    if not photo_folder:
        photo_folder = drive.get_file(r"(?i)(photo\s?b&?w)",
                                      'folder',
                                      Issue['id'])
    media_files = drive.get_children([art_folder['id'],
                                      photo_folder['id']],
                                     'image')

    imageName = drive.download_file(media_files[0])
    drive.post_media_file(imageName, {'medium[title]':'testing', 'medium[article_id]': 1, 'medium[user_id]': 1})

    return

    volume = 107  # int(raw_input('Volume (number): '))
    issue = 1  # int(raw_input('Issue: '))
    unprocessed_file_names = []

    # TODO if re.match(r'(?i)staff\s?ed', file['name']): article_data = articles.read_staff_ed(article_text)

    for section in drive.get_children(SBC['id'], 'folder'):

        section_id = sections.get_section_id_by_name(section['name'])
        section_articles = drive.get_children(section['id'], 'document')

        for file in section_articles:
            print('\n')

            file_unwanted = re.search(r"(?i)worldbeat|survey",
                                          file['name'])
            if file_unwanted:
                print(Fore.RED + Style.BRIGHT + file_unwanted.group().upper()
                      + ' skipped.' + Style.RESET_ALL)
                continue

            print(Fore.CYAN + Style.BRIGHT + section['name'].upper()
                  + Fore.BLUE + ' ' + file['name'] + Style.RESET_ALL, end=' ')
            article_text = drive.download_document(file)

            if articles.file_article_exists(article_text):
                print(Fore.RED + Style.BRIGHT + file['name'].encode("utf-8")
                      + ' already exists.' + Style.RESET_ALL)
                continue

            article_data = articles.read_article(article_text)

            if raw_input(Fore.GREEN + Style.BRIGHT + 'upload media? (y/n): '
                                 + Style.RESET_ALL) == 'y':
                media_data = choose_media(media_files,
                                          art_folder_id=art_folder['id'],
                                          photo_folder_id=photo_folder['id'])
            if type(article_data) is str:
                # read_article failed and returned file title
                unprocessed_file_names.append(file['name'])
                continue

            section_id = sections.choose_subsection(section_id) or section_id

            article_attributes = ['title', 'content', 'summary', 'content']
            article_post_data = {
                key: value for key, value in article_data.items()
                               if key in article_attributes
            }
            for attr in ('volume', 'issue', 'section_id'):
                article_post_data[attr] = int(locals()[attr])  # adds specified local variables

            article_promise = Promise(
                lambda resolve, reject:
                    resolve(articles.post_article(article_post_data))
            )\
                .then(lambda article_id:
                      users.post_contributors(article_id,
                                              article_data['contributors']))\
                .then(lambda authorship_data:
                      authorships.post_authorships(authorship_data))\
                .then(lambda article_id:
                      outquotes.post_outquotes(article_id,
                                               article_data['outquotes']))\
                .then(lambda article_id:
                      media.post_media(article_id, media_data))\
                .then(lambda article_id:
                      print(Fore.GREEN + Style.BRIGHT
                            + '\nSuccessfully wrote Article {}: {}.'
                                .format(article_id, article_post_data['title'])
                            + Style.RESET_ALL))
    if len(unprocessed_file_names) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessed_file_names, sep='\n')


def choose_media(media_files, art_folder_id, photo_folder_id):
    output = []
    while 1:
        media_data = {}

        while 1:
            filename = raw_input(Fore.GREEN + Style.BRIGHT
                                 + 'filename (press ENTER to exit): '
                                 + Style.RESET_ALL).strip()
            if filename == '':
                return output
            if filename[0] == '*':
                media_data['is_featured'] = True
                filename = filename[1:]
            media = next((media_file for media_file in media_files
                          if media_file['name'] == filename), None)
            if media is not None:
                media_data['file'] = media
                media_parent = media.get('parents', [None])[0]
                if media_parent is None:
                    raise ValueError(filename + ' has no parents.\n' + media)
                if media_parent['id'] == photo_folder_id:
                    media_data['type'] = 'photo'
                elif media_parent['id'] == art_folder_id:
                    media_data['type'] = 'art'
                else:
                    raise ValueError('The parents of {} are not the folders '
                                     + 'Art ({}) or Photo ({}).'
                                     .format(filename, art_folder_id,
                                             photo_folder_id))
                break
            print('No media matches filename {}.'.format(filename))

        for field in ['title', 'caption', 'artist_name']:
            while 1:
                field_input = raw_input(Fore.GREEN + Style.BRIGHT + field
                                        + ': ' + Style.RESET_ALL).strip()
                if field_input != '':
                    media[field] = field_input
                    break
                print(field + ' field cannot be empty.')

        output.append(media_data)


        # imageName = drive.download_file(drive.get_file


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
