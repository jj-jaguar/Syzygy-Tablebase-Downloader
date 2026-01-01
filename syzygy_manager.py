import os
import sys
import time
import urllib.request
import urllib.error
import re
import platform
import ctypes
import shutil
import traceback
import subprocess
import threading  # <--- NEW IMPORT

# --- CONFIGURATION & CONSTANTS ---
PROGRAM_NAME = "SYZYGY MANAGER"
AUTHOR = "BY JJ_JAGUAR"
VERSION = "1.0"
GITHUB_REPO = "jj-jaguar/Syzygy-Tablebase-Downloader"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/syzygy_manager.py"

# Magic Bytes & Network
WDL_MAGIC = b'\x71\xe8'
DTZ_MAGIC = b'\xd7\x66'
BUFFER_SIZE = 128 * 1024
USER_AGENT = "SyzygyManager/1.0 (ChessDB)"
TIMEOUT = 30

# Status Codes
STATUS_FAILED = 0
STATUS_DOWNLOADED = 1
STATUS_SKIPPED = 2

# Global Variable for Update Status
NEW_UPDATE_VERSION = None

# Size Estimates
GB = 1024 ** 3
TB = 1024 ** 4
ESTIMATED_SIZES = {
    '1': 1.2 * GB, '2': 150 * GB, '3': 17.1 * TB, '4': 17.3 * TB
}

# --- CROSS-PLATFORM COLORS ---
os.system("") 

class Colors:
    HEADER = '\033[95m'; BLUE = '\033[94m'; CYAN = '\033[96m'
    GREEN = '\033[92m'; YELLOW = '\033[93m'; RED = '\033[91m'
    RESET = '\033[0m'; BOLD = '\033[1m'; WHITE = '\033[97m'; GREY = '\033[90m'

class BackException(Exception): pass
class DonateException(Exception): pass
class CleanExit(Exception): pass
class NetworkError(Exception): pass

# --- UI HELPERS ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def set_terminal_title(title):
    if os.name == 'nt': os.system(f'title {title}')
    else: sys.stdout.write(f"\x1b]2;{title}\x07")

def format_size(size_bytes):
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024; i += 1
    return f"{round(size_bytes, 2)} {size_name[i]}"

def print_header(subtitle="", context=None):
    clear_screen()
    print(f"{Colors.CYAN}========================================================")
    print(f"{Colors.BOLD}{Colors.WHITE} {PROGRAM_NAME} {VERSION} {Colors.YELLOW}{AUTHOR}{Colors.RESET}")
    print(f"{Colors.CYAN}========================================================")
    print(f"{Colors.GREY} Official Project: {GITHUB_URL}{Colors.RESET}")
    
    if context:
        print(f"{Colors.CYAN}========================================================{Colors.RESET}")
        for key, value in context.items():
            print(f" {Colors.YELLOW}{key}:{Colors.RESET} {value}")
            
    print(f"{Colors.CYAN}========================================================")
    if subtitle:
        print(f"{Colors.GREEN} {subtitle}")
        print(f"{Colors.CYAN}========================================================")
    print(f"{Colors.RESET}")

# --- BACKGROUND UPDATE CHECKER ---
def check_for_updates_thread():
    """
    Runs in background. Updates the global variable if a new version is found.
    """
    global NEW_UPDATE_VERSION
    try:
        req = urllib.request.Request(RAW_URL)
        req.add_header('User-Agent', USER_AGENT)
        # Timeout is 5s, but since it's a background thread, it won't block the UI
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('utf-8')
            match = re.search(r'VERSION\s*=\s*"([^"]+)"', content)
            if match:
                latest_version = match.group(1)
                if latest_version != VERSION:
                    NEW_UPDATE_VERSION = latest_version
    except:
        pass

def prevent_sleep():
    system_platform = platform.system()
    try:
        if system_platform == 'Windows':
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000003); return True
        elif system_platform == 'Darwin': 
            subprocess.Popen(['caffeinate', '-i', '-w', str(os.getpid())]); return True
        elif hasattr(sys, 'getandroidapilevel'): 
            os.system('termux-wake-lock'); return True
    except: pass
    return False

