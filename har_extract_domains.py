import json
import sys
from urllib.parse import urlparse

def extract_hostname(url):
    """从URL中提取主机名，无效或特殊URL返回None"""
    try:
        parsed = urlparse(url)
        if parsed.scheme in ('http', 'https') and parsed.hostname:
            return parsed.hostname.lower()
    except Exception:
        pass
    return None

def get_base_domain(hostname):
    """获取二级域名（最后两段）"""
    parts = hostname.split('.')
    if len(parts) <= 2:
        return hostname
    return '.'.join(parts[-2:])

def collect_hostnames_from_har(file_path):
    """从单个HAR文件中收集所有主机名"""
    hostnames = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            har = json.load(f)
        for entry in har['log']['entries']:
            url = entry['request']['url']
            hostname = extract_hostname(url)
            if hostname:
                hostnames.add(hostname)
    except FileNotFoundError:
        print(f"Warning: File not found - {file_path}", file=sys.stderr)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in {file_path}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Error processing {file_path}: {e}", file=sys.stderr)
    return hostnames

def process_har_files(file_paths):
    """处理多个HAR文件，返回最终的域名列表字符串"""
    all_hostnames = set()
    for path in file_paths:
        all_hostnames.update(collect_hostnames_from_har(path))
    
    if not all_hostnames:
        print("No valid hostnames found in the provided files.", file=sys.stderr)
        return ""

    # 按基础域分组
    groups = dict()
    for h in all_hostnames:
        base = get_base_domain(h)
        groups.setdefault(base, [])
        groups[base].append(h)

    result_domains = set()
    for base, domains in groups.items():
        # 找出所有子域名（排础域本身）
        sub_domains = [d for d in domains if d != base]
        if len(sub_domains) >= 2:
            # 多个子域名 → 使用通配符
            result_domains.add(f'*.{base}')
            if base in domains:
                result_domains.add(base)
        else:
            # 子域名少于2个，直接添加所有域名
            for d in domains:
                result_domains.add(d)

    return ' '.join(sorted(result_domains))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python har_extract_domains.py file1.har [file2.har ...]")
        sys.exit(1)
    
    output = process_har_files(sys.argv[1:])
    if output:
        print(output)

