# cli-uploader

A command line interface (CLI) for uploading articles from Google Drive Volume folders to our Rails API. 

We are currently rewriting our codebase to Go and GraphQL.

### Go Developer Resources
- [Go GraphQL Client](https://github.com/graphql-go/graphql)
- [Drive API Go Quickstart](https://developers.google.com/drive/v3/web/quickstart/go)

### Flags To Be Added

- **local**: Post data to a specific local port. To use with the Rails API, usage would be `python supr.py --local 3000`.
- **rescan**: If there have been structural or content changes in the Drive folders, use `--rescan` to update `files.in` (where the memoized Drive files are stored).
- **window**: If you want to open the Issue PDF, photo folder, and art folder, use the `--window` flag.
- **write\_url**: To post a solitary article from a Google Docs URL, use `--write_url GOOGLE_DOCS_URL`
- **write\_path**: To post a solitary article from a file path, use `--write_url PATH_NAME`
