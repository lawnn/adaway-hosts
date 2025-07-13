#!/usr/bin/env python3
import os
import re
import asyncio
import socket
import tempfile
import filecmp
import datetime
import shutil
import logging
import ipaddress
import requests

# ========== 設定 ==========
FILTER_URLS = {
    "Yuki": "https://yuki2718.github.io/adblock2/japanese/jpf-plus.txt",
    "Tofu": "https://raw.githubusercontent.com/tofukko/filter/master/Adblock_Plus_list.txt",
    "AdGuard DNS": "https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_7_Japanese/filter.txt",
}

MAX_TRIES = 5
CONCURRENCY = 8

# ========== ログ設定 ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ========== フィルタ取得 & ドメイン抽出 ==========
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
    if re.match(r'^[0-9.]+$', domain):
        return False
    if re.search(r'[^a-zA-Z0-9.-]', domain):
        return False
    return True

def extract_domains(text):
    domains = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(('!', '#', '@@')):
            continue
        m1 = re.findall(r'\|\|([^/\^*]+)\^', line)
        domains.update(m1)
        m2 = re.match(r'^([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$', line)
        if m2:
            domains.add(m2.group(1))
    return {d for d in domains if is_valid_domain(d)}

def fetch_adblock_domains():
    all_domains = set()
    for name, url in FILTER_URLS.items():
        logging.info(f"Fetching {name}...")
        try:
            text = requests.get(url, timeout=15).text
            domains = extract_domains(text)
            logging.info(f"  {len(domains)} valid domains from {name}")
            all_domains.update(domains)
        except Exception as e:
            logging.warning(f"  Error fetching {name}: {e}")
    return all_domains

# ========== 既存hostsの解析 ==========
def parse_blocks(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    header = []
    blocks = []
    idx = 0
    while idx < len(lines):
        header.append(lines[idx].rstrip('\n'))
        if lines[idx].strip() == "" and idx > 0 and lines[idx - 1].strip().startswith("#"):
            idx += 1
            break
        idx += 1

    cur = []
    for line in lines[idx:]:
        stripped = line.strip()
        if stripped == "":
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line.rstrip('\n'))
    if cur:
        blocks.append(cur)

    return header, blocks

# ========== 名前解決チェック ==========
async def resolve_domain(domain: str, sem: asyncio.Semaphore) -> bool:
    async with sem:
        for _ in range(MAX_TRIES):
            try:
                await asyncio.to_thread(socket.getaddrinfo, domain, None)
                return True
            except socket.gaierror:
                await asyncio.sleep(0.01)
        return False

async def filter_blocks(blocks: list[list[str]]) -> list[list[str]]:
    sem = asyncio.Semaphore(CONCURRENCY)
    result = []

    for block in blocks:
        new_block = []
        host_lines = []
        domains = []

        for line in block:
            if line.startswith("127.0.0.1"):
                parts = line.split()
                if len(parts) == 2:
                    domains.append(parts[1])
                    host_lines.append(line)
            else:
                new_block.append(line)

        ok_map = {}
        if domains:
            ok_list = await asyncio.gather(*(resolve_domain(d, sem) for d in domains))
            ok_map = {d: ok for d, ok in zip(domains, ok_list)}

        for line in host_lines:
            parts = line.split()
            if ok_map.get(parts[1], False):
                new_block.append(line)
            else:
                logging.info(f"除外: {line}")

        if any(l.strip() for l in new_block):
            result.append(new_block)

    return result

# ========== ファイル出力関連 ==========
def update_metadata(lines: list[str], block_count: int) -> list[str]:
    today_str = datetime.datetime.now().strftime("%Y/%m/%d")
    new_lines = []
    for line in lines:
        if line.startswith("# last updated:"):
            new_lines.append(f"# last updated: {today_str}")
        elif line.startswith("# block hosts:"):
            new_lines.append(f"# block hosts: {block_count} entry")
        else:
            new_lines.append(line)
    return new_lines

def update_readme_block_count(readme_path: str, count: int):
    if not os.path.exists(readme_path):
        logging.warning(f"⚠️ '{readme_path}' が見つかりません。README 更新スキップ。")
        return

    new_lines = []
    updated = False
    with open(readme_path, "r", encoding="utf-8") as f:
        for line in f:
            if "![ブロック数](" in line:
                new_lines.append(f"![ブロック数](https://img.shields.io/badge/block-{count}-red)\n")
                updated = True
            else:
                new_lines.append(line)

    if updated:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        logging.info(f"✅ README.md のブロック数バッジを {count} に更新しました。")

# 差分のみ書き込み

def write_if_changed(lines: list[str], path: str):
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

def change_current_directory():
    script_directly = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directly)

def git_pull():
    change_current_directory()
    os.system('git pull')

def git_command():
    change_current_directory()
    comment = datetime.datetime.now().strftime("%Y/%m/%d")
    os.system(f'git commit -a -m "Update {comment}"')
    os.system('git push')

# ========== メイン処理 ==========
def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 元のhosts.txt読み込み
    with open("hosts.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    header, blocks = parse_blocks(lines)

    # フィルタ経由ドメイン取得
    adblock_domains = fetch_adblock_domains()
    adblock_lines = [f"# {d}\n127.0.0.1 {d}" for d in sorted(adblock_domains)]
    adblock_blocks = [[l] for l in adblock_lines]

    # 名前解決フィルタリング
    merged_blocks = blocks + adblock_blocks
    filtered_blocks = asyncio.run(filter_blocks(merged_blocks))

    out_lines = [line.rstrip() for line in header if line.strip() != ""]
    out_lines.append("")
    for blk in filtered_blocks:
        cleaned = [l.rstrip() for l in blk if l.strip() != ""]
        out_lines.extend(cleaned)
        out_lines.append("")

    while out_lines and out_lines[-1].strip() == "":
        out_lines.pop()
    out_lines.append("")

    block_count = sum(1 for line in out_lines if line.startswith("127.0.0.1"))
    out_lines = update_metadata(out_lines, block_count)

    write_if_changed(out_lines, "hosts.txt")
    update_readme_block_count("README.md", block_count)

if __name__ == "__main__":
    git_pull()
    main()
    git_command()