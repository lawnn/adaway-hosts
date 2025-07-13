#!/usr/bin/env python3
import os
import datetime
import tempfile
import shutil
import filecmp
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_domain(host_line):
    parts = host_line.strip().split()
    if len(parts) == 2:
        return parts[1]
    return None

def build_hosts_lines(resolved_file):
    today = datetime.datetime.now().strftime("%Y/%m/%d")

    with open(resolved_file, 'r', encoding='utf-8') as f:
        raw_lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    count = len(raw_lines)

    # ヘッダー
    header = [
        "# AdAway Blocking Hosts File for Japan - Block List",
        "#",
        "# author: logroid",
        "#         https://github.com/logroid/adaway-hosts",
        "#         https://logroid.blogspot.com/",
        "#         https://twitter.com/logroid",
        "#",
        f"# last updated: {today}",
        f"# block hosts: {count} entry",
        ""
    ]

    # 本体
    body = []
    for line in raw_lines:
        domain = extract_domain(line)
        if domain:
            body.append(f"# {domain}")
            body.append(line)
            body.append("")  # ブロック間の空行

    # 最後の余分な空行は1つに調整
    while body and body[-1].strip() == "":
        body.pop()
    body.append("")

    return header + body

def write_if_changed(new_lines, dest_path):
    dirnm = os.path.dirname(dest_path) or "."
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=dirnm, delete=False) as tmp:
        for line in new_lines:
            tmp.write(line.rstrip() + "\n")
        tmp_path = tmp.name

    if not os.path.exists(dest_path) or not filecmp.cmp(tmp_path, dest_path, shallow=False):
        shutil.move(tmp_path, dest_path)
        logging.info(f"✅ '{dest_path}' を更新しました。")
    else:
        os.remove(tmp_path)
        logging.info(f"🟡 '{dest_path}' に変更はありません。")

def write_hosts(resolved_file='resolved_hosts.txt', hosts_file='hosts.txt'):
    lines = build_hosts_lines(resolved_file)
    write_if_changed(lines, hosts_file)
    logging.info(f"合計 {sum(1 for l in lines if l.startswith('127.0.0.1'))} 件を書き出しました。")

if __name__ == "__main__":
    write_hosts()