def smart_input(prompt, default="1", allow_back=True):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try: value = sys.stdin.readline().strip()
    except (KeyboardInterrupt, EOFError): raise CleanExit()
    
    if not value: return default
    if value.lower() == 'q': raise CleanExit()
    if value.lower() == 'd': raise DonateException()
    if allow_back and value.lower() == 'b': raise BackException()
    return value

def get_valid_input(prompt, valid_choices, default, allow_back=True):
    while True:
        val = smart_input(prompt, default, allow_back)
        if val in valid_choices: return val
        print(f"{Colors.RED} Invalid option. Allowed: {', '.join(valid_choices)}{Colors.RESET}")

# --- DONATE ---
def show_donate():
    print_header("SUPPORT THE PROJECT")
    print(f"{Colors.YELLOW} Thank you for using Syzygy Manager!{Colors.RESET}\n")
    print(f"{Colors.GREEN} Bitcoin (BTC) {Colors.GREY}[Network: Bitcoin / BTC]{Colors.RESET}")
    print(f"{Colors.WHITE} 12hpLsgfXGPoFjVf1oWsbjUMPiVaSavdTi{Colors.RESET}\n")
    print(f"{Colors.GREEN} Ethereum (ETH) {Colors.GREY}[Network: ERC20]{Colors.RESET}")
    print(f"{Colors.WHITE} 0x11ddf9da829559a2451237fc640d245883ea2793{Colors.RESET}\n")
    print(f"{Colors.GREEN} USDT (Tether) {Colors.GREY}[Network: TRC20 / Tron Only]{Colors.RESET}")
    print(f"{Colors.WHITE} TB37wTAiKme7CygZsgebhqo4P8xuwkPgpC{Colors.RESET}\n")
    try: smart_input("\n Press Enter or B to return... ", "", True)
    except (BackException, CleanExit, DonateException): return

def print_donation_msg():
    print(f"\n{Colors.CYAN}--------------------------------------------------------")
    print(f"{Colors.YELLOW} Enjoying the tool? Consider supporting the project! {Colors.RESET}")
    print(f" Press {Colors.BOLD}[D]{Colors.RESET} at any menu to see donation details.")
    print(f"{Colors.CYAN}--------------------------------------------------------{Colors.RESET}")

# --- CORE LOGIC ---
def check_disk_space(path, selection_key, type_key):
    required = ESTIMATED_SIZES.get(selection_key, 0)
    if type_key in ['2', '3']: required /= 2 
    check_path = os.path.abspath(path if path else ".")
    while not os.path.exists(check_path):
        parent = os.path.dirname(check_path)
        if parent == check_path: break 
        check_path = parent
    try:
        _, _, free = shutil.disk_usage(check_path)
        if free < required:
            print(f"\n{Colors.RED}========================================{Colors.RESET}")
            print(f"{Colors.RED} [!] WARNING: LOW DISK SPACE{Colors.RESET}")
            print(f" Target Drive:  {check_path}")
            print(f" Free Space:    {format_size(free)}")
            print(f" Est. Need:     ~{format_size(required)}")
            print(f" Deficit:       {Colors.RED}-{format_size(required - free)}{Colors.RESET}")
            if smart_input(f"{Colors.YELLOW} Continue anyway? (y/n): {Colors.RESET}", "n", False).lower() != 'y': 
                raise BackException()
    except OSError: pass

def create_request(url, start_byte=0):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    if start_byte > 0: req.add_header('Range', f'bytes={start_byte}-')
    return req

