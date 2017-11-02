from __future__ import print_function
import httplib2
import os
import io
import re

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

from colorama import init, Fore, Back, Style
init()

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Spec-Uploader CLI'


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

# TODO: make Issue for terminal calculating columns wrong. see https://bugs.python.org/issue17337 and its attached S.O. post

def readArticle(text):
    metadata = text.split('\n')
    title = metadata[0].strip() # gets first line of text
    if 'Title: ' in title:
        title = title[title.find('Title: ') + len('Title: '):]
    title = raw_input('title: ({0})'.format(title[:-1])) or title # defaults to title

    try:
        byline = next((line for line in metadata if line.find('By') >= 0))
        print(byline)
        if 'By:' in byline:
            byline = byline[len('By:'):].strip()
        else:
            byline = byline[len('By'):].strip()

        # splits string into words and punctuation
        byline = re.findall(r"[\w']+|[.,!?;]", byline)
        contributors = []
        cutoff = 0
        for i in range(0, len(byline)):
            if byline[i] in ',&and':
                contributors.append((' '.join(byline[cutoff:i])).replace(' - ', '-'))
                cutoff = i + 1
        contributors.append(' '.join(byline[cutoff:]))  # clean up last one
        contributors = filter(None, contributors)  # removes empty strings
        byline = raw_input('contributors: ({0})'.format(', '.join(contributors))) or byline
    except StopIteration: # no byline found
        print(Fore.RED + 'No byline found.' + Fore.RESET)
        contributors = []
        for line in metadata:
            if 'words' in line.lower(): # print heading up to word count
                contributors = raw_input('enter contributors separated by ", ": ').split(', ')


def getFoldersInFile(files, parentFolderId):
    folders = {}
    # find first file in files with name 'SBC'

    for file in files:
        # check if parent folder is SBC and file type is folder
        if file.get('parents', [None])[0] == parentFolderId and file.get('mimeType') == 'application/vnd.google-apps.folder':
            folders[file['id']] = file['name']
    return folders

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)

    # Gets all folder names under SBC
    page_token = None
    response = drive_service.files().list(q="(mimeType='application/vnd.google-apps.folder' or mimeType='application/vnd.google-apps.document') and not trashed",
                                          spaces='drive',
                                          fields='nextPageToken, files(id, name, parents, mimeType)',
                                          pageToken=page_token).execute()
    files = response.get('files', []) # if no key 'files', defaults to []
    SBC = next((file for file in files if file['name'] == 'SBC'), None)
    folders = getFoldersInFile(files, SBC['id'])
    for file in files:
        if file['mimeType'] == 'application/vnd.google-apps.document' and file.get('parents', [None])[0] in folders:

            # find sectionName by getting folder with parentId
            sectionName = folders[file.get('parents', [None])[0]].upper()

            # create new download request
            request = drive_service.files().export_media(fileId=file['id'],
                                                         mimeType='text/plain')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(Back.BLACK + Fore.WHITE + sectionName, end='')
                print(Back.RESET + Fore.BLUE + ' ' + file['name'] + Fore.RESET, end=' ')
                print('%d%%' % int(status.progress() * 100))

            readArticle(fh.getvalue())
    page_token = response.get('nextPageToken', None)
    if page_token is None:
        return

if __name__ == '__main__':
    testing = """Title: A Discussion on Discussion
    Spectator/Opinions/Issue 1
    Emily Hur
    Words: 780
    Focus Sentence: The freedom of open discussion is not as important as being mindful of sensitive issues related to our history of oppression. 
    Outquotes: 
    “...this prejudice hasn’t been erased, but rather has evolved.”
    
    Areas like New York City and Silicon Valley have long been acknowledged as places that lean politically left, a culture that remains pervasive both at school and in the workplace. But recently, James Damore, a former engineer at Google, released an internal memo in an act of rebellion that challenged these ideas of liberalism and equality.
    
    Following the implementation of a diversity program at Google intended to help the company fight bias in the workplace, Damore voices his thoughts in a memo titled “Google’s Ideological Echo Chamber.” In it, he outlines inherent differences between men and women, suggesting that women have a propensity for lower stress jobs because of their genetic predisposition for “neuroticism,” which "may contribute to the higher levels of anxiety women report on Googlegeist and to the lower number of women in high stress jobs." And, since they generally have an interest in “people rather than things,” he suggests that they may be better suited for jobs in “social or artistic areas,” especially since he claims women have a higher level of “agreeableness” that makes them unsuited for leadership positions. 
    
    Many of his coworkers were quick to condemn him for sexism and promoting harmful gender stereotypes, including the CEO of Google, Sundar Pichai. Others, however, sent him personal messages applauding his bravery for opening up discussion. They claimed they were afraid to openly show support because of political discrimination. In our current political climate, many Americans, including our own president, have spoken out about feeling suffocated by political correctness, which they argue shames dissenters into silence. 
    
    But this so-called “political suffocation” should by no means be used as justification to promote ideas that are blatantly sexist and foster harmful stereotypes.
    
    Damore did succeed in bringing attention to his ideas. Yet he was not successful in proving his own claims because he shared erroneous information that threatened to reverse strides made in closing the gender gap. For instance, despite Damore’s simplistic view of the neuroticism of women, personality traits are qualitative, meaning any data gathered from research conducted by psychologists can be interpreted in hundreds of ways. Even David Schmitt, the director of the study cited by Damore in his memo, has voiced disagreement with Damore’s analysis, saying, “It is unclear to me that this sex difference would play a role in success within the Google workplace.”
    
    This is not an isolated event, but part of a long trend in which men reinforce age-old gender stereotypes that allow this bias to persevere. For instance, in 2005, Larry Summers, the former president of Harvard, gave a statement crediting the shortage of successful women in science to a lack of an “innate ability” to perform as well as men in certain academic disciplines. Similarly, in 2015, Michael Moritz from Sequoia Capital gave a statement in an interview saying he would consider hiring more women in the future, but he didn’t want to “lower the standards” of the company. 
    
    As a country, we’ve spent decades trying to reverse a history of oppression. Yet it’s clear that this prejudice hasn’t been erased, merely evolved. Many people have gone from believing that women are incapable of joining the workforce to thinking that they’re incapable of holding senior positions because their supposedly more caring nature makes them better suited for jobs like teaching. Sexism still lingers, and the many incidents involving insensitive comments made by men expressing their outdated opinions serve to reinforce these ideas. 
    
    Many people take advantage of online forums to express controversial opinions, even illegitimate ones with no scientific backing. Similarly, Google allows its employees to engage in discussion through internal messages. However, Damore argues that “Google’s left bias has created a politically correct monoculture that maintains its hold by shaming dissenters into silence.” 
    
    The problem at hand actually goes beyond Google’s political agenda. This isn’t an issue of silencing conservatives or shunning the ideas of someone who simply wants to stimulate discussion—it’s an issue of a Google employee who decided to immaturely attack women and their role in the tech industry. Though Google decided to fire Damore for “advancing harmful gender stereotypes” and rightly chose to prioritize their female employees, the impact of his memo will be felt for years to come. 
    
    Damore’s baseless conclusions, which have been drawn by multiple men in the past, will only serve to increase hostility in the workplace and increase the wage gap. His ideas are discouraging to women trying to pursue a career in the STEM field, and they have no scientific backing. 
    
    Ultimately, open discussion is essential for honest and intelligent discourse. But honesty and intelligence stem from being informed and having tact, something that is much harder to come by. 
    """

    readArticle(testing)
    #main()