import re
import requests
import ipaddress

FILTER_URLS = {
    "Yuki": "https://yuki2718.github.io/adblock2/japanese/jpf-plus.txt",
    "Tofu": "https://raw.githubusercontent.com/tofukko/filter/master/Adblock_Plus_list.txt",
    "AdGuard DNS": "https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_7_Japanese/filter.txt",
}

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
        m1 = re.findall(r'\|\|([^\/\^\*]+)\^', line)
        domains.update(m1)
        m2 = re.match(r'^([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$', line)
        if m2:
            domains.add(m2.group(1))
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
    return all_domains

def write_hosts(domains, output_path="hosts.txt"):
    with open(output_path, "w") as f:
        for domain in sorted(domains):
            f.write(f"0.0.0.0 {domain}\n")
    print(f"✅ Generated {output_path} with {len(domains)} entries")

if __name__ == "__main__":
    merged_domains = fetch_and_merge_domains()
    write_hosts(merged_domains, "adblock-hosts.txt")
