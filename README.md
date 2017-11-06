# cli-uploader
A CLI for uploading articles from Google Drive Volume folders to our Rails API. Written in Python.

## Prerequisites
To run this CLI (command line interface), you'll need:
- Python 2.6 or greater
- The [pip](https://pypi.python.org/pypi/pip) package management tool.
- Access to the internet and a web browser.

## Setup
### CLI-Uploader
1. Clone this repository, and `cd` into the project directory.
2. To install required packages, install [`pip`](https://pip.pypa.io/en/stable/installing) if you have not already, and, in the project directory, type:
```
pip install -r requirements.txt
```
3. You'll need credentials to call the Drive Client API. Get the Google Console login credentials by contacting the current maintainer at [`jkao1@stuy.edu`](mailto:jkao1@stuy.edu).
4. Log in to the Google Console with the credentials, and navigate to the `spec-uploader` project.
5. Go to APIs & services. Select the Credentials tab, and download the `spec-uploader-cli` OAuth client ID.
6. Move this file to the `cli-uploader` repo and rename it to `client_secret.json`.

### Rails API
1. We need something to upload to. If you are testing/developing this project rather than uploading from it, you will need a test API for your garbage data.
2. Follow the instructions on the [Rails API repo](http://github.com/stuyspec/stuy-spec-api) to install/localhost.


You are now ready to run the uploader! Use the flag `--local` to `POST` articles to the Rails API (`localhost:3000`).
