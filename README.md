# cli-uploader
A command line interface (CLI) for uploading articles from Google Drive Volume folders to our Rails API. Written in Python.

## Prerequisites
To run this CLI (command line interface), you'll need:
- Python 2.6 or greater
- The [pip](https://pypi.python.org/pypi/pip) package management tool.
- Access to the internet and a web browser.

## Setup
### The Uploader
1. Clone this repository, and `cd` into the project directory.
2. To install required packages, install [`pip`](https://pip.pypa.io/en/stable/installing) if you have not already, and, in the project directory, type:
```
pip install -r requirements.txt
```
3. You'll need credentials to call the Drive Client API. Get the Google Console login credentials by contacting the current maintainer at [`jkao1@stuy.edu`](mailto:jkao1@stuy.edu).
4. Log in to the Google Console with the credentials, and navigate to the `spec-uploader` project.
5. Go to APIs & services. Select the Credentials tab, and download the `spec-uploader-cli` OAuth client ID.
6. Move this file to the `cli-uploader` repo and rename it to `client_secret.json`.
7. To manipulate the database, you need a user account on our production database (the prod db is the "official" one, the one you can call from `api.stuyspec.com`). Users also need a security credential level > 0 in the database. You can do this yourself if you know how to SSH into our Elastic Compute Cloud instance (EC2) where we host the API. If you do not, ask Jason. Store these credentials in a `.env` file like so:
```
EMAIL=your@email.here
PASSWORD=yourpassword
```

### Rails API
1. We need something to upload to. If you are testing/developing this project rather than uploading from it, you will need a test API for your garbage data.
2. Follow the instructions on the [Rails API repo](http://github.com/stuyspec/stuy-spec-api) to install/localhost.

## Running the program
Run the program with `python supr.py`. Use the flag `--local NNNN` to `POST` articles to the Rails API running on `localhost:NNNN` (typically 3000).
