import os
import datetime

def count_lines(file_name):
    with open(file_name, 'r') as file:
        lines = file.readlines()
        return len(lines)

def update_last_updated(hosts_filename):
    today_date = datetime.datetime.now().strftime("%Y/%m/%d")
    updated_lines = []

    with open(hosts_filename, 'r') as file:
        for line in file:
            if "# last updated:" in line:
                updated_lines.append(f"# last updated: {today_date}\n")
            else:
                updated_lines.append(line)

    with open(hosts_filename, 'w') as file:
        for line in updated_lines:
            file.write(line)


def update_block_hosts(read_file, hosts_filename):
    with open(hosts_filename, 'r') as file:
        lines = file.readlines()

    entries = count_lines(read_file)
    updated_lines = []
    for line in lines:
        if "# block hosts:" in line:
            updated_lines.append(f"# block hosts: {entries} entry\n")
        else:
            updated_lines.append(line)

    with open(hosts_filename, 'w') as file:
        for line in updated_lines:
            file.write(line)


def update_readme_block_count(file_name, new_count):
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        if "![ブロック数](" in line:
            count_string = f"![ブロック数](https://img.shields.io/badge/block-{new_count}-red)"
            replaced_line = line.replace(line, count_string)
            updated_lines.append(replaced_line)
        else:
            updated_lines.append(line)

    with open(file_name, 'w', encoding='utf-8') as file:
        for line in updated_lines:
            file.write(line)

def git_command():
    comment = datetime.datetime.now().strftime("%Y/%m/%d")
    os.system(f'git commit -a -m "Update {comment}"')
    os.system('git push')

if __name__ == "__main__":
    # ドメインの生存確認
    filename = 'hosts.txt'
    update_block_hosts('resolved_hosts.txt', filename)
    print(f"'block hosts' line in '{filename}' has been updated.")
    # ドメイン数のカウント
    update_last_updated(filename)
    print(f"'last updated' line in '{filename}' has been updated.")
    # readmeのドメイン数カウント
    readme_filename = 'readme.md'
    new_count = count_lines('resolved_hosts.txt')
    update_readme_block_count(readme_filename, new_count)
    print(f"'ブロック数' line in '{readme_filename}' has been updated.")
    git_command()
