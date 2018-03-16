# cli-uploader

[![GoDoc](https://godoc.org/github.com/stuyspec/uploader?status.svg)](https://godoc.org/github.com/stuyspec/uploader)
[![Go Report Card](https://goreportcard.com/badge/github.com/stuyspec/uploader)](https://goreportcard.com/report/github.com/stuyspec/uploader)
[![codebeat badge](https://codebeat.co/badges/1b7c5b89-9c46-4267-a7bc-f29017c5138a)](https://codebeat.co/projects/github-com-stuyspec-uploader-master)

A command line interface (CLI) for uploading articles from Google Drive Volume folders to our Rails API.

## Usage
```sh
# Compile program and create binary
$ go install

# Run bulk upload for Volume 108 Issue 11
$ uploader -m 108 -i 11
```

#### Optional flags
- **--window, -w:** open core files when bulk uploading (e.g. Photo/Art folders, Newspaper PDF)
- **--local PORT, -l PORT:** use a locally hosted GraphQL server

## Uploading

For specific instructions on how to clean Issue folders for uploading, please visit the [UPLOADING.md](UPLOADING.md) file.

## Roadmap

For information on the things which are currently being focused on, please visit the [ROADMAP.md](ROADMAP.md) file.

## Manual Upload

The code in this repository will never be perfect. There may be an article that will not upload no matter what you try. In this unfortunate case, refer to [UPLOADING.md](UPLOADING.md) to view instructions on how to use the Rails console to manually upload an article.