def get_server_files_generator(url, ext, deep_scan=False):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(create_request(url), timeout=TIMEOUT) as r:
                html = r.read().decode('utf-8')
            if deep_scan:
                subdirs = sorted(list(set(re.findall(r'href="([^"/]+)/"', html))))
                subdirs = [d for d in subdirs if not d.startswith('.') and "Parent" not in d]
                for d in subdirs:
                    subdir_url = url + d + "/"
                    try:
                        with urllib.request.urlopen(create_request(subdir_url), timeout=10) as sr:
                            sub_html = sr.read().decode('utf-8')
                            files = sorted(list(set(re.findall(f'href="([^"]+{ext})"', sub_html))))
                            for f in files: yield (subdir_url + f, f)
                    except: pass 
                return
            else:
                files = sorted(list(set(re.findall(f'href="([^"]+{ext})"', html))))
                for f in files: yield (url + f, f)
                return
        except (urllib.error.URLError, socket.timeout):
            if attempt < max_retries - 1: time.sleep(1 + attempt)
            else: raise NetworkError(f"Failed to fetch index from {url}")
    return

def download_file(url, filepath):
    resume_byte = 0
    if os.path.exists(filepath): resume_byte = os.path.getsize(filepath)
    try:
        req_head = urllib.request.Request(url, method='HEAD')
        req_head.add_header('User-Agent', USER_AGENT)
        with urllib.request.urlopen(req_head, timeout=TIMEOUT) as response:
            total_size_online = int(response.info().get('Content-Length', 0))
        if resume_byte == total_size_online and total_size_online > 0:
            print(f"\r    {Colors.GREEN}[OK] Verified complete.{Colors.RESET}                                    ")
            return STATUS_SKIPPED
        if resume_byte > total_size_online:
            print(f"\r    {Colors.RED}[FIX] Corruption detected. Deleting...{Colors.RESET}       ")
            try: os.remove(filepath)
            except: pass; resume_byte = 0
            
        with urllib.request.urlopen(create_request(url, resume_byte), timeout=TIMEOUT) as response:
            status = response.getcode()
            if status == 206: mode = 'ab'; total_expected = resume_byte + int(response.info().get('Content-Length', 0))
            elif status == 200: mode = 'wb'; resume_byte = 0; total_expected = int(response.info().get('Content-Length', 0))
            else: return STATUS_FAILED

            with open(filepath, mode) as f:
                downloaded = resume_byte
                start_time = time.time(); last_up = 0
                while True:
                    chunk = response.read(BUFFER_SIZE)
                    if not chunk: break
                    f.write(chunk); downloaded += len(chunk); now = time.time()
                    if now - last_up > 0.25:
                        spd = (downloaded - resume_byte) / (now - start_time + 0.001)
                        pct = (downloaded / total_expected * 100) if total_expected else 0
                        sys.stdout.write(f"\r    Downloading... {pct:.1f}% @ {format_size(spd)}/s   ")
                        sys.stdout.flush(); last_up = now
                f.flush(); os.fsync(f.fileno())
        print(f"\r    {Colors.GREEN}[OK] Download Complete.{Colors.RESET}                                      ")
        return STATUS_DOWNLOADED
    except: return STATUS_FAILED

def get_config(pieces, mirror):
    is_deep = False; urls = ("", "")
    if 3 in pieces:
        urls = ("https://tablebase.lichess.ovh/tables/standard/3-4-5-wdl/", "https://tablebase.lichess.ovh/tables/standard/3-4-5-dtz/") if mirror=='1' else ("http://tablebase.sesse.net/syzygy/3-4-5/", "http://tablebase.sesse.net/syzygy/3-4-5/")
    elif 6 in pieces:
        urls = ("https://tablebase.lichess.ovh/tables/standard/6-wdl/", "https://tablebase.lichess.ovh/tables/standard/6-dtz/") if mirror=='1' else ("http://tablebase.sesse.net/syzygy/6-WDL/", "http://tablebase.sesse.net/syzygy/6-DTZ/")
    elif 7 in pieces:
        urls = ("https://tablebase.lichess.ovh/tables/standard/7/", "https://tablebase.lichess.ovh/tables/standard/7/") if mirror=='1' else ("http://tablebase.sesse.net/syzygy/7-WDL/", "http://tablebase.sesse.net/syzygy/7-DTZ/")
        if mirror=='1': is_deep = True
    return urls, is_deep

