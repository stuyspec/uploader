from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'


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

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)

    # Gets all folder names under SBC
    page_token = None
    folders = []
    response = drive_service.files().list(q="(mimeType='application/vnd.google-apps.folder' or mimeType='application/vnd.google-apps.document') and not trashed",
                                          spaces='drive',
                                          fields='nextPageToken, files(id, name, parents, mimeType)',
                                          pageToken=page_token).execute()
    files = response.get('files', [])
    SBC = next((file for file in files if file['name'] == 'SBC'), None)
    for file in response.get('files', []):
        try:
            if file.get('parents')[0] == SBC.get('id') and file.get('mimeType') == 'application/vnd.google-apps.folder':
                folders.append((file.get('id'), file.get('name')))
        except TypeError: # cannot index a NoneType, file is a document...?
            # print(file.get('name'))
            pass

    folders = dict(folders)
    for file in response.get('files', []):
        try:
            if file.get('mimeType') == 'application/vnd.google-apps.document' and file.get('parents')[0] in folders:
                sectionName = folders[file.get('parents')[0]]
                print('%s: %s' % (sectionName, file['name']))
        except TypeError: # same as before :(
            pass
    page_token = response.get('nextPageToken', None)
    if page_token is None:
        return

if __name__ == '__main__':
    main()
