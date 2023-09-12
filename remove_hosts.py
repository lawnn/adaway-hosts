import os
import asyncio
import socket
import time
import shutil
import logging

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def resolve_domain(domain, semaphore):
    async with semaphore:
        count = 0
        while True:
            try:
                ip_address = await asyncio.to_thread(socket.gethostbyname, domain)
                return domain, ip_address
            except socket.gaierror:
                count += 1
                if count > 5:
                    return None
                await asyncio.sleep(1)

async def process_line(line, semaphore):
    if "127.0.0.1" in line:
        domain = line.split()[1]
        ip_address = await resolve_domain(domain, semaphore)
        if ip_address is not None:
            return f"127.0.0.1 {domain}\n"
    return None

async def main():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(script_directory, 'hosts.txt')
    output_filename = os.path.join(script_directory, 'resolved_hosts.txt')

    semaphore = asyncio.Semaphore(10)  # 同時実行を制限するためのセマフォ

    with open(input_filename, 'r') as file:
        tasks = [process_line(line.strip(), semaphore) for line in file]
        processed_lines = await asyncio.gather(*tasks)

    with open(output_filename, 'w') as output_file:
        for line in processed_lines:
            if line is not None:
                output_file.write(line)

    logging.info(f"Processed and resolved domains have been saved to '{output_filename}'.")


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

        logging.info(f"{len(new_domains)} new domains added to '{existing_hosts_filename}'.")
    else:
        logging.info("No new domains to add.")

    if removed_domains:
        logging.info(f"{len(removed_domains)} domains removed from '{existing_hosts_filename}':")
        for domain in removed_domains:
            logging.info(domain)
            with open(existing_hosts_filename, 'r') as file:
                lines = file.readlines()
            with open(existing_hosts_filename, 'w') as file:
                for line in lines:
                    if domain not in line:
                        file.write(line)
        logging.info(f"{len(removed_domains)} domains removed from '{existing_hosts_filename}'.")
    else:
        logging.info("No domains removed.")


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
    logging.info("Total execution time: %s seconds", time.time() - st)
