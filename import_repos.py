import os
from dotenv import load_dotenv
load_dotenv()
import requests
import logging
from urllib.parse import urlparse
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ORG = os.getenv('ORG')
API_URL = 'https://api.github.com'
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json',
}

def get_org_name_from_url(org_url):
    path = urlparse(org_url).path
    return path.rstrip('/').split('/')[-1]

def list_public_repos(org):
    repos = []
    page = 1
    while True:
        url = f"{API_URL}/orgs/{org}/repos?type=public&per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            logging.error(f"Failed to list repos for org {org}: {r.text}")
            break
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def repo_exists(org, repo_name):
    url = f"{API_URL}/repos/{org}/{repo_name}"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200

def fork_repo(source_owner, source_repo, org):
    url = f"{API_URL}/repos/{source_owner}/{source_repo}/forks"
    data = {"organization": org}
    r = requests.post(url, headers=HEADERS, json=data)
    if r.status_code in (202, 201):
        logging.info(f"Fork started for {source_owner}/{source_repo} into {org}")
        return True
    else:
        logging.error(f"Failed to fork {source_owner}/{source_repo} into {org}: {r.text}")
        return False

def wait_for_fork(org, repo_name, timeout=120):
    url = f"{API_URL}/repos/{org}/{repo_name}"
    for _ in range(timeout // 5):
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return True
        time.sleep(5)
    logging.error(f"Timed out waiting for fork of {org}/{repo_name}")
    return False

def wait_for_fork_ready(org, repo_name, timeout=120):
    url = f"{API_URL}/repos/{org}/{repo_name}"
    for _ in range(timeout // 5):
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            repo = r.json()
            if repo.get('default_branch'):
                return True
        time.sleep(5)
    logging.error(f"Timed out waiting for fork {org}/{repo_name} to be ready for rename")
    return False

def rename_repo(org, old_name, new_name):
    url = f"{API_URL}/repos/{org}/{old_name}"
    data = {"name": new_name}
    r = requests.patch(url, headers=HEADERS, json=data)
    if r.status_code == 200:
        logging.info(f"Renamed repo {org}/{old_name} to {new_name}")
        return True
    else:
        logging.error(f"Failed to rename repo {org}/{old_name} to {new_name}: {r.text}")
        return False

def delete_repo(org, repo_name):
    url = f"{API_URL}/repos/{org}/{repo_name}"
    r = requests.delete(url, headers=HEADERS)
    if r.status_code == 204:
        logging.info(f"Deleted existing repo: {org}/{repo_name}")
        return True
    else:
        logging.error(f"Failed to delete repo {org}/{repo_name}: {r.text}")
        return False

def get_default_branch(org, repo_name):
    url = f"{API_URL}/repos/{org}/{repo_name}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json().get('default_branch')
    return None

def create_tag(org, repo_name, tag_name, branch):
    # Get the latest commit SHA on the default branch
    url = f"{API_URL}/repos/{org}/{repo_name}/git/refs/heads/{branch}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        logging.error(f"Failed to get branch ref for {org}/{repo_name}:{branch}")
        return False
    commit_sha = r.json()['object']['sha']
    # Create tag object
    tag_url = f"{API_URL}/repos/{org}/{repo_name}/git/tags"
    tag_data = {
        "tag": tag_name,
        "message": f"Tag for customer {tag_name}",
        "object": commit_sha,
        "type": "commit",
        "tagger": {
            "name": "OSS Scanner Bot",
            "email": "oss-scanner@example.com"
        }
    }
    tag_resp = requests.post(tag_url, headers=HEADERS, json=tag_data)
    if tag_resp.status_code not in (201, 200):
        logging.error(f"Failed to create tag object for {org}/{repo_name}: {tag_resp.text}")
        return False
    tag_sha = tag_resp.json()['sha']
    # Create tag ref
    ref_url = f"{API_URL}/repos/{org}/{repo_name}/git/refs"
    ref_data = {
        "ref": f"refs/tags/{tag_name}",
        "sha": tag_sha
    }
    ref_resp = requests.post(ref_url, headers=HEADERS, json=ref_data)
    if ref_resp.status_code in (201, 200):
        logging.info(f"Tagged {org}/{repo_name} with {tag_name}")
        return True
    else:
        logging.error(f"Failed to create tag ref for {org}/{repo_name}: {ref_resp.text}")
        return False

def main(customer_name, customer_org_url):
    customer_org = get_org_name_from_url(customer_org_url)
    repos = list_public_repos(customer_org)
    if not repos:
        logging.error(f"No public repos found in customer org: {customer_org}")
        return
    for repo in repos:
        orig_repo_name = repo['name']
        source_owner = customer_org
        new_repo_name = f"{customer_name}-{orig_repo_name}"
        if repo_exists(ORG, new_repo_name):
            if not delete_repo(ORG, new_repo_name):
                continue
        # Fork the repo
        if not fork_repo(source_owner, orig_repo_name, ORG):
            continue
        # Wait for the fork to appear
        if not wait_for_fork(ORG, orig_repo_name):
            continue
        # Wait for the fork to be ready for rename
        if not wait_for_fork_ready(ORG, orig_repo_name):
            continue
        # Rename the forked repo
        if not rename_repo(ORG, orig_repo_name, new_repo_name):
            continue
        branch = get_default_branch(ORG, new_repo_name)
        if branch:
            create_tag(ORG, new_repo_name, customer_name, branch)
        else:
            logging.error(f"Could not determine default branch for {ORG}/{new_repo_name}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python import_repos.py <customer_name> <customer_github_org_url>")
        exit(1)
    main(sys.argv[1], sys.argv[2]) 