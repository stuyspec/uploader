# uploader

[![GoDoc](https://godoc.org/github.com/stuyspec/uploader?status.svg)](https://godoc.org/github.com/stuyspec/uploader)
[![Go Report Card](https://goreportcard.com/badge/github.com/stuyspec/uploader)](https://goreportcard.com/report/github.com/stuyspec/uploader)
[![codebeat badge](https://codebeat.co/badges/1b7c5b89-9c46-4267-a7bc-f29017c5138a)](https://codebeat.co/projects/github-com-stuyspec-uploader-master)

A command line interface (CLI) for uploading articles from Google Drive Volume folders to our Rails API.

## Setup

You must have an admin account (security level > 0) in the database to be able to use the uploader. Put the credentials to the account in a dotenv file like so:
```
EMAIL=YOUR_EMAIL
PASSWORD=YOUR_PASSWORD
```

## Usage

```sh
# Compile program and create binary
$ go install

# Run bulk upload for Volume 108 Issue 11
$ uploader -m 108 -i 11
```

For specific instructions on how to clean Issue folders for uploading (a must for every issue), please visit the [UPLOADING.md](UPLOADING.md) file.

#### Optional flags
- **--window, -w:** open core files when bulk uploading (e.g. Photo/Art folders, Newspaper PDF)
- **--local PORT, -l PORT:** use a locally hosted GraphQL server

## Roadmap

For information on the things which are currently being focused on, please visit the [ROADMAP.md](ROADMAP.md) file.