def run_download(base_path, do_wdl, do_dtz, grp, mirror, context):
    print_header(f"DOWNLOADING {grp}-PIECE", context)
    urls, is_deep = get_config(grp, mirror)
    print(f"{Colors.YELLOW} 1. Indexing server...{Colors.RESET}")
    
    suffix = "345" if 3 in grp else str(grp[0])
    queue = []
    try:
        def queue_files(url, ext, folder_suffix):
            folder_name = f"Syzygy{suffix}{folder_suffix}"
            target_dir = os.path.join(base_path, folder_name)
            if not os.path.exists(target_dir): os.makedirs(target_dir)
            c = 0
            for full_url, fname in get_server_files_generator(url, ext, is_deep):
                queue.append((full_url, os.path.join(target_dir, fname))); c += 1
            return c

        found = 0
        if do_wdl: found += queue_files(urls[0], '.rtbw', "WDL")
        if do_dtz: found += queue_files(urls[1], '.rtbz', "DTZ")
        if found == 0: raise NetworkError("No files found on server.")
    except NetworkError as e: raise e

    queue.sort(key=lambda x: os.path.basename(x[1])) # Canonical Sort
    print(f"{Colors.GREEN}    Index successfully retrieved: {len(queue)} files.{Colors.RESET}")
    print(f"\n{Colors.CYAN} 2. Processing (Smart Resume Active)...{Colors.RESET}")

    count = len(queue); skipped = 0; downloaded = 0
    for i, (url, fpath) in enumerate(queue):
        fname = os.path.basename(fpath)
        if os.path.exists(fpath):
            if i + 1 < count:
                if os.path.exists(queue[i+1][1]): 
                    skipped += 1
                    if skipped % 50 == 0: 
                        sys.stdout.write(f"\r    Verifying existing files... [{skipped}/{count}] Valid.")
                        sys.stdout.flush()
                    continue 
        
        sys.stdout.write(f"\r{' '*60}\r")
        print(f"{Colors.YELLOW} [{i+1}/{count}] {fname}{Colors.RESET}")
        
        success = False
        for attempt in range(3):
            status = download_file(url, fpath)
            if status == STATUS_DOWNLOADED: downloaded += 1; success = True; break
            elif status == STATUS_SKIPPED: skipped += 1; success = True; break
            print(f"{Colors.RED}    Connection failed. Retrying... ({attempt+1}/3){Colors.RESET}")
            time.sleep(2)
        if not success: print(f"{Colors.RED}    [FAILED] Skipping file.{Colors.RESET}")

    print(f"\n{Colors.CYAN}--------------------------------------------------------{Colors.RESET}")
    print(f" {Colors.WHITE}SESSION SUMMARY: Total {count} | {Colors.GREEN}Verified {skipped}{Colors.RESET} | {Colors.YELLOW}Downloaded {downloaded}{Colors.RESET}")
    print(f"{Colors.CYAN}--------------------------------------------------------{Colors.RESET}")

