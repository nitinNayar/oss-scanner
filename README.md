# OSS Repo Importer

This Python script automates the process of importing public GitHub repositories into your organization (`semgrep-oss-scanner`), tagging them with a customer name, and skipping any that already exist.

## Features
- Reads a CSV file with source repo URLs and customer names
- Creates a new repo in your GitHub org for each entry (named `<customer_name>-<original_repo_name>`)
- Uses the GitHub Import API to import the source repo
- Tags the default branch with the customer name
- Skips and logs a warning if the repo already exists in your org

## Requirements
- Python 3.7+
- [requests](https://pypi.org/project/requests/)
- [pandas](https://pypi.org/project/pandas/)

Install dependencies:
```bash
pip install -r requirements.txt
```

## GitHub Token Permissions
Generate a [Personal Access Token](https://github.com/settings/tokens) with the following scopes:
- `repo` (Full control of private repositories)
- `admin:org` (Full control of orgs and teams)

For public repos only, `public_repo` and `admin:org` are sufficient, but `repo` is recommended for full compatibility.

Export your token as an environment variable:
```bash
export GITHUB_TOKEN=ghp_xxxYOURTOKENxxx
```

## CSV Format
The CSV file should have the following columns:

| repo_url                        | customer_name |
|---------------------------------|--------------|
| https://github.com/user/repo1   | AcmeCorp     |
| https://github.com/user/repo2   | BetaInc      |

## Usage
```bash
python import_repos.py repos.csv
```

- The script will create new repos in your org named `<customer_name>-<original_repo_name>`.
- If a repo already exists, it will be skipped and a warning will be logged.
- Each imported repo will be tagged with the customer name.

## Logging
The script logs info, warnings, and errors to the console.

## License
MIT 