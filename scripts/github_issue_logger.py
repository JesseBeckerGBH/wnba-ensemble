import os
import sys
import json
import logging
from urllib import request, error

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_issue(title, body):
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    repo = os.getenv("GITHUB_TARGET_REPO")
    
    if not token or not repo:
        logger.warning("[!] GITHUB_ACCESS_TOKEN or GITHUB_TARGET_REPO missing in environment context. Skipping GitHub Issue automation.")
        return

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Killershades-Agent"
    }
    # Pushing issues as Open by default.
    data = json.dumps({"title": title, "body": body}).encode("utf-8")

    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            issue_number = res_data.get('number')
            logger.info(f"[*] Autonomously Generated GitHub Issue #{issue_number}: {title}")
            
            # Immediately close the issue to serve strictly as a completed background log
            patch_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
            patch_req = request.Request(patch_url, data=json.dumps({"state": "closed"}).encode("utf-8"), headers=headers, method="PATCH")
            with request.urlopen(patch_req) as patch_res:
                logger.info(f"[*] Marked Issue #{issue_number} as CLOSED (Automated Background Sync).")
                logger.info(f"    --> URL: {res_data.get('html_url')}")
    except error.HTTPError as e:
        logger.error(f"[!] Target GitHub API Error: {e.code} - {e.read().decode()}")
    except Exception as e:
        logger.error(f"[!] System Failed to fire GitHub Issue payload: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("Usage: python github_issue_logger.py 'Task Title' 'Task Description Body'")
        sys.exit(1)
    
    title = sys.argv[1]
    body = sys.argv[2]
    create_issue(title, body)
