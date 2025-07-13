#!/usr/bin/env python3
import os
import re
import ipaddress
import requests
import socket
import asyncio
import tempfile
import filecmp
import datetime
import shutil
import logging

# === 設定 ===
FILTER_URLS = {
    "Yuki": "https://yuki2718.github.io/adblock2/japanese/jpf-plus.txt",
    "Tofu": "https://raw.githubusercontent.com/tofukko/filter/master/Adblock_Plus_list.txt",
    "AdGuard DNS": "https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_7_Japanese/filter.txt",
}
CONCURRENCY = 5
MAX_RETRIES = 5

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === ドメイン抽出 ===
def is_valid_domain(domain):
    try:
        ipaddress.ip_address(domain)
        return False
    except ValueError:
        pass
    if domain in ('localhost', ''):
        return False
    if domain.endswith('.local') or domain.startswith('['):
        return False
    if re.match(r'^[0-9\.]+$', domain):
        return False
    if re.search(r'[^a-zA-Z0-9\.\-]', domain):
        return False
    return True

def extract_domains(text):
    domains = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(('!', '#', '@@')):
            continue
        domains.update(re.findall(r'\|\|([^\/\^\*]+)\^', line))
        if m := re.match(r'^([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$', line):
            domains.add(m.group(1))
    return {d for d in domains if is_valid_domain(d)}

def fetch_and_merge_domains():
    all_domains = set()
    for name, url in FILTER_URLS.items():
        print(f"Fetching {name}...")
        try:
            text = requests.get(url, timeout=15).text
            domains = extract_domains(text)
            print(f"  {len(domains)} valid domains")
            all_domains.update(domains)
        except Exception as e:
            print(f"  Error fetching {name}: {e}")
    return sorted(all_domains)

# === 名前解決チェック ===
async def resolve_domain(domain, sem):
    async with sem:
        for _ in range(MAX_RETRIES):
            try:
                await asyncio.to_thread(socket.getaddrinfo, domain, None)
                return domain
            except socket.gaierror:
                await asyncio.sleep(0.01)
    return None

async def filter_resolvable(domains):
    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = [resolve_domain(d, sem) for d in domains]
    resolved = await asyncio.gather(*tasks)
    return sorted(d for d in resolved if d)

# === hosts.txt 書き込み ===
def generate_hosts_lines(domains):
    today = datetime.datetime.now().strftime("%Y/%m/%d")
    lines = [
        "# AdAway Blocking Hosts File for Japan - Block List",
        "#",
        "# author: lawn",
        "#         https://github.com/lawnn/adaway-hosts",
        "#",
        f"# last updated: {today}",
        f"# block hosts: {len(domains)} entry",
        ""
    ]
    for domain in domains:
        lines.append(f"# {domain}")
        lines.append(f"127.0.0.1 {domain}")
        lines.append("")
    return lines

def write_if_changed(lines, path):
    dirnm = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=dirnm, delete=False) as tmp:
        for l in lines:
            tmp.write(l.rstrip() + "\n")
        tmp_path = tmp.name

    if not os.path.exists(path) or not filecmp.cmp(tmp_path, path, shallow=False):
        shutil.move(tmp_path, path)
        logging.info(f"✅ '{path}' を更新しました。")
    else:
        os.remove(tmp_path)
        logging.info(f"🟡 '{path}' に変更はありません。")

# === メイン処理 ===
def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    domains = fetch_and_merge_domains()
    resolved_domains = asyncio.run(filter_resolvable(domains))
    lines = generate_hosts_lines(resolved_domains)
    write_if_changed(lines, "uBO-to-hosts.txt")

if __name__ == "__main__":
    main()
