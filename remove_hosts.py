#!/usr/bin/env python3
import os
import asyncio
import socket
import tempfile
import filecmp
import datetime
import shutil
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# パラメータ
MAX_TRIES = 5
CONCURRENCY = 8

async def resolve_domain(domain: str, sem: asyncio.Semaphore) -> bool:
    async with sem:
        for _ in range(MAX_TRIES):
            try:
                await asyncio.to_thread(socket.getaddrinfo, domain, None)
                return True
            except socket.gaierror:
                await asyncio.sleep(0.01)
                
        return False

def parse_blocks(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """ ヘッダーとブロックに分割 """
    header = []
    blocks = []
    idx = 0

    # ヘッダー取得（最初の空行まで）
    while idx < len(lines):
        header.append(lines[idx].rstrip('\n'))
        if lines[idx].strip() == "" and idx > 0 and lines[idx - 1].strip().startswith("#"):
            idx += 1
            break
        idx += 1

    # ブロックを構成
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

async def filter_blocks(blocks: list[list[str]]) -> list[list[str]]:
    """ 各ブロックの行ごとに名前解決、解決できる行のみ残す """
    sem = asyncio.Semaphore(CONCURRENCY)
    result = []

    for block in blocks:
        new_block = []
        host_lines = []
        domains = []

        # 分離
        for line in block:
            if line.startswith("127.0.0.1"):
                parts = line.split()
                if len(parts) == 2:
                    domains.append(parts[1])
                    host_lines.append(line)
            else:
                new_block.append(line)

        # 名前解決チェック
        ok_map = {}
        if domains:
            ok_list = await asyncio.gather(*(resolve_domain(d, sem) for d in domains))
            ok_map = {d: ok for d, ok in zip(domains, ok_list)}

        # 有効なホスト行のみ追加
        for line in host_lines:
            parts = line.split()
            if ok_map.get(parts[1], False):
                new_block.append(line)
            else:
                logging.info(f"除外: {line}")

        # 何か残っていればブロックとして採用
        if any(l.strip() for l in new_block):
            result.append(new_block)

    return result

def write_if_changed(lines: list[str], path: str):
    """ 差分があるときのみ書き換え """
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
                newline = f"![ブロック数](https://img.shields.io/badge/block-{count}-red)\n"
                new_lines.append(newline)
                updated = True
            else:
                new_lines.append(line)

    if updated:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        logging.info(f"✅ README.md のブロック数バッジを {count} に更新しました。")
    else:
        logging.warning("⚠️ README にブロック数バッジが見つかりませんでした。")

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

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    src = "hosts.txt"
    # 読み込み
    with open(src, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 分割
    header, blocks = parse_blocks(lines)

    # フィルタ処理
    filtered = asyncio.run(filter_blocks(blocks))

    # 出力再構成
    out_lines = []
    out_lines.extend(line.rstrip() for line in header if line.strip() != "")
    out_lines.append("")  # ヘッダー末尾に1行空ける

    for blk in filtered:
        cleaned = [l.rstrip() for l in blk if l.strip() != ""]
        out_lines.extend(cleaned)
        out_lines.append("")  # ブロック間空行

    # 末尾の空行が2つ以上にならないよう調整
    while out_lines and out_lines[-1].strip() == "":
        out_lines.pop()
    out_lines.append("")

    # メタ情報更新
    block_count = sum(1 for line in out_lines if line.startswith("127.0.0.1"))
    out_lines = update_metadata(out_lines, block_count)

    # 差分ありの場合のみ書き込み
    write_if_changed(out_lines, src)

    # ✅ README.md のブロック数も更新
    update_readme_block_count("README.md", block_count)

if __name__ == "__main__":
    git_pull()
    main()
    git_command()