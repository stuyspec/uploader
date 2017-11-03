# spec-uploader
A CLI for uploading articles from Google Drive Volume folders to our Rails API. Written in Python.

## Prerequisites
To run this CLI (command line interface), you'll need:
- Python 2.6 or greater
- The [pip](https://pypi.python.org/pypi/pip) package management tool.
- Access to the internet and a web browser.

## Setup
1. You need credentials to use the Drive API. Get the Google Console login credentials from one of the editors.
2. Log in to the Google Console with the credentials, and navigate to the `spec-uploader` project.
3. Go to APIs & services. Select the Credentials tab, and download the `spec-uploader-cli` OAuth client ID.
4. Move this file to your working directory (spec-uploader repository) and rename it to client_secret.json The file is .gitignored.
