# Snapshots Directory

This directory is used to store HTML snapshots captured during the crawl stage.

## Generated Files

When you run the crawl command, the following files will be created here:

- `crawl_results.json` - Metadata about crawled URLs and HTTP responses
- `*.html` - Individual HTML snapshots with unique hash-based filenames

## Usage

```bash
# This command will populate this directory:
python -m retrievability.cli crawl samples/urls.txt --out samples/snapshots/
```

## Note

Generated files in this directory are excluded from version control via `.gitignore` since they are runtime artifacts that vary based on live web content.