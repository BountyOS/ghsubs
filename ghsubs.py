#!/usr/bin/env python3

import argparse
import os
import re
import requests
import time
import concurrent.futures
import html
import urllib.parse

# === Config ===
GITHUB_TOKEN = "<TOKEN>"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
MAX_THREADS = 2  # Number of parallel downloads

# === Functions ===

def fetch_github_links(domain):
    page = 1
    links = []

    print(f"[*] Searching GitHub for '{domain}'...")

    while True:
        url = f"https://api.github.com/search/code?q={urllib.parse.quote(domain)}&per_page=100&page={page}&sort=created&order=asc"
        response = requests.get(url, headers=HEADERS)
        data = response.json()

        if "items" not in data or not data["items"]:
            break

        page_links = [item["html_url"] for item in data["items"]]
        links.extend(page_links)

        print(f"[*] Page {page}: {len(page_links)} results")
        if len(page_links) < 100:
            break

        page += 1
        time.sleep(1.5)

    links = sorted(set(links))
    os.makedirs("tmp", exist_ok=True)
    with open("tmp/target-links.tmp", "w") as f:
        f.write("\n".join(links))

    return links

def download_file(url, idx, total):
    try:
        local_name = os.path.join("tmp/files", url.split("/")[-1])
        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

        print(f"[{idx}/{total}] Checking: {raw_url}")
        
        # Check Content-Length before downloading
        head = requests.head(raw_url, timeout=10)
        size = int(head.headers.get("Content-Length", 0))
        if size > 100 * 1024 * 1024:
            print(f"[-] Skipping {raw_url} (Size: {size / (1024*1024):.2f} MB)")
            return None

        print(f"[{idx}/{total}] Downloading: {raw_url}")
        response = requests.get(raw_url, timeout=10)
        if response.status_code == 200:
            with open(local_name, "wb") as f:
                f.write(response.content)
            return local_name
    except Exception as e:
        print(f"[-] Failed to download {url}: {e}")
    return None

def download_all(links):
    os.makedirs("tmp/files", exist_ok=True)
    print(f"[*] Downloading {len(links)} files...\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {
            executor.submit(download_file, url, i + 1, len(links)): url
            for i, url in enumerate(links)
        }
        concurrent.futures.wait(futures)

def decode_content(content):
    # Decode HTML entities (&amp;, &lt;, etc)
    content = html.unescape(content)
    
    # Decode URL encoded strings (%2F, %3A)
    try:
        content = urllib.parse.unquote(content)
    except Exception:
        pass
    
    # Decode JSON unicode escapes (\u002f)
    try:
        content = re.sub(
            r'\\u[0-9a-fA-F]{4}',
            lambda m: chr(int(m.group(0)[2:], 16)),
            content
        )
    except Exception:
        pass

    return content

def extract_subdomains(domain, output_file=None):
    print(f"\n[*] Extracting subdomains of {domain}...")
    pattern = re.compile(rf"\b(?:[a-zA-Z0-9-]+\.)*{re.escape(domain)}\b", re.IGNORECASE)
    found = set()

    for root, _, files in os.walk("tmp/files"):
        for fname in files:
            try:
                with open(os.path.join(root, fname), "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    content = decode_content(content)  # decode before regex matching
                    matches = pattern.findall(content)
                    found.update(matches)
            except Exception as e:
                print(f"[-] Error reading {fname}: {e}")

    results = sorted(sub.lower() for sub in found)  # convert to lowercase

    if output_file:
        with open(output_file, "w") as out:
            out.write("\n".join(results))
        print(f"[+] Saved {len(results)} subdomains to {output_file}")
    else:
        for sub in results:
            print(sub)

# === Main ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Subdomain Finder")
    parser.add_argument("-d", "--domain", required=True, help="Target domain, e.g. example.com")
    parser.add_argument("-o", "--output", help="File to save extracted subdomains")
    args = parser.parse_args()

    all_links = fetch_github_links(args.domain)
    download_all(all_links)
    extract_subdomains(args.domain, args.output)
