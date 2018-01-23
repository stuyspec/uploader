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
3. You'll need credentials to call the Drive Client API. Get the Google Console login credentials by contacting the current maintainer, Jason Kao.
4. Log in to the Google Console with the credentials, and navigate to the `spec-uploader` project.
5. Go to APIs & services. Select the Credentials tab, and download the `spec-uploader-cli` OAuth client ID.
6. Move this file to the `cli-uploader` repo and rename it to `client_secret.json`.
7. To manipulate the database, you need a user account on our production database (the prod db is the "official" one, the one you can call from `api.stuyspec.com`). Users also need a security credential level of 1 in the database. You can do this yourself if you know how to SSH into our Elastic Compute Cloud instance (EC2) where we host the API. If you do not, ask Jason. Store these credentials in a `.env` file like so:
```
EMAIL=your@email.here
PASSWORD=yourpassword
```

### Rails API
1. We need something to upload to. If you are testing/developing this project rather than uploading from it, you will need a test API for your garbage data.
2. Follow the instructions on the [Rails API repo](http://github.com/stuyspec/stuy-spec-api) to install/localhost.

## Running the program
Simply run the program with `python supr.py` and follow the prompts. If it is your first time running, use the flag `--rescan` to memoize all Drive files.

### Optional Flags
- **local**: Post data to a specific local port. To use with the Rails API, usage would be `python supr.py --local 3000`.
- **rescan**: If there have been structural or content changes in the Drive folders, use `--rescan` to update `files.in` (where the memoized Drive files are stored).
- **window**: If you want to open the Issue PDF, photo folder, and art folder, use the `--window` flag.
- **write_url**: To post a solitary article from a Google Docs URL, use `--write_url GOOGLE_DOCS_URL`
- **write_path**: To post a solitary article from a file path, use `--write_url PATH_NAME`
