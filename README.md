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

If you are testing/developing this project rather than uploading from it, you will need a test API for your garbage and possibly messed up data. Follow the instructions on the [Rails API repo](http://github.com/stuyspec/stuy-spec-api) to install and host it locally.

After you have set up the local API, in the rails console create a user with the same email and password as in your .env file.
```rb
> u = User.new(email: your@email.here, password: yourpassword password_confirmation: yourpassword )
> u.skip_confirmation! # equivalent to clicking the confirm link in email
> u.save!
```

## Cleaning content to be uploaded

Before you can run the program, housekeeping needs to be done on the writers' content.

1. In the Drive folder (named Issue N), make sure the photo and art folders are named Photo Color/Photo and Art (not fart, which is common).

2. Go into `SBC` (seen by copy) and make sure the staff editorial is a direct child (the program will look for any file with any name like "staff ed", "staff editorial", etc.)

3. In each department's folder, open every article and make sure:
- The first line is the title (it's okay if it starts with "Title: ")
- There is a byline
- The way the content uploader finds the content start is it starts from the last paragraph and increments upwards until it hits what it deems the start of the slug (a sentence with "Focus sentence", "NN words", "Outquote:", etc.) Make sure such a sentence exists.
  - Some writers put outquotes on multiple lines, and the `cli-uploadeer` does not know which line is the slug start. In cases like those, move the focus sentence, which is always on one line, after the outquote. Or add a blank "Focus sentence:" on a newline after the outquote
  - If the outquote is "At least two" or the focus sentence is "none" or something like that, make it empty
- RESOLVE/REMOVE ALL COMMENTS/SUGGESTIONS
- If there are notes below the article from the writer (e.g. email interview, quotes) delete them.

Don't worry about "fixing" these ignored [files](https://github.com/stuyspec/cli-uploader/blob/master/supr.py#L474).
  
4. Formatting: there are several styles that can be applied via markup (HTML) in the doc. These are hardcoded into the body of `client-app` and as a whole can be viewed [here](https://github.com/stuyspec/client-app/blob/develop/src/js/modules/articles/components/ArticleBody.js#L25). Available markup is as follows:
- `<t></t>`: indent, useful for faking a `<ul>` (hopefully we'll add `<ul>` into this list at a later point)
- `<hr/>`: horizontal rule/line, often used to separate footer notes from content
- `<h5> ... </h5>`: bold and uppercase
- `<h4> ... </h4>`: bold, uppercase, and centered

These are the ones styled specially in client-app, but any HTML markup can be used (e.g. `<b>`, `<i>`, `<u>`).



## Running the program

Simply run the program with `python supr.py` and follow the prompts. If it is your first time running, use the flag `--rescan` to memoize all Drive files.

If the article upload is interrupted by "no email found for ...", find the author's email by searching their name in GMail's "To: ..." prompt. Names/emails will pop up for their stuy.edu account.

### Optional Flags

- **local**: Post data to a specific local port. To use with the Rails API, usage would be `python supr.py --local 3000`.
- **rescan**: If there have been structural or content changes in the Drive folders, use `--rescan` to update `files.in` (where the memoized Drive files are stored).
- **window**: If you want to open the Issue PDF, photo folder, and art folder, use the `--window` flag.
- **write_url**: To post a solitary article from a Google Docs URL, use `--write_url GOOGLE_DOCS_URL`
- **write_path**: To post a solitary article from a file path, use `--write_url PATH_NAME`
