from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from pyfiglet import figlet_format
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from PIL import Image
import httplib2
import base64
import requests
import json
from slugify import slugify

import os
import re
import io

import constants

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Spec-Uploader CLI'


files = []
drive_service = None

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
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def init():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    global drive_service
    drive_service = discovery.build('drive', 'v3', http=http)

    print('\n')
    print(figlet_format('SPEC CLI', font='slant'))

    page_token = None
    response = drive_service.files().list(
        q="(mimeType='application/vnd.google-apps.folder'"
          + " or mimeType='application/vnd.google-apps.document')"
          #+ " or mimeType contains 'image')"
          + " and not trashed",
        spaces='drive',
        fields='nextPageToken, files(id, name, parents, mimeType)',
        pageToken=page_token
    ).execute()
    page_token = response.get('nextPageToken', None)
    # if page_token is None:
    #     return

    media_response = drive_service.files().list(
        q="mimeType contains 'image' and not trashed",
        spaces='drive',
        fields='nextPageToken, files(id, name, parents, mimeType)',
        pageToken=page_token
    ).execute()
    page_token = media_response.get('nextPageToken', None)
    # if page_token is None:
    #     return

    if not os.path.exists('/tmp'):
        os.makedirs('/tmp')

    global files
    files = response.get('files', []) + media_response.get('files', [])
    print(len(files))
    # todo: in the future, files should be sorted into dictionary by issue num


def get_file(name_pattern, file_type, parent_id=None):
    mime_type = 'application/vnd.google-apps.' + file_type
    if parent_id:
        return next((
            f for f in files if (f['mimeType'] == mime_type and
                                 re.match(name_pattern, f['name']) and
                                 f.get('parents', [None])[0] == parent_id)
        ))
    return next((
        f for f in files if (f['mimeType'] == mime_type and
                             re.match(name_pattern, f['name']))
    ))


def get_children(parent_id, file_type=None):
    if type(parent_id) is str:
        parent_id = [parent_id]
    if file_type is not None:
        if file_type in ['document', 'folder']:
            mime_type = 'application/vnd.google-apps.' + file_type
        elif file_type == 'image':
            mime_type = 'image'
        else:
            raise ValueError('Expected file type document, folder, image, but received: {}.'.format(file_type))
        return [
            f for f in files if (mime_type in f['mimeType'] and
                                 f.get('parents', ['trash||'])[0] in parent_id)
        ]
    return [
        f for f in files if f.get('parents', [None])[0] in parent_id
    ]


def download_document(file):
    if file['mimeType'] != 'application/vnd.google-apps.document':
        raise ValueError('File of MIME type {} should not be downloaded here.'
                         .format(file['mimeType']))
    request = drive_service.files().export_media(
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
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print('Download {} {}%.'.format(file['name'],
                                          int(status.progress() * 100))),
    fh.seek(0)

    image = Image.open(fh)
    imageName = 'tmp/' + slugify(file['name']) + '.' + file['mimeType'].split('/')[1]
    open(imageName, 'a').close() # touch the file
    image.save(imageName)

    return imageName


def post_media_file(filename, data):
    """Takes a filename and media data dictionary."""
    image = Image.open(filename)
    for key in data.keys():
        data['medium[{}]'.format(key)] = data.pop(key)
    files = {
        'medium[attachment]': open(filename, 'rb')
    }
    response = requests.post(constants.API_MEDIA_ENDPOINT,
                             files=files,
                             data=data)
    response.raise_for_status()









