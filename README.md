# ghsubs

**ghsubs** is a fast and efficient tool to find subdomains of a target domain by searching through GitHub repositories. It leverages GitHub's API to quickly extract subdomains associated with your target domain from public code and documentation.

## Features

- Finds subdomains of your target domain by scanning GitHub repositories  
- Requires only a GitHub personal access token for authentication  
- Very fast and lightweight  
- Case-insensitive search for maximum coverage  
- Simple and easy to use CLI interface  

## Requirements

- Python 3.7+  
- A GitHub personal access token with at least `repo` scope (can be generated [here](https://github.com/settings/tokens))

## Installation

Usage:

```bash
git clone https://github.com/yourusername/ghsubs.git
cd ghsubs
python3 ghsubs.py -d target.com -o subdomains.txt
```
⚠️ Do not forget to add your token to ghsubs.py
