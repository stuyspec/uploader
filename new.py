from __future__ import print_function
from promise import Promise
import httplib2
import os
import re
import io
import ast
import json
import requests
import constants
import sections
import articles
import config
import utils
import webbrowser
import users
import articles

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaIoBaseDownload
from slugify import slugify
from PIL import Image

from colorama import Fore, Back, Style
import colorama

try:
    import argparse

    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--local', help='post data to a specified port')
    parser.add_argument('-s', dest='scan', action='store_true',
                        help='first scan files for id adjustments')
    parser.add_argument('--window', dest='window', action='store_true',
                        help='open windows on Drive load')
    parser.set_defaults(window=False)
    parser.set_defaults(scan=False)

    flags = parser.parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Spec CLI'

DRIVE_STORAGE_FILENAME = 'files.in'
files = []

ISSUE_DATES = {
    '107': {
        '16': '2017-06-09',
        '15': '2017-05-26',
        '14': '2017-05-08',
        '13': '2017-04-21',
        '12': '2017-03-31',
        '11': '2017-03-10',
    },
    '108': {
        '1': '2017-09-11',
        '2': '2017-09-29',
        '3': '2017-10-17',
        '4': '2017-10-31',
        '5': '2017-11-10',
        '6': '2017-12-01',
        '7': '2017-12-20',
    },
}

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def scan_drive_files(service):
    page_token = None
    files = []

    while 1:
        response = service.files().list(
            q="not trashed and (mimeType='application/vnd.google-apps.folder'" +
              " or mimeType='application/vnd.google-apps.document'" +
              " or mimeType='application/pdf'" +
              " or mimeType contains 'image')",
            spaces='drive',
            fields='nextPageToken, files(id, name, parents, mimeType)',
            pageToken=page_token).execute()
        files += response.get('files', [])
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
        print('Scanned {} Drive files.'.format(len(files)))

    with open(DRIVE_STORAGE_FILENAME, 'w') as f:
        f.write(str(files))
        print('[100%] Scanned all {} Drive files into {}.'
              .format(len(files), DRIVE_STORAGE_FILENAME))


def get_children(parent_ids, file_type=None):
    if type(parent_ids) is unicode or type(parent_ids) is str:
        parent_ids = [parent_ids]
    if file_type is not None:
        if file_type in ['document', 'folder']:
            mime_type = 'application/vnd.google-apps.' + file_type
        elif file_type == 'image':
            mime_type = 'image'
        else:
            raise ValueError(
                'Expected file type document, folder, image, but received: {}.'.
                format(file_type))
        return [
            f for f in files
            if (mime_type in f['mimeType']
                and any(p in f.get('parents', []) for p in parent_ids))
        ]
    return [
        f for f in files if any(p in f.get('parents', []) for p in parent_ids)
    ]


def get_file(name_pattern, file_type, parent_id=None):
    mime_type = 'application/vnd.google-apps.' + file_type if file_type in ['folder', 'document'] else file_type
    if parent_id is not None:
        return next((
            f for f in files
            if (f['mimeType'] == mime_type
                and re.search(name_pattern, f['name'])
                and parent_id in f.get('parents', []))
        ))
    return next((
        f for f in files
        if (f['mimeType'] == mime_type
            and re.search(name_pattern, f['name']))
    ))


def download_document(file):
    if file['mimeType'] != 'application/vnd.google-apps.document':
        raise ValueError('File of MIME type {} should not be downloaded here.'
                         .format(file['mimeType']))
    request = service.files().export_media(
        fileId=file['id'], mimeType='text/plain')
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print('%d%%' % int(status.progress() * 100))
    return fh.getvalue()


def download_file(file):
    file_id = file['id']
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print('Download {} {}%.'.format(file['name'],
                                        int(status.progress() * 100)))
    fh.seek(0)

    image = Image.open(fh)
    imageName = 'tmp/' + slugify(
        file['name']) + '.' + file['mimeType'].split('/')[1]
    open(imageName, 'a').close()  # touch the file
    image.save(imageName)

    return imageName


# TODO: this middleman function is unnecessary. just analyze_issue => post_modify_headers
def post_article(data):
    data['created_at'] = ISSUE_DATES[str(data['volume'])][str(data['issue'])] + 'T17:57:55.149-05:00'
    article = utils.post_modify_headers(
        constants.API_ARTICLES_ENDPOINT,
        data=json.dumps(data))
    return article