def run_verify(target_path, check_wdl, check_dtz, mode_pieces, mirror, context):
    print_header("INTEGRITY CHECK", context)
    if not os.path.exists(target_path): 
        print(f"\n{Colors.RED} [!] Error: Folder does not exist.{Colors.RESET}")
        smart_input("\nPress Enter...", "", False); return

    print(f"{Colors.YELLOW} [1/3] Indexing server files...{Colors.RESET}")
    server_set = set(); groups = []
    if 3 in mode_pieces: groups.append([3,4,5])
    if 6 in mode_pieces: groups.append([6])
    if 7 in mode_pieces: groups.append([7])
    
    for grp in groups:
        urls, is_deep = get_config(grp, mirror)
        sys.stdout.write(f"    Scanning {grp}-piece...")
        sys.stdout.flush()
        if check_wdl:
            for _, f in get_server_files_generator(urls[0], '.rtbw', is_deep): server_set.add(f)
        if check_dtz:
            for _, f in get_server_files_generator(urls[1], '.rtbz', is_deep): server_set.add(f)
        sys.stdout.write(f"\r{' '*30}\r")
    
    if not server_set: raise NetworkError("Server index empty.")
    print(f"    {Colors.GREEN}Server Index: {len(server_set)} files known.{Colors.RESET}")

    print(f"\n{Colors.YELLOW} [2/3] Checking local drive...{Colors.RESET}")
    local_set = set(); verify_list = []
    for root, _, files in os.walk(target_path):
        for f in files:
            if f in server_set: local_set.add(f); verify_list.append(os.path.join(root, f))
    
    missing = server_set - local_set
    if missing:
        print(f"{Colors.RED}    MISSING: {len(missing)} files.{Colors.RESET}")
        for m in sorted(list(missing))[:5]: print(f"     - {m}")
        if len(missing) > 5: print("     ... and others.")
    else: print(f"{Colors.GREEN}    File count matches.{Colors.RESET}")

    print(f"\n{Colors.YELLOW} [3/3] Verifying file headers...{Colors.RESET}")
    corrupt = 0; total = len(verify_list)
    for i, f in enumerate(verify_list):
        if i % 100 == 0: sys.stdout.write(f"\r    Progress: {int(i/total*100)}%")
        try:
            with open(f, 'rb') as fd:
                h = fd.read(4); valid = False
                if f.endswith('.rtbw') and h.startswith(WDL_MAGIC): valid = True
                if f.endswith('.rtbz') and h.startswith(DTZ_MAGIC): valid = True
                if not valid: print(f"\n{Colors.RED}    [X] Corrupt: {os.path.basename(f)}{Colors.RESET}"); corrupt += 1
        except: print(f"\n{Colors.RED}    [!] Read Error.{Colors.RESET}"); corrupt += 1
    print("\r    Progress: 100%       ")
    print_donation_msg(); smart_input("\nPress Enter to return...", "", False)

