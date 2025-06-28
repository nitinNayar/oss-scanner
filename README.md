# OSS Repo Importer

This Python script automates the process of forking all public repositories from a customer's GitHub organization into your own organization, renaming and tagging them for tracking, and overwriting any that already exist.

## Features
- Accepts customer name and customer GitHub org URL as CLI arguments
- Lists all public repos in the customer's GitHub org (handles pagination for large orgs)
- Forks each repo into your GitHub org (from `.env`)
- Renames the forked repo to `<customer_name>-<original_repo_name>`
- Tags the default branch with the customer name
- If a repo with the target name already exists, it is deleted and replaced

## Requirements
- Python 3.7+
- [requests](https://pypi.org/project/requests/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

Install dependencies:
```bash
pip install -r requirements.txt
```

## GitHub Token and Organization Setup
Generate a [Personal Access Token](https://github.com/settings/tokens) with the following scopes:
- `repo` (Full control of private repositories)
- `admin:org` (Full control of orgs and teams)

Create a `.env` file in your project root with the following content:
```env
GITHUB_TOKEN=ghp_xxxYOURTOKENxxx
ORG=your-org-name
```
Replace `your-org-name` with the name of your GitHub organization.

## Usage
Run the script with the customer name and the customer's GitHub org URL:
```bash
python import_repos.py <customer_name> <customer_github_org_url>
```
**Example:**
```bash
python import_repos.py AcmeCorp https://github.com/acme-corp
```
- The script will fork and rename all public repos from the customer org into your org, naming them `<customer_name>-<original_repo_name>`.
- If a repo already exists, it will be deleted and replaced.
- Each imported repo will be tagged with the customer name.

## Logging
The script logs info, warnings, and errors to the console.

## License
MIT 