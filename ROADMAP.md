# Roadmap

The roadmap here is a living document of where this CLI uploader is intending to go and things needed to be done in the near future.

## Text-only Uploading for Volume/Issues

- Traverse the Drive file tree and find relevant files
- Download file bytes
- Open CLI to text options (r, o, y, n)
- Subsection choosing
- Get contributors

#### GraphQL Mutations:
- Create article mutation, compatible with contributors, profiles

## Media Uploading for Volume/Issues

- Open CLI to media options (filename, title, caption, artist)

#### GraphQL Mutations:
- Paperclip and GraphQL

## Flag Roadmap

- **local**: Post data to a specific local port. To use with the Rails API, usage would be `python supr.py --local 3000`.
- **rescan**: If there have been structural or content changes in the Drive folders, use `--rescan` to update `files.in` (where the memoized Drive files are stored).
- **window**: If you want to open the Issue PDF, photo folder, and art folder, use the `--window` flag.
- **write\_url**: To post a solitary article from a Google Docs URL, use `--write_url GOOGLE_DOCS_URL`
- **write\_path**: To post a solitary article from a file path, use `--write_url PATH_NAME`