def analyze_issue(volume, issue):
    volume_folder = get_file(r"Volume {}".format(volume), 'folder')
    issue_folder = get_file(r"Issue\s?{}".format(issue), 'folder',
                                  volume_folder['id'])
    sbc_folder = get_file(r"SBC", 'folder', issue_folder['id'])
    newspaper_pdf = get_file("(?i)Issue\s?\d{1,2}(\.pdf)$",
                                   'application/pdf',
                                   issue_folder['id'])
    art_folder = get_file(r"(?i)art", 'folder', issue_folder['id'])
    try: 
        photo_folder = get_file(r"(?i)(photo\s?color)", 'folder', 
                                      issue_folder['id']) 
    except StopIteration: 
        photo_folder = get_file(r"(?i)(photo\s?b&?w)", 'folder', 
                                      issue_folder['id']) 
    media_files = get_children([art_folder['id'], photo_folder['id']], 'image')

    if flags.window:
        webbrowser.open(
            'https://drive.google.com/file/d/{}/view'.format(newspaper_pdf['id']), new=2)
        webbrowser.open(
            'https://drive.google.com/drive/folders/' + photo_folder['id'],
            new=2)
        webbrowser.open(
            'https://drive.google.com/drive/folders/' + art_folder['id'],
            new=2)

    for section_name in ['News', 'Features', 'Opinions', 'A&E', 'Humor', 'Sports']:
        section_folder = get_file(section_name, 'folder', sbc_folder['id'])
        section_id = sections.get_section_id(section_name)
        section_articles = get_children(section_folder['id'], 'document')
        if section_folder['name'] == 'Opinions':
            try:
                section_articles.append(
                    get_file(r'(?i)staff\s?ed', 'document', sbc_folder['id']))
            except StopIteration:
                print(Fore.RED + Style.BRIGHT + 'No staff-ed found in Volume {} Issue {}.'.format(volume, issue))
        f = -1
        while f < len(section_articles) - 1:
            f += 1
            article_file = section_articles[f]
            print('\n')
            if re.search(r"(?i)worldbeat|survey|newsbeat|spookbeat",
                         article_file['name']):
                print(Fore.RED + Style.BRIGHT + article_file['name'] + ' unwanted.'
                      + Style.RESET_ALL)
                continue
            print(
                Fore.CYAN + Style.BRIGHT
                 + ("STAFF EDITORIAL" if re.search(r'(?i)staff\s?ed', article_file['name']) else section_name.upper())
                 + Fore.BLUE + ' ' + article_file['name'] + Style.RESET_ALL,
                end=' ')
            raw_text = download_document(article_file)
            if articles.does_file_exist(raw_text):
                print(Fore.RED + Style.BRIGHT + article_file['name'] + ' exists; skipped.'
                      + Style.RESET_ALL)
                continue

            if re.search(r'(?i)staff\s?ed', article_file['name']):
                article_data = articles.analyze_staffed(raw_text)
            else:
                article_data = articles.analyze_article(raw_text)

            if section_name == "Humor": 
                if issue == 4: 
                    subsection_id = sections.get_section_id("Spooktator") 
                if issue == 12: 
                    subsection_id = sections.get_section_id("Disrespectator") 
            elif section_name == "Opinions": 
                if re.search(r'(?i)staff\s?ed', article_file['name']): 
                    subsection_id = sections.get_section_id('Staff Editorials') 
                else: 
                    subsection_id = section_id 
            else: 
                subsection_id = sections.choose_subsection(section_name)

            article_data.update({
                'volume': volume,
                'issue': issue,
                'section_id': subsection_id
            })
            confirmation = raw_input(Fore.GREEN + Style.BRIGHT
                                     + 'post article? (n, r, o, default: y) ' + Style.RESET_ALL)
            while confirmation == 'o':
                webbrowser.open(
                    'https://docs.google.com/document/d/' + article_file['id'],
                    new=2)
                confirmation = raw_input(Fore.GREEN + Style.BRIGHT
                                         + 'post article? (n, r, o, default: y) '
                                         + Style.RESET_ALL)
            if confirmation == 'n':
                continue
            if confirmation == 'r':
                f = f - 1
                continue                

            new_article = post_article(article_data)
            article_data['id'] = new_article['id']
            articles.articles += [new_article]

            if re.search(r'(?i)staff\s?ed', article_file['name']):
                images = []
            else:
                images = choose_media(media_files, photo_folder['id'])

            def rollback(res):
                try:
                    print(
                        Fore.RED + Style.BRIGHT + '\nCaught error: {}'.format(
                            res) + Style.RESET_ALL)
                    articles.remove_article(article_data['id'])
                    utils.delete_modify_headers(
                        constants.API_ARTICLES_ENDPOINT + '/{}'.format(
                            article_data['id']))
                    return True
                except Exception as e:
                    print('Rollback failed with {}. Article {} remains evilly.'
                          .format(e, article_data['id']))
            article_create = Promise(
                lambda resolve, reject: resolve(users.post_contributors(article_data))
            )\
                .then(lambda authorship_data: articles.post_authorships(authorship_data))\
                .then(lambda res: articles.post_outquotes(article_data))\
                .then(lambda article_id: post_media(article_id, images)) \
                .then(lambda article_id: print(
                    Fore.GREEN + Style.BRIGHT
                    + '\nSuccessfully wrote Article #{}: {}.'
                    .format(article_data['id'], article_data['title'])
                    + Style.RESET_ALL)) \
                .catch(lambda res: rollback(res))
            result = article_create.get()

            if result is not None and result is True:
                print('Rollback completed. Re-prompting article.'
                      + Style.RESET_ALL)
                f = f - 1

