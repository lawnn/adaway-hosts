import os
import datetime


def change_current_directory():
    script_directly = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directly)

def count_lines(file_name):
    with open(file_name, 'r') as file:
        lines = file.readlines()
        return len(lines)


def update_last_updated(hosts_file_name):
    today_date = datetime.datetime.now().strftime("%Y/%m/%d")
    updated_lines = []

    with open(hosts_file_name, 'r') as file:
        for line in file:
            if "# last updated:" in line:
                updated_lines.append(f"# last updated: {today_date}\n")
            else:
                updated_lines.append(line)

    with open(hosts_file_name, 'w') as file:
        for line in updated_lines:
            file.write(line)


def update_block_hosts(read_file, hosts_file_name):
    with open(hosts_file_name, 'r') as file:
        lines = file.readlines()

    entries = count_lines(read_file)
    updated_lines = []
    for line in lines:
        if "# block hosts:" in line:
            updated_lines.append(f"# block hosts: {entries} entry\n")
        else:
            updated_lines.append(line)

    with open(hosts_file_name, 'w') as file:
        for line in updated_lines:
            file.write(line)


def update_readme_block_count(file_name, new_counts):
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        if "![ブロック数](" in line:
            count_string = f"![ブロック数](https://img.shields.io/badge/block-{new_counts}-red)\n"
            replaced_line = line.replace(line, count_string)
            updated_lines.append(replaced_line)
        else:
            updated_lines.append(line)

    with open(file_name, 'w', encoding='utf-8') as file:
        for line in updated_lines:
            file.write(line)


def git_command():
    change_current_directory()
    comment = datetime.datetime.now().strftime("%Y/%m/%d")
    os.system('git pull')
    os.system(f'git commit -a -m "Update {comment}"')
    os.system('git push')


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hosts_filename = os.path.join(script_dir, 'hosts.txt')
    resolved_hosts_filename = os.path.join(script_dir, 'resolved_hosts.txt')
    readme_filename = os.path.join(script_dir, 'README.md')

    # ドメインの生存確認
    update_block_hosts(resolved_hosts_filename, hosts_filename)
    print(f"'block hosts' line in '{hosts_filename}' has been updated.")

    # ドメイン数のカウント
    update_last_updated(hosts_filename)
    print(f"'last updated' line in '{hosts_filename}' has been updated.")

    # readmeのドメイン数カウント
    new_count = count_lines(resolved_hosts_filename)
    update_readme_block_count(readme_filename, new_count)
    print(f"'ブロック数' line in '{readme_filename}' has been updated.")

    # git command の実行
    git_command()
