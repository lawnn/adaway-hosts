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

def git_command():
    comment = datetime.datetime.now().strftime("%Y/%m/%d")
    os.system(f'git commit -a -m "Update {comment}"')
    os.system('git push')

if __name__ == "__main__":
    filename = 'hosts.txt'
    update_block_hosts('resolved_hosts.txt', filename)
    print(f"'block hosts' line in '{filename}' has been updated.")
    update_last_updated(filename)
    print(f"'last updated' line in '{filename}' has been updated.")
    git_command()