# --- MAIN MENU ---
def main():
    set_terminal_title(f"{PROGRAM_NAME} {VERSION}")
    
    # START THREAD: This prevents the 5-second blocking!
    update_thread = threading.Thread(target=check_for_updates_thread, daemon=True)
    update_thread.start()
    
    while True:
        context = {} 
        try:
            print_header("MAIN MENU")
            
            # Non-blocking notification
            if NEW_UPDATE_VERSION:
                print(f"{Colors.YELLOW} [!] UPDATE AVAILABLE: v{NEW_UPDATE_VERSION} is out!{Colors.RESET}")
                print(f"     Download at: {GITHUB_URL}\n")
            
            print(f"{Colors.YELLOW} Operation:{Colors.RESET}")
            print(f"{Colors.GREEN}   [1] Download / Resume{Colors.RESET}")
            print(f"{Colors.CYAN}   [2] Verify Integrity{Colors.RESET}")
            print(f"\n{Colors.RED}   [Q] Quit{Colors.RESET}    {Colors.YELLOW}[D] Donate{Colors.RESET}")
            
            op = get_valid_input("\n Choice: ", ['1', '2', 'q', 'd'], "1", False)
            if op.lower() == 'q': sys.exit()
            if op.lower() == 'd': show_donate(); continue

            op_map = {'1': 'Download / Resume', '2': 'Verify Integrity'}
            context['OPERATION'] = op_map.get(op)

            print_header("SELECT GENERATION", context)
            print(f"{Colors.GREEN}   [1] 3-4-5 Piece [~1 GB]{Colors.RESET}")
            print(f"{Colors.CYAN}   [2] 6 Piece     [~150 GB]{Colors.RESET}")
            print(f"{Colors.CYAN}   [3] 7 Piece     [~17 TB]{Colors.RESET}")
            print(f"{Colors.CYAN}   [4] All         [~17.2 TB]{Colors.RESET}")
            print(f"\n{Colors.RED}   [Q] Quit    [B] Back{Colors.RESET}    {Colors.YELLOW}[D] Donate{Colors.RESET}")
            tb = get_valid_input("\n Choice: ", ['1', '2', '3', '4', 'q', 'b', 'd'], "1")
            tb_map = {'1': '3-4-5 Piece', '2': '6 Piece', '3': '7 Piece', '4': 'All (Complete)'}
            context['GENERATION'] = tb_map.get(tb)
            
            queues = []
            if tb == '1': queues = [[3,4,5]]
            elif tb == '2': queues = [[6]]
            elif tb == '3': queues = [[7]]
            elif tb == '4': queues = [[3,4,5], [6], [7]]

            print_header("SELECT MIRROR", context)
            print(f"{Colors.GREEN}   [1] Lichess (Global / Fastest){Colors.RESET}")
            print(f"{Colors.CYAN}   [2] Sesse (Backup Mirror){Colors.RESET}")
            print(f"\n{Colors.RED}   [Q] Quit    [B] Back{Colors.RESET}    {Colors.YELLOW}[D] Donate{Colors.RESET}")
            mirror = get_valid_input("\n Choice: ", ['1', '2', 'q', 'b', 'd'], "1")
            context['MIRROR'] = 'Lichess' if mirror == '1' else 'Sesse'

            print_header("STORAGE PATH", context)
            print(f"{Colors.YELLOW} Enter the folder where you want to save the files:{Colors.RESET}")
            path = smart_input(f"\n Path: ", "").strip('"').strip("'")
            if not path: continue
            context['SAVE PATH'] = path

            if op == '2': 
                run_verify(path, True, True, [x for q in queues for x in q], mirror, context)
                continue

            print_header("DOWNLOAD OPTIONS", context)
            print(f"{Colors.GREEN}   [1] Both (WDL + DTZ){Colors.RESET}")
            print(f"{Colors.CYAN}   [2] WDL Only{Colors.RESET}")
            print(f"{Colors.CYAN}   [3] DTZ Only{Colors.RESET}")
            print(f"\n{Colors.RED}   [Q] Quit    [B] Back{Colors.RESET}    {Colors.YELLOW}[D] Donate{Colors.RESET}")
            ftype = get_valid_input("\n Choice: ", ['1', '2', '3', 'q', 'b', 'd'], "1")
            ftype_map = {'1': 'Both (WDL + DTZ)', '2': 'WDL Only', '3': 'DTZ Only'}
            context['DOWNLOAD OPTIONS'] = ftype_map.get(ftype)
            check_disk_space(path, tb, ftype)
            do_w = ftype in ['1', '2']; do_d = ftype in ['1', '3']

            print_header("SLEEP PREVENTION", context)
            print(f"{Colors.GREEN}   [1] Yes (Keep Awake){Colors.RESET}")
            print(f"{Colors.CYAN}   [2] No{Colors.RESET}")
            print(f"\n{Colors.RED}   [Q] Quit    [B] Back{Colors.RESET}    {Colors.YELLOW}[D] Donate{Colors.RESET}")
            slp = get_valid_input("\n Choice: ", ['1', '2', 'q', 'b', 'd'], "1")
            if slp == '1': prevent_sleep(); context['SLEEP PREVENTION'] = 'Active'
            else: context['SLEEP PREVENTION'] = 'Disabled'

            for q in queues: run_download(path, do_w, do_d, q, mirror, context)
            print(f"\n{Colors.GREEN}All Tasks Finished.{Colors.RESET}")
            print_donation_msg(); smart_input("Press Enter to return...", "", False)

        except NetworkError as e:
            print(f"\n{Colors.RED}[!] NETWORK ERROR: {e}{Colors.RESET}")
            smart_input("\nPress Enter...", "", False)
        except (BackException, CleanExit):
            if isinstance(sys.exc_info()[1], CleanExit): sys.exit()
            continue
        except DonateException: show_donate(); continue
        except KeyboardInterrupt: sys.exit()
        except Exception: 
            traceback.print_exc(); input(f"\n{Colors.RED}[CRASH] Press Enter...{Colors.RESET}"); sys.exit()

if __name__ == "__main__": main()