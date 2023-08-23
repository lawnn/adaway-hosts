import os
import asyncio
import socket
import time
import shutil


async def resolve_domain(domain):
    try:
        ip_address = await asyncio.to_thread(socket.gethostbyname, domain)
        return domain, ip_address
    except socket.gaierror:
        return None


async def process_line(line):
    if "127.0.0.1" in line:
        domain = line.split()[1]
        ip_address = await resolve_domain(domain)
        if ip_address is not None:
            return f"127.0.0.1 {domain}\n"
    return None


async def main():
    script_directly = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(script_directly, 'hosts.txt')
    output_filename = os.path.join(script_directly, 'resolved_hosts.txt')

    processed_lines = []

    with open(input_filename, 'r') as file:
        for line in file:
            cleaned_line = line.strip()
            processed_line = await process_line(cleaned_line)
            if processed_line is not None:
                processed_lines.append(processed_line)

    with open(output_filename, 'w') as output_file:
        for line in processed_lines:
            output_file.write(line)

    print(f"Processed and resolved domains have been saved to '{output_filename}'.")


def read_hosts_file(filename):
    domains = set()
    with open(filename, 'r') as file:
        for line in file:
            cleaned_line = line.strip()
            if cleaned_line and "127.0.0.1" in cleaned_line:
                domain = cleaned_line.split()[1]
                domains.add(domain)
    return domains


def update_hosts_file(existing_hosts_filename, resolved_hosts_file_name):
    existing_domains = read_hosts_file(existing_hosts_filename)
    resolved_domains = read_hosts_file(resolved_hosts_file_name)

    new_domains = resolved_domains - existing_domains
    removed_domains = existing_domains - resolved_domains

    if new_domains:
        with open(existing_hosts_filename, 'a') as file:
            for domain in new_domains:
                file.write(f"127.0.0.1 {domain}\n")

        print(f"{len(new_domains)} new domains added to '{existing_hosts_filename}'.")
    else:
        print("No new domains to add.")

    if removed_domains:
        print(f"{len(removed_domains)} domains removed from '{existing_hosts_filename}':")
        for domain in removed_domains:
            print(domain)
            with open(existing_hosts_filename, 'r') as file:
                lines = file.readlines()
            with open(existing_hosts_filename, 'w') as file:
                for line in lines:
                    if domain not in line:
                        file.write(line)
        print(f"{len(removed_domains)} domains removed from '{existing_hosts_filename}'.")
    else:
        print("No domains removed.")


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    st = time.time()
    asyncio.run(main())

    script_dir = os.path.dirname(os.path.abspath(__file__))
    hosts_filename = os.path.join(script_dir, 'hosts.txt')
    hosts_old_filename = os.path.join(script_dir, 'hosts_old.txt')
    resolved_hosts_filename = os.path.join(script_dir, 'resolved_hosts.txt')
    shutil.copyfile(hosts_filename, hosts_old_filename)  # バックアップ

    update_hosts_file(hosts_filename, resolved_hosts_filename)
    print("Total execution time:", time.time() - st)