def choose_media(media_files, photo_folder_id):
    images = []
    media_confirmation = None
    while media_confirmation != 'y' and media_confirmation != 'n':
        media_confirmation = raw_input(
            Fore.GREEN + Style.BRIGHT + 'upload media? (y/n): ' +
            Style.RESET_ALL)
    if media_confirmation == 'n':
        return images

    while True:
        image = {
            'is_featured': False,
            'media_type': 'illustration',
        }
        while True:
            filename = raw_input(Fore.GREEN + Style.BRIGHT +
                                 '-> filename (press ENTER to exit): ' +
                                 Style.RESET_ALL).strip()
            if filename == '':
                return images
            if filename[0] == '*':
                image['is_featured'] = True
                filename = filename[1:]
            try:
                target_file = next((
                    medium for medium in media_files
                        if medium['name'] == filename
                ))
                image['file'] = target_file
                if any(parent_id == photo_folder_id
                       for parent_id in target_file.get('parents', [])):
                    image['media_type'] = 'photo'
                break
            except StopIteration:
                print(Fore.RED + Style.BRIGHT
                      + 'No file matches {}.'.format(filename)
                      + Style.REST_ALL)

        for optional_field in ['title', 'caption']:
            field_input = raw_input(Fore.GREEN + Style.BRIGHT + '-> '
                                    + optional_field + ': ' + Style.RESET_ALL)\
                .strip()
            image[optional_field] = field_input

        while True:
            artist_name = raw_input(Fore.GREEN + Style.BRIGHT
                                    + '-> artist name: ' + Style.RESET_ALL)\
                .strip()
            if artist_name == '':
                print(
                    '\tartist name cannot be empty. check the Issue PDF for credits.'
                )
            else:
                image['artist_name'] = artist_name
                break

        images.append(image)


def post_media_file(filename, data):
    """Takes a filename and media data dictionary."""
    for key in data.keys():
        data['medium[{}]'.format(key)] = data.pop(key)
    files = {'medium[attachment]': open(filename, 'rb')}
    return utils.post_modify_headers(
        constants.API_MEDIA_ENDPOINT,
        files=files,
        data=data)


def post_media(article_id, medias):
    """Takes array of objects with artist_name, file, title, caption."""
    for media in medias:
        for field in [
                'artist_name', 'file', 'title', 'caption', 'is_featured',
                'media_type'
        ]:
            if field not in media:
                raise ValueError('Media object has no attribute {}.'
                                 .format(field))
        filename = download_file(media['file'])
        user_id = users.create_artist(media['artist_name'],
                                      media['media_type'])
        response = post_media_file(filename, {
            'article_id': article_id,
            'user_id': user_id,
            'media_type': media['media_type'],
            'is_featured': media['is_featured'],
            'title': media['title'],
            'caption': media['caption']
        })


def main():
    volume = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Volume #: ' + Style.RESET_ALL).strip())
    issue = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Issue #: ' + Style.RESET_ALL.strip()))

    try:
        ISSUE_DATES[str(volume)][str(issue)]
    except KeyError:
        print(Fore.RED + Style.BRIGHT + 'Volume {} Issue {} does not have a date'.format(volume, issue))
        return

    analyze_issue(volume, issue)


def init():
    global service
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    if flags.scan:
        scan_drive_files(service)

    global files
    with open(DRIVE_STORAGE_FILENAME, 'r') as f:
        files = ast.literal_eval(f.read())
    print(Fore.YELLOW + Style.BRIGHT + 'Scanned in {} Drive files from storage.'
        .format(len(files)) + Style.RESET_ALL)

    config.sign_in()

if __name__ == '__main__':
    colorama.init()
    if flags.local is not None:
        constants.init('localhost:{}'.format(flags.local))
    else:
        constants.init()
    config.init()
    init()
    sections.init()

    articles.init()
    users.init()
    main()
