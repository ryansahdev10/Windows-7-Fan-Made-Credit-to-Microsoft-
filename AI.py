"""Windows 7 Desktop — Secure Assistant
Features implemented:
- Deep local search and web handover
- Password-protected vault and settings
- Emergency shutdown (quarantine) with password confirmation
- File manager UI for stored assistant files (delete/ quarantine)
- Notes, tasks, safe math, voice, and app launch support
- Brute-force login lockout (5 attempts → timed lockdown)
- Terminal command blocklist (destructive commands blocked)
- Security audit log (all auth events recorded)
- Windows Defender scanner simulation
- Secure encrypted vault with TOTP 2FA simulation
- Intrusion Detection System monitor

Security/Destructive actions are intentionally limited to assistant data directory only.
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import simpledialog, messagebox, filedialog, ttk
import os
import json
import hashlib
import shutil
import subprocess
import webbrowser
import csv
import re
import ast
import struct
import urllib.parse
import random
import time
import math
import threading
import pyttsx3
import speech_recognition as sr
import calendar
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

def show_winver():
    winver_text = (
        "Microsoft Windows 7 Simulation\n"
        "Version 6.1 (Build 7601: Service Pack 1)\n"
        "Copyright © 2009-2026 Microsoft Corporation. All rights reserved.\n\n"
        "This simulation is an open-source fan project created for educational "
        "purposes and is not affiliated with Microsoft."
    )
    messagebox.showinfo("About Windows", winver_text)

# --- New Modular Imports (v2.0) ---
try:
    from config import (
        AERO_BLUE, AERO_LIGHT, AERO_DARK, DEFAULT_STATE,
        BIOS_DEFAULTS, AI_RECOMMENDATIONS, DESTRUCTIVE_COMMANDS
    )
except ImportError:
    AERO_BLUE = '#4f80d4'
    AERO_LIGHT = '#dce9f8'
    AERO_DARK = '#1c3f73'

try:
    from bios_simulator import get_bios, get_repair_system
    BIOS_AVAILABLE = True
except ImportError:
    BIOS_AVAILABLE = False

try:
    from ai_recommendations import get_ai_assistant
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    from system_repair import show_repair_automation_ui
    REPAIR_AVAILABLE = True
except ImportError:
    REPAIR_AVAILABLE = False

try:
    from features_expansion import (
        get_all_features, get_features_by_category, count_features,
        show_features_browser, SYSTEM_UTILITIES, PRODUCTIVITY_TOOLS,
        GAMES_ENTERTAINMENT, CREATIVE_TOOLS, LEARNING_EDUCATION,
        MONITORING_DIAGNOSTICS, CUSTOMIZATION_SETTINGS,
        COMMUNICATION_SOCIAL, UTILITIES_HELPERS, ADVANCED_FEATURES
    )
    FEATURES_AVAILABLE = True
except ImportError:
    FEATURES_AVAILABLE = False

try:
    import winsound
except Exception:
    winsound = None
try:
    import psutil
except Exception:
    psutil = None
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

# --- Paths and storage ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'celine_data')
QUARANTINE_ROOT = os.path.join(BASE_DIR, 'quarantine_storage')
RECYCLE_DIR = os.path.join(DATA_DIR, 'recycle_bin')
SEC_FILE = os.path.join(DATA_DIR, 'security.json')
MEMORY_FILE = os.path.join(DATA_DIR, 'celine_memory.json')
SHUTDOWN_FLAG = os.path.join(BASE_DIR, 'shutdown.lock')
AUDIT_LOG_FILE = os.path.join(DATA_DIR, 'security_audit.log')
VAULT_FILE = os.path.join(DATA_DIR, 'secure_vault.enc')
ENC_SUFFIX = '.enc'

# ── Brute-force login lockout state (in-memory, resets on app restart) ───────
_login_attempts = {'count': 0, 'locked_until': 0.0}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 30

ACTIVE_APPS = {} # Global tracker for taskbar: {window: button}

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(QUARANTINE_ROOT, exist_ok=True)
os.makedirs(RECYCLE_DIR, exist_ok=True)

# --- Minimal persistent state ---
# --- Minimal persistent state ---
state = {
    'user_name': 'User',
    'first_name': 'Generic',
    'last_name': 'Account',
    'notes': [],
    'tasks': [],
    'remember_me': False,
    'preferences': {'voice': 'male'},
    'ram_size': '8GB',
    'user_age': '20',
    'os_version': 'Ultimate',
    'welcome_sound_path': '',
    'volume': 55,
    'drivers_installed': True,
    'show_driver_prompt': False,
    'signin_mode': 'Aero',
    'core_deleted': False,
    'bios_security_disabled': False,   # True = security off, dangerous cmds allowed
    'os_corrupted': False,             # True = every boot attempt triggers BSOD
    'journal': [],
    'alarms': [],
    'bookmarks': [],
    'chat_history': [],
    'pomodoro_sessions': 0,
    'habit_tracker': {},
    'shortcuts': {},
    'clipboard_history': [],
    'weather_city': 'New York',
    'security_features': {
        'firewall': True,
        'virus_protection': True,
        'account_protection': True,
        'system_guard': True,
        'driver_support': True,
    },
}


# --- Voice setup ---
engine = pyttsx3.init()
engine.setProperty('rate', 150)
managed_windows = []

# --- New UI Helpers ---
def create_glass_gradient(canvas, width, height):
    """Simulates realistic Windows 7 Aero glass — multi-stop gradient with gloss sheen."""
    # Deep blue base fill
    canvas.create_rectangle(0, 0, width, height, fill='#b8d4ee', outline='')
    # Multi-stop vertical gradient
    stops = [
        (0,   0xf0, 0xf8, 0xff),
        (int(height*0.12), 0xd8, 0xee, 0xff),
        (int(height*0.45), 0xa0, 0xcc, 0xf0),
        (int(height*0.70), 0x78, 0xb0, 0xe0),
        (int(height*0.88), 0x58, 0x90, 0xcc),
        (height-1, 0x38, 0x70, 0xb0),
    ]
    for i in range(len(stops)-1):
        y0, r0, g0, b0 = stops[i]
        y1, r1, g1, b1 = stops[i+1]
        for y in range(y0, y1+1):
            t = (y-y0)/(y1-y0) if y1 > y0 else 0
            r = int(r0+(r1-r0)*t)
            g = int(g0+(g1-g0)*t)
            b = int(b0+(b1-b0)*t)
            canvas.create_line(0, y, width, y, fill=f'#{r:02x}{g:02x}{b:02x}')
    # Gloss sheen on top third
    sheen_h = height // 3
    canvas.create_polygon(
        0, 0, width, 0, width, sheen_h, 0, sheen_h,
        fill='#e8f6ff', outline='', stipple='gray50')
    # Subtle inner highlight line
    canvas.create_line(1, 1, width-1, 1, fill='#ffffff', width=1)
    # Bottom shadow line
    canvas.create_line(0, height-1, width, height-1, fill='#8ab0cc', width=1)
    # Cross-hatch texture at bottom
    for i in range(0, width, 20):
        canvas.create_line(i, height-12, i+12, height,
                           fill='#ffffff', width=1, stipple='gray25')


def _draw_rounded_rect(canvas, x1, y1, x2, y2, r=12, **kwargs):
    """Draw a rounded rectangle on a canvas."""
    r = min(r, (x2-x1)//2, (y2-y1)//2)
    fill   = kwargs.get('fill', '')
    outline = kwargs.get('outline', '')
    width  = kwargs.get('width', 1)
    # Main body
    canvas.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline='')
    canvas.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline='')
    # Corners
    for cx, cy, s, e in [
        (x1, y1, 90,  180),
        (x2-2*r, y1, 0,   90),
        (x1, y2-2*r, 180, 270),
        (x2-2*r, y2-2*r, 270, 360),
    ]:
        canvas.create_arc(cx, cy, cx+2*r, cy+2*r,
                          start=s, extent=90,
                          fill=fill, outline='', style='pieslice')
    # Outline arcs
    if outline:
        for cx, cy, s in [
            (x1, y1, 90),
            (x2-2*r, y1, 0),
            (x1, y2-2*r, 180),
            (x2-2*r, y2-2*r, 270),
        ]:
            canvas.create_arc(cx, cy, cx+2*r, cy+2*r,
                              start=s, extent=90,
                              outline=outline, style='arc', width=width)
        canvas.create_line(x1+r, y1,   x2-r, y1,   fill=outline, width=width)
        canvas.create_line(x1+r, y2,   x2-r, y2,   fill=outline, width=width)
        canvas.create_line(x1,   y1+r, x1,   y2-r, fill=outline, width=width)
        canvas.create_line(x2,   y1+r, x2,   y2-r, fill=outline, width=width)

def center_window(win, width, height):
    win.update_idletasks()
    sc_w = win.winfo_screenwidth()
    sc_h = win.winfo_screenheight()
    x = (sc_w // 2) - (width // 2)
    y = (sc_h // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def apply_aero_widget_style(win):
    try:
        win.option_add('*Listbox.selectBackground', '#4f80d4')
        win.option_add('*Listbox.selectForeground', 'white')
        win.option_add('*Listbox.activestyle', 'none')
        win.option_add('*Text.selectBackground', '#4f80d4')
        win.option_add('*Text.selectForeground', 'white')
        win.option_add('*Entry.highlightbackground', '#4f80d4')
        win.option_add('*Entry.highlightcolor', '#4f80d4')
        win.option_add('*Button.relief', 'flat')
    except Exception:
        pass


def create_curvy_panel(parent, width=520, height=70, bg='#ffffff', outline='#7aa6d8', radius=16):
    canvas = tk.Canvas(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0, bd=0)
    create_rounded_rect(canvas, 2, 2, width-2, height-2, r=radius, fill=bg, outline=outline, width=1)
    inner = tk.Frame(canvas, bg=bg)
    canvas.create_window(4, 4, anchor='nw', window=inner, width=width-8, height=height-8)
    return canvas, inner


def check_drivers(feature_name):
    if not state.get('drivers_installed', True):
        messagebox.showwarning("Hardware Error", f"{feature_name} requires drivers. Please install them in Windows Security > Advanced.")
        return False
    return True


def open_path_in_system(path):
    try:
        if os.path.exists(path):
            os.startfile(path)
            return True
    except Exception:
        try:
            subprocess.run(f'start "" "{path}"', shell=True, check=False)
            return True
        except Exception:
            pass
    return False

# --- Utilities ---
def load_state():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                s = json.load(f)
                state.update(s)
    except Exception:
        pass


def save_state():
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    pwd = password.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd, salt, 200000)
    return salt.hex(), key.hex()


def verify_password(password, salt_hex, key_hex):
    salt = bytes.fromhex(salt_hex)
    _, candidate = hash_password(password, salt)
    return candidate == key_hex


def load_security():
    if os.path.exists(SEC_FILE):
        try:
            with open(SEC_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_security(sec):
    try:
        with open(SEC_FILE, 'w', encoding='utf-8') as f:
            json.dump(sec, f, indent=2)
    except Exception:
        pass


# ── Security Audit Log ────────────────────────────────────────────────────────
def audit_log(event: str, detail: str = '', severity: str = 'INFO') -> None:
    """Append a timestamped entry to the security audit log file."""
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{ts}] [{severity:<8}] {event}'
        if detail:
            line += f' — {detail}'
        with open(AUDIT_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def read_audit_log(max_lines: int = 200) -> list:
    """Return the last max_lines entries from the audit log."""
    try:
        if not os.path.exists(AUDIT_LOG_FILE):
            return ['No audit events yet.']
        with open(AUDIT_LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()
        return lines[-max_lines:] if lines else ['Empty log.']
    except Exception:
        return ['Could not read audit log.']


# --- Security helpers ---
security = load_security()


def ensure_password_set():
    global security
    if 'salt' in security and 'key' in security:
        return True
    # Prompt to set password
    pwd = simpledialog.askstring('Set Password', 'No assistant password found. Create a password:', show='*')
    if not pwd:
        return False
    salt, key = hash_password(pwd)
    security = {'salt': salt, 'key': key}
    save_security(security)
    messagebox.showinfo('Password Set', 'Assistant password created.')
    return True


def ask_password(prompt='Enter password'):
    pwd = simpledialog.askstring('Password', prompt, show='*')
    return pwd


def check_password(prompt='Enter password'):
    sec = load_security()
    if not sec or 'salt' not in sec or 'key' not in sec:
        return False
    pwd = ask_password(prompt)
    if not pwd:
        return False
    return verify_password(pwd, sec['salt'], sec['key'])


def change_password():
    if not check_password('Current password'):
        messagebox.showwarning('Denied', 'Current password incorrect.')
        return
    new = simpledialog.askstring('New password', 'Enter new password:', show='*')
    if not new:
        return
    salt, key = hash_password(new)
    save_security({'salt': salt, 'key': key})
    messagebox.showinfo('Updated', 'Password updated.')

# --- Emergency shutdown (quarantine) ---

def emergency_shutdown():
    if not check_password('Confirm emergency shutdown password'):
        messagebox.showwarning('Cancelled', 'Password verification failed.')
        return
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    quarantine = os.path.join(QUARANTINE_ROOT, 'celine_data_' + ts)
    try:
        if os.path.exists(QUARANTINE_ROOT) and os.path.exists(DATA_DIR):
            shutil.move(DATA_DIR, quarantine)
            with open(SHUTDOWN_FLAG, 'w', encoding='utf-8') as f:
                f.write(quarantine)
            messagebox.showinfo('Shutdown', f'Data quarantined to:\n{quarantine}\nAssistant disabled.')
            root.destroy()
        else:
            messagebox.showerror('Error', 'No active assistant data found to quarantine.')
    except Exception as e:
        messagebox.showerror('Error', 'Could not quarantine data: ' + str(e))

# --- File management (only within DATA_DIR) ---

def list_data_files():
    items = []
    for fname in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, fname)
        if os.path.isfile(path):
            items.append(path)
    return items


def delete_data_file(path, permanent=False):
    # Only allow deleting files inside DATA_DIR
    try:
        norm = os.path.normpath(path)
        if not norm.startswith(os.path.normpath(DATA_DIR)):
            return False, 'Not allowed'
        if permanent:
            os.remove(norm)
            return True, 'Permanently deleted.'
        else:
            qdir = os.path.join(DATA_DIR, 'quarantine')
            os.makedirs(qdir, exist_ok=True)
            dest = os.path.join(qdir, os.path.basename(norm))
            shutil.move(norm, dest)
            return True, f'Moved to quarantine: {dest}'
    except Exception as e:
        return False, str(e)

# --- Encryption helpers ---

def derive_key(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200000, dklen=16)
    return salt, key


def xtea_encrypt_block(block, key):
    v0, v1 = struct.unpack('>2I', block)
    k = struct.unpack('>4I', key)
    sum_ = 0
    delta = 0x9E3779B9
    for _ in range(32):
        v0 = (v0 + (((v1 << 4 ^ v1 >> 5) + v1) ^ (sum_ + k[sum_ & 3]))) & 0xFFFFFFFF
        sum_ = (sum_ + delta) & 0xFFFFFFFF
        v1 = (v1 + (((v0 << 4 ^ v0 >> 5) + v0) ^ (sum_ + k[(sum_ >> 11) & 3]))) & 0xFFFFFFFF
    return struct.pack('>2I', v0, v1)


def xtea_ctr_encrypt(data, key, nonce):
    result = bytearray()
    counter = int.from_bytes(nonce, 'big')
    for i in range(0, len(data), 8):
        block = data[i:i+8]
        ctr = (counter + (i // 8)).to_bytes(8, 'big')
        keystream = xtea_encrypt_block(ctr, key)
        result.extend(bytes(a ^ b for a, b in zip(block, keystream[:len(block)])))
    return bytes(result)


def encrypt_bytes(data, password):
    salt, key = derive_key(password)
    nonce = os.urandom(8)
    ciphertext = xtea_ctr_encrypt(data, key, nonce)
    return salt + nonce + ciphertext


def decrypt_bytes(payload, password):
    try:
        salt = payload[:16]
        nonce = payload[16:24]
        ciphertext = payload[24:]
        _, key = derive_key(password, salt)
        return xtea_ctr_encrypt(ciphertext, key, nonce)
    except Exception:
        raise ValueError('Decryption failed')


def encrypt_data_file(path):
    if not os.path.exists(path):
        return False, 'File not found'
    pwd = ask_password('Enter password for encryption')
    if not pwd:
        return False, 'Password required'
    try:
        with open(path, 'rb') as f:
            data = f.read()
        payload = encrypt_bytes(data, pwd)
        out = path + ENC_SUFFIX
        with open(out, 'wb') as f:
            f.write(payload)
        os.remove(path)
        return True, f'Encrypted to {out}'
    except Exception as e:
        return False, str(e)


def decrypt_data_file(path):
    if not os.path.exists(path) or not path.endswith(ENC_SUFFIX):
        return False, 'Encrypted file required'
    pwd = ask_password('Enter password to decrypt file')
    if not pwd:
        return False, 'Password required'
    try:
        with open(path, 'rb') as f:
            payload = f.read()
        clear = decrypt_bytes(payload, pwd)
        out = path[:-len(ENC_SUFFIX)]
        with open(out, 'wb') as f:
            f.write(clear)
        os.remove(path)
        return True, f'Decrypted to {out}'
    except Exception as e:
        return False, str(e)


def restore_quarantine():
    if not check_password('Enter password to restore assistant'):
        return False
    if not os.path.exists(SHUTDOWN_FLAG):
        return False
    try:
        with open(SHUTDOWN_FLAG, 'r', encoding='utf-8') as f:
            path = f.read().strip()
    except Exception:
        return False
    if not path or not os.path.exists(path):
        return False
    try:
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        shutil.move(path, DATA_DIR)
        os.remove(SHUTDOWN_FLAG)
        return True
    except Exception:
        return False

# --- Deep search and handover ---

def deep_search(query):
    # Search notes, tasks, and text files in DATA_DIR
    results = []
    q = query.lower()
    for n in state.get('notes', []):
        if q in n.get('text', '').lower():
            results.append({'type': 'note', 'id': n['id'], 'text': n['text']})
    for t in state.get('tasks', []):
        if q in t.get('task', '').lower():
            results.append({'type': 'task', 'id': t['id'], 'text': t['task']})
    for fname in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, fname)
        if os.path.isfile(path) and fname.lower().endswith(('.txt', '.md', '.log', '.json')):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if q in content.lower():
                    results.append({'type': 'file', 'path': path, 'excerpt': excerpt(content, q)})
            except Exception:
                pass
    return results


def excerpt(text, q, radius=40):
    i = text.lower().find(q)
    if i == -1:
        return text[:120]
    start = max(0, i - radius)
    end = min(len(text), i + len(q) + radius)
    return text[start:end].replace('\n', ' ')

# --- Basic assistant features ---

def safe_eval(expr):
    expr = expr.replace('^', '**')
    node = ast.parse(expr, mode='eval')
    def walk(n):
        if isinstance(n, ast.Expression):
            return walk(n.body)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float)):
                return n.value
            raise ValueError('Invalid constant')
        if isinstance(n, ast.BinOp):
            left = walk(n.left)
            right = walk(n.right)
            if isinstance(n.op, ast.Add):
                return left + right
            if isinstance(n.op, ast.Sub):
                return left - right
            if isinstance(n.op, ast.Mult):
                return left * right
            if isinstance(n.op, ast.Div):
                return left / right
            if isinstance(n.op, ast.Mod):
                return left % right
            if isinstance(n.op, ast.Pow):
                return left ** right
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            value = walk(n.operand)
            return +value if isinstance(n.op, ast.UAdd) else -value
        raise ValueError('Unsupported')
    return walk(node)

# --- App launching (safe mapping) ---
APP_MAP = {
    'google': lambda: show_google_app(),
    'notepad': lambda: show_text_editor(),
    'text editor': lambda: show_text_editor(),
    'calculator': lambda: show_calculator_app(),
    'file explorer': lambda: show_file_explorer(),
    'explorer': lambda: show_file_explorer(),
    'wifi': lambda: show_wifi_manager(),
    'paint': lambda: show_paint_app(),
    'system info': lambda: show_system_info_app(),
    'settings': lambda: show_settings_app(),
    'control panel': lambda: show_control_panel(),
    'action center': lambda: show_action_center(),
    'device manager': lambda: show_device_manager(),
    'network center': lambda: show_network_center(),
    'windows update': lambda: show_windows_update(),
    'update': lambda: show_windows_update(),
    'gadgets': lambda: show_gadgets(),
    'media center': lambda: show_windows_media_center(),
    'security center': lambda: show_windows_security(),
    'minesweeper': lambda: show_minesweeper_game(),
    'tic tac toe': lambda: show_tic_tac_toe_game(),
    'guess the number': lambda: show_guess_number_game(),
    'system monitor': lambda: show_system_monitor(),
    'monitor': lambda: show_system_monitor(),
    'performance': lambda: show_system_monitor(),
    'task manager': lambda: show_task_manager(),
    'tasks': lambda: show_task_manager(),
    'themes': lambda: show_themes(),
    'personalize': lambda: show_themes(),
    'appearance': lambda: show_themes(),
    'volume': lambda: show_volume_control(),
    'sound': lambda: show_volume_control(),
    'volume mixer': lambda: show_volume_control(),
    'disk cleanup': lambda: show_disk_cleaner(),
    'cleanup': lambda: show_disk_cleaner(),
    'disk cleaner': lambda: show_disk_cleaner(),
    'snake': lambda: show_snake_game(),
    'sticky notes': lambda: show_sticky_notes(),
    'calendar': lambda: show_calendar_app(),
    'installer': lambda: show_windows_installer_helper(),
    'installer helper': lambda: show_windows_installer_helper(),
    'boot iso': lambda: show_windows_installer_helper(),
    'aero': lambda: show_aero_glass_gallery(),
    'aero gallery': lambda: show_aero_glass_gallery(),
    'Ethernet': lambda: show_wifi_manager(),
    # --- 20 New Features ---
    'journal': lambda: show_journal(),
    'diary': lambda: show_journal(),
    'alarm': lambda: show_alarm_manager(),
    'reminder': lambda: show_alarm_manager(),
    'bookmarks': lambda: show_bookmark_manager(),
    'bookmark': lambda: show_bookmark_manager(),
    'pomodoro': lambda: show_pomodoro(),
    'focus timer': lambda: show_pomodoro(),
    'habit': lambda: show_habit_tracker(),
    'habits': lambda: show_habit_tracker(),
    'converter': lambda: show_unit_converter(),
    'unit converter': lambda: show_unit_converter(),
    'password generator': lambda: show_password_generator(),
    'text analyzer': lambda: show_text_analyzer(),
    'word count': lambda: show_text_analyzer(),
    'quote': lambda: show_quote_of_day(),
    'inspiration': lambda: show_quote_of_day(),
    'clipboard': lambda: show_clipboard_history(),
    'shortcuts': lambda: show_shortcuts_manager(),
    'world clock': lambda: show_world_clock(),
    'color picker': lambda: show_color_picker(),
    'typing test': lambda: show_typing_test(),
    'flashcards': lambda: show_math_flashcards(),
    'math flashcards': lambda: show_math_flashcards(),
    'note search': lambda: show_note_search(),
    'stopwatch': lambda: show_stopwatch(),
    'finance': lambda: show_finance_tracker(),
    'budget': lambda: show_finance_tracker(),
    'ascii art': lambda: show_ascii_art(),
    'task board': lambda: show_task_board(),
    'kanban': lambda: show_task_board(),
    # --- New v2.0 Modular Features ---
    'bios': lambda: (get_bios().show_bios_ui(desktop_win or root) if BIOS_AVAILABLE else messagebox.showwarning('BIOS', 'BIOS simulator not available. Check config.py and bios_simulator.py')),
    'bios setup': lambda: (get_bios().show_bios_ui(desktop_win or root) if BIOS_AVAILABLE else messagebox.showwarning('BIOS', 'BIOS simulator not available.')),
    'celine': lambda: (get_ai_assistant().show_ai_panel(desktop_win or root, state, get_bios().settings if BIOS_AVAILABLE else {}) if AI_AVAILABLE else messagebox.showwarning('AI', 'AI assistant not available.')),
    'ai': lambda: (get_ai_assistant().show_ai_panel(desktop_win or root, state, get_bios().settings if BIOS_AVAILABLE else {}) if AI_AVAILABLE else messagebox.showwarning('AI', 'AI assistant not available.')),
    'repair': lambda: (show_repair_automation_ui(desktop_win or root) if REPAIR_AVAILABLE else messagebox.showwarning('Repair', 'Repair automation not available.')),
    'system repair': lambda: (show_repair_automation_ui(desktop_win or root) if REPAIR_AVAILABLE else messagebox.showwarning('Repair', 'Repair automation not available.')),
    'windows repair': lambda: (show_repair_automation_ui(desktop_win or root) if REPAIR_AVAILABLE else messagebox.showwarning('Repair', 'Repair automation not available.')),
    'defender': lambda: show_windows_defender_scanner(),
    'windows defender': lambda: show_windows_defender_scanner(),
    
    # --- 350+ FEATURES EXPANSION (v2.0) ---
    # Feature Browser
    'features': lambda: (show_features_browser(desktop_win or root) if FEATURES_AVAILABLE else messagebox.showinfo('Features', '350+ features available!\nFeature browser not available.')),
    'feature browser': lambda: (show_features_browser(desktop_win or root) if FEATURES_AVAILABLE else messagebox.showinfo('Features', 'Check features_expansion.py')),
    'all features': lambda: messagebox.showinfo('Total Features', f'Celine v2.0 has {count_features() if FEATURES_AVAILABLE else "350+"} features available!'),
    
    # System Utilities (50 features)
    'ipconfig': lambda: (messagebox.showinfo('IP Configuration', 'IPv4: 192.168.1.100\nIPv6: ::1\nDHCP: Enabled'), show_system_notification('System', 'IP config displayed')),
    'ping test': lambda: messagebox.showinfo('Ping Test', 'google.com: 25ms\n8.8.8.8: 28ms\nAll hosts responding ✓'),
    'tracert': lambda: messagebox.showinfo('Trace Route', 'Route to google.com:\n1. 192.168.1.1\n2. 10.0.0.1\n3. 8.8.8.8'),
    'nslookup': lambda: messagebox.showinfo('DNS Lookup', 'google.com resolves to: 142.251.175.14'),
    'netstat': lambda: messagebox.showinfo('Network Stats', 'Active connections: 15\nListening ports: 8\nEstablished: 7'),
    'systeminfo': lambda: messagebox.showinfo('System Info', f'Windows 7 Ultimate\nProcessor: Intel Core i7\nRAM: 8GB\nUptime: 2 days, 14 hours'),
    'tree': lambda: messagebox.showinfo('Directory Tree', 'c:\\\n├── Windows\n├── Program Files\n├── Users\n└── Documents'),
    'fc': lambda: messagebox.showinfo('File Compare', 'Comparing files...\nDifferences found: 3 lines'),
    'chkdsk': lambda: messagebox.showinfo('Check Disk', 'Scanning disk sectors...\nNo errors found ✓'),
    'defrag': lambda: messagebox.showinfo('Defragmentation', 'Defragmenting drive C:\n0% ... 100% Complete!\nDisk optimized ✓'),
    
    # Productivity Tools (60 features)
    'calendar': lambda: messagebox.showinfo('Calendar', f'June 2026\nToday: 13th\nUpcoming events: 3'),
    'daily planner': lambda: messagebox.showinfo('Daily Planner', '09:00 - Team Meeting\n11:00 - Project Review\n14:00 - Client Call\n16:00 - Documentation'),
    'project manager': lambda: messagebox.showinfo('Project Manager', 'Active Projects: 5\nCompleted: 12\nDeadline Today: 1'),
    'notes': lambda: messagebox.showinfo('Notes', 'Recent notes:\n1. Meeting notes\n2. Todo list\n3. Code snippets'),
    'wiki': lambda: messagebox.showinfo('Personal Wiki', 'Pages: 45\nRecent edits: 3 today'),
    'form builder': lambda: messagebox.showinfo('Form Builder', 'Create surveys and questionnaires\nTemplates available: 15'),
    'email client': lambda: messagebox.showinfo('Email', 'Inbox: 12 messages\nUnread: 3\nSent: 2 today'),
    'contact manager': lambda: messagebox.showinfo('Contacts', 'Total contacts: 145\nRecent: 5\nFavorites: 8'),
    'email templates': lambda: messagebox.showinfo('Email Templates', 'Available templates:\n1. Business\n2. Personal\n3. Support\n4. Newsletter'),
    'appointment booking': lambda: messagebox.showinfo('Appointments', 'Available slots today: 4\nBookings: 3'),
    'room scheduler': lambda: messagebox.showinfo('Room Booking', 'Available rooms:\n1. Conference A\n2. Meeting Room B\n3. Lab C'),
    'timezone converter': lambda: messagebox.showinfo('Timezone Converter', 'Current time:\nNY: 10:30 AM\nLondon: 3:30 PM\nTokyo: 11:30 PM'),
    'world timer': lambda: messagebox.showinfo('World Clock', 'New York: 10:30\nLondon: 3:30\nSydney: 12:30'),
    'invoice generator': lambda: messagebox.showinfo('Invoice', 'Generate professional invoices\nTemplates: 10'),
    'receipt printer': lambda: messagebox.showinfo('Receipt', 'Last receipt printed: Today 2:45 PM'),
    'label maker': lambda: messagebox.showinfo('Label Maker', 'Create custom labels\nSizes: 5 options'),
    'certificate maker': lambda: messagebox.showinfo('Certificate', 'Design certificates for events\nTemplates: 20'),
    
    # Games & Entertainment (60 features)
    'sudoku': lambda: messagebox.showinfo('Sudoku', 'Puzzle 1 loaded\nDifficulty: Medium\nTime: 00:00'),
    'crossword': lambda: messagebox.showinfo('Crossword', 'Daily crossword\nClues: 40\nCompleted: 15/40'),
    'solitaire': lambda: messagebox.showinfo('Solitaire', 'Starting new game...\nWins: 24\nWin rate: 48%'),
    'chess': lambda: messagebox.showinfo('Chess', 'Chess with AI\nDifficulty: Medium\nRating: 1600'),
    'checkers': lambda: messagebox.showinfo('Checkers', 'New game started\nPlay against AI'),
    'minesweeper': lambda: messagebox.showinfo('Minesweeper', 'Difficulty: Hard\nMines: 50\nBoardSize: 16x16'),
    'pac man': lambda: messagebox.showinfo('Pac-Man', 'Game Started!\nScore: 0\nLevel: 1'),
    'breakout': lambda: messagebox.showinfo('Breakout', 'Brick breaker game\nLevel: 1\nBalls: 3'),
    'hangman': lambda: messagebox.showinfo('Hangman', 'Guess the word!\nGuesses left: 6'),
    'trivia quiz': lambda: messagebox.showinfo('Trivia', 'Quiz started!\nQuestions: 10\nScore: 0/10'),
    'music trivia': lambda: messagebox.showinfo('Music Trivia', 'Music knowledge test\nDifficulty: Medium'),
    'memory match': lambda: messagebox.showinfo('Memory', 'Match the pairs!\nTime: 00:00\nMatches: 0/8'),
    'typing race': lambda: messagebox.showinfo('Typing Race', 'Race against AI\nWPM: 0\nAccuracy: 0%'),
    'dice roller': lambda: messagebox.showinfo('Dice Roller', 'Roll: [4, 2, 5, 1, 6]\nTotal: 18'),
    'coin flipper': lambda: messagebox.showinfo('Coin Flip', 'Result: HEADS'),
    'higher lower': lambda: messagebox.showinfo('Higher or Lower', 'Card: 7♠\nGuess higher or lower?'),
    'lucky draw': lambda: messagebox.showinfo('Lucky Draw', 'Drawing... Winner!\nTicket #: 4782'),
    'fortune teller': lambda: messagebox.showinfo('Fortune', '🔮 Your fortune:\n"Great things await you"'),
    'music player': lambda: messagebox.showinfo('Music Player', 'Now playing: Song Name\nDuration: 3:45'),
    'slideshow': lambda: messagebox.showinfo('Slideshow', 'Photos: 245\nDuration per slide: 3s\nStarting...'),
    
    # Creative Tools (50 features)
    'paint': lambda: show_paint_app(),
    'color picker': lambda: show_color_picker(),
    'logo designer': lambda: messagebox.showinfo('Logo Designer', 'Design professional logos\nTemplates: 50'),
    'poster maker': lambda: messagebox.showinfo('Poster Maker', 'Create custom posters\nSizes: 10 options'),
    'card designer': lambda: messagebox.showinfo('Card Designer', 'Design business cards\nLayouts: 30'),
    'banner creator': lambda: messagebox.showinfo('Banner Creator', 'Create web banners\nSizes: 15 standards'),
    'infographic tool': lambda: messagebox.showinfo('Infographics', 'Design infographics\nElements: 200+'),
    'image editor': lambda: messagebox.showinfo('Image Editor', 'Filters: 25+\nEffects: 15+'),
    'photo filter': lambda: messagebox.showinfo('Photo Filters', 'Apply filters:\n1. Sepia\n2. B&W\n3. Vintage'),
    'ascii art': lambda: show_ascii_art(),
    
    # Learning & Education (40 features)
    'dictionary': lambda: messagebox.showinfo('Dictionary', 'Word: Example\nDefinition: A representative form or pattern'),
    'thesaurus': lambda: messagebox.showinfo('Thesaurus', 'Word: Happy\nSynonyms: Joyful, Cheerful, Content'),
    'calculator advanced': lambda: messagebox.showinfo('Advanced Calculator', 'Functions: Trig, Log, Exponential\nMemory: Available'),
    'periodic table': lambda: messagebox.showinfo('Periodic Table', 'Elements: 118\nGroups: 18\nPeriods: 7'),
    'typing tutor': lambda: messagebox.showinfo('Typing Tutor', 'Lesson 1: Home row keys\nWPM target: 60'),
    'vocabulary builder': lambda: messagebox.showinfo('Vocabulary', 'Words learned today: 5\nTotal: 250'),
    'flashcard quiz': lambda: messagebox.showinfo('Flashcards', 'Deck: Spanish 101\nCards: 50\nLearning: 20'),
    
    # Monitoring & Diagnostics (40 features)
    'cpu monitor': lambda: messagebox.showinfo('CPU Monitor', 'Usage: 15%\nSpeed: 2.4 GHz\nCores: 4'),
    'memory monitor': lambda: messagebox.showinfo('Memory Monitor', 'RAM Used: 4.2 GB / 8 GB\nUsage: 52.5%'),
    'disk monitor': lambda: messagebox.showinfo('Disk Monitor', 'C: Used: 180 GB / 500 GB (36%)\nFree: 320 GB'),
    'network monitor': lambda: messagebox.showinfo('Network Monitor', 'Upload: 125 KB/s\nDownload: 450 KB/s\nPing: 25ms'),
    'temperature monitor': lambda: messagebox.showinfo('Temperature', 'CPU: 45°C\nGPU: 52°C\nHDD: 38°C'),
    'process monitor': lambda: messagebox.showinfo('Process Monitor', 'Running processes: 150\nCritical: 8'),
    'system health': lambda: messagebox.showinfo('System Health', 'Overall: EXCELLENT\nSecurity: Protected\nPerformance: Optimal'),
    'virus scanner': lambda: messagebox.showinfo('Virus Scan', 'Starting quick scan...\nFiles scanned: 0/50000'),
    'backup checker': lambda: messagebox.showinfo('Backup Status', 'Last backup: 2 hours ago\nBackup size: 2.5 GB'),
    'error log viewer': lambda: messagebox.showinfo('Error Log', 'Errors today: 2\nWarnings: 5'),
    
    # Customization & Settings (40 features)
    'wallpaper': lambda: messagebox.showinfo('Wallpaper', 'Available wallpapers: 50+\nCurrent: Windows 7 Default'),
    'theme': lambda: show_themes(),
    'font size': lambda: messagebox.showinfo('Font Size', 'Current: 11pt\nOptions: 9pt-16pt'),
    'color scheme': lambda: messagebox.showinfo('Colors', 'Schemes available: 15\nCurrent: Aero Blue'),
    'sound theme': lambda: messagebox.showinfo('Sounds', 'Themes: 10+\nCurrent: Windows 7'),
    'keyboard layout': lambda: messagebox.showinfo('Keyboard', 'Current: English (US)\nAvailable: 50+ layouts'),
    'mouse speed': lambda: messagebox.showinfo('Mouse', 'Speed: 5/10\nAcceleration: Enabled'),
    'power settings': lambda: messagebox.showinfo('Power Options', 'Plan: Balanced\nSleep: 15 min\nHibernate: Enabled'),
    'startup programs': lambda: messagebox.showinfo('Startup', 'Enabled: 8\nDisabled: 12\nTotal: 20'),
    'accessibility': lambda: messagebox.showinfo('Accessibility', 'High Contrast: Off\nMagnifier: Off\nNarrator: Off'),
    
    # Communication & Social (30 features)
    'contact list': lambda: messagebox.showinfo('Contacts', 'Total: 145\nRecent: 5\nFavorites: 10'),
    'email': lambda: messagebox.showinfo('Email', 'Inbox: 12\nUnread: 3\nFolders: 8'),
    'message history': lambda: messagebox.showinfo('Messages', 'Total: 450\nToday: 15'),
    'notification center': lambda: messagebox.showinfo('Notifications', 'Pending: 5\nRecent: 2'),
    'reminder service': lambda: messagebox.showinfo('Reminders', 'Active: 3\nToday: 1'),
    'feed reader': lambda: messagebox.showinfo('RSS Feeds', 'Subscribed: 10\nNew articles: 25'),
    'news aggregator': lambda: messagebox.showinfo('News', 'Sources: 15\nArticles: 250+'),
    'podcast player': lambda: messagebox.showinfo('Podcasts', 'Subscribed: 5\nNew episodes: 3'),
    'playlist manager': lambda: messagebox.showinfo('Playlists', 'Playlists: 8\nSongs: 450+'),
    'shared folder': lambda: messagebox.showinfo('Shared Folders', 'Shared: 3\nTotal size: 5 GB'),
    
    # Utilities & Helpers (50 features)
    'text converter': lambda: messagebox.showinfo('Text Converter', 'Convert: UPPER, lower, Title Case'),
    'unit converter': lambda: show_unit_converter(),
    'currency converter': lambda: messagebox.showinfo('Currency', '1 USD = 0.92 EUR\n1 GBP = 1.27 USD'),
    'temperature converter': lambda: messagebox.showinfo('Temperature', '32°F = 0°C\n98.6°F = 37°C'),
    'base converter': lambda: messagebox.showinfo('Base Converter', '255 (decimal) = FF (hex) = 11111111 (binary)'),
    'calculator': lambda: show_calculator_app(),
    'mortgage calculator': lambda: messagebox.showinfo('Mortgage', 'Loan: $300,000\nRate: 4%\nMonthly: $1,432'),
    'loan calculator': lambda: messagebox.showinfo('Loan', 'Calculate loan payments\nInterest: Configurable'),
    'investment calculator': lambda: messagebox.showinfo('Investment', 'Initial: $10,000\nRate: 8%\nFuture: $46,610'),
    'tax calculator': lambda: messagebox.showinfo('Tax', 'Income: $50,000\nTax rate: 22%\nTax: $11,000'),
    'tip calculator': lambda: messagebox.showinfo('Tip', 'Bill: $100\nTip %: 18%\nTip: $18'),
    'file merger': lambda: messagebox.showinfo('File Merger', 'Merge multiple files\nFormats: TXT, PDF, CSV'),
    'file splitter': lambda: messagebox.showinfo('File Splitter', 'Split large files\nChunk size: Configurable'),
    'duplicate finder': lambda: messagebox.showinfo('Duplicate Finder', 'Files scanned: 15,000\nDuplicates found: 250'),
    'batch rename': lambda: messagebox.showinfo('Batch Rename', 'Files selected: 0\nPattern: [date]-[name]'),
    'find replace': lambda: messagebox.showinfo('Find & Replace', 'Find: [pattern]\nReplace: [text]'),
    'text cleaner': lambda: messagebox.showinfo('Text Cleaner', 'Remove extra spaces, special chars'),
    'text splitter': lambda: messagebox.showinfo('Text Splitter', 'Split by: Line, Word, Comma'),
    
    # Advanced Features (40+ features)
    'macro recorder': lambda: messagebox.showinfo('Macro', 'Record: Start/Stop\nMacros saved: 5'),
    'task scheduler': lambda: messagebox.showinfo('Scheduler', 'Scheduled tasks: 8\nNext: 14:30'),
    'batch processor': lambda: messagebox.showinfo('Batch', 'Process files in bulk\nTemplates: 10'),
    'workflow builder': lambda: messagebox.showinfo('Workflow', 'Workflows created: 3\nActive: 1'),
    'script editor': lambda: messagebox.showinfo('Script Editor', 'Languages: Batch, PowerShell, Python'),
    'api connector': lambda: messagebox.showinfo('API', 'Connected APIs: 0\nSaved endpoints: 5'),
    'database viewer': lambda: messagebox.showinfo('Database', 'Databases: 0\nTables: 0'),
    'backup manager': lambda: messagebox.showinfo('Backup', 'Last backup: 2h ago\nBackups: 10'),
    'restore manager': lambda: messagebox.showinfo('Restore', 'Available backups: 10\nLatest: Today 12:00'),
    'data analyzer': lambda: messagebox.showinfo('Data Analysis', 'Analyze CSV, Excel, JSON'),
    'report generator': lambda: messagebox.showinfo('Reports', 'Templates: 25\nGenerated: 15'),
    'plugin manager': lambda: messagebox.showinfo('Plugins', 'Installed: 8\nAvailable: 50+'),
}


def launch_app(name):
    cmd_text = name.lower()
    if cmd_text.startswith('launch '):
        cmd_text = cmd_text[7:]
    parts = re.split(r'[\.;,]+', cmd_text)
    launched = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        matched = False
        for key in APP_MAP:
            if key in part:
                try:
                    # ── Terminal feature-block gate ────────────────────────
                    if key in _TERMINAL_BLOCKED_FEATURES:
                        msg = f'⛔ "{key}" is BLOCKED by Terminal. Use: unblock {key}'
                        launched.append(msg)
                        show_system_notification('Access Denied', msg)
                        matched = True
                        break
                    # ── BIOS block gate ────────────────────────────────────
                    if _BIOS_BLOCKED and key in ('bios', 'bios setup'):
                        msg = '🔐 BIOS is LOCKED by Terminal. Run: unlock-bios'
                        launched.append(msg)
                        show_system_notification('BIOS Locked', msg)
                        matched = True
                        break
                    # ── Activation gate ────────────────────────────────────
                    if not state.get('activated', False) and key not in _ACTIVATION_FREE:
                        _require_activation(key.title())
                    else:
                        APP_MAP[key]()
                    launched.append(key)
                    matched = True
                    break
                except Exception as e:
                    launched.append(f'{key} failed: {e}')
                    matched = True
                    break
        if not matched:
            launched.append(f'Unknown: {part}')
    if not launched:
        return 'Application not recognized.'
    return ' | '.join(launched)

# --- OS-style desktop helpers ---
login_win = None
desktop_win = None
desktop_bg_label = None
desktop_wallpaper_image = None
desktop_start_menu = None
desktop_center_frame = None
desktop_term_output = None
desktop_term_entry = None
taskbar = None
taskbar_overlay = None


def play_windows7_beep_sequence(sequence):
    """Play a sequence of (freq, duration_ms) beeps in a background thread."""
    if not winsound:
        return
    def _play():
        for freq, duration in sequence:
            try:
                winsound.Beep(freq, duration)
            except Exception:
                pass
    threading.Thread(target=_play, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTIC WINDOWS 7 SOUND SIGNATURES
# Each sequence is carefully tuned to match the real Windows 7 audio profile.
# The real W7 sounds are multi-note chords/arpeggios — recreated here with
# precise frequencies and timings matched to the original soundscape.
# ─────────────────────────────────────────────────────────────────────────────

def play_windows7_logon():
    """Windows 7 Startup Sound — the iconic ascending 4-note W7 chime."""
    sound_path = state.get('welcome_sound_path', '')
    if sound_path and os.path.exists(sound_path):
        try:
            if winsound:
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                os.startfile(sound_path)
        except Exception:
            pass
        return
    if winsound and hasattr(winsound, 'Beep'):
        # Real W7 startup: warm ascending notes with slight bell quality
        # D4 → F#4 → A4 → D5 (D major arpeggio, the actual W7 key)
        sequence = [
            (294, 180),   # D4  — deep warm opening note
            (370, 160),   # F#4 — mid rise
            (494, 140),   # B4  — bright peak
            (587, 90),    # D5  — quick top note
            (494, 100),   # B4  — gentle fall
            (740, 260),   # F#5 — final soaring note (the signature W7 tail)
        ]
        play_windows7_beep_sequence(sequence)


def play_windows7_logoff():
    """Windows 7 Logoff/Shutdown Sound — descending warm chord."""
    if winsound and hasattr(winsound, 'Beep'):
        # Descending mirror of the logon, ends on a low stable note
        sequence = [
            (587, 100),   # D5
            (494, 100),   # B4
            (370, 130),   # F#4
            (294, 200),   # D4  — settle
        ]
        play_windows7_beep_sequence(sequence)


def play_windows7_notification():
    """Windows 7 Notification / New Mail sound — bright two-tone chime."""
    if winsound and hasattr(winsound, 'Beep'):
        # Clean double-chime matching the W7 'Windows Notify' .wav
        sequence = [
            (880, 80),    # A5 — bright ding
            (1108, 140),  # C#6 — sparkle tail
        ]
        play_windows7_beep_sequence(sequence)


def play_windows7_error():
    """Windows 7 Critical Stop / Error Sound."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [
            (300, 200),   # Low buzz
            (250, 300),   # Drop
        ]
        play_windows7_beep_sequence(sequence)


def play_windows7_exclamation():
    """Windows 7 Exclamation / Warning Sound."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [
            (523, 80),    # C5
            (659, 80),    # E5
            (784, 120),   # G5
        ]
        play_windows7_beep_sequence(sequence)


def play_windows7_asterisk():
    """Windows 7 Asterisk / Information Sound — gentle single chime."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [
            (784, 80),
            (1047, 160),
        ]
        play_windows7_beep_sequence(sequence)


def play_windows7_question():
    """Windows 7 Question / UAC prompt sound."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [
            (659, 80),    # E5
            (784, 80),    # G5
            (659, 100),   # E5 again
        ]
        play_windows7_beep_sequence(sequence)


def play_windows7_device_connect():
    """Windows 7 Hardware Insert (USB plug-in) sound."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [
            (1047, 60),   # C6
            (1319, 100),  # E6
        ]
        play_windows7_beep_sequence(sequence)


def play_windows7_device_disconnect():
    """Windows 7 Hardware Remove (USB unplug) sound."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [
            (1319, 60),   # E6
            (1047, 100),  # C6
        ]
        play_windows7_beep_sequence(sequence)


def play_windows7_minimize():
    """Soft whoosh for minimize action."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [(523, 40), (392, 50)]
        play_windows7_beep_sequence(sequence)


def play_windows7_maximize():
    """Soft whoosh for maximize action."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [(392, 40), (523, 50)]
        play_windows7_beep_sequence(sequence)


def play_windows7_menu_popup():
    """Very subtle click for menu/popup open."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [(880, 30)]
        play_windows7_beep_sequence(sequence)

def play_windows7_battery_low():
    """Windows 7 Low Battery alarm sound."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [(440, 200), (440, 200), (440, 400)]
        play_windows7_beep_sequence(sequence)


def play_windows7_recycle_empty():
    """Recycle bin empty sound — paper crumple analog."""
    if winsound and hasattr(winsound, 'Beep'):
        sequence = [(300, 40), (260, 40), (220, 80)]
        play_windows7_beep_sequence(sequence)


def show_control_panel():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Control Panel')
    win.geometry('620x440')
    style_aero_window(win, '#eef5ff')
    center_window(win, 620, 440)

    tk.Label(win, text='Control Panel', bg='#eef5ff', fg='#1c3f73', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    content = tk.Frame(win, bg='#eef5ff')
    content.pack(fill='both', expand=True, padx=16, pady=8)

    categories = [
        ('System and Security', show_windows_security),
        ('Windows Defender', show_windows_defender_scanner),
        ('Network and Internet', show_network_center),
        ('Hardware and Sound', show_volume_control),
        ('Programs', show_windows_update),
        ('User Accounts', show_settings_app),
        ('Appearance and Personalization', show_themes),
        ('Clock, Language, and Region', show_gadgets),
        ('Ease of Access', show_action_center)
    ]

    for name, action in categories:
        row = tk.Frame(content, bg='#eef5ff')
        row.pack(fill='x', pady=6)
        tk.Label(row, text=name, bg='#eef5ff', fg='#18406e', font=('Segoe UI', 11, 'bold')).pack(side='left')
        tk.Button(row, text='Open', bg='#4f80d4', fg='white', font=('Segoe UI', 9), width=10, command=lambda a=action: a()).pack(side='right', padx=8)


def show_action_center():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Action Center')
    win.geometry('520x420')
    style_aero_window(win, '#eef3ff')
    center_window(win, 520, 420)

    tk.Label(win, text='Action Center', bg='#eef3ff', fg='#1f4a7b', font=('Segoe UI', 16, 'bold')).pack(pady=(14,6))
    tk.Label(win, text='Your important alerts and quick actions are shown here.', bg='#eef3ff', fg='#3b5c88', font=('Segoe UI', 10)).pack(pady=(0,10))

    items = [
        ('Security', 'Firewall is active and protecting your PC.'),
        ('Windows Defender', 'Real-time protection is active.'),
        ('Maintenance', 'No actions needed.'),
        ('Backup', 'File History is set up.'),
        ('Network', 'Connected to Ethernet (Strong).'),
        ('Windows Update', 'No updates available.')
    ]

    for title, desc in items:
        frame = tk.Frame(win, bg='white', bd=1, relief='solid')
        frame.pack(fill='x', padx=16, pady=6)
        tk.Label(frame, text=title, bg='white', fg='#1b3c6c', font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=10, pady=(8,0))
        tk.Label(frame, text=desc, bg='white', fg='#3b4f7d', font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(0,10))

    quick = tk.Frame(win, bg='#eef3ff')
    quick.pack(fill='x', padx=16, pady=10)
    for text, action in [('Wi-Fi', show_network_center), ('Battery Saver', show_windows_security), ('Night Light', show_themes), ('Open Settings', show_settings_app)]:
        tk.Button(quick, text=text, bg='#4f80d4', fg='white', relief='flat', command=lambda a=action: a()).pack(side='left', expand=True, fill='x', padx=4, pady=2)

    tk.Button(win, text='Clear all notifications', bg='#2f5aa8', fg='white', command=lambda: messagebox.showinfo('Action Center', 'Notifications cleared.')).pack(pady=(6,0))


def show_device_manager():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Device Manager')
    win.geometry('560x420')
    style_aero_window(win, '#eef5ff')
    center_window(win, 560, 420)

    tk.Label(win, text='Device Manager', bg='#eef5ff', fg='#1f4a7b', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    frame = tk.Frame(win, bg='#eef5ff')
    frame.pack(fill='both', expand=True, padx=16, pady=8)

    devices = [
        ('Display adapters', 'Intel HD Graphics 5500'),
        ('Network adapters', 'Intel Wireless 7260'),
        ('Sound, video and game controllers', 'Realtek Audio'),
        ('Disk drives', 'Virtual Disk'),
        ('Processors', 'Intel Core i7 (4 cores)'),
        ('Universal Serial Bus controllers', 'USB Root Hub')
    ]

    for name, status in devices:
        row = tk.Frame(frame, bg='#eef5ff')
        row.pack(fill='x', pady=4)
        tk.Label(row, text=name, bg='#eef5ff', fg='#1b3e72', font=('Segoe UI', 11, 'bold')).pack(side='left')
        tk.Label(row, text=status, bg='#eef5ff', fg='#3a5480', font=('Segoe UI', 10)).pack(side='right')

    tk.Button(win, text='Scan for hardware changes', bg='#4f80d4', fg='white', command=lambda: messagebox.showinfo('Device Manager', 'Scan complete. No changes found.')).pack(pady=12)
    tk.Button(win, text='Open Driver Manager', bg='#5b98eb', fg='white', command=show_driver_manager).pack(pady=4)


def show_driver_manager():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Driver Manager')
    win.geometry('540x420')
    style_aero_window(win, '#eef5ff')
    center_window(win, 540, 420)

    tk.Label(win, text='Driver Manager', bg='#eef5ff', fg='#1f4a7b', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    frame = tk.Frame(win, bg='#eef5ff')
    frame.pack(fill='both', expand=True, padx=16, pady=8)

    installed = state.get('drivers_installed', True)
    drivers = [
        ('Intel Wireless 7260', installed),
        ('Realtek Audio', True),
        ('Intel HD Graphics 5500', installed),
        ('USB Root Hub', True),
        ('Virtual Disk', True),
        ('Secure Access Driver', installed)
    ]

    for name, present in drivers:
        row = tk.Frame(frame, bg='#eef5ff')
        row.pack(fill='x', pady=4)
        tk.Label(row, text=name, bg='#eef5ff', fg='#1b3e72', font=('Segoe UI', 11, 'bold')).pack(side='left')
        tk.Label(row, text='Installed' if present else 'Missing', bg='#eef5ff', fg='#3a5480' if present else '#d04f4f', font=('Segoe UI', 10)).pack(side='right')

    status_label = tk.Label(win, text=('All critical drivers are installed.' if installed else 'Critical drivers are missing.'), bg='#eef5ff', fg='#3b5c88', font=('Segoe UI', 10))
    status_label.pack(pady=(8,0))

    def fix_drivers():
        state['drivers_installed'] = True
        save_state()
        status_label.config(text='Drivers installed. Terminal and hardware features enabled.')
        messagebox.showinfo('Driver Manager', 'Driver repair complete. Restart the system for best results.')
    tk.Button(win, text='Repair Missing Drivers', bg='#4f80d4', fg='white', command=fix_drivers).pack(pady=10)
    tk.Button(win, text='Refresh Status', bg='#7ba4d6', fg='white', command=lambda: show_driver_manager()).pack()


def show_network_center():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Network and Sharing Center')
    win.geometry('520x420')
    style_aero_window(win, '#eef5ff')
    center_window(win, 520, 420)

    tk.Label(win, text='Network and Sharing Center', bg='#eef5ff', fg='#1f4a7b', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    tk.Label(win, text='View basic network information and set up connections.', bg='#eef5ff', fg='#3b5c88', font=('Segoe UI', 10)).pack(pady=(0,10))

    info = [
        ('Connection', 'WIN7-HOME'),
        ('Access type', 'Internet'),
        ('IPv4 address', '192.168.1.42'),
        ('IPv6 address', 'fe80::f2de:f1ff:fe07:1234'),
        ('Signal strength', 'Excellent'),
        ('Network type', 'Private')
    ]
    content = tk.Frame(win, bg='#eef5ff')
    content.pack(fill='both', expand=True, padx=16, pady=8)

    for label, value in info:
        row = tk.Frame(content, bg='#eef5ff')
        row.pack(fill='x', pady=4)
        tk.Label(row, text=label + ':', bg='#eef5ff', fg='#1c3f73', font=('Segoe UI', 10, 'bold')).pack(side='left')
        tk.Label(row, text=value, bg='#eef5ff', fg='#3a5480', font=('Segoe UI', 10)).pack(side='right')

    tk.Button(win, text='Connect to a network', bg='#4f80d4', fg='white', command=show_wifi_manager).pack(pady=12)


def show_aero_glass_gallery():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Aero Glass Gallery')
    win.geometry('540x440')
    style_aero_window(win, '#eff4ff')
    center_window(win, 540, 440)

    tk.Label(win, text='Aero Glass Gallery', bg='#eff4ff', fg='#1c4872', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    tk.Label(win, text='Preview Aero effects, flip through windows, and customize your desktop depth.', bg='#eff4ff', fg='#385b84', font=('Segoe UI', 10)).pack(pady=(0,8))

    preview_frame = tk.Frame(win, bg='#eef4ff')
    preview_frame.pack(fill='both', expand=True, padx=16, pady=10)

    cards = [
        ('Desktop Glass', 'Live transparency and blur effects.'),
        ('Flip 3D', 'Simulated window switching with classic Aero.'),
        ('Peek', 'Hover on taskbar to preview your desktop.'),
        ('Gadgets', 'Widgets for clock, weather, and CPU usage.')
    ]
    for title, desc in cards:
        card = tk.Frame(preview_frame, bg='white', bd=1, relief='solid')
        card.pack(fill='x', pady=6)
        tk.Label(card, text=title, bg='white', fg='#1b3d6d', font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=10, pady=(10,0))
        tk.Label(card, text=desc, bg='white', fg='#3a5480', font=('Segoe UI', 10), wraplength=480, justify='left').pack(anchor='w', padx=10, pady=(4,10))
        tk.Button(card, text='Apply', bg='#4f80d4', fg='white', command=lambda t=title: show_system_notification('Aero Gallery', f'Applied {t}.')).pack(anchor='e', padx=10, pady=(0,10))

    tk.Button(win, text='Open Desktop Gadgets', bg='#4f80d4', fg='white', command=show_gadgets).pack(pady=(0,8))
    tk.Button(win, text='Activate Aero Peek', bg='#5f98f1', fg='white', command=lambda: show_system_notification('Aero Peek', 'Hover over the taskbar to preview desktop.')).pack()


def show_windows_installer_helper():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Windows 7 Installer Helper')
    win.geometry('620x520')
    style_aero_window(win, '#f7f8ff')
    center_window(win, 620, 520)

    tk.Label(win, text='Windows 7 Installer Helper', bg='#f7f8ff', fg='#1c466e', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    tk.Label(win, text='Build install media, prepare virtual machines, and run compatibility checks in one place.', bg='#f7f8ff', fg='#3b5b84', font=('Segoe UI', 10), wraplength=580, justify='left').pack(pady=(0,8))

    body = tk.Frame(win, bg='#f7f8ff')
    body.pack(fill='both', expand=True, padx=16, pady=10)

    tk.Button(body, text='Create Bootable ISO', bg='#4c81d5', fg='white', width=22, command=lambda: start_installer_task('Creating bootable ISO...', win)).pack(pady=8)
    tk.Button(body, text='Prepare VirtualBox Image', bg='#4c81d5', fg='white', width=22, command=lambda: start_installer_task('Creating VirtualBox image...', win)).pack(pady=8)
    tk.Button(body, text='Run Compatibility Check', bg='#4c81d5', fg='white', width=22, command=lambda: start_installer_task('Running compatibility check...', win)).pack(pady=8)
    tk.Button(body, text='Open Installer Folder', bg='#4c81d5', fg='white', width=22, command=lambda: open_path_in_system(DATA_DIR)).pack(pady=8)

    tk.Label(body, text='Tips:', bg='#f7f8ff', fg='#2e4f74', font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(14,4))
    tk.Label(body, text='• Use the ISO tool to simulate Windows 7 install media.\n• Use VirtualBox generation for testing virtual images.\n• Save custom boot assets in the Windows 7 data folder.', bg='#f7f8ff', fg='#3b5b84', font=('Segoe UI', 9), justify='left', wraplength=560).pack(anchor='w')

    log_frame = tk.Frame(body, bg='#e9f1ff', bd=1, relief='solid')
    log_frame.pack(fill='both', expand=True, pady=(12,0))
    log_text = tk.Text(log_frame, bg='white', fg='#1c2c58', font=('Consolas', 9), wrap='word', height=8)
    log_text.pack(fill='both', expand=True, padx=6, pady=6)
    log_text.insert('end', 'Installer log will appear here...\n')
    log_text.config(state='disabled')

    def append_log(message):
        log_text.config(state='normal')
        log_text.insert('end', message + '\n')
        log_text.see('end')
        log_text.config(state='disabled')

    def start_installer_task(message, parent):
        append_log(message)
        progress = tk.Canvas(parent, width=560, height=18, bg='#dae4f4', highlightthickness=0)
        progress.pack(pady=6)
        bar = progress.create_rectangle(2, 2, 2, 16, fill='#4f81d4', outline='')
        steps = [15, 35, 55, 75, 95, 100]
        def step(i=0):
            if i < len(steps):
                progress.coords(bar, 2, 2, 2 + int(5.5 * steps[i]), 16)
                parent.after(600, lambda: step(i+1))
            else:
                append_log('Task completed successfully. Ready for the next installer action.')
                show_system_notification('Installer Helper', 'Your installer task is complete.')
        step()

    win.wait_visibility()


def show_windows_update():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Windows Update')
    win.geometry('520x380')
    style_aero_window(win, '#eef5ff')
    center_window(win, 520, 380)

    tk.Label(win, text='Windows Update', bg='#eef5ff', fg='#1f4a7b', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    status = tk.Label(win, text='Your system is up to date.', bg='#eef5ff', fg='#3b5c88', font=('Segoe UI', 11))
    status.pack(pady=(0,8))

    tk.Label(win, text='Last checked: ' + datetime.now().strftime('%Y-%m-%d %H:%M'), bg='#eef5ff', fg='#3a5480', font=('Segoe UI', 10)).pack(pady=(0,10))
    tk.Button(win, text='Check for updates', bg='#4f80d4', fg='white', command=lambda: [status.config(text='Checking for updates...'), win.after(1200, lambda: status.config(text='No updates available.'))]).pack(pady=10)
    tk.Button(win, text='View installed updates', bg='#5f9cdf', fg='white', command=lambda: messagebox.showinfo('Windows Update', 'Installed updates shown in list.')).pack(pady=6)


def show_gadgets():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Desktop Gadgets')
    win.geometry('420x440')
    style_aero_window(win, '#eef5ff')
    center_window(win, 420, 440)

    tk.Label(win, text='Desktop Gadgets', bg='#eef5ff', fg='#1f4a7b', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    tk.Label(win, text='Live widgets for clock, weather, CPU, and calendar.', bg='#eef5ff', fg='#3b5c88', font=('Segoe UI', 10)).pack(pady=(0,10))

    gadget_frame = tk.Frame(win, bg='#eef5ff')
    gadget_frame.pack(fill='both', expand=True, padx=16, pady=8)

    clock_card = tk.Frame(gadget_frame, bg='white', bd=1, relief='solid')
    clock_card.pack(fill='x', pady=6)
    clock_label = tk.Label(clock_card, text='Clock', bg='white', fg='#1b3d6d', font=('Segoe UI', 12, 'bold'))
    clock_label.pack(anchor='w', padx=10, pady=(10,0))
    clock_value = tk.Label(clock_card, text=datetime.now().strftime('%H:%M:%S'), bg='white', fg='#3a5480', font=('Segoe UI', 16, 'bold'))
    clock_value.pack(anchor='w', padx=10, pady=(4,10))

    weather_card = tk.Frame(gadget_frame, bg='white', bd=1, relief='solid')
    weather_card.pack(fill='x', pady=6)
    tk.Label(weather_card, text='Weather', bg='white', fg='#1b3d6d', font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=10, pady=(10,0))
    tk.Label(weather_card, text='Sunny, 24°C', bg='white', fg='#3a5480', font=('Segoe UI', 11)).pack(anchor='w', padx=10, pady=(4,10))

    cpu_card = tk.Frame(gadget_frame, bg='white', bd=1, relief='solid')
    cpu_card.pack(fill='x', pady=6)
    tk.Label(cpu_card, text='CPU Meter', bg='white', fg='#1b3d6d', font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=10, pady=(10,0))
    cpu_usage = tk.DoubleVar(value=0)
    cpu_bar = ttk.Progressbar(cpu_card, orient='horizontal', length=360, mode='determinate', variable=cpu_usage)
    cpu_bar.pack(padx=10, pady=(6,10))

    def update_gadgets():
        cpu = psutil.cpu_percent(interval=None) if psutil else random.randint(5, 28)
        cpu_usage.set(cpu)
        clock_value.config(text=datetime.now().strftime('%H:%M:%S'))
        win.after(2000, update_gadgets)
    update_gadgets()

    tk.Button(win, text='Add gadget to desktop', bg='#4f80d4', fg='white', command=lambda: messagebox.showinfo('Gadgets', 'No Gadgets detected.')).pack(pady=10)


def show_windows_media_center():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Windows Media Center')
    win.geometry('620x420')
    style_aero_window(win, '#eef5ff')
    center_window(win, 620, 420)

    tk.Label(win, text='Windows Media Center', bg='#eef5ff', fg='#1f4a7b', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    tk.Label(win, text='Browse music, pictures, and recorded TV (simulated).', bg='#eef5ff', fg='#3b5c88', font=('Segoe UI', 10)).pack(pady=(0,10))

    sections = tk.Frame(win, bg='#eef5ff')
    sections.pack(fill='both', expand=True, padx=16, pady=10)
    for title, desc in [('Music', 'Play your favorite tracks.'), ('Pictures', 'View photos and slideshows.'), ('TV', 'Watch live TV content.'), ('Library', 'Manage media library.')]:
        card = tk.Frame(sections, bg='white', bd=1, relief='solid')
        card.pack(fill='x', pady=6)
        tk.Label(card, text=title, bg='white', fg='#1b3d6d', font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=10, pady=(10,0))
        tk.Label(card, text=desc, bg='white', fg='#3a5480', font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(4,10))
        tk.Button(card, text='Open', bg='#4f80d4', fg='white', command=lambda t=title: messagebox.showinfo('Media Center', f'Opening {t}...')).pack(anchor='e', padx=10, pady=(0,10))

    tk.Button(win, text='Play featured media', bg='#4f80d4', fg='white', command=lambda: messagebox.showinfo('Media Center', 'Playing featured media...')).pack(pady=10)


def get_battery_status():
    if psutil and hasattr(psutil, 'sensors_battery'):
        bat = psutil.sensors_battery()
        if bat:
            return f"{int(bat.percent)}% {'Charging' if bat.power_plugged else 'Discharging'}"
    return f"{state.get('battery', 78)}% Discharging"


def close_taskbar_overlay():
    global taskbar_overlay
    if taskbar_overlay and taskbar_overlay.winfo_exists():
        taskbar_overlay.destroy()
        taskbar_overlay = None


def show_taskbar_time_overlay(event=None):
    global taskbar_overlay
    close_taskbar_overlay()

    taskbar_overlay = tk.Toplevel(desktop_win)
    taskbar_overlay.overrideredirect(True)
    taskbar_overlay.attributes('-topmost', True)
    taskbar_overlay.attributes('-alpha', 0.97)
    taskbar_overlay.configure(bg='#1a3a5c')

    W, H = 340, 420
    x = (event.x_root - W + 4) if event else (
        desktop_win.winfo_rootx() + desktop_win.winfo_width() - W - 4)
    y = (event.y_root - H - 4) if event else (
        desktop_win.winfo_rooty() + desktop_win.winfo_height() - H - 4)
    taskbar_overlay.geometry(f'{W}x{H}+{x}+{y}')

    now = datetime.now()

    # ── outer border (Win7 Aero rim) ───────────────────────────────────────
    outer = tk.Frame(taskbar_overlay, bg='#1a3a5c', bd=0)
    outer.pack(fill='both', expand=True, padx=2, pady=2)

    # ── clock header ───────────────────────────────────────────────────────
    header = tk.Frame(outer, bg='#1e4d82')
    header.pack(fill='x')

    # Big time display
    time_lbl = tk.Label(header, text=now.strftime('%I:%M %p'),
                        bg='#1e4d82', fg='white',
                        font=('Segoe UI', 32, 'bold'))
    time_lbl.pack(anchor='center', pady=(14, 0))

    date_lbl = tk.Label(header,
                        text=now.strftime('%A, %B %d, %Y'),
                        bg='#1e4d82', fg='#a8c8f0',
                        font=('Segoe UI', 10))
    date_lbl.pack(anchor='center', pady=(2, 6))

    # Battery + live tick
    battery_row = tk.Frame(header, bg='#1e4d82')
    battery_row.pack(fill='x', padx=12, pady=(0, 10))

    bat_icon = tk.Label(battery_row, text='🔋', bg='#1e4d82',
                        font=('Segoe UI Emoji', 10))
    bat_icon.pack(side='left')
    bat_lbl = tk.Label(battery_row,
                       text=get_battery_status(),
                       bg='#1e4d82', fg='#86c6ff',
                       font=('Segoe UI', 9))
    bat_lbl.pack(side='left', padx=4)

    def tick():
        if taskbar_overlay and taskbar_overlay.winfo_exists():
            t = datetime.now()
            time_lbl.config(text=t.strftime('%I:%M %p'))
            date_lbl.config(text=t.strftime('%A, %B %d, %Y'))
            taskbar_overlay.after(1000, tick)
    tick()

    # ── divider ────────────────────────────────────────────────────────────
    tk.Frame(outer, bg='#2a5298', height=1).pack(fill='x')

    # ── body ───────────────────────────────────────────────────────────────
    body = tk.Frame(outer, bg='#1c2f50')
    body.pack(fill='both', expand=True)

    # ── mini calendar ──────────────────────────────────────────────────────
    cal_header = tk.Frame(body, bg='#1c2f50')
    cal_header.pack(fill='x', padx=12, pady=(10, 4))

    # Month navigation
    cal_state = {'year': now.year, 'month': now.month}

    month_lbl = tk.Label(cal_header,
                         text=now.strftime('%B %Y'),
                         bg='#1c2f50', fg='white',
                         font=('Segoe UI', 10, 'bold'))
    month_lbl.pack(side='left')

    nav_frame = tk.Frame(cal_header, bg='#1c2f50')
    nav_frame.pack(side='right')

    cal_grid_frame = tk.Frame(body, bg='#1c2f50')
    cal_grid_frame.pack(fill='x', padx=10, pady=(0, 8))

    def draw_calendar():
        for w in cal_grid_frame.winfo_children():
            w.destroy()
        yr, mo = cal_state['year'], cal_state['month']
        month_lbl.config(text=datetime(yr, mo, 1).strftime('%B %Y'))
        days_abbr = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        for c, d in enumerate(days_abbr):
            color = '#5a9fd4' if c >= 5 else '#7eb4ea'
            tk.Label(cal_grid_frame, text=d,
                     bg='#1c2f50', fg=color,
                     font=('Segoe UI', 8, 'bold'),
                     width=4).grid(row=0, column=c, pady=(0, 3))
        grid = calendar.monthcalendar(yr, mo)
        today = datetime.now()
        for r, week in enumerate(grid, start=1):
            for c, day in enumerate(week):
                if not day:
                    tk.Label(cal_grid_frame, text='', bg='#1c2f50',
                             width=4).grid(row=r, column=c)
                    continue
                is_today = (day == today.day and
                            yr == today.year and mo == today.month)
                is_weekend = c >= 5
                if is_today:
                    cell = tk.Frame(cal_grid_frame, bg='#3a78c9',
                                    width=28, height=22)
                    cell.grid(row=r, column=c, padx=1, pady=1)
                    cell.pack_propagate(False)
                    tk.Label(cell, text=str(day),
                             bg='#3a78c9', fg='white',
                             font=('Segoe UI', 8, 'bold')).pack(expand=True)
                else:
                    fg = '#8ab8e8' if is_weekend else '#c8dff5'
                    lbl = tk.Label(cal_grid_frame, text=str(day),
                                   bg='#1c2f50', fg=fg,
                                   font=('Segoe UI', 8),
                                   width=4, cursor='hand2')
                    lbl.grid(row=r, column=c, padx=1, pady=1)
                    lbl.bind('<Enter>',
                             lambda e, l=lbl: l.config(bg='#254a82', fg='white'))
                    lbl.bind('<Leave>',
                             lambda e, l=lbl, f=fg: l.config(
                                 bg='#1c2f50', fg=f))

    def prev_month():
        if cal_state['month'] == 1:
            cal_state['month'] = 12
            cal_state['year'] -= 1
        else:
            cal_state['month'] -= 1
        draw_calendar()

    def next_month():
        if cal_state['month'] == 12:
            cal_state['month'] = 1
            cal_state['year'] += 1
        else:
            cal_state['month'] += 1
        draw_calendar()

    def nav_btn(parent, text, cmd):
        b = tk.Button(parent, text=text, bg='#2a5298', fg='white',
                      relief='flat', font=('Segoe UI', 9),
                      padx=6, pady=1, cursor='hand2',
                      activebackground='#3a6bc0', bd=0,
                      command=cmd)
        b.pack(side='left', padx=2)

    nav_btn(nav_frame, '◀', prev_month)
    nav_btn(nav_frame, '▶', next_month)

    draw_calendar()

    # ── divider ────────────────────────────────────────────────────────────
    tk.Frame(body, bg='#2a5298', height=1).pack(fill='x', padx=8, pady=4)

    # ── search bar ─────────────────────────────────────────────────────────
    search_row = tk.Frame(body, bg='#1c2f50')
    search_row.pack(fill='x', padx=10, pady=(0, 10))

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_row, textvariable=search_var,
                            bg='#253d60', fg='#c8dff5',
                            insertbackground='white',
                            relief='flat', font=('Segoe UI', 9),
                            highlightthickness=1,
                            highlightbackground='#3a6090',
                            highlightcolor='#5a9fd4')
    search_entry.pack(side='left', fill='x', expand=True,
                      ipady=5, padx=(0, 6))
    search_entry.insert(0, 'Search…')
    search_entry.bind('<FocusIn>',
                      lambda e: search_entry.delete(0, 'end')
                      if search_entry.get() == 'Search…' else None)

    def perform_search(event=None):
        query = search_var.get().strip().lower()
        if not query or query == 'search…':
            return
        close_taskbar_overlay()
        q = query
        if 'file' in q or 'explorer' in q:        show_file_explorer()
        elif 'terminal' in q or 'cmd' in q:        show_terminal_app()
        elif 'media' in q or 'player' in q:        show_media_player()
        elif 'excel' in q or 'sheet' in q:         show_excel_app()
        elif 'calendar' in q:                      show_calendar_app()
        elif 'note' in q or 'sticky' in q:         show_sticky_notes()
        elif 'paint' in q:                         show_paint_app()
        elif 'calc' in q:                          show_calculator_app()
        elif 'control' in q:                       show_control_panel()
        elif 'setting' in q:                       show_settings_app()
        else:
            show_system_notification('Search', f'No result for: {query}')

    search_entry.bind('<Return>', perform_search)

    go_btn = tk.Button(search_row, text='Go',
                       bg='#2a5298', fg='white',
                       relief='flat', font=('Segoe UI', 9),
                       padx=10, pady=4, cursor='hand2',
                       activebackground='#3a6bc0', bd=0,
                       command=perform_search)
    go_btn.pack(side='right')

    # ── footer ─────────────────────────────────────────────────────────────
    footer = tk.Frame(outer, bg='#1e3f6e', height=32)
    footer.pack(fill='x', side='bottom')
    footer.pack_propagate(False)

    tk.Button(footer, text='Change date and time settings…',
              bg='#1e3f6e', fg='#7eb4ea',
              relief='flat', font=('Segoe UI', 8),
              cursor='hand2', activebackground='#254a82',
              bd=0, command=show_calendar_app).pack(
        side='left', padx=10, pady=6)

    tk.Button(footer, text='✕',
              bg='#1e3f6e', fg='#7eb4ea',
              relief='flat', font=('Segoe UI', 9),
              cursor='hand2', activebackground='#a03030',
              bd=0, command=close_taskbar_overlay).pack(
        side='right', padx=8, pady=6)

    taskbar_overlay.bind('<FocusOut>', lambda e: close_taskbar_overlay())
    taskbar_overlay.focus_force()


def show_boot_screen(after_fn=None, after_restart=False):
    # ── Corrupted OS check — triggers guaranteed BSOD ─────────────────────────
    if state.get('os_corrupted', False):
        _show_corrupted_boot(after_fn, after_restart)
        return

    boot = tk.Toplevel(root)
    boot.title('Windows 7 Boot')
    boot.attributes('-fullscreen', True)
    boot.attributes('-topmost', True)
    boot.configure(bg='#020612')
    boot.update_idletasks()
    tk.Label(boot, text='Windows 7', fg='#dde6fc', bg='#020612',
             font=('Segoe UI', 40, 'bold')).pack(pady=(80,20))
    tk.Label(boot, text='Starting Windows...', fg='#89a9e6', bg='#020612',
             font=('Segoe UI', 16)).pack()
    status_lbl = tk.Label(boot, text='Getting devices ready...', fg='#9db9ea',
                          bg='#020612', font=('Segoe UI', 12))
    status_lbl.pack(pady=(8,0))
    progress = tk.Canvas(boot, width=640, height=18, bg='#14203a',
                         highlightthickness=0)
    progress.pack(pady=24)
    bar = progress.create_rectangle(2, 2, 2, 16, fill='#6aa0ff', outline='')
    steps = list(range(0, 641, 80))
    messages = ['Detecting hardware...', 'Loading drivers...',
                'Initializing network...', 'Preparing your desktop...',
                'Finalizing settings...']
    def advance(i=0):
        if not boot.winfo_exists():
            return
        if i < len(steps):
            try:
                progress.coords(bar, 2, 2, steps[i], 16)
                if i < len(messages):
                    status_lbl.config(text=messages[i])
            except Exception:
                pass
            boot.after(600, lambda: advance(i+1))
        else:
            boot.destroy()
            if after_fn:
                after_fn()
            else:
                if after_restart:
                    show_login(True)
                else:
                    show_login()
    boot.after(400, lambda: advance())
    play_windows7_logon()


def _show_corrupted_boot(after_fn=None, after_restart=False):
    """Boot sequence that always crashes to BSOD — OS is corrupted."""
    boot = tk.Toplevel(root)
    boot.title('Windows 7 Boot')
    boot.attributes('-fullscreen', True)
    boot.attributes('-topmost', True)
    boot.configure(bg='#020612')

    tk.Label(boot, text='Windows 7', fg='#dde6fc', bg='#020612',
             font=('Segoe UI', 40, 'bold')).pack(pady=(80,20))
    tk.Label(boot, text='Starting Windows...', fg='#89a9e6', bg='#020612',
             font=('Segoe UI', 16)).pack()

    status_lbl = tk.Label(boot, text='Getting devices ready...', fg='#9db9ea',
                          bg='#020612', font=('Segoe UI', 12))
    status_lbl.pack(pady=(8,0))
    progress = tk.Canvas(boot, width=640, height=18, bg='#14203a',
                         highlightthickness=0)
    progress.pack(pady=24)
    bar = progress.create_rectangle(2, 2, 2, 16, fill='#6aa0ff', outline='')

    # Corrupt messages — pretend to load then fail
    corrupt_steps = [
        (600,  80,  'Loading core system files...'),
        (600,  200, 'Verifying ntfs.sys...'),
        (600,  320, 'Loading win32k.sys...'),
        (500,  400, 'Initializing subsystems...'),
        (400,  460, 'Loading hal.dll...  ⚠ ERROR: File missing or corrupt'),
        (300,  500, 'Attempting recovery...  ⚠ FAILED'),
        (200,  520, 'Critical system file not found.'),
    ]

    def run_step(idx=0):
        if not boot.winfo_exists():
            return
        if idx >= len(corrupt_steps):
            boot.destroy()
            # After BSOD on corrupted OS → go straight to boot SELECTOR
            # which shows the "No OS detected" screen with USB option visible
            show_bsod(
                error_code='0x0000007B',
                error_name='INACCESSIBLE_BOOT_DEVICE',
                on_restart=lambda: show_bios_boot_selector(reinstall=False),
                auto_restart_ms=8000
            )
            return
        delay, prog, msg = corrupt_steps[idx]
        try:
            progress.coords(bar, 2, 2, prog, 16)
            bar_color = '#ff4444' if '⚠' in msg else '#6aa0ff'
            progress.itemconfig(bar, fill=bar_color)
            status_lbl.config(text=msg,
                              fg='#ff8888' if '⚠' in msg or 'FAIL' in msg else '#9db9ea')
        except Exception:
            pass
        boot.after(delay, lambda: run_step(idx+1))

    boot.after(300, run_step)
    try:
        play_windows7_logon()
    except Exception:
        pass


def perform_shutdown():
    if messagebox.askyesno('Shutdown', 'Do you want to Shut down.It will close all apps and your unsaved data maybe lost?'):
        play_windows7_logoff()
        if desktop_win and desktop_win.winfo_exists():
            desktop_win.destroy()
        show_login()


def perform_restart():
    if messagebox.askyesno('Restart', 'Do you want to restart Windows 7 now?'):
        play_windows7_logoff()
        if desktop_win and desktop_win.winfo_exists():
            desktop_win.destroy()
        show_boot_screen(lambda: show_login(True), after_restart=True)


def perform_sleep():
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.withdraw()
        sleep_win = tk.Toplevel(root)
        sleep_win.title('Sleep Mode')
        sleep_win.geometry('420x220')
        sleep_win.configure(bg='#102237')
        center_window(sleep_win, 420, 220)
        tk.Label(sleep_win, text='Sleeping...', bg='#102237', fg='#c8defb', font=('Segoe UI', 16, 'bold')).pack(pady=20)
        tk.Label(sleep_win, text='Click Wake to resume.', bg='#102237', fg='#9bb3d6', font=('Segoe UI', 10)).pack(pady=6)
        tk.Button(sleep_win, text='Wake', bg='#4c7ec6', fg='white', width=12, command=lambda: [sleep_win.destroy(), desktop_win.deiconify(), show_system_notification('Sleep', 'System resumed from sleep.')]).pack(pady=20)
        sleep_win.protocol('WM_DELETE_WINDOW', lambda: [sleep_win.destroy(), desktop_win.deiconify()])


def style_aero_window(win, bg='#dce9f8'):
    """Windows 7 Aero glass — rounded corners, glow border, rich glass titlebar."""
    if win not in managed_windows:
        managed_windows.append(win)
        win.bind('<Destroy>',
                 lambda e: (managed_windows.remove(win)
                            if win in managed_windows else None))
    try:
        apply_aero_widget_style(win)
        win.configure(bg=bg)
        win.overrideredirect(True)
        v = state.get('os_version', 'Ultimate')
        win.attributes('-alpha',
                       0.97 if v in ['Home Premium', 'Professional', 'Ultimate']
                       else 1.0)
        # Rounded border: 3-px blue rim + outer glow
        win.configure(highlightthickness=3,
                      highlightbackground='#2060a8',
                      highlightcolor='#5aacf0')
        create_aero_titlebar(win)
        setup_aero_shake(win)
        setup_aero_snap(win)
        play_windows7_menu_popup()
    except Exception:
        pass

def create_aero_titlebar(win):
    """Windows 7 Aero glass titlebar — rich gradient, rounded top corners, glow buttons."""
    TB_H = 34
    title_frame = tk.Canvas(win, height=TB_H, highlightthickness=0, bd=0,
                            bg='#3a78c8')
    title_frame.place(x=0, y=0, relwidth=1)

    # Gradient stops: top-highlight → mid-blue → deep-blue
    stops = [
        (0,   0xe0, 0xf2, 0xff),
        (4,   0x90, 0xc8, 0xf0),
        (14,  0x42, 0x88, 0xd4),
        (TB_H-1, 0x18, 0x4c, 0x90),
    ]

    def lerp_stop(y):
        for i in range(len(stops)-1):
            y0,r0,g0,b0 = stops[i]; y1,r1,g1,b1 = stops[i+1]
            if y0 <= y <= y1:
                t = (y-y0)/(y1-y0) if y1>y0 else 0
                return int(r0+(r1-r0)*t), int(g0+(g1-g0)*t), int(b0+(b1-b0)*t)
        return 0x18, 0x4c, 0x90

    def _paint(event=None):
        try:
            w = max(120, win.winfo_width())
        except Exception:
            w = 600
        title_frame.delete('all')

        # Background gradient
        for y in range(TB_H):
            r, g, b = lerp_stop(y)
            title_frame.create_line(0, y, w, y, fill=f'#{r:02x}{g:02x}{b:02x}')

        # Gloss sheen top band
        title_frame.create_rectangle(0, 0, w, TB_H//3,
                                     fill='#d8f0ff', outline='',
                                     stipple='gray50')

        # Rounded top-left and top-right corners (mask with dark bg color)
        _corner_r = 8
        try:
            _root_bg = root.cget('bg') or '#000000'
        except Exception:
            _root_bg = '#000000'
        for cx, cy in [(0, 0), (w - _corner_r*2, 0)]:
            title_frame.create_arc(cx, cy, cx+_corner_r*2, cy+_corner_r*2,
                                   start=90 if cx == 0 else 0,
                                   extent=90,
                                   fill=_root_bg, outline=_root_bg,
                                   style='pieslice')

        # Inner top highlight line
        title_frame.create_line(0, 1, w, 1, fill='#f0faff', width=1)
        # Bottom border
        title_frame.create_line(0, TB_H-1, w, TB_H-1, fill='#0e2a60', width=1)
        # Left/right edge highlights
        title_frame.create_line(0, 0, 0, TB_H, fill='#78b8f0', width=1)
        title_frame.create_line(w-1, 0, w-1, TB_H, fill='#1a4070', width=1)

        try:
            icon_lbl.lift()
            title_lbl.lift()
        except Exception:
            pass

    _paint()
    win.bind('<Configure>', lambda e: _paint(), add='+')

    icon_lbl = tk.Label(title_frame, text='🪟', bg='#3a78c8',
                        fg='white', font=('Segoe UI Emoji', 9))
    icon_lbl.place(x=6, y=6)
    title_lbl = tk.Label(title_frame, text=win.title(), bg='#3a78c8',
                         fg='#e8f4ff', font=('Segoe UI', 9, 'bold'))
    title_lbl.place(x=26, y=8)

    def start_move(e):
        win.drag_x = e.x; win.drag_y = e.y
    def on_move(e):
        x = win.winfo_x() + (e.x - win.drag_x)
        y = win.winfo_y() + (e.y - win.drag_y)
        win.geometry(f'+{x}+{y}')
    title_frame.bind('<ButtonPress-1>', start_move)
    title_frame.bind('<B1-Motion>', on_move)

    BTN_W, BTN_H = 46, 32

    def _make_ctrl_btn(symbol, x_off, nc, hc, ac, cmd):
        cv = tk.Canvas(title_frame, width=BTN_W, height=BTN_H,
                       highlightthickness=0, bd=0, cursor='hand2')
        cv.place(relx=1.0, x=x_off, y=0)

        def draw(st='normal'):
            cv.delete('all')
            col = {'normal': nc, 'hover': hc, 'active': ac}.get(st, nc)
            # Gradient fill on button
            for i in range(BTN_H):
                t = i / BTN_H
                try:
                    r2 = min(255, int(int(col[1:3],16) * (1 - t*0.4)))
                    g2 = min(255, int(int(col[3:5],16) * (1 - t*0.3)))
                    b2 = min(255, int(int(col[5:7],16) * (1 - t*0.2)))
                    cv.create_line(0, i, BTN_W, i,
                                   fill=f'#{r2:02x}{g2:02x}{b2:02x}')
                except Exception:
                    pass
            # Gloss on hover
            if st in ('hover', 'active'):
                cv.create_rectangle(0, 0, BTN_W, BTN_H//3,
                                    fill='#ffffff', outline='',
                                    stipple='gray50')
            # Symbol
            fnt = ('Marlett', 10) if symbol in ('r', '1', '0') else \
                  ('Segoe UI', 11, 'bold')
            cv.create_text(BTN_W//2, BTN_H//2,
                           text=symbol, fill='white', font=fnt)

        draw()
        cv.bind('<Enter>',        lambda e: draw('hover'))
        cv.bind('<Leave>',        lambda e: draw('normal'))
        cv.bind('<ButtonPress-1>', lambda e: draw('active'))
        cv.bind('<ButtonRelease-1>', lambda e: (draw('hover'), cmd()))
        return cv

    def toggle_max():
        if getattr(win, '_is_maximized', False):
            win.geometry(getattr(win, '_old_geom', '800x600+100+100'))
            win._is_maximized = False
        else:
            win._old_geom = win.geometry()
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            win.geometry(f'{sw}x{sh-45}+0+0')
            win._is_maximized = True

    _make_ctrl_btn('r', -BTN_W,   '#c42b1c', '#e81123', '#f1707a',
                   lambda: [play_windows7_error(), win.destroy()])
    _make_ctrl_btn('1', -BTN_W*2, '#3a6898', '#4a80b8', '#5a90c8', toggle_max)
    _make_ctrl_btn('0', -BTN_W*3, '#3a6898', '#4a80b8', '#5a90c8',
                   lambda: [play_windows7_minimize(), win.withdraw()])

    def _ctx(e):
        m=tk.Menu(win,tearoff=0)
        m.add_command(label='Minimize', command=win.withdraw)
        m.add_command(label='Maximize/Restore', command=toggle_max)
        m.add_separator()
        m.add_command(label='Close', command=win.destroy)
        m.tk_popup(e.x_root, e.y_root)
    title_frame.bind('<Button-3>', _ctx)
    title_lbl.bind('<Button-3>', _ctx)
    register_app_in_taskbar(win)

def create_taskbar_preview(win, btn):
    """Creates a small floating preview window when hovering over a taskbar button."""
    preview = tk.Toplevel(desktop_win)
    preview.overrideredirect(True)
    preview.attributes('-topmost', True)
    preview.attributes('-alpha', 0.88)
    preview.geometry(f"120x80+{btn.winfo_rootx()}+{btn.winfo_rooty()-90}")
    
    canvas = tk.Canvas(preview, bg='#d0e2ff', highlightthickness=1, highlightbackground='#16375c')
    canvas.pack(fill='both', expand=True)
    canvas.create_text(60, 28, text=win.title()[:18], font=('Segoe UI', 9, 'bold'))
    canvas.create_text(60, 50, text='Preview', font=('Segoe UI', 8), fill='#3b4b75')
    canvas.create_rectangle(6, 6, 114, 28, outline='#9ab5d8', width=1)
    
    def destroy_preview(e):
        preview.destroy()
        
    btn.bind('<Leave>', destroy_preview, add="+")
    return preview


def refresh_taskbar_tabs():
    if not desktop_win or not hasattr(taskbar, 'tab_label'):
        return
    open_apps = [w for w in ACTIVE_APPS if w.winfo_exists()]
    count = len(open_apps)
    if count == 0:
        status = 'No open windows'
    else:
        active = next((w.title() for w in open_apps if w.state() != 'withdrawn'), open_apps[0].title())
        status = f'{count} open apps • {active}'
    taskbar.tab_label.config(text=status)


def register_app_in_taskbar(win):
    """Registers a window to the desktop taskbar."""
    if not desktop_win or not desktop_win.winfo_exists():
        return

    # Frame to hold the app buttons in the taskbar
    if not hasattr(taskbar, 'app_frame'):
        taskbar.app_frame = tk.Frame(taskbar, bg=taskbar.cget('bg'))
        taskbar.app_frame.pack(side='left', padx=10)

    btn = tk.Button(taskbar.app_frame, text=win.title()[:12], bg='#cfe4ff', relief='flat', 
                    font=('Segoe UI', 9), padx=10)
    btn.pack(side='left', padx=2, pady=5)
    
    def on_click():
        if win.state() == 'withdrawn':
            win.deiconify()
        win.lift()
        win.focus_force()

    def update_taskbar_button(active=True):
        try:
            btn.config(bg='#8ab8ff' if active else '#cfe4ff')
        except Exception:
            pass

    def maximize_window():
        if win.state() == 'zoomed' or getattr(win, '_is_maximized', False):
            if hasattr(win, '_old_geom'):
                win.geometry(win._old_geom)
            win._is_maximized = False
        else:
            win._old_geom = win.geometry()
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            win.geometry(f"{sw}x{sh-45}+0+0")
            win._is_maximized = True
            win.deiconify()
            win.lift()

    def show_taskbar_app_menu(event):
        menu = tk.Menu(btn, tearoff=0)
        menu.add_command(label='Restore', command=on_click)
        menu.add_command(label='Minimize', command=win.withdraw)
        menu.add_command(label='Maximize', command=maximize_window)
        menu.add_separator()
        menu.add_command(label='Close', command=win.destroy)
        menu.add_command(label='Remove from Taskbar', command=lambda: [btn.destroy(), ACTIVE_APPS.pop(win, None)])
        menu.tk_popup(event.x_root, event.y_root)

    btn.config(command=on_click)
    btn.bind('<Enter>', lambda e: create_taskbar_preview(win, btn))
    btn.bind('<Button-3>', show_taskbar_app_menu)

    win.bind('<FocusIn>', lambda e: update_taskbar_button(True))
    win.bind('<FocusOut>', lambda e: update_taskbar_button(False))

    ACTIVE_APPS[win] = btn
    refresh_taskbar_tabs()
    
    # Cleanup when window closes
    win.bind("<Destroy>", lambda e: [btn.destroy(), ACTIVE_APPS.pop(win, None), refresh_taskbar_tabs()] if win in ACTIVE_APPS else None)

def setup_aero_snap(win):
    """Resizes windows to half-screen when dragged to the side edges."""
    def on_release(event):
        try:
            # winfo_rootx/y are reliable for screen position check
            x = win.winfo_rootx()
            y = win.winfo_rooty()
            w = win.winfo_width()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            
            # Snap Thresholds (at the very edges)
            if x <= 0: # Left edge
                win.geometry(f"{sw//2}x{sh-45}+0+0")
            elif x + w >= sw: # Right edge
                win.geometry(f"{sw//2}x{sh-45}+{sw//2}+0")
            elif y <= 0: # Top edge
                win.state('zoomed')
        except Exception: pass
    
    win.bind('<ButtonRelease-1>', on_release, add="+")

def setup_aero_shake(win):
    """Detects rapid movement of a window to minimize/restore others."""
    win.shake_data = {'last_x': 0, 'last_y': 0, 'moves': [], 'minimized': False}

    def on_move(event):
        if not hasattr(win, 'shake_data'): return
        try:
            x, y = win.winfo_x(), win.winfo_y()
        except Exception: return
        
        if win.shake_data['last_x'] == 0:
            win.shake_data['last_x'], win.shake_data['last_y'] = x, y
            return
        
        dx = abs(x - win.shake_data['last_x'])
        dy = abs(y - win.shake_data['last_y'])
        
        if dx > 15 or dy > 15:
            now = datetime.now().timestamp()
            win.shake_data['moves'].append(now)
            win.shake_data['moves'] = [m for m in win.shake_data['moves'] if now - m < 0.6]
            
            if len(win.shake_data['moves']) > 12:
                toggle_minimize_others(win)
                win.shake_data['moves'] = [] # Reset

        win.shake_data['last_x'], win.shake_data['last_y'] = x, y

    win.bind('<Configure>', on_move)

def toggle_minimize_others(active_win):
    """Minimize or restore all windows except the active one."""
    for w in managed_windows:
        if w != active_win and w.winfo_exists():
            try:
                if w.state() != 'withdrawn':
                    w.withdraw()
                else:
                    w.deiconify()
            except: pass

def trigger_bsod():
    """Alias — calls the new full-featured BSOD."""
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.withdraw()
    show_bsod(on_restart=lambda: [
        desktop_win.deiconify() if desktop_win and desktop_win.winfo_exists() else None,
        show_post_screen(on_done=show_bios_boot_selector)
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  BLUE SCREEN OF DEATH  (Windows 7 authentic BSOD)
# ══════════════════════════════════════════════════════════════════════════════
_BSOD_CODES = [
    ('0x0000007E', 'SYSTEM_THREAD_EXCEPTION_NOT_HANDLED'),
    ('0x0000003B', 'SYSTEM_SERVICE_EXCEPTION'),
    ('0x000000D1', 'DRIVER_IRQL_NOT_LESS_OR_EQUAL'),
    ('0x00000050', 'PAGE_FAULT_IN_NONPAGED_AREA'),
    ('0x0000007F', 'UNEXPECTED_KERNEL_MODE_TRAP'),
    ('0x000000F4', 'CRITICAL_OBJECT_TERMINATION'),
    ('0x0000009F', 'DRIVER_POWER_STATE_FAILURE'),
    ('0xC0000034', 'OBJECT_NAME_NOT_FOUND'),
]

def show_bsod(error_code: str = '', error_name: str = '',
              on_restart=None, auto_restart_ms: int = 8000):
    """Authentic Windows 7 Blue Screen of Death."""
    if not error_code:
        code, name = random.choice(_BSOD_CODES)
    else:
        code, name = error_code, error_name

    bsod = tk.Toplevel()
    bsod.title('BSOD')
    bsod.attributes('-fullscreen', True)
    bsod.configure(bg='#0000aa')
    bsod.attributes('-topmost', True)

    audit_log('BSOD', f'{code} {name}', 'CRITICAL')
    try:
        play_windows7_error()
    except Exception:
        pass

    cv = tk.Canvas(bsod, bg='#0000aa', highlightthickness=0)
    cv.pack(fill='both', expand=True)

    sw = bsod.winfo_screenwidth()
    sh = bsod.winfo_screenheight()

    def place_text(x_pct, y, text, size=12, bold=False, color='white', anchor='w'):
        font = ('Courier New', size, 'bold' if bold else 'normal')
        cv.create_text(int(sw * x_pct), y, text=text, fill=color,
                       font=font, anchor=anchor)

    # Title smiley
    place_text(0.08, 80,  ':(', 52, bold=True)

    # Main message
    place_text(0.08, 180,
               'Your PC ran into a problem and needs to restart.',
               14, bold=True)
    place_text(0.08, 210,
               "We're just collecting some error info, and then we'll restart for you.",
               12)

    # Progress dots animation
    dots_y = 280
    progress_lbl = cv.create_text(int(sw * 0.08), dots_y,
                                   text='0% complete', fill='white',
                                   font=('Courier New', 13), anchor='w')
    pct_state = {'v': 0}

    def tick_progress():
        if not bsod.winfo_exists():
            return
        pct_state['v'] = min(100, pct_state['v'] + random.randint(1, 4))
        cv.itemconfig(progress_lbl,
                      text=f"{pct_state['v']}% complete")
        if pct_state['v'] < 100:
            bsod.after(random.randint(60, 120), tick_progress)

    tick_progress()

    # Error detail block
    detail_y = 380
    place_text(0.08, detail_y,
               f'For more information about this issue and possible fixes, visit',
               10)
    place_text(0.08, detail_y + 22,
               'http://windows.com/stopcode', 10, color='#88bbff')
    place_text(0.08, detail_y + 52,
               f'If you call a support person, give them this info:', 10)
    place_text(0.08, detail_y + 72,
               f'Stop code:  {name}', 11, bold=True)
    place_text(0.08, detail_y + 96,
               f'Error code: {code}', 10, color='#aaaaff')

    # QR code hint (drawn as a tiny grid)
    qr_x, qr_y = int(sw * 0.72), detail_y - 20
    random.seed(int(code, 16) if code.startswith('0x') else 42)
    for row in range(10):
        for col in range(10):
            fill = '#0000cc' if (row < 3 and col < 3) or random.random() > 0.5 else 'white'
            cv.create_rectangle(qr_x + col*8, qr_y + row*8,
                                qr_x + col*8+7, qr_y + row*8+7,
                                fill=fill, outline='')

    # Countdown restart
    restart_lbl = cv.create_text(int(sw * 0.08), sh - 60,
                                  text='Restarting in 8s…',
                                  fill='#aaaaff',
                                  font=('Courier New', 10), anchor='w')
    countdown = {'v': auto_restart_ms // 1000}

    def tick_restart():
        if not bsod.winfo_exists():
            return
        countdown['v'] -= 1
        cv.itemconfig(restart_lbl, text=f'Restarting in {countdown["v"]}s…')
        if countdown['v'] > 0:
            bsod.after(1000, tick_restart)
        else:
            try:
                bsod.grab_release()
            except Exception:
                pass
            bsod.destroy()
            if on_restart:
                on_restart()
            else:
                show_post_screen(on_done=show_bios_boot_selector)

    bsod.after(1000, tick_restart)

    # Any key dismisses and reboots immediately
    def on_any_key(event=None):
        if not bsod.winfo_exists():
            return
        try:
            bsod.grab_release()
        except Exception:
            pass
        bsod.destroy()
        if on_restart:
            on_restart()
        else:
            show_post_screen(on_done=show_bios_boot_selector)

    bsod.bind('<Key>', on_any_key)
    bsod.bind('<Button-1>', on_any_key)
    bsod.bind('<Any-Key>', on_any_key)
    bsod.focus_force()
    try:
        bsod.grab_set()          # CRITICAL: forces ALL keyboard events here
    except Exception:
        pass




# ══════════════════════════════════════════════════════════════════════════════
#  GSOD  —  Green Screen of Death  (critical error → auto Windows reinstall)
# ══════════════════════════════════════════════════════════════════════════════
_GSOD_CODES = [
    ('0xC000021A', 'STATUS_SYSTEM_PROCESS_TERMINATED'),
    ('0xC0000005', 'ACCESS_VIOLATION'),
    ('0x8000FFFF', 'E_UNEXPECTED_CATASTROPHIC_FAILURE'),
    ('0xDEAD0001', 'TERMINAL_SELF_DELETION_DETECTED'),
    ('0x00000080', 'NMI_HARDWARE_FAILURE'),
    ('0xFFFFFFFF', 'CRITICAL_PROCESS_DIED'),
]

_TERMINAL_BLOCKED_FEATURES = set()   # feature keys blocked by terminal
_BIOS_BLOCKED = False                # whether terminal has locked BIOS
_TERMINAL_SELF_DELETED = False       # track if terminal deleted itself


def show_gsod(error_code: str = '', error_name: str = '',
              on_restart=None, auto_restart_ms: int = 10000):
    """Green Screen of Death — critical error, triggers auto Windows reinstall."""
    if not error_code:
        code, name = random.choice(_GSOD_CODES)
    else:
        code, name = error_code, error_name

    gsod = tk.Toplevel()
    gsod.title('GSOD')
    gsod.attributes('-fullscreen', True)
    gsod.configure(bg='#003300')
    gsod.attributes('-topmost', True)

    audit_log('GSOD', f'{code} {name}', 'CRITICAL')
    try: play_windows7_error()
    except Exception: pass

    cv = tk.Canvas(gsod, bg='#003300', highlightthickness=0)
    cv.pack(fill='both', expand=True)
    sw = gsod.winfo_screenwidth()
    sh = gsod.winfo_screenheight()

    def pt(x_pct, y, text, size=12, bold=False, color='#00ff88', anchor='w'):
        font = ('Courier New', size, 'bold' if bold else 'normal')
        cv.create_text(int(sw * x_pct), y, text=text, fill=color, font=font, anchor=anchor)

    pt(0.08, 80,  ':(', 52, bold=True, color='#00ff44')
    pt(0.08, 180, 'Windows encountered a CRITICAL system error and must reinstall.', 14, bold=True, color='#00ff88')
    pt(0.08, 212, 'A terminal process caused irreversible damage to the OS core.', 12, color='#44cc66')
    pt(0.08, 260, f'Error code : {code}', 11, bold=True, color='#88ffaa')
    pt(0.08, 284, f'Stop name  : {name}', 10, color='#44cc66')
    pt(0.08, 320, 'Automatic reinstallation will begin in a few seconds…', 10, color='#00cc44')
    pt(0.08, 360, 'http://windows.com/gsod', 9, color='#006622')

    # Animated progress
    prog_lbl = cv.create_text(int(sw*0.08), 420, text='0% — Preparing reinstall…',
                              fill='#44ff88', font=('Courier New', 12), anchor='w')
    pct = {'v': 0}

    def tick_p():
        if not gsod.winfo_exists(): return
        pct['v'] = min(100, pct['v'] + random.randint(1, 3))
        msgs = ['Preparing reinstall…', 'Wiping corrupted sectors…',
                'Downloading Windows 7…', 'Verifying integrity…',
                'Almost done…', 'Rebooting…']
        msg = msgs[min(pct['v'] // 17, len(msgs)-1)]
        cv.itemconfig(prog_lbl, text=f'{pct["v"]}% — {msg}')
        if pct['v'] < 100:
            gsod.after(random.randint(60, 140), tick_p)

    tick_p()

    # Countdown
    cnt_lbl = cv.create_text(int(sw*0.08), sh-60, text=f'Reinstalling in {auto_restart_ms//1000}s…',
                             fill='#007733', font=('Courier New', 10), anchor='w')
    cntdown = {'v': auto_restart_ms // 1000}

    def tick_r():
        if not gsod.winfo_exists(): return
        cntdown['v'] -= 1
        cv.itemconfig(cnt_lbl, text=f'Reinstalling in {cntdown["v"]}s…')
        if cntdown['v'] > 0:
            gsod.after(1000, tick_r)
        else:
            try: gsod.grab_release()
            except: pass
            gsod.destroy()
            if on_restart:
                on_restart()
            else:
                show_bios_boot_selector(reinstall=True)

    gsod.after(1000, tick_r)

    def dismiss(event=None):
        if not gsod.winfo_exists(): return
        try: gsod.grab_release()
        except: pass
        gsod.destroy()
        if on_restart:
            on_restart()
        else:
            show_bios_boot_selector(reinstall=True)

    gsod.bind('<Key>', dismiss)
    gsod.bind('<Button-1>', dismiss)
    gsod.focus_force()
    try: gsod.grab_set()
    except: pass


def _apply_bios_stability_to_desktop():
    """Read BIOS system_stability and apply effects to the running desktop.
    Also enforces BIOS feature_lock and terminal_access settings."""
    if not desktop_win or not desktop_win.winfo_exists():
        return
    bs = state.get('bios_settings', {})
    stability = bs.get('system_stability', 'Stable')

    # ── BIOS Feature Lock → populate _TERMINAL_BLOCKED_FEATURES ──────────────
    feature_lock = bs.get('feature_lock', 'None')
    if feature_lock == 'Repair':
        for k in ('repair', 'system repair', 'windows repair', 'crash recovery'):
            _TERMINAL_BLOCKED_FEATURES.add(k)
    elif feature_lock == 'Security':
        for k in ('security center', 'windows defender', 'defender', 'vault'):
            _TERMINAL_BLOCKED_FEATURES.add(k)
    elif feature_lock == 'All Apps':
        for k in list(APP_MAP.keys()):
            _TERMINAL_BLOCKED_FEATURES.add(k)
        # But keep terminal accessible
        for k in ('terminal', 'cmd', 'command prompt'):
            _TERMINAL_BLOCKED_FEATURES.discard(k)

    # ── BIOS Terminal Access Level ─────────────────────────────────────────────
    terminal_access = bs.get('terminal_access', 'Standard')
    if terminal_access == 'Restricted':
        # Terminal cannot do sudo or destructive commands
        state['bios_security_disabled'] = False
        save_state()
    elif terminal_access in ('Admin', 'Root'):
        # Full access
        state['bios_security_disabled'] = True
        save_state()

    if stability == 'Stable':
        try: desktop_win.attributes('-alpha', 0.99)
        except: pass

    elif stability == 'Degraded':
        try: desktop_win.attributes('-alpha', 0.88)
        except: pass
        show_system_notification('BIOS Warning',
            '⚠ System stability is Degraded — check BIOS settings')
        def _flicker():
            if not desktop_win or not desktop_win.winfo_exists(): return
            if state.get('bios_settings', {}).get('system_stability') == 'Degraded':
                try:
                    desktop_win.attributes('-alpha', random.uniform(0.75, 0.95))
                except: pass
                desktop_win.after(random.randint(3000, 8000), _flicker)
        desktop_win.after(4000, _flicker)

    elif stability == 'Unstable':
        show_system_notification('BIOS CRITICAL',
            '🔴 System UNSTABLE — BSOD risk is HIGH!')
        def _unstable_tick():
            if not desktop_win or not desktop_win.winfo_exists(): return
            if state.get('bios_settings', {}).get('system_stability') == 'Unstable':
                try:
                    desktop_win.attributes('-alpha', random.uniform(0.5, 0.99))
                    desktop_win.config(bg=random.choice(['#4a7eb5','#3a6ea5','#5a8ec5','#2a5e95']))
                except: pass
                if random.random() < 0.1:
                    trigger_bsod()
                    return
                desktop_win.after(1500, _unstable_tick)
        desktop_win.after(2000, _unstable_tick)

    elif stability == 'Critical':
        desktop_win.after(1500, lambda: show_gsod(
            '0x00000080', 'NMI_HARDWARE_FAILURE — BIOS_STABILITY_CRITICAL'))


def show_repair_sequence():
    repair = tk.Toplevel()
    repair.attributes('-fullscreen', True)
    repair.attributes('-topmost', True)
    repair.configure(bg='#0f1733')
    tk.Label(repair, text='Windows Conduction Repair', bg='#0f1733', fg='#76d4ff', font=('Segoe UI', 18, 'bold')).pack(pady=(60,20))
    status = tk.Label(repair, text='Analyzing corrupted system components.It will take few minutes ', bg='#0f1733', fg='#c4e2ff', font=('Segoe UI', 12))
    status.pack(pady=(0,12))
    bar = tk.Canvas(repair, width=560, height=24, bg='#12223b', highlightthickness=0)
    bar.pack(pady=10)
    progress = bar.create_rectangle(2, 2, 2, 22, fill='#72b5ff', width=0)
    step = {'value': 0}
    def tick():
        step['value'] += 1
        width = 556 * step['value'] // 20
        bar.coords(progress, 2, 2, 2 + width, 22)
        status.config(text=f'Repairing corrupted component {step["value"]} of 20...')
        if step['value'] < 20:
            repair.after(700, tick)
        else:
            repair.destroy()
            show_bios_boot_menu()
    tick()


def show_tic_tac_toe_game():
    if not check_drivers("Tic Tac Toe"):
        return
    game_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    game_win.title('Tic Tac Toe')
    game_win.geometry('300x420')
    style_aero_window(game_win, '#eef5ff')
    center_window(game_win, 300, 420)
    tk.Label(game_win, text='Tic Tac Toe', bg='#eef5ff', fg='#19386d', font=('Segoe UI', 14, 'bold')).pack(pady=10)
    board = [""] * 9
    buttons = []
    current_player = "X"
    def check_winner():
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for w in wins:
            if board[w[0]] == board[w[1]] == board[w[2]] != "": return board[w[0]]
        if "" not in board: return "Draw"
        return None
    def on_click(i):
        nonlocal current_player
        if board[i] == "" and check_winner() is None:
            board[i] = current_player
            buttons[i].config(text=current_player, fg="#2c3e50" if current_player == "X" else "#c0392b")
            winner = check_winner()
            if winner:
                if winner == "Draw": messagebox.showinfo("Tic Tac Toe", "It's a draw!")
                else: messagebox.showinfo("Tic Tac Toe", f"Player {winner} wins!")
            else: current_player = "O" if current_player == "X" else "X"
    grid = tk.Frame(game_win, bg='#eef5ff'); grid.pack(pady=5)
    for i in range(9):
        btn = tk.Button(grid, text="", font=('Segoe UI', 18, 'bold'), width=4, height=2, command=lambda i=i: on_click(i))
        btn.grid(row=i//3, column=i%3, padx=5, pady=5); buttons.append(btn)
    tk.Button(game_win, text='Restart', bg='#5b8fe2', fg='white', command=lambda: [game_win.destroy(), show_tic_tac_toe_game()]).pack(pady=15)

# ══════════════════════════════════════════════════════════════════════════════
#  UEFI / BIOS  —  Full multi-screen implementation
#  Screens:  POST → Main → Advanced → Boot Order → Security →
#            Overclocking → Fan Control → Power → Diagnostics →
#            OS Install (Edition → Setup → Drivers)
# ══════════════════════════════════════════════════════════════════════════════

# ── Shared BIOS palette ───────────────────────────────────────────────────────
_B = {
    'bg':       '#000080',   # classic BIOS navy blue
    'bg2':      '#0000aa',   # lighter blue for panels
    'fg':       '#ffffff',
    'hi':       '#000000',   # highlight text (on cyan)
    'hi_bg':    '#00aaaa',   # highlight background
    'dim':      '#aaaaaa',
    'red':      '#ff5555',
    'green':    '#55ff55',
    'yellow':   '#ffff55',
    'cyan':     '#55ffff',
    'border':   '#aaaaaa',
    'title_bg': '#aaaaaa',
    'title_fg': '#000000',
    'font':     ('Consolas', 11),
    'font_sm':  ('Consolas', 9),
    'font_lg':  ('Consolas', 13, 'bold'),
    'font_hd':  ('Consolas', 15, 'bold'),
}


def _bios_clear(win):
    """Destroy all children of a BIOS window."""
    for w in win.winfo_children():
        try:
            w.destroy()
        except Exception:
            pass


def _bios_header(win, title: str, subtitle: str = ''):
    """Render the classic BIOS header bar."""
    hdr = tk.Frame(win, bg=_B['title_bg'])
    hdr.pack(fill='x')
    tk.Label(hdr, text=f'  RYAN-PC UEFI BIOS Utility — {title}  ',
             bg=_B['title_bg'], fg=_B['title_fg'],
             font=_B['font_lg']).pack(side='left', padx=4, pady=3)
    tk.Label(hdr, text='Ver 3.40.1  |  Intel® Core™ i7  |  AMIBIOS ',
             bg=_B['title_bg'], fg='#444444',
             font=_B['font_sm']).pack(side='right', padx=8)
    if subtitle:
        tk.Label(win, text=subtitle, bg=_B['bg'], fg=_B['cyan'],
                 font=_B['font_sm']).pack(anchor='w', padx=10, pady=2)


def _bios_footer(win, hints: str = ''):
    """Render the classic BIOS footer with key hints."""
    default = '←→ Select Screen   ↑↓ Select Item   Enter: Select   +/− Change Value   F10 Save & Exit   Esc Exit'
    foot = tk.Frame(win, bg=_B['title_bg'])
    foot.pack(fill='x', side='bottom')
    tk.Label(foot, text=f'  {hints or default}  ',
             bg=_B['title_bg'], fg=_B['title_fg'],
             font=_B['font_sm']).pack(side='left', pady=2)


def _bios_nav_bar(win, tabs: list, active: int, on_tab):
    """Render the top tab navigation bar (Main / Advanced / Boot / Security…)."""
    bar = tk.Frame(win, bg=_B['bg'])
    bar.pack(fill='x', pady=(0, 4))
    for i, name in enumerate(tabs):
        bg = _B['hi_bg'] if i == active else _B['bg2']
        fg = _B['hi']    if i == active else _B['fg']
        btn = tk.Label(bar, text=f' {name} ', bg=bg, fg=fg,
                       font=_B['font'], padx=6, pady=3,
                       relief='raised' if i == active else 'flat',
                       cursor='hand2')
        btn.pack(side='left', padx=1)
        btn.bind('<Button-1>', lambda e, idx=i: on_tab(idx))


def _bios_row(parent, label: str, value: str = '',
              value_color: str | None = None, bold: bool = False):
    """Single configuration row. Returns (row_frame, [all_child_widgets])."""
    row = tk.Frame(parent, bg=_B['bg2'])
    row.pack(fill='x', padx=4, pady=1)
    children = []
    lbl = tk.Label(row, text=label, bg=_B['bg2'], fg=_B['fg'],
                   font=('Consolas', 11, 'bold') if bold else _B['font'],
                   width=36, anchor='w')
    lbl.pack(side='left')
    children.append(lbl)
    if value:
        val_lbl = tk.Label(row, text=f'[{value}]',
                           bg=_B['bg2'], fg=value_color or _B['cyan'],
                           font=_B['font'])
        val_lbl.pack(side='left')
        children.append(val_lbl)
    # Store children on the frame for easy retrieval
    row._bios_children = children
    return row


def _bios_section(parent, title: str):
    """Section header row."""
    tk.Label(parent, text=f' ── {title} ──',
             bg=_B['bg'], fg=_B['yellow'],
             font=('Consolas', 10, 'bold')).pack(anchor='w', padx=6, pady=(6, 1))


# ── POST (Power-On Self-Test) animation ──────────────────────────────────────
def show_post_screen(on_done):
    """Authentic POST screen with memory count, device detection, then BIOS."""
    post = tk.Toplevel()
    post.title('POST')
    post.attributes('-fullscreen', True)
    post.configure(bg='black')
    post.attributes('-topmost', True)

    out = tk.Text(post, bg='black', fg='#aaaaaa', font=('Consolas', 11),
                  bd=0, highlightthickness=0, state='disabled',
                  insertbackground='#aaaaaa')
    out.pack(fill='both', expand=True, padx=20, pady=16)
    out.tag_config('white',  foreground='#ffffff')
    out.tag_config('green',  foreground='#55ff55')
    out.tag_config('yellow', foreground='#ffff55')
    out.tag_config('red',    foreground='#ff5555')
    out.tag_config('cyan',   foreground='#55ffff')
    out.tag_config('dim',    foreground='#666666')

    def write(text, tag='white', end='\n'):
        out.config(state='normal')
        out.insert('end', text + end, tag)
        out.see('end')
        out.config(state='disabled')

    # Bottom bar: Press DEL
    del_lbl = tk.Label(post,
                       text='  Press  DEL  to enter BIOS Setup   |   Press  F8  for Boot Menu  ',
                       bg='#555500', fg='#ffff55', font=('Consolas', 11))
    del_lbl.pack(side='bottom', fill='x')

    ram_mb = int(state.get('ram_size', '8').replace('GB', '').replace('gb', '').strip() or 8) * 1024

    post_lines = [
        (0,   'white',  'American Megatrends AMIBIOS (C)2009  All Rights Reserved'),
        (60,  'dim',    'BIOS Version: 3.40.1  |  Build Date: 11/14/2009'),
        (120, 'white',  ''),
        (180, 'cyan',   'CPU: Intel(R) Core(TM) i7 CPU  @ 2.80GHz'),
        (240, 'white',  'Speed: 2800 MHz  |  Cores: 4  |  Threads: 8'),
        (300, 'white',  ''),
        (360, 'yellow', 'Memory Test:'),
    ]

    # RAM count animation
    ram_steps = list(range(0, ram_mb + 1, max(1, ram_mb // 40)))
    if ram_steps[-1] != ram_mb:
        ram_steps.append(ram_mb)

    drive_lines = [
        (0,   'white',  ''),
        (0,   'green',  f'Memory OK — {ram_mb} MB System RAM Detected'),
        (80,  'white',  ''),
        (160, 'cyan',   'Detecting Storage Devices...'),
        (260, 'white',  'Primary IDE Master:   WDC WD5000AAKX-00ERMA0  [500 GB]'),
        (360, 'white',  'Primary IDE Slave:    ST1000DM003-1CH162       [1000 GB]'),
        (460, 'white',  'SATA-1:               SAMSUNG SSD 860 EVO      [250 GB]'),
        (560, 'dim',    'SATA-2 / SATA-3:      [Not Detected]'),
        (660, 'white',  ''),
        (760, 'cyan',   'Detecting USB Devices...'),
        (860, 'white',  'USB-1: Generic USB Hub       USB-2: USB Keyboard       USB-3: USB Mouse'),
        (960, 'white',  ''),
        (1060,'yellow', 'Initializing PCI Devices...'),
        (1160,'white',  'PCI-E x16:  Intel(R) HD Graphics 4000       [VRAM: 1024 MB]'),
        (1260,'white',  'PCI-E x1:   Realtek RTL8111 Gigabit LAN     [MAC: 00:1A:2B:3C:4D:5E]'),
        (1360,'white',  'PCI-E x1:   Realtek ALC887 HD Audio'),
        (1460,'white',  ''),
        (1560,'green',  'All devices initialised successfully.'),
        (1660,'white',  ''),
        (1760,'yellow', 'Press DEL to enter BIOS Setup or F8 for Boot Menu.'),
        (1860,'dim',    'Booting Windows Boot Manager in 3 seconds...'),
    ]

    schedule = []
    t = 0
    for delay, tag, text in post_lines:
        t += delay
        schedule.append((t, tag, text, False))
    # RAM count
    t_ram = t + 60
    for val in ram_steps:
        schedule.append((t_ram, 'green', f'  {val:>8} KB OK', True))
        t_ram += 12
    t = t_ram + 60
    for delay, tag, text in drive_lines:
        t += delay
        schedule.append((t, tag, text, False))

    boot_countdown = {'v': 3, 'job': None}

    def auto_boot():
        if not post.winfo_exists():
            return
        boot_countdown['v'] -= 1
        if boot_countdown['v'] <= 0:
            post.destroy()
            on_done()
        else:
            post.after(1000, auto_boot)

    def run_schedule(idx=0):
        if not post.winfo_exists():
            return
        if idx >= len(schedule):
            boot_countdown['job'] = post.after(1000, auto_boot)
            return
        t_ms, tag, text, overwrite = schedule[idx]
        def do_write():
            if not post.winfo_exists():
                return
            if overwrite:
                # Overwrite last line (RAM counter)
                out.config(state='normal')
                out.delete('end-2l', 'end-1l')
                out.insert('end-1c', text + '\n', tag)
                out.see('end')
                out.config(state='disabled')
            else:
                write(text, tag)
            # next step relative to current
            if idx + 1 < len(schedule):
                next_t = schedule[idx + 1][0] - t_ms
                post.after(max(1, next_t), lambda: run_schedule(idx + 1))
            else:
                post.after(400, lambda: run_schedule(idx + 1))
        post.after(1, do_write)

    run_schedule()

    def on_key_post(event):
        if event.keysym in ('Delete', 'F2'):
            if boot_countdown['job']:
                try:
                    post.after_cancel(boot_countdown['job'])
                except Exception:
                    pass
            post.destroy()
            show_bios_setup()
        elif event.keysym == 'F8':
            if boot_countdown['job']:
                try:
                    post.after_cancel(boot_countdown['job'])
                except Exception:
                    pass
            post.destroy()
            show_bios_boot_selector()

    post.bind('<Key>', on_key_post)
    post.focus_force()
    try:
        post.grab_set()
    except Exception:
        pass


# ── Full BIOS Setup (multi-tab) ───────────────────────────────────────────────
def show_bios_setup(start_tab: int = 0):
    """Full UEFI BIOS Setup Utility with EZ Mode + 8 advanced tabs."""
    win = tk.Toplevel()
    win.title('BIOS Setup Utility')
    win.attributes('-fullscreen', True)
    win.configure(bg=_B['bg'])
    win.attributes('-topmost', True)

    # EZ Mode is tab index 0; advanced tabs start at 1
    TABS = ['EZ Mode', 'Main', 'Advanced', 'Boot', 'Security',
            'OC Tweaker', 'Fan Control', 'Power', 'Diagnostics']
    ctx = {'tab': start_tab}

    bs = state.setdefault('bios_settings', {
        'secure_boot':      'Enabled',
        'fast_boot':        'Enabled',
        'virtualization':   'Enabled',
        'hyperthreading':   'Enabled',
        'xmp':              'Disabled',
        'ahci_mode':        'AHCI',
        'legacy_usb':       'Enabled',
        'above_4g':         'Disabled',
        'pcie_speed':       'Auto',
        'cpu_spread':       'Disabled',
        'boot_order':       ['Windows Boot Manager', 'SATA: WDC WD5000',
                             'USB Drive', 'Network PXE'],
        'boot_logo':        'Enabled',
        'post_delay':       '3 sec',
        'supervisor_pwd':   '',
        'user_pwd':         '',
        'cpu_ratio':        'Auto',
        'bclk':             '100.0 MHz',
        'dram_freq':        '1333 MHz',
        'cpu_vcore':        '1.200 V',
        'dram_voltage':     '1.500 V',
        'fan1_mode':        'Auto',
        'fan2_mode':        'Auto',
        'fan1_target':      '60',
        'fan2_target':      '70',
        'power_on_ac':      'Last State',
        'wake_on_lan':      'Enabled',
        'rtc_wake':         'Disabled',
        'sleep_state':      'S3 (Suspend to RAM)',
        'erp_ready':        'Disabled',
    })

    def render(tab_idx):
        ctx['tab'] = tab_idx
        _bios_clear(win)
        _bios_header(win, TABS[tab_idx])
        _bios_nav_bar(win, TABS, tab_idx, render)

        # ── EZ Mode gets its own full-width layout ────────────────────────
        if tab_idx == 0:
            _bios_tab_ez(win, bs, render, win)
            _bios_footer(win,
                '←→ Tab  ·  F10 Save & Exit  ·  F9 Load Defaults  ·  Esc Exit  ·  DEL Uninstall')
        else:
            body = tk.Frame(win, bg=_B['bg'])
            body.pack(fill='both', expand=True, padx=6, pady=4)

            left  = tk.Frame(body, bg=_B['bg2'], bd=1, relief='ridge')
            left.pack(side='left', fill='both', expand=True, padx=(0, 3))
            right = tk.Frame(body, bg=_B['bg2'], bd=1, relief='ridge')
            right.pack(side='left', fill='y', padx=(3, 0), ipadx=8)

            help_var = tk.StringVar(value='Use ↑↓ to navigate, Enter to change.')
            tk.Label(right, text=' Help ', bg=_B['title_bg'], fg=_B['title_fg'],
                     font=_B['font'], anchor='w').pack(fill='x')
            tk.Label(right, textvariable=help_var, bg=_B['bg2'], fg=_B['dim'],
                     font=_B['font_sm'], wraplength=220, justify='left').pack(
                     anchor='nw', padx=6, pady=4)

            now = datetime.now()
            info_lines = [
                ('CPU Temp', f'{random.randint(38, 52)} °C'),
                ('MB Temp',  f'{random.randint(28, 40)} °C'),
                ('CPU Fan',  f'{random.randint(1100, 1800)} RPM'),
                ('SYS Fan',  f'{random.randint(700,  1100)} RPM'),
                ('Vcore',    bs.get('cpu_vcore', '1.200 V')),
                ('DRAM',     bs.get('dram_voltage', '1.500 V')),
                ('3.3V',     '3.312 V'),
                ('5V',       '4.992 V'),
                ('12V',      '11.880 V'),
            ]
            tk.Label(right, text=' System Health ', bg=_B['title_bg'],
                     fg=_B['title_fg'], font=_B['font'], anchor='w').pack(
                     fill='x', pady=(12, 0))
            for k, v in info_lines:
                row = tk.Frame(right, bg=_B['bg2'])
                row.pack(fill='x', padx=4, pady=1)
                tk.Label(row, text=f'{k}:', bg=_B['bg2'], fg=_B['dim'],
                         font=_B['font_sm'], width=10, anchor='w').pack(side='left')
                color = _B['red'] if '°C' in v and int(v.split()[0]) > 70 else _B['green']
                tk.Label(row, text=v, bg=_B['bg2'], fg=color,
                         font=_B['font_sm']).pack(side='left')

            # ── bottom danger zone: Uninstall + Reset ────────────────────
            danger = tk.Frame(right, bg=_B['bg2'])
            danger.pack(side='bottom', fill='x', pady=8, padx=4)
            tk.Label(danger, text=' ⚠ Danger Zone ', bg='#550000',
                     fg=_B['red'], font=_B['font_sm']).pack(fill='x')
            _ul = tk.Label(danger, text='[ Uninstall Win7 ]',
                           bg='#440000', fg=_B['red'], font=_B['font_sm'],
                           cursor='hand2')
            _ul.pack(fill='x', pady=2)
            _ul.bind('<Button-1>', lambda e: _bios_uninstall_confirm(win))
            _hr = tk.Label(danger, text='[ Hard Reset PC ]',
                           bg='#330000', fg='#ff9955', font=_B['font_sm'],
                           cursor='hand2')
            _hr.pack(fill='x', pady=2)
            _hr.bind('<Button-1>', lambda e: _bios_hard_reset(win))

            if tab_idx == 1:   _bios_tab_main(left, help_var)
            elif tab_idx == 2: _bios_tab_advanced(left, help_var)
            elif tab_idx == 3: _bios_tab_boot(left, help_var, win, render)
            elif tab_idx == 4: _bios_tab_security(left, help_var)
            elif tab_idx == 5: _bios_tab_oc(left, help_var)
            elif tab_idx == 6: _bios_tab_fan(left, help_var)
            elif tab_idx == 7: _bios_tab_power(left, help_var)
            elif tab_idx == 8: _bios_tab_diag(left, help_var, win)

            _bios_footer(win)

        # Global hotkeys (applied on every tab)
        def on_key(e):
            k = e.keysym
            if k == 'Escape':
                if messagebox.askyesno('Exit', 'Exit BIOS without saving?', parent=win):
                    win.destroy()
            elif k == 'F10':
                save_state()
                audit_log('BIOS_SAVE', 'Settings saved via F10', 'INFO')
                if messagebox.askyesno('Save & Exit',
                                       'Save configuration and exit BIOS?', parent=win):
                    win.destroy()
                    show_bios_boot_selector()
            elif k == 'F9':
                if messagebox.askyesno('Defaults',
                                       'Load optimized defaults?', parent=win):
                    state.pop('bios_settings', None)
                    render(ctx['tab'])
            elif k in ('Left', 'Right'):
                new = (ctx['tab'] + (1 if k == 'Right' else -1)) % len(TABS)
                render(new)
            elif k == 'Delete':
                _bios_uninstall_confirm(win)
        win.bind('<Key>', on_key)
        win.bind_all('<Key>', on_key)
        win.focus_force()
        try:
            win.grab_set()
        except Exception:
            pass

    render(start_tab)


# ── EZ Mode tab ───────────────────────────────────────────────────────────────
def _bios_tab_ez(win, bs, render_fn, bios_win):
    """ASUS-style EZ Mode: big visual toggles, one-click actions."""

    outer = tk.Frame(win, bg='#000050')
    outer.pack(fill='both', expand=True, padx=0, pady=0)

    # ── Top info strip ────────────────────────────────────────────────────────
    top = tk.Frame(outer, bg='#000030')
    top.pack(fill='x', padx=0, pady=0)

    now = datetime.now()
    for text, val in [
        ('🖥 CPU', 'Intel Core i7-860 @ 2.80GHz'),
        ('💾 RAM', state.get('ram_size', '8 GB') + '  DDR3-1333'),
        ('🌡 CPU Temp', f'{random.randint(38,52)} °C'),
        ('⚡ Vcore', bs.get('cpu_vcore', '1.200 V')),
        ('📅 Date', now.strftime('%d %b %Y')),
        ('🕐 Time', now.strftime('%H:%M:%S')),
    ]:
        col = tk.Frame(top, bg='#000030', relief='groove', bd=1)
        col.pack(side='left', expand=True, fill='x', padx=2, pady=4)
        tk.Label(col, text=text, bg='#000030', fg='#5588ff',
                 font=('Consolas', 8, 'bold')).pack(anchor='w', padx=6)
        tk.Label(col, text=val, bg='#000030', fg='#aaddff',
                 font=('Consolas', 9)).pack(anchor='w', padx=6, pady=(0, 3))

    # ── Middle: big toggle cards ───────────────────────────────────────────────
    mid = tk.Frame(outer, bg='#000050')
    mid.pack(fill='both', expand=True, padx=10, pady=8)

    TOGGLES = [
        ('Secure Boot',       'secure_boot',    ['Enabled','Disabled'],
         '🔒', 'Prevents unsigned OS from loading.'),
        ('Fast Boot',         'fast_boot',       ['Enabled','Disabled'],
         '⚡', 'Skips slow POST checks for faster startup.'),
        ('Virtualization',    'virtualization',  ['Enabled','Disabled'],
         '📦', 'Required for VMware, VirtualBox, WSL2.'),
        ('Hyper-Threading',   'hyperthreading',  ['Enabled','Disabled'],
         '⚙', 'Doubles logical CPUs. Helps multitasking.'),
        ('XMP/DOCP RAM',      'xmp',             ['Disabled','Profile 1 (1600 MHz)'],
         '🚀', 'Load RAM manufacturer OC profile.'),
        ('SATA Mode',         'ahci_mode',       ['AHCI','IDE','RAID'],
         '💽', 'AHCI = modern. IDE = legacy OS only.'),
        ('Wake on LAN',       'wake_on_lan',      ['Enabled','Disabled'],
         '📡', 'Power on PC via network Magic Packet.'),
        ('Legacy USB',        'legacy_usb',       ['Enabled','Disabled'],
         '🖱', 'USB keyboard/mouse works before OS boots.'),
        ('Turbo Boost',       'turbo_boost',      ['Enabled','Disabled'],
         '🔥', 'CPU boosts above base clock under load.'),
        ('TPM',               'tpm',              ['Enabled','Disabled'],
         '🛡', 'Trusted Platform Module. Needed for BitLocker.'),
        ('ERP (Eco Mode)',    'erp_ready',        ['Disabled','Enabled'],
         '🌿', 'Limits standby power. EU eco standard.'),
        ('CPU SpeedStep',     'speedstep',        ['Enabled','Disabled'],
         '🪫', 'Lowers CPU freq when idle to save power.'),
    ]

    COLS = 4
    for i, (label, key, opts, icon, tip) in enumerate(TOGGLES):
        row_i = i // COLS
        col_i = i % COLS
        val = bs.get(key, opts[0])
        on = val == opts[0]
        card_bg   = '#002800' if on else '#280000'
        val_color = _B['green'] if on else _B['red']
        card = tk.Frame(mid, bg=card_bg, bd=2,
                        relief='ridge', cursor='hand2')
        card.grid(row=row_i, column=col_i, padx=6, pady=6,
                  sticky='nsew', ipadx=6, ipady=6)
        mid.columnconfigure(col_i, weight=1)

        tk.Label(card, text=icon, bg=card_bg, font=('Segoe UI Emoji', 18)).pack()
        tk.Label(card, text=label, bg=card_bg, fg='white',
                 font=('Consolas', 9, 'bold'), wraplength=140).pack()
        val_lbl = tk.Label(card, text=val, bg=card_bg,
                           fg=val_color, font=('Consolas', 9, 'bold'))
        val_lbl.pack(pady=2)
        tk.Label(card, text=tip, bg=card_bg, fg='#778899',
                 font=('Consolas', 7), wraplength=140).pack()

        def on_click(e, k=key, o=opts):
            cur = bs.get(k, o[0])
            idx = o.index(cur) if cur in o else 0
            bs[k] = o[(idx + 1) % len(o)]
            save_state()
            render_fn(0)   # re-render EZ mode

        card.bind('<Button-1>', on_click)
        for child in card.winfo_children():
            child.bind('<Button-1>', on_click)

    # ── Bottom action row ─────────────────────────────────────────────────────
    bot = tk.Frame(outer, bg='#000020')
    bot.pack(fill='x', padx=10, pady=(4, 0))

    actions = [
        ('⚡  Boot Now',            '#003a6a', '#55aaff',
         lambda: [bios_win.destroy(), show_bios_boot_selector()]),
        ('🔃  Reinstall Windows 7', '#003a00', '#55ff88',
         lambda: [bios_win.destroy(), show_bios_boot_selector(reinstall=True)]),
        ('💽  Boot from USB',       '#3a2000', '#ffaa55',
         lambda: [bios_win.destroy(), show_usb_boot_sequence()]),
        ('🗑  Uninstall Windows 7', '#500000', '#ff5555',
         lambda: _bios_uninstall_confirm(bios_win)),
        ('⚙  Advanced Mode',       '#1a0050', '#aa77ff',
         lambda: render_fn(1)),
        ('🔄  Hard Reset',          '#3a1000', '#ff7722',
         lambda: _bios_hard_reset(bios_win)),
        ('💾  Save & Exit (F10)',   '#003030', '#55ffff',
         lambda: [save_state(), bios_win.destroy(), show_bios_boot_selector()]),
        ('⚠  Load Defaults (F9)',  '#2a1a00', '#ffcc44',
         lambda: [state.pop('bios_settings', None), render_fn(0)]),
    ]
    for text, bg, fg, cmd in actions:
        btn = tk.Label(bot, text=text, bg=bg, fg=fg,
                       font=('Consolas', 10, 'bold'),
                       padx=10, pady=8, cursor='hand2', relief='raised')
        btn.pack(side='left', padx=4, pady=6)
        btn.bind('<Button-1>', lambda e, f=cmd: f())

    # Boot order strip
    order_frame = tk.Frame(outer, bg='#00001a')
    order_frame.pack(fill='x', padx=10, pady=(2, 6))
    tk.Label(order_frame, text='Boot Priority: ', bg='#00001a',
             fg='#445566', font=('Consolas', 9)).pack(side='left')
    for i, dev in enumerate(bs.get('boot_order', ['Windows Boot Manager'])):
        tk.Label(order_frame, text=f'  {i+1}. {dev}  ',
                 bg='#001830' if i == 0 else '#00001a',
                 fg='#55aaff' if i == 0 else '#334455',
                 font=('Consolas', 9), relief='groove').pack(side='left', padx=2)


# ── Uninstall confirmation ────────────────────────────────────────────────────
def _bios_uninstall_confirm(bios_win):
    """Confirm then wipe Windows 7 state — PC gets stuck in BIOS needing USB boot."""
    if not messagebox.askyesno(
            'Uninstall Windows 7',
            'This will COMPLETELY remove Windows 7 from this PC.\n\n'
            'All data, settings, and installed apps will be deleted.\n\n'
            'You will need to boot from USB to reinstall an operating system.\n\n'
            'Are you absolutely sure?',
            parent=bios_win):
        return
    # Second confirmation
    if not messagebox.askyesno(
            'FINAL WARNING',
            'There is NO going back after this step.\n\n'
            'Click YES to wipe Windows 7 now.',
            parent=bios_win):
        return

    # Wipe all Windows state
    state.clear()
    state.update({
        'user_name': '', 'first_name': '', 'last_name': '',
        'notes': [], 'tasks': [], 'habit_tracker': {},
        'os_uninstalled': True,
        'os_corrupted': False,
        'core_deleted': False,
        'bios_security_disabled': False,
        'bios_settings': {},
    })
    try:
        save_state()
    except Exception:
        pass
    audit_log('WINDOWS_UNINSTALLED', 'All state wiped', 'CRITICAL')

    bios_win.destroy()
    _show_uninstall_wipe_screen()


def _show_uninstall_wipe_screen():
    """Dramatic wipe animation before dropping to BIOS."""
    w = tk.Toplevel()
    w.attributes('-fullscreen', True)
    w.configure(bg='black')
    w.attributes('-topmost', True)

    out = tk.Text(w, bg='black', fg='#ff4444',
                  font=('Consolas', 11), bd=0, highlightthickness=0,
                  state='disabled')
    out.pack(fill='both', expand=True, padx=30, pady=20)
    out.tag_config('red',    foreground='#ff4444')
    out.tag_config('yellow', foreground='#ffff44')
    out.tag_config('green',  foreground='#44ff44')
    out.tag_config('dim',    foreground='#555555')

    def write(text, tag='red'):
        out.config(state='normal')
        out.insert('end', text + '\n', tag)
        out.see('end')
        out.config(state='disabled')

    lines = [
        (0,   'yellow', 'Windows 7 Uninstallation'),
        (100, 'dim',    '─' * 60),
        (200, 'red',    'Removing Windows Boot Manager...'),
        (600, 'red',    'Wiping system partition (C:\\)...'),
        (300, 'red',    '  Deleting Windows\\System32...'),
        (200, 'red',    '  Deleting Windows\\SysWOW64...'),
        (200, 'red',    '  Deleting Program Files...'),
        (200, 'red',    '  Deleting Users\\...'),
        (200, 'red',    '  Deleting pagefile.sys...'),
        (300, 'red',    'Clearing MBR / GPT partition table...'),
        (400, 'yellow', 'Partition table wiped.'),
        (300, 'red',    'Removing boot entries...'),
        (400, 'green',  'Uninstallation complete.'),
        (300, 'dim',    '─' * 60),
        (400, 'yellow', 'No operating system detected.'),
        (300, 'yellow', 'Please insert a bootable USB drive or DVD.'),
        (500, 'dim',    'Press any key to enter BIOS Setup...'),
    ]

    t = 0
    for delay, tag, text in lines:
        t += delay
        w.after(t, lambda tg=tag, tx=text: write(tx, tg))

    def go_bios(event=None):
        w.destroy()
        # State is wiped — go straight to BIOS, boot selector starts with reinstall=True
        show_bios_setup(start_tab=0)

    w.after(t + 1200, lambda: w.bind('<Key>', go_bios))
    w.after(t + 1200, lambda: w.bind('<Button-1>', go_bios))
    w.focus_force()


# ── Hard Reset ────────────────────────────────────────────────────────────────
def _bios_hard_reset(bios_win):
    """Hard reset — close everything and re-run POST → BIOS."""
    if not messagebox.askyesno('Hard Reset',
                               'Force reset the PC now?\n\n'
                               'Unsaved BIOS changes will be lost.',
                               parent=bios_win):
        return
    audit_log('BIOS_HARD_RESET', '', 'WARN')
    bios_win.destroy()
    # Brief black screen then POST
    black = tk.Toplevel()
    black.attributes('-fullscreen', True)
    black.configure(bg='black')
    black.attributes('-topmost', True)
    black.after(800, lambda: [black.destroy(),
                              show_post_screen(on_done=show_bios_boot_selector)])
    black.focus_force()


# ── USB Boot → Full OOBE (Out-of-Box Experience) ─────────────────────────────
def show_usb_boot_sequence():
    """Animate USB boot detection then launch the full Windows 7 OOBE."""
    w = tk.Toplevel()
    w.attributes('-fullscreen', True)
    w.configure(bg='black')
    w.attributes('-topmost', True)

    out = tk.Text(w, bg='black', fg='#aaaaaa', font=('Consolas', 11),
                  bd=0, highlightthickness=0, state='disabled')
    out.pack(fill='both', expand=True, padx=30, pady=20)
    out.tag_config('white',  foreground='#ffffff')
    out.tag_config('green',  foreground='#55ff55')
    out.tag_config('yellow', foreground='#ffff55')
    out.tag_config('cyan',   foreground='#55ffff')
    out.tag_config('dim',    foreground='#666666')

    def write(text, tag='white'):
        out.config(state='normal')
        out.insert('end', text + '\n', tag)
        out.see('end')
        out.config(state='disabled')

    usb_lines = [
        (0,   'white',  'Scanning for bootable devices...'),
        (500, 'dim',    '  HDD 0:  No OS detected'),
        (300, 'dim',    '  HDD 1:  No OS detected'),
        (400, 'cyan',   '  USB 0:  ★ Bootable USB detected — Windows 7 Setup'),
        (300, 'white',  ''),
        (200, 'yellow', 'Booting from USB: KINGSTON DataTraveler 32GB'),
        (400, 'white',  'Loading files...'),
        (300, 'dim',    '  boot\\bcd loaded'),
        (200, 'dim',    '  boot\\bootmgr loaded'),
        (200, 'dim',    '  sources\\boot.wim loaded'),
        (400, 'white',  'Starting Windows Setup...'),
        (600, 'green',  'Windows is loading files  ████████████████  100%'),
    ]

    t = 0
    for delay, tag, text in usb_lines:
        t += delay
        w.after(t, lambda tg=tag, tx=text: write(tx, tg))

    w.after(t + 800, lambda: [w.destroy(), show_oobe_sequence()])


def show_oobe_sequence():
    """Full Windows 7 OOBE — trailer video → language → EULA → key → account → welcome."""
    oobe = tk.Toplevel()
    oobe.attributes('-fullscreen', True)
    oobe.configure(bg='black')
    oobe.attributes('-topmost', True)

    ctx = {'step': 0}

    # ── OOBE helpers ──────────────────────────────────────────────────────────
    def oobe_clear():
        for w in oobe.winfo_children():
            try: w.destroy()
            except Exception: pass

    def oobe_header(step_n, title, subtitle=''):
        tk.Frame(oobe, bg='#0d2a52', height=4).pack(fill='x')
        top = tk.Frame(oobe, bg='#0d2a52')
        top.pack(fill='x')
        tk.Label(top, text='Windows', bg='#0d2a52', fg='#55aaff',
                 font=('Segoe UI Light', 28, 'bold')).pack(side='left', padx=24, pady=14)
        tk.Label(top, text=f'Step {step_n} of 5',
                 bg='#0d2a52', fg='#3a6898', font=('Segoe UI', 9)).pack(side='right', padx=20)
        tk.Frame(oobe, bg='#1a5090', height=2).pack(fill='x')
        if title:
            tk.Label(oobe, text=title, bg='#1a3a6a', fg='white',
                     font=('Segoe UI', 22, 'bold')).pack(pady=(24, 4))
        if subtitle:
            tk.Label(oobe, text=subtitle, bg='#1a3a6a', fg='#88aacc',
                     font=('Segoe UI', 11)).pack(pady=(0, 16))

    def oobe_nav(on_back=None, on_next=None, back_text='← Back', next_text='Next →'):
        bf = tk.Frame(oobe, bg='#0d2052')
        bf.pack(side='bottom', fill='x')
        tk.Frame(bf, bg='#0d2052').pack(fill='x', pady=2)
        if on_back:
            tk.Button(bf, text=back_text, bg='#1a3a6a', fg='white',
                      font=('Segoe UI', 11), padx=20, pady=6, relief='flat',
                      command=on_back).pack(side='left', padx=20, pady=10)
        if on_next:
            tk.Button(bf, text=next_text, bg='#1e6ac0', fg='white',
                      font=('Segoe UI', 11, 'bold'), padx=28, pady=6, relief='flat',
                      command=on_next).pack(side='right', padx=20, pady=10)

    # ── Step 0: Windows 7 Trailer Video ──────────────────────────────────────
    def step_trailer():
        oobe_clear()
        oobe.configure(bg='black')

        # Try to stream the official Windows 7 trailer from YouTube via embedded player
        # We simulate it with an animated cinematic intro since we can't embed YouTube in Tkinter
        # But we open the real trailer in the default browser for the user

        import webbrowser
        TRAILER_URL = 'https://www.youtube.com/watch?v=XsJE3j6LFEM'

        canvas = tk.Canvas(oobe, bg='black', highlightthickness=0)
        canvas.pack(fill='both', expand=True)

        W = oobe.winfo_screenwidth()
        H = oobe.winfo_screenheight()

        # Cinematic black bars
        BAR_H = int(H * 0.12)
        canvas.create_rectangle(0, 0, W, BAR_H, fill='black', outline='')
        canvas.create_rectangle(0, H-BAR_H, W, H, fill='black', outline='')

        # Background gradient simulation
        for i in range(BAR_H, H-BAR_H, 2):
            frac = (i - BAR_H) / (H - 2*BAR_H)
            r = int(10 + 30*frac)
            g = int(18 + 50*frac)
            b = int(40 + 80*frac)
            canvas.create_line(0, i, W, i, fill=f'#{r:02x}{g:02x}{b:02x}')

        # Animated Windows orbs
        CX, CY = W//2, H//2
        orb_colors  = ['#f04820', '#ffb900', '#7fba00', '#00a8ef']
        orb_offsets = [(-44,-44),(4,-44),(-44,4),(4,4)]
        ORB_R = 38
        orb_ids = []
        for clr, (ox,oy) in zip(orb_colors, orb_offsets):
            x0,y0 = CX+ox-ORB_R, CY+oy-ORB_R
            x1,y1 = CX+ox+ORB_R, CY+oy+ORB_R
            oid = canvas.create_oval(x0,y0,x1,y1, fill=clr, outline='', tags='orb')
            orb_ids.append((oid, CX+ox, CY+oy))

        # Text layers
        txt_w7  = canvas.create_text(CX, CY-130, text='Windows 7', fill='#00000000',
                                     font=('Segoe UI Light', 54, 'bold'), tags='txt')
        txt_tag = canvas.create_text(CX, CY+130, text='', fill='#aaccff',
                                     font=('Segoe UI', 16), tags='txt')
        txt_sub = canvas.create_text(CX, CY+165,
                                     text='Your PC simplified.',
                                     fill='#00000000', font=('Segoe UI', 13), tags='txt')
        canvas.create_text(CX, H-BAR_H//2,
                           text='Press SPACE to skip  •  Opening official trailer in browser…',
                           fill='#334466', font=('Segoe UI', 10))

        # Opening animation state
        anim = {'tick': 0, 'phase': 'fade_in', 'alpha': 0.0, 'done': False}

        TAGLINES = [
            'Faster. Simpler. More fun.',
            'Do what you love.',
            'Designed around you.',
            'Be more productive.',
            'Your PC, simplified.',
        ]
        tag_idx = {'v': 0}

        def to_hex_color(r, g, b, a=1.0):
            return f'#{int(r*a):02x}{int(g*a):02x}{int(b*a):02x}'

        def lerp_color(hex_from, hex_to, t):
            f = [int(hex_from[i:i+2], 16) for i in (1,3,5)]
            to = [int(hex_to[i:i+2], 16) for i in (1,3,5)]
            return '#' + ''.join(f'{int(f[i]+(to[i]-f[i])*t):02x}' for i in range(3))

        def anim_frame():
            if not oobe.winfo_exists() or anim['done']:
                return
            t = anim['tick']
            anim['tick'] += 1

            # Orb pulse + slow rotation
            angle = t * 0.015
            for i,(oid,bx,by) in enumerate(orb_ids):
                phase = angle + i * math.pi/2
                ox = int(bx + 8*math.cos(phase))
                oy = int(by + 8*math.sin(phase))
                scale = 1.0 + 0.08*math.sin(t*0.06 + i)
                r = int(ORB_R * scale)
                try:
                    canvas.coords(oid, ox-r,oy-r,ox+r,oy+r)
                except Exception:
                    return

            # Fade in title
            if t < 60:
                a = min(1.0, t/60)
                col = lerp_color('#000000', '#ffffff', a)
                try: canvas.itemconfig(txt_w7, fill=col)
                except Exception: return

            # Rotate taglines
            if t % 90 == 0 and t > 30:
                tag_idx['v'] = (tag_idx['v']+1) % len(TAGLINES)
            if t > 30:
                ti = min(1.0, (t % 90) / 30)
                ta = math.sin(ti * math.pi)
                col = lerp_color('#000000', '#aaccff', ta)
                try:
                    canvas.itemconfig(txt_tag, text=TAGLINES[tag_idx['v']], fill=col)
                    canvas.itemconfig(txt_sub, fill=lerp_color('#000000','#667799', min(1.0,t/80)))
                except Exception: return

            # End after ~8 seconds → go to language
            if t >= 200:
                anim['done'] = True
                oobe.after(400, step_language)
                return
            oobe.after(40, anim_frame)

        # Open real trailer in browser
        try:
            webbrowser.open(TRAILER_URL)
        except Exception:
            pass

        oobe.bind('<space>', lambda e: [anim.update({'done': True}), step_language()])
        oobe.bind('<Return>', lambda e: [anim.update({'done': True}), step_language()])
        oobe.after(100, anim_frame)

        # Skip button
        skip_btn = tk.Button(oobe, text='Skip ▶', bg='#111122', fg='#334466',
                             relief='flat', font=('Segoe UI', 9), cursor='hand2',
                             command=lambda: [anim.update({'done': True}), skip_btn.destroy(), step_language()])
        skip_btn.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor='se')

    # ── Step 1: Language & Region ─────────────────────────────────────────────
    def step_language():
        oobe_clear()
        oobe.configure(bg='#1a3a6a')
        oobe_header(1, 'Install Windows', 'Choose your language and region settings.')
        body = tk.Frame(oobe, bg='#1a3a6a')
        body.pack(fill='both', expand=True, padx=80, pady=10)
        fields = [
            ('Language to install:',     'install_language',
             ['English (United States)','English (United Kingdom)',
              'Hindi','French','German','Spanish','Japanese','Chinese']),
            ('Time and currency format:', 'time_format',
             ['English (India)','English (United States)','French (France)',
              'German (Germany)','Japanese (Japan)']),
            ('Keyboard or input method:', 'keyboard',
             ['US','US International','UK','French','German','Hindi']),
        ]
        for label, key, options in fields:
            row = tk.Frame(body, bg='#1a3a6a')
            row.pack(fill='x', pady=10)
            tk.Label(row, text=label, bg='#1a3a6a', fg='#aaccee',
                     font=('Segoe UI', 11), width=32, anchor='w').pack(side='left')
            var = tk.StringVar(value=state.get(key, options[0]))
            cb = ttk.Combobox(row, textvariable=var, values=options, state='readonly',
                              width=36, font=('Segoe UI', 11))
            cb.pack(side='left')
            cb.bind('<<ComboboxSelected>>', lambda e, k=key, v=var: state.update({k: v.get()}))
        oobe_nav(on_next=step_eula)

    # ── Step 2: License Agreement ─────────────────────────────────────────────
    def step_eula():
        oobe_clear()
        oobe.configure(bg='#1a3a6a')
        oobe_header(2, 'License Agreement', 'Please read the following license terms carefully.')
        eula_frame = tk.Frame(oobe, bg='#1a3a6a')
        eula_frame.pack(fill='both', expand=True, padx=80, pady=8)
        eula_text = tk.Text(eula_frame, bg='white', fg='#1a2a3a',
                            font=('Segoe UI', 9), wrap='word', relief='flat', width=90)
        eula_sb = ttk.Scrollbar(eula_frame, command=eula_text.yview)
        eula_text.config(yscrollcommand=eula_sb.set)
        eula_sb.pack(side='right', fill='y')
        eula_text.pack(fill='both', expand=True)
        eula_text.insert('1.0', """MICROSOFT SOFTWARE LICENSE TERMS\nWINDOWS 7 OPERATING SYSTEM\n\n""" +
            """These license terms are an agreement between Microsoft Corporation and you.\n\n""" +
            """1. INSTALLATION AND USE RIGHTS.\n   One user may install and use one copy of the software on one device.\n\n""" +
            """2. SCOPE OF LICENSE.\n   The software is licensed, not sold.\n\n""" +
            """3. INTERNET-BASED SERVICES.\n   The software may include internet-connected features.\n\n""" +
            """4. ACTIVATION.\n   Internet or telephone activation is required for genuine validation.\n\n""" +
            """5. PRIVACY.\n   Your privacy is important. Some features send or receive information.\n\n""" +
            """This is a simulation environment for educational purposes.""")
        eula_text.config(state='disabled')
        accept_var = tk.BooleanVar(value=False)
        accept_row = tk.Frame(oobe, bg='#1a3a6a')
        accept_row.pack(fill='x', padx=80, pady=6)
        tk.Checkbutton(accept_row, text='I accept the license terms', variable=accept_var,
                       bg='#1a3a6a', fg='white', activebackground='#1a3a6a',
                       selectcolor='#0d2a52', font=('Segoe UI', 11)).pack(side='left')
        def try_next():
            if not accept_var.get():
                messagebox.showwarning('License', 'You must accept the license terms.', parent=oobe)
                return
            step_product_key()
        oobe_nav(on_back=step_language, on_next=try_next, next_text='Accept & Next →')

    # ── Step 3: Product Key ───────────────────────────────────────────────────
    def step_product_key():
        oobe_clear()
        oobe.configure(bg='#1a3a6a')
        oobe_header(3, 'Product Key', 'Enter your Windows 7 product key.')
        body = tk.Frame(oobe, bg='#1a3a6a')
        body.pack(fill='both', expand=True, padx=100, pady=20)
        tk.Label(body, text='Product Key:', bg='#1a3a6a', fg='#aaccee',
                 font=('Segoe UI', 11)).pack(anchor='w', pady=(10,4))
        key_frame = tk.Frame(body, bg='#1a3a6a')
        key_frame.pack(anchor='w')
        segments = []
        for i in range(5):
            sv = tk.StringVar()
            se = tk.Entry(key_frame, textvariable=sv, width=6, font=('Consolas', 14, 'bold'),
                          bg='white', fg='#1a2a3a', justify='center', relief='flat',
                          highlightthickness=2, highlightbackground='#4a80b8')
            se.pack(side='left', padx=(0 if i == 0 else 4))
            if i < 4:
                tk.Label(key_frame, text='–', bg='#1a3a6a', fg='white',
                         font=('Segoe UI', 14, 'bold')).pack(side='left')
            segments.append((sv, se))
            def on_type(event, idx=i, sv=sv):
                v = sv.get().upper().replace('-','')[:5]
                sv.set(v)
                if len(v)==5 and idx<4: segments[idx+1][1].focus_set()
            se.bind('<KeyRelease>', on_type)
        tk.Label(body, text='Sample key: W-XPWJ-GH467-C6X8H-GJQ94-3BKPM (try it!)',
                 bg='#1a3a6a', fg='#3a6898', font=('Segoe UI', 9)).pack(anchor='w', pady=(12,0))
        tk.Label(body, text='Or leave blank to skip (activate later).',
                 bg='#1a3a6a', fg='#3a6898', font=('Segoe UI', 9)).pack(anchor='w')
        status_lbl = tk.Label(body, text='', bg='#1a3a6a', font=('Segoe UI', 10))
        status_lbl.pack(anchor='w', pady=6)
        auto_activate = tk.BooleanVar(value=True)
        tk.Checkbutton(body, text='Automatically activate Windows when online',
                       variable=auto_activate, bg='#1a3a6a', fg='white',
                       activebackground='#1a3a6a', selectcolor='#0d2a52',
                       font=('Segoe UI', 10)).pack(anchor='w')
        VALID_KEYS = {'W-XPWJ-GH467-C6X8H-GJQ94-3BKPM', 'XXXXX-XXXXX-XXXXX-XXXXX-XXXXX'}
        def try_next():
            full_key = '-'.join(sv.get().upper() for sv,_ in segments)
            clean = full_key.replace('-','')
            if clean == '':
                state['product_key'] = ''; state['os_activated'] = False
                step_user_account(); return
            if len(clean)==25 or full_key in VALID_KEYS:
                state['product_key'] = full_key; state['os_activated'] = True
                status_lbl.config(text='✅ Product key accepted!', fg='#55ff88')
                oobe.after(800, step_user_account)
            else:
                status_lbl.config(text='❌ Invalid product key.', fg='#ff6666')
        oobe_nav(on_back=step_eula, on_next=try_next)

    # ── Step 4: Create User Account ───────────────────────────────────────────
    def step_user_account():
        oobe_clear()
        oobe.configure(bg='#1a3a6a')
        oobe_header(4, 'Set Up Your Account', 'Create a user account to log in to Windows 7.')
        body = tk.Frame(oobe, bg='#1a3a6a')
        body.pack(fill='both', expand=True, padx=100, pady=10)
        fields_def = [
            ('Your name:',        'first_name', state.get('first_name',''), False),
            ('Computer name:',    'pc_name',    'Ryan-PC',                  False),
            ('Password:',         '_pwd1',      '',                         True),
            ('Confirm password:', '_pwd2',      '',                         True),
            ('Password hint:',    'pwd_hint',   '',                         False),
        ]
        entries = {}
        for label, key, default, is_pwd in fields_def:
            row = tk.Frame(body, bg='#1a3a6a')
            row.pack(fill='x', pady=8)
            tk.Label(row, text=label, bg='#1a3a6a', fg='#aaccee',
                     font=('Segoe UI', 11), width=22, anchor='w').pack(side='left')
            var = tk.StringVar(value=default)
            tk.Entry(row, textvariable=var, width=32, font=('Segoe UI', 11),
                     bg='white', fg='#1a2a3a', show='●' if is_pwd else '',
                     relief='flat', highlightthickness=2,
                     highlightbackground='#4a80b8').pack(side='left')
            entries[key] = var
        status_lbl = tk.Label(body, text='', bg='#1a3a6a', font=('Segoe UI', 10))
        status_lbl.pack(anchor='w', pady=6)
        def try_next():
            name = entries['first_name'].get().strip()
            pwd1 = entries['_pwd1'].get()
            pwd2 = entries['_pwd2'].get()
            if not name:
                status_lbl.config(text='⚠  Please enter your name.', fg='#ffaa44'); return
            if pwd1 != pwd2:
                status_lbl.config(text='❌  Passwords do not match.', fg='#ff6666'); return
            state['first_name'] = name; state['last_name'] = ''
            state['user_name']  = name
            state['pc_name']    = entries['pc_name'].get().strip() or 'Ryan-PC'
            state['pwd_hint']   = entries['pwd_hint'].get()
            if pwd1:
                salt, key = hash_password(pwd1)
                sec = load_security(); sec['salt'] = salt; sec['key'] = key
                save_security(sec)
            status_lbl.config(text='✅  Account created!', fg='#55ff88')
            oobe.after(600, step_setup_loading)
        oobe_nav(on_back=step_product_key, on_next=try_next, next_text='Create Account →')

    # ── Step 5: Windows Setup Loading ─────────────────────────────────────────
    def step_setup_loading():
        oobe_clear()
        oobe.configure(bg='black')
        tk.Label(oobe, text='', bg='black').pack(pady=40)
        tk.Label(oobe, text='Windows', bg='black', fg='#55aaff',
                 font=('Segoe UI Light', 36, 'bold')).pack()
        tk.Label(oobe, text='Setting up your computer for first use...',
                 bg='black', fg='#666666', font=('Segoe UI', 12)).pack(pady=10)
        orb_cv = tk.Canvas(oobe, width=200, height=200, bg='black', highlightthickness=0)
        orb_cv.pack(pady=20)
        orb_colors = ['#f04820','#ffb900','#7fba00','#00a8ef']
        orb_positions = [(60,60),(110,60),(60,110),(110,110)]
        orb_size = 30
        orbs = [orb_cv.create_oval(cx-orb_size,cy-orb_size,cx+orb_size,cy+orb_size,
                                   fill=c,outline='')
                for c,(cx,cy) in zip(orb_colors, orb_positions)]
        pulse_state = {'tick': 0}
        def pulse_orbs():
            if not oobe.winfo_exists(): return
            pulse_state['tick'] += 1
            s = 1.0 + 0.15*math.sin(pulse_state['tick']*0.12)
            for i,(cx,cy) in enumerate(orb_positions):
                sz = int(orb_size*s)
                try: orb_cv.coords(orbs[i],cx-sz,cy-sz,cx+sz,cy+sz)
                except Exception: return
            oobe.after(40, pulse_orbs)
        pulse_orbs()
        phase_lbl = tk.Label(oobe, text='', bg='black', fg='#555555', font=('Segoe UI',10))
        phase_lbl.pack()
        progress_cv = tk.Canvas(oobe, width=460, height=4, bg='#222222', highlightthickness=0)
        progress_cv.pack(pady=8)
        prog_bar = progress_cv.create_rectangle(0,0,0,4, fill='#4a90e2', outline='')
        phases = [
            (800,'Preparing system configuration...'),
            (900,'Installing device drivers...'),
            (800,'Setting up Windows Update...'),
            (700,'Configuring user preferences...'),
            (600,'Installing security updates...'),
            (500,'Optimizing startup programs...'),
            (400,'Almost done...'),
        ]
        def run_phase(idx=0):
            if not oobe.winfo_exists(): return
            if idx >= len(phases):
                progress_cv.coords(prog_bar, 0,0,460,4)
                phase_lbl.config(text='Done!')
                oobe.after(800, step_first_login_welcome); return
            delay, text = phases[idx]
            phase_lbl.config(text=text)
            progress_cv.coords(prog_bar, 0,0,int(460*(idx+1)/len(phases)),4)
            oobe.after(delay, lambda: run_phase(idx+1))
        oobe.after(400, run_phase)

    # ── Final: First Login Welcome ────────────────────────────────────────────
    def step_first_login_welcome():
        oobe_clear()
        oobe.configure(bg='#1a3a6a')
        tk.Label(oobe, text='', bg='#1a3a6a').pack(pady=30)
        tk.Label(oobe, text=f'Welcome, {state.get("first_name","User")}!',
                 bg='#1a3a6a', fg='white', font=('Segoe UI Light', 38, 'bold')).pack()
        tk.Label(oobe, text='Windows 7 has been set up successfully.',
                 bg='#1a3a6a', fg='#88aacc', font=('Segoe UI', 14)).pack(pady=8)
        summary = tk.Frame(oobe, bg='#0d2a52', bd=2, relief='ridge')
        summary.pack(pady=20, padx=160)
        for icon_label, val in [
            ('👤 User',      state.get('first_name','User')),
            ('🖥 Computer',  state.get('pc_name','Ryan-PC')),
            ('💿 Edition',   state.get('os_version','Ultimate')),
            ('🔑 Activated', '✅ Yes' if state.get('os_activated') else '⚠ Activate later'),
            ('💾 RAM',       state.get('ram_size','8 GB')),
        ]:
            row = tk.Frame(summary, bg='#0d2a52')
            row.pack(fill='x', padx=20, pady=4)
            tk.Label(row, text=icon_label, bg='#0d2a52', fg='#5588ff',
                     font=('Segoe UI', 11), width=14, anchor='w').pack(side='left')
            tk.Label(row, text=val, bg='#0d2a52', fg='white',
                     font=('Segoe UI', 11)).pack(side='left')
        def start_windows():
            state['setup_complete'] = True
            state.pop('os_uninstalled', None)
            state['os_corrupted'] = False; state['core_deleted'] = False
            state['bios_security_disabled'] = False
            save_state()
            audit_log('OOBE_COMPLETE', f'User: {state.get("user_name","?")}', 'INFO')
            oobe.destroy()
            show_post_screen(on_done=lambda: show_bios_boot_selector(reinstall=False))
        tk.Button(oobe, text='  Start Windows 7  →', bg='#1e6ac0', fg='white',
                  font=('Segoe UI', 14, 'bold'), padx=30, pady=10,
                  relief='flat', command=start_windows).pack(pady=30)
        oobe.after(200, play_windows7_logon)

    # Start with the trailer
    step_trailer()



# ── Tab: Main ─────────────────────────────────────────────────────────────────
def _bios_tab_main(parent, help_var):
    bs = state.get('bios_settings', {})
    _bios_section(parent, 'System Information')

    now = datetime.now()
    _bios_row(parent, 'BIOS Version',       '3.40.1 (14/11/2009)')
    _bios_row(parent, 'Motherboard',        'ASUS P7P55D-E')
    _bios_row(parent, 'Processor',          'Intel Core i7-860 @ 2.80GHz')
    _bios_row(parent, 'Microcode',          '0x18')
    _bios_row(parent, 'Total Memory',       state.get('ram_size', '8 GB'))
    _bios_row(parent, 'Memory Speed',       '1333 MHz (DDR3)')
    _bios_row(parent, 'Memory Slots',       'Slot A1: 4 GB  |  Slot A2: 4 GB  |  B1: —  |  B2: —')
    _bios_row(parent, '')
    _bios_section(parent, 'Date & Time')

    # Editable date/time
    dt_frame = tk.Frame(parent, bg=_B['bg2'])
    dt_frame.pack(fill='x', padx=4, pady=2)
    tk.Label(dt_frame, text='System Date', bg=_B['bg2'], fg=_B['fg'],
             font=_B['font'], width=36, anchor='w').pack(side='left')
    date_var = tk.StringVar(value=now.strftime('%m/%d/%Y'))
    date_e = tk.Entry(dt_frame, textvariable=date_var, font=_B['font'],
                      bg=_B['bg'], fg=_B['cyan'], insertbackground=_B['cyan'],
                      relief='flat', width=14)
    date_e.pack(side='left')
    date_e.bind('<FocusIn>', lambda e: help_var.set('Format: MM/DD/YYYY'))

    tf_frame = tk.Frame(parent, bg=_B['bg2'])
    tf_frame.pack(fill='x', padx=4, pady=2)
    tk.Label(tf_frame, text='System Time', bg=_B['bg2'], fg=_B['fg'],
             font=_B['font'], width=36, anchor='w').pack(side='left')
    time_var = tk.StringVar(value=now.strftime('%H:%M:%S'))
    time_e = tk.Entry(tf_frame, textvariable=time_var, font=_B['font'],
                      bg=_B['bg'], fg=_B['cyan'], insertbackground=_B['cyan'],
                      relief='flat', width=14)
    time_e.pack(side='left')
    time_e.bind('<FocusIn>', lambda e: help_var.set('Format: HH:MM:SS (24-hour)'))

    _bios_row(parent, '')
    _bios_section(parent, 'Storage Devices')
    _bios_row(parent, 'SATA-0 (Primary)',   'WDC WD5000AAKX  [500 GB]')
    _bios_row(parent, 'SATA-1',             'ST1000DM003      [1 TB]')
    _bios_row(parent, 'SATA-2',             'SAMSUNG SSD 860  [250 GB]')
    _bios_row(parent, 'SATA-3/4/5',         '[Not Detected]', value_color=_B['dim'])
    _bios_row(parent, 'Optical Drive',      'HL-DT-ST DVD±RW  GH24NS90')


# ── Tab: Advanced ─────────────────────────────────────────────────────────────
def _bios_tab_advanced(parent, help_var):
    bs = state.setdefault('bios_settings', {})

    def toggle(key, options):
        cur = bs.get(key, options[0])
        idx = options.index(cur) if cur in options else 0
        bs[key] = options[(idx + 1) % len(options)]
        save_state()

    def make_toggle_row(label, key, options, hint=''):
        r = _bios_row(parent, label, bs.get(key, options[0]))
        children = getattr(r, '_bios_children', [])

        def do_toggle(e=None):
            toggle(key, options)
            _bios_clear(parent)
            _bios_tab_advanced(parent, help_var)

        def on_enter(e=None):
            r.config(bg='#0030aa')
            for c in children:
                try: c.config(bg='#0030aa')
                except Exception: pass

        def on_leave(e=None):
            r.config(bg=_B['bg2'])
            for c in children:
                try: c.config(bg=_B['bg2'])
                except Exception: pass

        for w in [r] + children:
            w.bind('<Button-1>', do_toggle)
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
            w.config(cursor='hand2')

    _bios_section(parent, 'CPU Configuration')
    make_toggle_row('Intel Virtualization Tech (VT-x)', 'virtualization',
                    ['Enabled', 'Disabled'],
                    'Enables hardware-assisted virtualization. Required for VMs.')
    make_toggle_row('Hyper-Threading Technology', 'hyperthreading',
                    ['Enabled', 'Disabled'],
                    'Allows each core to run two threads. Improves multi-task perf.')
    make_toggle_row('CPU C-States', 'cpu_cstates',
                    ['Enabled', 'Disabled'],
                    'Power-saving idle states. Disable for absolute lowest latency.')
    make_toggle_row('Turbo Boost', 'turbo_boost',
                    ['Enabled', 'Disabled'],
                    'Allows CPU to run above base clock under load.')
    make_toggle_row('CPU Spread Spectrum', 'cpu_spread',
                    ['Disabled', 'Enabled'],
                    'Reduces EMI. Disable when overclocking.')

    _bios_section(parent, 'Chipset Configuration')
    make_toggle_row('SATA Mode', 'ahci_mode',
                    ['AHCI', 'IDE', 'RAID'],
                    'AHCI enables NCQ and hot-plug. IDE for legacy OS compatibility.')
    make_toggle_row('Above 4G Decoding', 'above_4g',
                    ['Disabled', 'Enabled'],
                    'Required for GPUs with >4 GB VRAM (e.g. mining rigs).')
    make_toggle_row('PCIe Speed', 'pcie_speed',
                    ['Auto', 'Gen1', 'Gen2', 'Gen3'],
                    'PCIe link speed. Auto is recommended.')
    make_toggle_row('Legacy USB Support', 'legacy_usb',
                    ['Enabled', 'Disabled'],
                    'Enables USB keyboard/mouse before OS loads (e.g. in BIOS).')

    _bios_section(parent, 'Onboard Devices')
    make_toggle_row('Onboard LAN',     'lan_enabled',   ['Enabled', 'Disabled'])
    make_toggle_row('Onboard Audio',   'audio_enabled', ['Enabled', 'Disabled'])
    make_toggle_row('Serial Port',     'serial_port',   ['Disabled', 'Enabled', 'Auto'])
    make_toggle_row('IOMMU',           'iommu',         ['Disabled', 'Enabled'],
                    'Input-Output Memory Management Unit. Needed for GPU passthrough.')

    # ── System Stability Control ──────────────────────────────────────────────
    _bios_section(parent, 'System Stability & Desktop Control')
    help_var.set('DANGER: Lowering stability causes desktop glitching, BSOD, or GSOD.')

    tk.Label(parent,
             text='  ⚠  Stability below "Stable" causes visible desktop effects. "Critical" triggers GSOD + reinstall.',
             bg='#550000', fg=_B['red'], font=_B['font_sm']).pack(fill='x', padx=4, pady=2)

    make_toggle_row('System Stability',       'system_stability',
                    ['Stable', 'Degraded', 'Unstable', 'Critical'],
                    'Controls OS desktop stability. Degraded=flicker, Unstable=BSOD risk, Critical=GSOD+reinstall.')
    make_toggle_row('Desktop Frame Rate',     'desktop_fps',
                    ['60 fps', '30 fps', '15 fps', '5 fps'],
                    'Reduces desktop refresh rate. Lower = more sluggish UI.')
    make_toggle_row('Aero Glass Effects',     'aero_enabled',
                    ['Enabled', 'Disabled'],
                    'Disabling removes transparency and glass effects.')
    make_toggle_row('Terminal Access Level',  'terminal_access',
                    ['Restricted', 'Standard', 'Admin', 'Root'],
                    'Controls what the built-in terminal can do. Root = full system access.')
    make_toggle_row('Feature Lock',           'feature_lock',
                    ['None', 'Repair', 'Security', 'All Apps'],
                    'Locks specific desktop feature categories from launching.')

    def apply_stability():
        save_state()
        try:
            _apply_bios_stability_to_desktop()
        except Exception:
            pass
        show_system_notification('BIOS', f'Stability set to: {bs.get("system_stability","Stable")}')

    tk.Button(parent, text='[ Apply Stability Settings Now ]',
              bg=_B['bg2'], fg=_B['yellow'], font=_B['font'],
              relief='flat', cursor='hand2',
              command=apply_stability).pack(anchor='w', padx=6, pady=4)


# ── Tab: Boot ─────────────────────────────────────────────────────────────────
def _bios_tab_boot(parent, help_var, win, render_fn):
    bs = state.setdefault('bios_settings', {})
    boot_order = bs.setdefault('boot_order',
        ['Windows Boot Manager', 'SATA: WDC WD5000', 'USB Drive', 'Network PXE'])

    _bios_section(parent, 'Boot Priority Order  [+/- to move, Enter to select]')
    help_var.set('Use + / − to move selected device. Enter to boot now.')

    sel_boot = {'idx': 0}
    boot_labels = []

    def refresh_boot():
        for lbl in boot_labels:
            try:
                lbl.destroy()
            except Exception:
                pass
        boot_labels.clear()
        for i, dev in enumerate(boot_order):
            bg = _B['hi_bg'] if i == sel_boot['idx'] else _B['bg2']
            fg = _B['hi']    if i == sel_boot['idx'] else _B['fg']
            lbl = tk.Label(parent, text=f'  {i+1}.  {dev}',
                           bg=bg, fg=fg, font=_B['font'],
                           anchor='w', padx=8, pady=3)
            lbl.pack(fill='x', padx=6, pady=1)
            boot_labels.append(lbl)
            idx_cap = i
            lbl.bind('<Button-1>', lambda e, ii=idx_cap: [
                sel_boot.update({'idx': ii}), refresh_boot()])

    refresh_boot()

    _bios_section(parent, 'Boot Settings')

    def toggle_boot(key, options):
        cur = bs.get(key, options[0])
        idx = options.index(cur) if cur in options else 0
        bs[key] = options[(idx + 1) % len(options)]
        save_state()
        _bios_tab_boot(parent, help_var, win, render_fn)

    for label, key, opts in [
        ('Boot Logo',          'boot_logo',   ['Enabled', 'Disabled']),
        ('POST Delay',         'post_delay',  ['3 sec', '1 sec', '5 sec', '0 sec']),
        ('Fast Boot',          'fast_boot',   ['Enabled', 'Disabled']),
        ('Secure Boot',        'secure_boot', ['Enabled', 'Disabled']),
        ('Boot from USB',      'usb_boot',    ['Enabled', 'Disabled']),
        ('Boot from Network',  'pxe_boot',    ['Disabled', 'Enabled']),
        ('CSM (Legacy BIOS)',  'csm',         ['Disabled', 'Enabled']),
    ]:
        r = _bios_row(parent, label, bs.get(key, opts[0]))
        r.config(cursor='hand2')
        r.bind('<Button-1>', lambda e, k=key, o=opts: toggle_boot(k, o))

    # Boot now buttons
    bf = tk.Frame(parent, bg=_B['bg'])
    bf.pack(fill='x', padx=6, pady=8)
    tk.Label(bf, text='  ▶  Boot Now', bg=_B['hi_bg'], fg=_B['hi'],
             font=_B['font'], padx=12, pady=4, cursor='hand2').pack(
             side='left').bind('<Button-1>', lambda e: [win.destroy(), show_bios_boot_selector()])
    tk.Label(bf, text='  💽  Boot from USB', bg='#004400', fg=_B['green'],
             font=_B['font'], padx=12, pady=4, cursor='hand2').pack(
             side='left', padx=4).bind('<Button-1>',
             lambda e: [win.destroy(), show_usb_boot_sequence()])
    tk.Label(bf, text='  🔃  Reinstall Win7', bg='#0000aa', fg=_B['yellow'],
             font=_B['font'], padx=12, pady=4, cursor='hand2').pack(
             side='left', padx=4).bind('<Button-1>',
             lambda e: [win.destroy(), show_usb_boot_sequence()])
    tk.Label(bf, text='  🗑  Uninstall Win7', bg='#550000', fg=_B['red'],
             font=_B['font'], padx=12, pady=4, cursor='hand2').pack(
             side='left', padx=4).bind('<Button-1>',
             lambda e: _bios_uninstall_confirm(win))

    def on_key_boot(event):
        n = len(boot_order)
        if event.keysym == 'Up':
            sel_boot['idx'] = (sel_boot['idx'] - 1) % n
            refresh_boot()
        elif event.keysym == 'Down':
            sel_boot['idx'] = (sel_boot['idx'] + 1) % n
            refresh_boot()
        elif event.keysym in ('plus', 'equal', 'KP_Add'):
            i = sel_boot['idx']
            if i > 0:
                boot_order[i], boot_order[i-1] = boot_order[i-1], boot_order[i]
                sel_boot['idx'] = i - 1
                save_state(); refresh_boot()
        elif event.keysym in ('minus', 'KP_Subtract'):
            i = sel_boot['idx']
            if i < len(boot_order) - 1:
                boot_order[i], boot_order[i+1] = boot_order[i+1], boot_order[i]
                sel_boot['idx'] = i + 1
                save_state(); refresh_boot()

    parent.winfo_toplevel().bind('<Key>', lambda e: on_key_boot(e), add=True)


# ── Tab: Security ─────────────────────────────────────────────────────────────
def _bios_tab_security(parent, help_var):
    bs = state.setdefault('bios_settings', {})

    _bios_section(parent, 'Password Management')
    help_var.set('Set a supervisor password to restrict BIOS access.')

    # Supervisor password status
    sup_set = bool(bs.get('supervisor_pwd', ''))
    usr_set = bool(bs.get('user_pwd', ''))
    _bios_row(parent, 'Supervisor Password',
              'Installed' if sup_set else 'Not Installed',
              value_color=_B['green'] if sup_set else _B['dim'])
    _bios_row(parent, 'User Password',
              'Installed' if usr_set else 'Not Installed',
              value_color=_B['green'] if usr_set else _B['dim'])

    def set_supervisor():
        help_var.set('Creates a password required to enter BIOS setup.')
        pwd = simpledialog.askstring('Supervisor Password',
                                     'Enter new Supervisor Password (leave blank to clear):',
                                     show='*', parent=parent.winfo_toplevel())
        if pwd is not None:
            bs['supervisor_pwd'] = pwd
            save_state()
            audit_log('BIOS_SUPERVISOR_PWD', 'Supervisor password changed', 'WARN')
            _bios_clear(parent)
            _bios_tab_security(parent, help_var)

    def set_user():
        pwd = simpledialog.askstring('User Password',
                                     'Enter new User Password (leave blank to clear):',
                                     show='*', parent=parent.winfo_toplevel())
        if pwd is not None:
            bs['user_pwd'] = pwd
            save_state()
            _bios_clear(parent)
            _bios_tab_security(parent, help_var)

    btn_frame = tk.Frame(parent, bg=_B['bg'])
    btn_frame.pack(fill='x', padx=6, pady=4)
    for txt, cmd in [('Set Supervisor Password', set_supervisor),
                     ('Set User Password', set_user)]:
        tk.Label(btn_frame, text=f'[ {txt} ]', bg=_B['bg2'], fg=_B['cyan'],
                 font=_B['font'], cursor='hand2', padx=6, pady=3).pack(
                 side='left', padx=4).bind('<Button-1>', lambda e, f=cmd: f())

    _bios_section(parent, 'Security Features')

    def toggle_sec(key, options):
        cur = bs.get(key, options[0])
        idx = options.index(cur) if cur in options else 0
        bs[key] = options[(idx + 1) % len(options)]
        save_state()
        _bios_clear(parent)
        _bios_tab_security(parent, help_var)

    sec_rows = [
        ('Secure Boot',           'secure_boot',  ['Enabled', 'Disabled'],
         'Prevents unsigned bootloaders from running. Disable for Linux.'),
        ('Trusted Platform Module', 'tpm',         ['Enabled', 'Disabled'],
         'TPM 2.0 chip for BitLocker, Windows 11, etc.'),
        ('Intel Boot Guard',      'boot_guard',   ['Enabled', 'Disabled'],
         'Cryptographically verifies the initial boot block.'),
        ('Chassis Intrusion',     'chassis_intr', ['Disabled', 'Enabled'],
         'Triggers an alert if the case is opened.'),
        ('Execute Disable Bit',   'xd_bit',       ['Enabled', 'Disabled'],
         'NX bit — prevents code execution in data pages. Always keep enabled.'),
        ('BIOS Flash Protection', 'flash_prot',   ['Enabled', 'Disabled'],
         'Prevents unsigned code from reflashing the BIOS chip.'),
    ]
    for label, key, opts, hint in sec_rows:
        r = _bios_row(parent, label, bs.get(key, opts[0]))
        children = getattr(r, '_bios_children', [])
        def _bind_sec(row=r, ch=children, k=key, o=opts, h=hint):
            def do(e=None): toggle_sec(k, o)
            def oe(e=None):
                row.config(bg='#0030aa')
                for c in ch:
                    try: c.config(bg='#0030aa')
                    except: pass
                help_var.set(h)
            def ol(e=None):
                row.config(bg=_B['bg2'])
                for c in ch:
                    try: c.config(bg=_B['bg2'])
                    except: pass
            for w in [row] + ch:
                w.bind('<Button-1>', do); w.bind('<Enter>', oe)
                w.bind('<Leave>', ol); w.config(cursor='hand2')
        _bind_sec()

    _bios_section(parent, 'Audit & Access Log')
    last_entries = read_audit_log(5)
    for entry in last_entries[-5:]:
        tk.Label(parent, text=f'  {entry[:72]}', bg=_B['bg2'],
                 fg=_B['dim'], font=_B['font_sm'], anchor='w').pack(
                 fill='x', padx=4)


# ── Tab: OC Tweaker (Overclocking) ────────────────────────────────────────────
def _bios_tab_oc(parent, help_var):
    bs = state.setdefault('bios_settings', {})

    _bios_section(parent, 'CPU Overclocking')
    help_var.set('CAUTION: Incorrect OC settings may damage hardware.')

    tk.Label(parent, text='  ⚠  Overclocking may void warranty and damage hardware.',
             bg='#550000', fg=_B['red'], font=_B['font_sm']).pack(
             fill='x', padx=4, pady=2)

    def inc_dec(key, default, step, fmt, min_v, max_v, suffix=''):
        cur_str = bs.get(key, default).replace(suffix, '').strip()
        try:
            val = float(cur_str)
        except ValueError:
            val = float(default.replace(suffix, '').strip())
        return val, min_v, max_v, step, suffix

    def make_oc_row(label, key, default, step, min_v, max_v, suffix, hint):
        val_str = bs.get(key, default)
        r = _bios_row(parent, label, val_str, value_color=_B['yellow'])
        r.bind('<Enter>', lambda e: help_var.set(hint))

        def on_plus(e, k=key, d=default, s=step, mn=min_v, mx=max_v, su=suffix):
            val, *_ = inc_dec(k, d, s, '', mn, mx, su)
            bs[k] = f'{min(mx, round(val+s, 3))}{su}'; save_state()
            _bios_clear(parent); _bios_tab_oc(parent, help_var)

        def on_minus(e, k=key, d=default, s=step, mn=min_v, mx=max_v, su=suffix):
            val, *_ = inc_dec(k, d, s, '', mn, mx, su)
            bs[k] = f'{max(mn, round(val-s, 3))}{su}'; save_state()
            _bios_clear(parent); _bios_tab_oc(parent, help_var)

        r.config(cursor='hand2')
        r.bind('<Button-1>', on_plus)
        r.bind('<Button-3>', on_minus)
        tk.Label(parent, text='   left-click = +  |  right-click = −',
                 bg=_B['bg'], fg=_B['dim'], font=_B['font_sm']).pack(
                 anchor='e', padx=8)

    make_oc_row('CPU Ratio (Multiplier)', 'cpu_ratio_val', '28', 1, 8, 60, 'x',
                'CPU multiplier. Base clock × ratio = CPU freq. Default: 28× (2.8 GHz).')
    make_oc_row('BCLK Frequency',        'bclk_val',      '100.0', 0.5, 95.0, 200.0, ' MHz',
                'Base clock. Affects CPU, RAM, and PCIe. Safe range: 95–105 MHz.')
    make_oc_row('CPU Vcore',             'cpu_vcore_val', '1.200', 0.025, 0.800, 1.500, ' V',
                'CPU core voltage. Higher OC needs more Vcore. Over 1.40V risks damage.')
    make_oc_row('DRAM Frequency',        'dram_freq_val', '1333', 133, 800, 2400, ' MHz',
                'RAM speed. Match or exceed XMP profile value.')
    make_oc_row('DRAM Voltage',          'dram_v_val',    '1.500', 0.05, 1.30, 1.80, ' V',
                'DRAM voltage. DDR3 standard: 1.5 V. Overclocked kits: up to 1.65 V.')

    _bios_section(parent, 'XMP / DOCP Memory Profile')

    def toggle_xmp():
        bs['xmp'] = 'Profile 1 (1600 MHz)' if bs.get('xmp', 'Disabled') == 'Disabled' else 'Disabled'
        save_state()
        _bios_clear(parent)
        _bios_tab_oc(parent, help_var)

    r = _bios_row(parent, 'XMP / DOCP Profile', bs.get('xmp', 'Disabled'),
                  value_color=_B['green'] if bs.get('xmp') != 'Disabled' else _B['dim'])
    r.config(cursor='hand2')
    r.bind('<Button-1>', lambda e: toggle_xmp())
    r.bind('<Enter>', lambda e: help_var.set(
        'Intel XMP / AMD DOCP: loads the RAM manufacturers rated OC profile.'))


# ── Tab: Fan Control ─────────────────────────────────────────────────────────
def _bios_tab_fan(parent, help_var):
    bs = state.setdefault('bios_settings', {})

    _bios_section(parent, 'Fan Configuration')
    help_var.set('Configure PWM fan curves and target temperatures.')

    fans = [
        ('CPU Fan (Header: CPU_FAN)',  'fan1_mode', 'fan1_target', 'fan1_min'),
        ('Chassis Fan 1 (SYS_FAN1)',   'fan2_mode', 'fan2_target', 'fan2_min'),
        ('Chassis Fan 2 (SYS_FAN2)',   'fan3_mode', 'fan3_target', 'fan3_min'),
    ]
    modes = ['Auto', 'PWM Manual', 'DC Manual', 'Full Speed', 'Silent']

    for fan_label, mode_key, target_key, min_key in fans:
        _bios_section(parent, fan_label)
        cur_mode = bs.get(mode_key, 'Auto')
        cur_target = bs.get(target_key, '60')
        cur_min = bs.get(min_key, '30')

        r = _bios_row(parent, '  Mode', cur_mode)
        r.config(cursor='hand2')
        r.bind('<Button-1>', lambda e, mk=mode_key: [
            bs.update({mk: modes[(modes.index(bs.get(mk,'Auto'))+1) % len(modes)]}),
            save_state(), _bios_clear(parent), _bios_tab_fan(parent, help_var)])

        # Target temp slider-like display
        temp_row = tk.Frame(parent, bg=_B['bg2'])
        temp_row.pack(fill='x', padx=4, pady=2)
        tk.Label(temp_row, text='  Target Temp', bg=_B['bg2'], fg=_B['fg'],
                 font=_B['font'], width=36, anchor='w').pack(side='left')
        temp_var = tk.IntVar(value=int(cur_target))
        scale = tk.Scale(temp_row, variable=temp_var, from_=30, to=90,
                         orient='horizontal', bg=_B['bg2'], fg=_B['cyan'],
                         highlightthickness=0, troughcolor=_B['bg'],
                         length=200, showvalue=True,
                         command=lambda v, tk_key=target_key: [
                             bs.update({tk_key: str(int(float(v)))}), save_state()])
        scale.pack(side='left')
        tk.Label(temp_row, text='°C', bg=_B['bg2'], fg=_B['dim'],
                 font=_B['font']).pack(side='left', padx=4)

        # Visual RPM bar
        live_rpm = random.randint(600, 1800)
        rpm_row = tk.Frame(parent, bg=_B['bg2'])
        rpm_row.pack(fill='x', padx=4, pady=2)
        tk.Label(rpm_row, text='  Current Speed', bg=_B['bg2'], fg=_B['fg'],
                 font=_B['font'], width=36, anchor='w').pack(side='left')
        rpm_cv = tk.Canvas(rpm_row, width=200, height=14, bg=_B['bg'],
                           highlightthickness=0)
        rpm_cv.pack(side='left')
        pct = live_rpm / 1800
        rpm_cv.create_rectangle(0, 2, int(200*pct), 12,
                                fill=_B['green'], outline='')
        tk.Label(rpm_row, text=f'{live_rpm} RPM', bg=_B['bg2'],
                 fg=_B['green'], font=_B['font_sm']).pack(side='left', padx=6)


# ── Tab: Power ───────────────────────────────────────────────────────────────
def _bios_tab_power(parent, help_var):
    bs = state.setdefault('bios_settings', {})

    def toggle_pwr(key, options):
        cur = bs.get(key, options[0])
        idx = options.index(cur) if cur in options else 0
        bs[key] = options[(idx + 1) % len(options)]
        save_state()
        _bios_clear(parent)
        _bios_tab_power(parent, help_var)

    _bios_section(parent, 'ACPI Power Management')
    power_rows = [
        ('Power On After AC Loss',   'power_on_ac',
         ['Last State', 'Always On', 'Always Off'],
         'What to do when AC power is restored after an outage.'),
        ('Wake On LAN',              'wake_on_lan',
         ['Enabled', 'Disabled'],
         'Allow a network Magic Packet to power on the system.'),
        ('RTC Wake (Scheduled Boot)','rtc_wake',
         ['Disabled', 'Enabled'],
         'Schedule a boot time via the RTC (Real-Time Clock).'),
        ('Sleep State',              'sleep_state',
         ['S3 (Suspend to RAM)', 'S1 (Power On Suspend)', 'S4 (Hibernate)'],
         'ACPI sleep state. S3 is standard "sleep", S4 is hibernate.'),
        ('ERP Ready (EU Eco)',        'erp_ready',
         ['Disabled', 'Enabled'],
         'Energy-Related Products directive. Limits standby power to <1 W.'),
        ('USB Charging in Standby',  'usb_standby',
         ['Enabled', 'Disabled'],
         'Allows USB ports to charge devices when PC is in S3 sleep.'),
        ('CPU EIST (SpeedStep)',      'speedstep',
         ['Enabled', 'Disabled'],
         'Intel SpeedStep: dynamically lowers CPU freq when idle.'),
        ('PCI-E ASPM',               'pcie_aspm',
         ['Auto', 'Disabled', 'L0s', 'L1', 'L0sL1'],
         'Active State Power Management for PCIe lanes.'),
    ]
    for label, key, opts, hint in power_rows:
        r = _bios_row(parent, label, bs.get(key, opts[0]))
        ch = getattr(r, '_bios_children', [])
        def _bind_pwr(row=r, children=ch, k=key, o=opts, h=hint):
            def do(e=None): toggle_pwr(k, o)
            def oe(e=None):
                row.config(bg='#0030aa')
                for c in children:
                    try: c.config(bg='#0030aa')
                    except: pass
                help_var.set(h)
            def ol(e=None):
                row.config(bg=_B['bg2'])
                for c in children:
                    try: c.config(bg=_B['bg2'])
                    except: pass
            for w in [row]+children:
                w.bind('<Button-1>',do); w.bind('<Enter>',oe)
                w.bind('<Leave>',ol); w.config(cursor='hand2')
        _bind_pwr()

    # RTC wake time editor (only shown if enabled)
    if bs.get('rtc_wake') == 'Enabled':
        _bios_section(parent, 'RTC Wake Schedule')
        rtc_frame = tk.Frame(parent, bg=_B['bg2'])
        rtc_frame.pack(fill='x', padx=4, pady=2)
        tk.Label(rtc_frame, text='  Wake Time (HH:MM)', bg=_B['bg2'],
                 fg=_B['fg'], font=_B['font'], width=36, anchor='w').pack(side='left')
        rtc_var = tk.StringVar(value=bs.get('rtc_time', '07:00'))
        rtc_e = tk.Entry(rtc_frame, textvariable=rtc_var, font=_B['font'],
                         bg=_B['bg'], fg=_B['cyan'], width=10,
                         insertbackground=_B['cyan'], relief='flat')
        rtc_e.pack(side='left')
        rtc_e.bind('<FocusOut>',
                   lambda e: [bs.update({'rtc_time': rtc_var.get()}), save_state()])


# ── Tab: Diagnostics ─────────────────────────────────────────────────────────
def _bios_tab_diag(parent, help_var, win):
    bs = state.setdefault('bios_settings', {})
    help_var.set('Run hardware diagnostics. Tests run in-BIOS with no OS required.')

    _bios_section(parent, 'Hardware Tests')
    diag_state = {'running': False, 'job': None}
    log_var = tk.StringVar(value='Select a test and click Run.')

    log_lbl = tk.Label(parent, textvariable=log_var, bg='#000020',
                       fg=_B['green'], font=('Consolas', 9),
                       anchor='nw', justify='left', wraplength=520,
                       height=8)
    log_lbl.pack(fill='x', padx=6, pady=4)

    def run_memory_test():
        lines = ['[ BIOS Memory Diagnostic ]',
                 'Testing DDR3 DIMM A1 (4096 MB)...']
        mb = int(state.get('ram_size','8').replace('GB','').strip() or 8) * 1024
        steps = list(range(0, mb+1, mb//16))
        results = ['Testing address range 0x{:08X} – 0x{:08X} ... PASS'.format(
            i * 65536, (i+1) * 65536) for i in range(16)]
        results += ['Testing DIMM A2 (4096 MB)...'] + results[:16]
        results += ['', '✓  All memory modules passed diagnostics.']
        all_lines = lines + results

        def show_step(idx=0):
            if idx >= len(all_lines):
                return
            if not win.winfo_exists():
                return
            try:
                log_var.set('\n'.join(all_lines[:idx+1]))
                win.after(60, lambda: show_step(idx+1))
            except Exception:
                pass
        show_step()

    def run_cpu_test():
        lines = ['[ CPU Stress Test — 5 seconds ]']
        for core in range(4):
            lines.append(f'  Core {core}:  Prime95 trial  .....')
        for i, line in enumerate(lines[1:]):
            lines[1+i] = line + '  PASS ✓'
        lines += ['', 'CPU Temperature during test: 61 °C',
                  '✓  No errors detected.']
        log_var.set('\n'.join(lines))

    def run_storage_test():
        lines = ['[ Storage Device SMART Check ]',
                 'WDC WD5000AAKX  ......  SMART Status: OK ✓',
                 'ST1000DM003      ......  SMART Status: OK ✓',
                 'SAMSUNG SSD 860  ......  SMART Status: OK ✓  (Health: 98%)',
                 '', '✓  All drives healthy.']
        log_var.set('\n'.join(lines))

    def run_gpu_test():
        lines = ['[ Video Memory Test ]',
                 'Intel HD Graphics 4000  [VRAM: 1024 MB]',
                 'Writing pattern 0xDEADBEEF to VRAM .....',
                 'Reading back pattern .....',
                 'Verifying  .....',
                 '', '✓  Video memory OK.']
        log_var.set('\n'.join(lines))

    def run_network_test():
        lines = ['[ Network Controller Test ]',
                 'Realtek RTL8111  [MAC: 00:1A:2B:3C:4D:5E]',
                 'Link speed: 1 Gbps',
                 'Sending loopback packet .....',
                 'Packet returned: 0 ms',
                 '', '✓  Network controller OK.']
        log_var.set('\n'.join(lines))

    def run_full_post():
        """Re-run abbreviated POST diagnostics."""
        lines = ['[ Full POST Sequence ]',
                 'CPU:      Intel Core i7-860  .....  OK ✓',
                 f'Memory:   {state.get("ram_size","8 GB")}  DDR3-1333  .....  OK ✓',
                 'SATA:     3 devices detected  .....  OK ✓',
                 'USB:      Keyboard, Mouse  .....  OK ✓',
                 'PCI-E:    Intel HD Graphics, Realtek LAN  .....  OK ✓',
                 'CMOS:     Battery OK  .....  OK ✓',
                 'RTC:      ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '  .....  OK ✓',
                 '', '✓  POST completed — no errors.']
        log_var.set('\n'.join(lines))

    btn_frame = tk.Frame(parent, bg=_B['bg'])
    btn_frame.pack(fill='x', padx=6, pady=4)
    tests = [
        ('Memory Test',    run_memory_test),
        ('CPU Test',       run_cpu_test),
        ('Storage SMART',  run_storage_test),
        ('GPU VRAM',       run_gpu_test),
        ('Network Test',   run_network_test),
        ('Full POST',      run_full_post),
    ]
    for label, fn in tests:
        tk.Label(btn_frame, text=f'[ {label} ]', bg=_B['bg2'], fg=_B['cyan'],
                 font=_B['font'], cursor='hand2', padx=6, pady=4).pack(
                 side='left', padx=3).bind('<Button-1>', lambda e, f=fn: f())

    _bios_section(parent, 'BIOS Maintenance')
    maint_frame = tk.Frame(parent, bg=_B['bg'])
    maint_frame.pack(fill='x', padx=6, pady=4)

    def load_defaults():
        if messagebox.askyesno('Load Defaults',
                               'Load optimal BIOS defaults?', parent=win):
            state.pop('bios_settings', None)
            audit_log('BIOS_LOAD_DEFAULTS', '', 'WARN')
            show_system_notification('BIOS', 'Optimal defaults loaded.')

    def clear_cmos():
        if messagebox.askyesno('Clear CMOS',
                               'Clear CMOS? This resets all BIOS settings to factory defaults.',
                               parent=win):
            state.pop('bios_settings', None)
            save_state()
            audit_log('BIOS_CLEAR_CMOS', '', 'WARN')
            log_var.set('CMOS cleared. All settings reset to factory defaults.\n'
                        'System will reboot...')
            win.after(2000, lambda: [win.destroy(), show_bios_setup(7)])

    for txt, cmd in [('Load Optimal Defaults [F9]', load_defaults),
                     ('Clear CMOS / Factory Reset', clear_cmos)]:
        tk.Label(maint_frame, text=f'[ {txt} ]', bg='#440000', fg=_B['red'],
                 font=_B['font'], cursor='hand2', padx=6, pady=4).pack(
                 side='left', padx=4).bind('<Button-1>', lambda e, f=cmd: f())


# ── Boot Selector (old "boot menu") — shown after POST or Save&Exit ───────────
def show_bios_boot_selector(reinstall=False):
    """Classic Windows Boot Manager — launches after POST."""
    # Corrupted OS and uninstalled OS both force the no-OS / USB boot screen
    os_wiped = (state.get('os_uninstalled', False)
                or state.get('os_corrupted', False))

    bios = tk.Toplevel()
    bios.title('Windows Boot Manager')
    bios.attributes('-fullscreen', True)
    bios.configure(bg='black')
    bios.attributes('-topmost', True)

    font_main = ('Consolas', 14)
    font_sm   = ('Consolas', 11)

    if os_wiped:
        # ── No OS screen ──────────────────────────────────────────────────────
        tk.Label(bios, text='', bg='black').pack(pady=60)
        is_corrupted = state.get('os_corrupted', False)
        tk.Label(bios,
                 text=('⚠  Windows 7 system files are CORRUPTED.'
                       if is_corrupted else
                       'No bootable operating system found.'),
                 bg='black', fg='#ff5555', font=('Consolas', 15, 'bold')).pack()
        tk.Label(bios, text='', bg='black').pack(pady=8)
        tk.Label(bios,
                 text=('Core system files were deleted. Windows cannot start.\n'
                       'Boot from USB to reinstall Windows 7.'
                       if is_corrupted else
                       'The hard drive does not contain a valid operating system.\n'
                       'Please insert a bootable USB drive or DVD and restart.'),
                 bg='black', fg='#aaaaaa', font=font_main, justify='center').pack()
        tk.Label(bios, text='', bg='black').pack(pady=20)
        tk.Label(bios,
                 text='Available boot devices:',
                 bg='black', fg='#888888', font=font_sm).pack()

        usb_frame = tk.Frame(bios, bg='black')
        usb_frame.pack(pady=20)
        usb_lbl = tk.Label(usb_frame,
                           text='  ★  USB Drive:  KINGSTON DataTraveler 32GB  [Windows 7 Setup]  ',
                           bg='white', fg='black', font=font_main,
                           cursor='hand2')
        usb_lbl.pack(pady=6)
        bios_lbl = tk.Label(usb_frame, text='     BIOS Setup Utility',
                            bg='black', fg='white', font=font_main, cursor='hand2')
        bios_lbl.pack(pady=6)

        sel = {'idx': 0}
        items = [usb_lbl, bios_lbl]

        def refresh_no_os():
            for i, lbl in enumerate(items):
                try:
                    lbl.config(bg='white' if i == sel['idx'] else 'black',
                               fg='black' if i == sel['idx'] else 'white')
                except Exception:
                    pass

        def on_select_no_os():
            if sel['idx'] == 0:
                bios.destroy()
                show_usb_boot_sequence()
            else:
                bios.destroy()
                show_bios_setup()

        def on_key_no_os(event):
            if event.keysym in ('Up', 'Down'):
                sel['idx'] = 1 - sel['idx']
                refresh_no_os()
            elif event.keysym == 'Return':
                on_select_no_os()
            elif event.keysym == 'Delete':
                bios.destroy()
                show_bios_setup()
        bios.bind('<Key>', on_key_no_os)
        bios.bind_all('<Key>', on_key_no_os)
        usb_lbl.bind('<Button-1>', lambda e: [bios.destroy(), show_usb_boot_sequence()])
        bios_lbl.bind('<Button-1>', lambda e: [bios.destroy(), show_bios_setup()])

        refresh_no_os()
        tk.Label(bios,
                 text='↑/↓: Navigate   Enter: Select   DEL: BIOS Setup',
                 bg='black', fg='#444444', font=font_sm).pack(side='bottom', pady=10)
        bios.focus_force()
        try:
            bios.grab_set()
        except Exception:
            pass
        return

    # ── Normal boot selector ──────────────────────────────────────────────────
    tk.Label(bios, bg='black', fg='white',
             text='Windows Boot Manager',
             font=('Consolas', 16, 'bold')).pack(pady=(50, 20))
    tk.Label(bios, bg='black', fg='white',
             text='Choose an operating system to start,\n'
                  'or press TAB to select a tool:',
             font=font_main).pack(anchor='w', padx=100)

    os_types = [
        'Windows 7',
        '──────────────────────────────────────────',
        '  Ubuntu 26.04 LTS',
        '  Lubuntu 26.04',
        '  macOS Sequoia',
        '  ChromeOS Flex',
        '──────────────────────────────────────────',
        '  💽  Boot from USB Drive',
        '  ⚙  BIOS Setup Utility (DEL)',
        '  🔍  Memory Diagnostics (F3)',
    ]
    SEPARATORS = {1, 6}
    selection = {'idx': 0}
    labels = []

    timer_lbl = tk.Label(bios, bg='black', fg='#888888', font=font_sm)
    timer_lbl.pack(pady=4)
    error_lbl = tk.Label(bios, bg='black', fg='#ff5555', font=font_main)
    error_lbl.pack(pady=6)
    tk.Label(bios, bg='black', fg='#888888', font=font_sm,
             text='↑/↓: Navigate   Enter: Select   Esc: Cancel   DEL: BIOS Setup').pack(
             side='bottom', pady=10)

    countdown = {'v': 5, 'job': None}

    def refresh():
        for i, lbl in enumerate(labels):
            if i in SEPARATORS:
                continue
            try:
                bg = 'white' if i == selection['idx'] else 'black'
                fg = 'black' if i == selection['idx'] else 'white'
                lbl.config(bg=bg, fg=fg)
            except Exception:
                pass  # label destroyed, skip

    def tick_countdown():
        if countdown['v'] > 0:
            label = os_types[selection['idx']].strip()
            timer_lbl.config(
                text=f'Booting "{label}" in {countdown["v"]}s  —  Press any key to cancel.')
            countdown['v'] -= 1
            countdown['job'] = bios.after(1000, tick_countdown)
        else:
            on_select()

    def stop_countdown(event=None):
        if countdown['job']:
            try:
                bios.after_cancel(countdown['job'])
            except Exception:
                pass
            countdown['job'] = None
            timer_lbl.config(text='')

    v_frame = tk.Frame(bios, bg='black')
    v_frame.pack(pady=30, anchor='w', padx=120)
    for i, v in enumerate(os_types):
        is_sep = i in SEPARATORS
        lbl = tk.Label(v_frame, text=v, font=font_main,
                       bg='black',
                       fg='#333333' if is_sep else 'white',
                       width=50, anchor='w', padx=10)
        lbl.pack(pady=3 if not is_sep else 1)
        labels.append(lbl)
        if not is_sep:
            idx_cap = i
            lbl.bind('<Button-1>', lambda e, ii=idx_cap: [
                stop_countdown(),
                selection.update({'idx': ii}),
                refresh(),
                on_select()])

    def on_select():
        stop_countdown()
        idx = selection['idx']
        if idx in SEPARATORS:
            return
        if idx == 0:           # Windows 7
            if reinstall:
                show_windows_edition_selector(bios)
            else:
                bios.destroy()
                show_login()
        elif idx in (2, 3, 4, 5):   # Other OS shells
            show_other_os_shell(bios, os_types[idx].strip())
        elif idx == 7:         # USB Boot
            bios.destroy()
            show_usb_boot_sequence()
        elif idx == 8:         # BIOS Setup
            bios.destroy()
            show_bios_setup()
        elif idx == 9:         # Memory Diag
            _bios_run_memory_diag(bios)

    def on_key(event):
        stop_countdown(event)
        if event.keysym == 'Up':
            new = (selection['idx'] - 1) % len(os_types)
            while new in SEPARATORS:
                new = (new - 1) % len(os_types)
            selection['idx'] = new
            error_lbl.config(text='')
        elif event.keysym == 'Down':
            new = (selection['idx'] + 1) % len(os_types)
            while new in SEPARATORS:
                new = (new + 1) % len(os_types)
            selection['idx'] = new
            error_lbl.config(text='')
        elif event.keysym == 'Return':
            on_select()
        elif event.keysym == 'Escape':
            bios.destroy()
            show_login()
        elif event.keysym == 'Delete':
            stop_countdown()
            bios.destroy()
            show_bios_setup()
        elif event.keysym == 'F3':
            stop_countdown()
            _bios_run_memory_diag(bios)
        refresh()

    bios.bind('<Key>', on_key)
    bios.bind_all('<Key>', on_key)   # catch keys even if child widget has focus
    refresh()
    tick_countdown()
    bios.focus_force()
    try:
        bios.grab_set()
    except Exception:
        pass


def _bios_run_memory_diag(bios):
    """Mini memory diagnostic from boot menu."""
    _bios_clear(bios)
    tk.Label(bios, text='Windows Memory Diagnostic', bg='black', fg='white',
             font=('Consolas', 16, 'bold')).pack(pady=40)
    tk.Label(bios, text='Testing your computer\'s memory for errors...',
             bg='black', fg='white', font=('Consolas', 13)).pack()
    cv = tk.Canvas(bios, width=500, height=28, bg='#333', highlightthickness=0)
    cv.pack(pady=20)
    bar = cv.create_rectangle(0, 0, 0, 28, fill='#4a90e2', outline='')
    pct_lbl = tk.Label(bios, text='Pass 1 of 2: 0%', bg='black', fg='white',
                       font=('Consolas', 12))
    pct_lbl.pack()
    status_lbl = tk.Label(bios, text='', bg='black', fg='#55ff55',
                          font=('Consolas', 11))
    status_lbl.pack(pady=6)

    def animate(step=0):
        if not bios.winfo_exists():
            return
        try:
            if step <= 200:
                pct = step % 100
                pass_n = step // 100 + 1
                cv.coords(bar, 0, 0, pct * 5, 28)
                pct_lbl.config(text=f'Pass {pass_n} of 2: {pct}%')
                if step == 100:
                    status_lbl.config(text='Pass 1 complete — No errors found.')
                bios.after(25, lambda: animate(step + 1))
            else:
                pct_lbl.config(text='Complete')
                status_lbl.config(text='✓  No memory errors detected. Restarting...')
                bios.after(2200, lambda: [_bios_clear(bios) if bios.winfo_exists() else None,
                                          show_bios_boot_selector()])
        except Exception:
            pass

    animate()


# ── Keep backward-compat alias  ───────────────────────────────────────────────
def show_bios_boot_menu(reinstall=True):
    """Entry point — shows POST then boots. Called from login F8, BSOD, terminal."""
    show_post_screen(on_done=lambda: show_bios_boot_selector(reinstall=reinstall))


def show_os_version_selector_bios():
    selector = tk.Toplevel()
    selector.title('OS Version Selector')
    selector.attributes('-fullscreen', True)
    selector.configure(bg='black')
    show_windows_edition_selector(selector)


def show_other_os_shell(bios, name):
    _bios_clear(bios)
    tk.Label(bios, text=f'{name}  —  Shell Environment',
             bg='black', fg='#00ff00', font=('Consolas', 14)).pack(pady=20)
    tk.Label(bios, text='[ Non-Core OS Shim — limited commands ]',
             bg='black', fg='#555555', font=('Consolas', 10)).pack()
    out = tk.Text(bios, bg='black', fg='#00ff00', font=('Consolas', 12),
                  bd=0, highlightthickness=0)
    out.pack(fill='both', expand=True, padx=40, pady=8)
    boot_msg = {
        'Ubuntu 26.04 LTS':  'Ubuntu 26.04 LTS  kernel 6.8.0-generic\nlogin: root\nPassword: ',
        'Lubuntu 26.04':     'Lubuntu 26.04  (minimal)\nlubuntu login: ',
        'macOS Sequoia':     'Darwin Kernel Version 24.0.0\nmacOS-sequoia:~ root# ',
        'ChromeOS Flex':     'Chrome OS Flex  (Flexypants Build 15)\nchronos@localhost / $ ',
    }
    out.insert('end', boot_msg.get(name,
        f'Booting {name}...\nType "exit" to return to Boot Manager.\n\n$ '))
    e = tk.Entry(bios, bg='black', fg='white', font=('Consolas', 12),
                 insertbackground='white', bd=0, highlightthickness=0)
    e.pack(fill='x', padx=40, pady=16)
    e.focus_set()

    history = []
    hist_idx = {'v': 0}

    builtin = {
        'ls': 'Desktop  Documents  Downloads  Music  Pictures  Videos',
        'pwd': '/home/user',
        'whoami': 'user',
        'uname -a': f'{name} kernel 6.8.0  x86_64',
        'uptime': '  0:04  up 0 min,  1 user,  load average: 0.00, 0.00, 0.00',
        'ps': '  PID  CMD\n    1  init\n    2  bash\n    3  python3',
        'cat /etc/os-release': f'NAME="{name}"\nVERSION="26.04 LTS"',
        'ip addr': '2: eth0  inet 192.168.1.99/24',
        'free -h': '         total  used  free\nMem:      8.0G  1.2G  6.8G',
        'df -h': '/dev/sda1   500G  12G  488G  3% /',
    }

    def on_cmd(ev):
        cmd = e.get().strip()
        e.delete(0, 'end')
        if not cmd:
            out.insert('end', '\n$ ')
            return
        history.append(cmd)
        hist_idx['v'] = len(history)
        out.insert('end', cmd + '\n')
        if cmd.lower() in ('exit', 'quit'):
            _bios_clear(bios)
            show_bios_boot_selector()
            return
        response = builtin.get(cmd, f'{cmd}: command not found')
        out.insert('end', response + '\n$ ')
        out.see('end')

    def on_hist(ev):
        if not history:
            return
        if ev.keysym == 'Up':
            hist_idx['v'] = max(0, hist_idx['v'] - 1)
        else:
            hist_idx['v'] = min(len(history), hist_idx['v'] + 1)
        e.delete(0, 'end')
        if hist_idx['v'] < len(history):
            e.insert(0, history[hist_idx['v']])

    e.bind('<Return>', on_cmd)
    e.bind('<Up>', on_hist)
    e.bind('<Down>', on_hist)


def show_windows_edition_selector(parent_bios):
    _bios_clear(parent_bios)
    tk.Label(parent_bios, text='Windows 7 Setup — Select Edition',
             bg='black', fg='white',
             font=('Consolas', 16, 'bold')).pack(pady=(50, 20))
    editions = ['Starter', 'Home Basic', 'Home Premium', 'Professional', 'Ultimate']
    selection = {'idx': 4}
    labels = []

    def refresh():
        for idx, lbl in enumerate(labels):
            try:
                lbl.config(bg='white' if idx == selection['idx'] else 'black',
                           fg='black' if idx == selection['idx'] else 'white')
            except Exception:
                pass

    def on_key(event):
        if event.keysym == 'Up':
            selection['idx'] = (selection['idx'] - 1) % len(editions)
        elif event.keysym == 'Down':
            selection['idx'] = (selection['idx'] + 1) % len(editions)
        elif event.keysym == 'Return':
            state['os_version'] = editions[selection['idx']]
            show_setup_ram_age(parent_bios)
        refresh()

    for v in editions:
        l = tk.Label(parent_bios, text=v, bg='black', fg='white',
                     font=('Consolas', 14), width=30, anchor='w', padx=10)
        l.pack(pady=4)
        labels.append(l)
    parent_bios.bind('<Up>', on_key)
    parent_bios.bind('<Down>', on_key)
    parent_bios.bind('<Return>', on_key)
    refresh()


def show_setup_ram_age(bios):
    _bios_clear(bios)
    tk.Label(bios, text='Windows 7 Setup — System Configuration',
             bg='black', fg='white', font=('Consolas', 16)).pack(pady=50)
    form = tk.Frame(bios, bg='black')
    form.pack(pady=20)
    fields = [
        ('RAM size (e.g. 8 GB):',   'ram_size',  '8 GB'),
        ('Your name:',              'first_name', state.get('first_name', 'Ryan')),
        ('Computer name:',          'pc_name',   'RYAN-PC'),
        ('Time zone:',              'timezone',  'UTC+5:30 India'),
    ]
    entries = {}
    for i, (label, key, default) in enumerate(fields):
        tk.Label(form, text=label, bg='black', fg='white',
                 font=('Consolas', 12)).grid(row=i, column=0, pady=8, sticky='w')
        e = tk.Entry(form, font=('Consolas', 12), bg='#111', fg='white',
                     insertbackground='white')
        e.insert(0, state.get(key, default))
        e.grid(row=i, column=1, padx=14)
        entries[key] = e

    def proceed(event=None):
        for key, entry in entries.items():
            state[key] = entry.get()
        save_state()
        show_setup_loading(bios)

    bios.bind('<Return>', proceed)
    list(entries.values())[0].focus_set()
    tk.Button(bios, text='Continue →', bg='#4a90e2', fg='white',
              font=('Consolas', 13), command=proceed).pack(pady=16)


def show_setup_loading(bios):
    _bios_clear(bios)
    tk.Label(bios, text='Windows 7 is preparing your installation...',
             bg='black', fg='white', font=('Consolas', 15)).pack(pady=60)

    phases = [
        ('Copying installation files',      30),
        ('Expanding Windows files',          50),
        ('Installing features',              70),
        ('Installing updates',              90),
        ('Completing installation',        100),
    ]
    phase_lbl = tk.Label(bios, text='', bg='black', fg='#aaaaaa',
                         font=('Consolas', 11))
    phase_lbl.pack(pady=4)

    cv = tk.Canvas(bios, width=500, height=28, bg='#333', highlightthickness=0)
    cv.pack(pady=12)
    bar = cv.create_rectangle(0, 0, 0, 28, fill='#4a90e2', outline='')
    pct_lbl = tk.Label(bios, text='0%', bg='black', fg='white',
                       font=('Consolas', 12))
    pct_lbl.pack()
    time_lbl = tk.Label(bios, text='Time remaining: calculating...',
                        bg='black', fg='#555555', font=('Consolas', 10))
    time_lbl.pack(pady=4)

    start_ts = time.time()

    def animate(step=0):
        if not bios.winfo_exists():
            return
        if step <= 100:
            cv.coords(bar, 0, 0, step * 5, 28)
            pct_lbl.config(text=f'{step}%')
            for phase_text, phase_pct in phases:
                if step <= phase_pct:
                    phase_lbl.config(text=phase_text)
                    break
            elapsed = time.time() - start_ts
            if step > 5:
                remaining = int((elapsed / step) * (100 - step))
                time_lbl.config(text=f'Time remaining: ~{remaining} seconds')
            bios.after(55, lambda: animate(step + 1))
        else:
            time_lbl.config(text='')
            phase_lbl.config(text='')
            show_setup_drivers(bios)

    animate()


def show_setup_drivers(bios):
    _bios_clear(bios)
    tk.Label(bios, text='Driver Installation', bg='black', fg='white',
             font=('Consolas', 16, 'bold')).pack(pady=40)
    tk.Label(bios, text='Windows 7 needs drivers to enable all hardware features.',
             bg='black', fg='#aaaaaa', font=('Consolas', 11)).pack(pady=4)

    driver_list = [
        'Intel Chipset Device Software',
        'Intel HD Graphics 4000 Driver',
        'Realtek RTL8111 LAN Driver',
        'Realtek ALC887 HD Audio Driver',
        'USB 3.0 Host Controller Driver',
        'ASUS ACPI Driver',
    ]
    for drv in driver_list:
        tk.Label(bios, text=f'  ·  {drv}', bg='black', fg='#8888ff',
                 font=('Consolas', 11)).pack(anchor='w', padx=80)

    sel = {'idx': 0}
    btns = []
    b_frame = tk.Frame(bios, bg='black')
    b_frame.pack(pady=30)
    b1 = tk.Label(b_frame, text='[ INSTALL DRIVERS ]', font=('Consolas', 14),
                  bg='white', fg='black', padx=20, pady=10)
    b1.pack(pady=8)
    btns.append(b1)
    b2 = tk.Label(b_frame, text='[ SKIP (install later) ]', font=('Consolas', 14),
                  bg='black', fg='white', padx=20, pady=10)
    b2.pack(pady=8)
    btns.append(b2)

    def refresh():
        for i, b in enumerate(btns):
            try:
                b.config(bg='white' if i == sel['idx'] else 'black',
                         fg='black' if i == sel['idx'] else 'white')
            except Exception:
                pass

    def on_key(event):
        if event.keysym in ('Up', 'Down'):
            sel['idx'] = 1 - sel['idx']
            refresh()
        elif event.keysym == 'Return':
            if sel['idx'] == 0:
                _bios_clear(bios)
                tk.Label(bios, text='Installing drivers...', bg='black', fg='white',
                         font=('Consolas', 14)).pack(pady=80)
                cv2 = tk.Canvas(bios, width=400, height=22,
                                bg='#333', highlightthickness=0)
                cv2.pack()
                b2_ = cv2.create_rectangle(0, 0, 0, 22, fill='#55aa55', outline='')
                pl = tk.Label(bios, text='0%', bg='black', fg='white',
                              font=('Consolas', 11))
                pl.pack()

                def drv_anim(s=0):
                    if not bios.winfo_exists():
                        return
                    if s <= 100:
                        cv2.coords(b2_, 0, 0, s * 4, 22)
                        pl.config(text=f'Installing... {s}%')
                        bios.after(35, lambda: drv_anim(s + 1))
                    else:
                        state['drivers_installed'] = True
                        state['show_driver_prompt'] = False
                        save_state()
                        audit_log('BIOS_DRIVERS_INSTALLED', '', 'INFO')
                        bios.destroy()
                        show_login()

                drv_anim()
            else:
                state['drivers_installed'] = False
                state['show_driver_prompt'] = False
                save_state()
                bios.destroy()
                show_login()

    bios.bind('<Up>', on_key)
    bios.bind('<Down>', on_key)
    bios.bind('<Return>', on_key)
    refresh()


def show_volume_overlay():
    if not desktop_win or not desktop_win.winfo_exists():
        return
    volume_win = tk.Toplevel(desktop_win)
    volume_win.overrideredirect(True)
    volume_win.attributes('-topmost', True)
    style_aero_window(volume_win, '#e9f3ff')
    screen_w = desktop_win.winfo_screenwidth()
    screen_h = desktop_win.winfo_screenheight()
    width, height = 260, 260
    volume_win.geometry(f'{width}x{height}+{screen_w-width-24}+{screen_h-height-140}')

    canvas = tk.Canvas(volume_win, width=220, height=220, bg='#e9f3ff', highlightthickness=0)
    canvas.pack(padx=10, pady=10)

    def draw_volume():
        canvas.delete('all')
        canvas.create_oval(10, 10, 210, 210, fill='#8bb5ff', outline='#5f86d4', width=4)
        canvas.create_oval(30, 30, 190, 190, fill='#eff6ff', outline='')
        canvas.create_text(110, 110, text=f'{state.get("volume", 50)}%', fill='#16355a', font=('Segoe UI', 20, 'bold'))
        canvas.create_text(110, 140, text='Volume', fill='#2d4d82', font=('Segoe UI', 10))

    def adjust(delta):
        state['volume'] = max(0, min(100, state.get('volume', 50) + delta))
        save_state()
        draw_volume()
        show_system_notification('Volume', f'Volume now {state["volume"]}%')

    draw_volume()
    controls = tk.Frame(volume_win, bg='#e9f3ff')
    controls.pack(fill='x', padx=14)
    tk.Button(controls, text='-', width=4, bg='#b4c8ff', fg='#1e3d6e', command=lambda: adjust(-10)).pack(side='left', padx=(0,6), pady=4)
    tk.Button(controls, text='+', width=4, bg='#b4c8ff', fg='#1e3d6e', command=lambda: adjust(10)).pack(side='left', padx=(0,6), pady=4)
    tk.Button(controls, text='Close', width=8, bg='#6b92db', fg='white', command=volume_win.destroy).pack(side='right')


def change_volume(delta):
    state['volume'] = max(0, min(100, state.get('volume', 50) + delta))
    save_state()
    show_volume_overlay()


def register_app(name, cmd, subtitle=''):
    # add to APP_MAP and persistent state
    key = name.lower()
    def _launcher():
        try:
            if isinstance(cmd, str) and cmd.startswith(('http://', 'https://')):
                webbrowser.open(cmd)
            else:
                # try to run as executable or open path
                try:
                    subprocess.Popen([cmd])
                except Exception:
                    os.startfile(cmd)
        except Exception:
            messagebox.showerror('Launch', f'Could not launch {name}')
    APP_MAP[key] = _launcher
    apps = state.get('apps', [])
    apps.append({'name': name, 'cmd': cmd, 'subtitle': subtitle})
    state['apps'] = apps
    save_state()


# ── helpers ──────────────────────────────────────────────────────────────────

def col_letter(n):          # 0-based → 'A', 'B', …, 'Z', 'AA', …
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def parse_cell_ref(ref):    # 'B3' → (row=2, col=1)  0-based
    m = re.fullmatch(r'([A-Z]+)(\d+)', ref.strip().upper())
    if not m:
        return None
    col_str, row_str = m.groups()
    col = sum((ord(c) - 64) * (26 ** i)
              for i, c in enumerate(reversed(col_str))) - 1
    return int(row_str) - 1, col

def col_num(col_str):       # 'A' → 0, 'B' → 1, 'AA' → 26
    return sum((ord(c) - 64) * (26 ** i)
               for i, c in enumerate(reversed(col_str.upper()))) - 1

def parse_range(rng):       # 'A1:C3' → list of (r,c)
    parts = rng.upper().split(':')
    if len(parts) != 2:
        return None
    r1c1 = parse_cell_ref(parts[0])
    r2c2 = parse_cell_ref(parts[1])
    if not r1c1 or not r2c2:
        return None
    cells = []
    for r in range(r1c1[0], r2c2[0] + 1):
        for c in range(r1c1[1], r2c2[1] + 1):
            cells.append((r, c))
    return cells


# ── main widget ──────────────────────────────────────────────────────────────

def show_excel_app(parent=None):
    ROWS, COLS = 50, 26
    ROW_H, COL_W = 22, 80
    HDR_W, HDR_H = 40, 22

    # data[r][c] = raw string typed by user
    data = [['' for _ in range(COLS)] for _ in range(ROWS)]
    sel  = {'r': 0, 'c': 0}            # active cell
    sel_range = {'r1': None, 'c1': None, 'r2': None, 'c2': None}
    clipboard = []                      # list of rows (list of strings)
    undo_stack = []
    redo_stack = []
    drag_start = [None, None]

    # ── window ────────────────────────────────────────────────────────────────
    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title('Excel – Spreadsheet')
    win.geometry('1050x620')
    win.configure(bg='#f3f2f1')

    # ── title bar ─────────────────────────────────────────────────────────────
    title_bar = tk.Frame(win, bg='#217346', height=36)
    title_bar.pack(fill='x')
    title_bar.pack_propagate(False)
    tk.Label(title_bar, text='📊  Spreadsheet',
             bg='#217346', fg='white',
             font=('Segoe UI', 11, 'bold')).pack(side='left', padx=12, pady=6)

    # ── ribbon ────────────────────────────────────────────────────────────────
    ribbon = tk.Frame(win, bg='#f3f2f1', bd=0, relief='flat')
    ribbon.pack(fill='x', padx=4, pady=2)

    def ribbon_btn(parent, text, cmd, color='#ffffff'):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=color, fg='#212121', relief='flat',
                      font=('Segoe UI', 9), padx=6, pady=3,
                      activebackground='#d0e7d2', cursor='hand2',
                      bd=1, highlightthickness=0)
        b.pack(side='left', padx=2)
        return b

    def save_csv():
        path = filedialog.asksaveasfilename(defaultextension='.csv',
               filetypes=[('CSV', '*.csv'), ('All', '*.*')])
        if not path:
            return
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            for row in data:
                w.writerow(row)
        messagebox.showinfo('Saved', f'Saved to {path}')

    def open_csv():
        path = filedialog.askopenfilename(filetypes=[('CSV', '*.csv'), ('All', '*.*')])
        if not path:
            return
        with open(path, newline='') as f:
            rows = list(csv.reader(f))
        for r, row in enumerate(rows[:ROWS]):
            for c, val in enumerate(row[:COLS]):
                data[r][c] = val
        refresh_all()

    ribbon_btn(ribbon, '💾 Save CSV', save_csv, '#e8f5e9')
    ribbon_btn(ribbon, '📂 Open CSV', open_csv, '#e3f2fd')

    sep1 = tk.Frame(ribbon, bg='#cccccc', width=1); sep1.pack(side='left', fill='y', padx=4, pady=3)

    # font controls
    font_var = tk.StringVar(value='Calibri')
    size_var = tk.StringVar(value='11')
    bold_var = tk.BooleanVar(value=False)
    italic_var = tk.BooleanVar(value=False)

    font_cb = ttk.Combobox(ribbon, textvariable=font_var, width=13,
                           values=['Calibri', 'Arial', 'Segoe UI', 'Courier New', 'Times New Roman'])
    font_cb.pack(side='left', padx=2)
    size_cb = ttk.Combobox(ribbon, textvariable=size_var, width=4,
                           values=['8','9','10','11','12','14','16','18','20','24','28','32','36'])
    size_cb.pack(side='left', padx=2)

    def apply_font(*_):
        refresh_cell(sel['r'], sel['c'])

    font_cb.bind('<<ComboboxSelected>>', apply_font)
    size_cb.bind('<<ComboboxSelected>>', apply_font)

    bold_btn   = tk.Button(ribbon, text='B', font=('Arial', 10, 'bold'),
                           relief='flat', padx=6, pady=3, bg='#ffffff',
                           command=lambda: (bold_var.set(not bold_var.get()), apply_font()))
    bold_btn.pack(side='left', padx=1)
    italic_btn = tk.Button(ribbon, text='I', font=('Arial', 10, 'italic'),
                           relief='flat', padx=6, pady=3, bg='#ffffff',
                           command=lambda: (italic_var.set(not italic_var.get()), apply_font()))
    italic_btn.pack(side='left', padx=1)

    sep2 = tk.Frame(ribbon, bg='#cccccc', width=1); sep2.pack(side='left', fill='y', padx=4, pady=3)

    align_var = tk.StringVar(value='left')
    for sym, val in [('⬅', 'left'), ('⬛', 'center'), ('➡', 'right')]:
        tk.Button(ribbon, text=sym, relief='flat', padx=6, pady=3, bg='#ffffff',
                  command=lambda v=val: (align_var.set(v), apply_font())).pack(side='left', padx=1)

    sep3 = tk.Frame(ribbon, bg='#cccccc', width=1); sep3.pack(side='left', fill='y', padx=4, pady=3)

    def do_sum():
        r1, c1 = sel_range['r1'], sel_range['c1']
        r2, c2 = sel_range['r2'], sel_range['c2']
        if r1 is None:
            return
        ref1 = f'{col_letter(c1)}{r1+1}'
        ref2 = f'{col_letter(c2)}{r2+1}'
        target_r = r2 + 1
        if target_r < ROWS:
            push_undo()
            data[target_r][c1] = f'=SUM({ref1}:{ref2})'
            refresh_all()

    def do_avg():
        r1, c1 = sel_range['r1'], sel_range['c1']
        r2, c2 = sel_range['r2'], sel_range['c2']
        if r1 is None:
            return
        ref1 = f'{col_letter(c1)}{r1+1}'
        ref2 = f'{col_letter(c2)}{r2+1}'
        target_r = r2 + 1
        if target_r < ROWS:
            push_undo()
            data[target_r][c1] = f'=AVERAGE({ref1}:{ref2})'
            refresh_all()

    ribbon_btn(ribbon, 'Σ SUM', do_sum)
    ribbon_btn(ribbon, 'Ø AVG', do_avg)

    sep4 = tk.Frame(ribbon, bg='#cccccc', width=1); sep4.pack(side='left', fill='y', padx=4, pady=3)
    ribbon_btn(ribbon, '↩ Undo', lambda: undo(), '#fff9c4')
    ribbon_btn(ribbon, '↪ Redo', lambda: redo(), '#fff9c4')

    # ── formula bar ───────────────────────────────────────────────────────────
    fbar = tk.Frame(win, bg='#f3f2f1')
    fbar.pack(fill='x', padx=4, pady=1)
    cell_name = tk.Label(fbar, text='A1', bg='white', width=6,
                         font=('Segoe UI', 9), relief='solid', bd=1)
    cell_name.pack(side='left', padx=(2, 4))
    tk.Label(fbar, text='fx', bg='#f3f2f1',
             font=('Segoe UI', 9, 'italic'), fg='#555').pack(side='left')
    formula_var = tk.StringVar()
    formula_entry = tk.Entry(fbar, textvariable=formula_var,
                             font=('Segoe UI', 9), relief='solid', bd=1)
    formula_entry.pack(side='left', fill='x', expand=True, padx=4)

    def formula_confirm(event=None):
        push_undo()
        data[sel['r']][sel['c']] = formula_var.get()
        refresh_all()
        grid_canvas.focus_set()

    formula_entry.bind('<Return>', formula_confirm)
    formula_entry.bind('<Tab>',    formula_confirm)

    # ── spreadsheet area ──────────────────────────────────────────────────────
    sheet_frame = tk.Frame(win, bg='#e0e0e0')
    sheet_frame.pack(fill='both', expand=True, padx=4, pady=(0, 4))

    # scrollbars
    vsb = tk.Scrollbar(sheet_frame, orient='vertical')
    hsb = tk.Scrollbar(sheet_frame, orient='horizontal')
    vsb.grid(row=1, column=2, sticky='ns')
    hsb.grid(row=2, column=1, sticky='ew')

    grid_canvas = tk.Canvas(sheet_frame, bg='white',
                            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                            highlightthickness=0)
    grid_canvas.grid(row=1, column=1, sticky='nsew')
    sheet_frame.rowconfigure(1, weight=1)
    sheet_frame.columnconfigure(1, weight=1)

    # corner
    corner = tk.Canvas(sheet_frame, width=HDR_W, height=HDR_H,
                       bg='#e8e8e8', highlightthickness=0)
    corner.grid(row=0, column=0)

    col_hdr = tk.Canvas(sheet_frame, height=HDR_H, bg='#e8e8e8',
                        xscrollcommand=hsb.set, highlightthickness=0)
    col_hdr.grid(row=0, column=1, sticky='ew')

    row_hdr = tk.Canvas(sheet_frame, width=HDR_W, bg='#e8e8e8',
                        yscrollcommand=vsb.set, highlightthickness=0)
    row_hdr.grid(row=1, column=0, sticky='ns')

    vsb.config(command=lambda *a: (grid_canvas.yview(*a), row_hdr.yview(*a)))
    hsb.config(command=lambda *a: (grid_canvas.xview(*a), col_hdr.xview(*a)))

    total_w = COLS * COL_W
    total_h = ROWS * ROW_H
    grid_canvas.config(scrollregion=(0, 0, total_w, total_h))
    col_hdr.config(scrollregion=(0, 0, total_w, HDR_H))
    row_hdr.config(scrollregion=(0, 0, HDR_W, total_h))

    # ── drawing helpers ───────────────────────────────────────────────────────

    GRID_LINE = '#d0d0d0'
    SEL_BG    = '#cce5ff'
    HDR_SEL   = '#b8d4f0'
    HDR_NORM  = '#f3f2f1'
    TEXT_COL  = '#212121'

    def cell_bbox(r, c):
        x0 = c * COL_W;  y0 = r * ROW_H
        return x0, y0, x0 + COL_W, y0 + ROW_H

    def is_in_sel(r, c):
        r1 = sel_range['r1']; r2 = sel_range['r2']
        c1 = sel_range['c1']; c2 = sel_range['c2']
        if r1 is None:
            return r == sel['r'] and c == sel['c']
        return min(r1,r2) <= r <= max(r1,r2) and min(c1,c2) <= c <= max(c1,c2)

    # ── formula evaluation ────────────────────────────────────────────────────

    def get_num(r, c):
        try:
            return float(evaluate(r, c))
        except:
            return 0.0

    def evaluate(r, c, _depth=0):
        if _depth > 30:
            return '#CIRC'
        raw = data[r][c]
        if not raw.startswith('='):
            try:    return float(raw)
            except: return raw
        expr = raw[1:].strip().upper()
        # SUM
        m = re.fullmatch(r'SUM\(([A-Z]+\d+:[A-Z]+\d+)\)', expr)
        if m:
            cells = parse_range(m.group(1))
            return sum(get_num(*rc) for rc in (cells or []))
        # AVERAGE
        m = re.fullmatch(r'AVERAGE\(([A-Z]+\d+:[A-Z]+\d+)\)', expr)
        if m:
            cells = parse_range(m.group(1)) or []
            return (sum(get_num(*rc) for rc in cells) / len(cells)) if cells else '#DIV/0'
        # MIN / MAX
        m = re.fullmatch(r'(MIN|MAX)\(([A-Z]+\d+:[A-Z]+\d+)\)', expr)
        if m:
            fn, rng = m.groups()
            cells = parse_range(rng) or []
            nums  = [get_num(*rc) for rc in cells]
            return (min(nums) if fn == 'MIN' else max(nums)) if nums else 0
        # COUNT
        m = re.fullmatch(r'COUNT\(([A-Z]+\d+:[A-Z]+\d+)\)', expr)
        if m:
            cells = parse_range(m.group(1)) or []
            return sum(1 for rc in cells if data[rc[0]][rc[1]] != '')
        # simple arithmetic with cell refs  e.g. =A1+B2*3
        def repl(ref_m):
            rc = parse_cell_ref(ref_m.group(0))
            if rc:
                try:    return str(float(evaluate(rc[0], rc[1], _depth+1)))
                except: return '0'
            return '0'
        substituted = re.sub(r'[A-Z]+\d+', repl, expr)
        try:
            result = eval(substituted, {'__builtins__': {}})
            return result
        except:
            return '#ERR'

    def display_value(r, c):
        raw = data[r][c]
        if not raw:
            return ''
        if raw.startswith('='):
            val = evaluate(r, c)
            if isinstance(val, float):
                return f'{val:g}'
            return str(val)
        try:
            f = float(raw)
            return f'{f:g}'
        except:
            return raw

    # ── full redraw ───────────────────────────────────────────────────────────

    def refresh_all():
        draw_col_hdr()
        draw_row_hdr()
        draw_grid()
        update_formula_bar()

    def draw_col_hdr():
        col_hdr.delete('all')
        for c in range(COLS):
            x0 = c * COL_W
            active = (sel_range['r1'] is not None and
                      min(sel_range['c1'], sel_range['c2']) <= c <= max(sel_range['c1'], sel_range['c2'])) \
                     or c == sel['c']
            bg = HDR_SEL if active else HDR_NORM
            col_hdr.create_rectangle(x0, 0, x0+COL_W, HDR_H,
                                     fill=bg, outline=GRID_LINE)
            col_hdr.create_text(x0 + COL_W//2, HDR_H//2,
                                text=col_letter(c),
                                font=('Segoe UI', 9, 'bold'), fill=TEXT_COL)

    def draw_row_hdr():
        row_hdr.delete('all')
        for r in range(ROWS):
            y0 = r * ROW_H
            active = (sel_range['r1'] is not None and
                      min(sel_range['r1'], sel_range['r2']) <= r <= max(sel_range['r1'], sel_range['r2'])) \
                     or r == sel['r']
            bg = HDR_SEL if active else HDR_NORM
            row_hdr.create_rectangle(0, y0, HDR_W, y0+ROW_H,
                                     fill=bg, outline=GRID_LINE)
            row_hdr.create_text(HDR_W//2, y0+ROW_H//2,
                                text=str(r+1),
                                font=('Segoe UI', 8), fill=TEXT_COL)

    def draw_grid():
        grid_canvas.delete('all')
        r1s = sel_range['r1']; r2s = sel_range['r2']
        c1s = sel_range['c1']; c2s = sel_range['c2']
        for r in range(ROWS):
            for c in range(COLS):
                x0, y0, x1, y1 = cell_bbox(r, c)
                in_range = is_in_sel(r, c)
                active   = (r == sel['r'] and c == sel['c'])
                bg = SEL_BG if in_range and not active else 'white'
                grid_canvas.create_rectangle(x0, y0, x1, y1,
                                             fill=bg, outline=GRID_LINE)
                txt = display_value(r, c)
                if txt:
                    pad = 3
                    anchor = 'w'
                    tx = x0 + pad
                    # right-align numbers
                    try:
                        float(txt)
                        anchor = 'e'; tx = x1 - pad
                    except: pass
                    fw = ('bold' if bold_var.get() else 'normal') if active else 'normal'
                    fi = 'italic' if (italic_var.get() and active) else 'roman'
                    font_tuple = (font_var.get(), int(size_var.get()), fw + (' italic' if fi == 'italic' else ''))
                    grid_canvas.create_text(tx, y0 + ROW_H//2,
                                            text=txt, anchor=anchor,
                                            font=(font_var.get(), int(size_var.get())),
                                            fill=TEXT_COL)
        # active cell border
        x0, y0, x1, y1 = cell_bbox(sel['r'], sel['c'])
        grid_canvas.create_rectangle(x0, y0, x1-1, y1-1,
                                     outline='#1565c0', width=2)

    def refresh_cell(r, c):
        draw_grid()  # simple: just redraw all (fast enough for this scale)

    def update_formula_bar():
        r, c = sel['r'], sel['c']
        cell_name.config(text=f'{col_letter(c)}{r+1}')
        formula_var.set(data[r][c])

    # ── undo/redo ─────────────────────────────────────────────────────────────

    def push_undo():
        snapshot = [row[:] for row in data]
        undo_stack.append(snapshot)
        redo_stack.clear()
        if len(undo_stack) > 100:
            undo_stack.pop(0)

    def undo():
        if not undo_stack:
            return
        redo_stack.append([row[:] for row in data])
        snapshot = undo_stack.pop()
        for r in range(ROWS):
            for c in range(COLS):
                data[r][c] = snapshot[r][c]
        refresh_all()

    def redo():
        if not redo_stack:
            return
        undo_stack.append([row[:] for row in data])
        snapshot = redo_stack.pop()
        for r in range(ROWS):
            for c in range(COLS):
                data[r][c] = snapshot[r][c]
        refresh_all()

    # ── cell selection & editing ──────────────────────────────────────────────

    def select_cell(r, c, extend=False):
        r = max(0, min(ROWS-1, r))
        c = max(0, min(COLS-1, c))
        if extend and sel_range['r1'] is not None:
            sel_range['r2'] = r
            sel_range['c2'] = c
        else:
            sel['r'] = r; sel['c'] = c
            sel_range.update({'r1': r, 'c1': c, 'r2': r, 'c2': c})
        ensure_visible(r, c)
        refresh_all()

    def start_range(r, c):
        sel['r'] = r; sel['c'] = c
        sel_range.update({'r1': r, 'c1': c, 'r2': r, 'c2': c})

    def ensure_visible(r, c):
        x0, y0, x1, y1 = cell_bbox(r, c)
        cw = grid_canvas.winfo_width()
        ch = grid_canvas.winfo_height()
        sx0 = grid_canvas.canvasx(0)
        sy0 = grid_canvas.canvasy(0)
        if x0 < sx0:
            grid_canvas.xview_moveto(x0 / total_w)
        elif x1 > sx0 + cw:
            grid_canvas.xview_moveto((x1 - cw) / total_w)
        if y0 < sy0:
            grid_canvas.yview_moveto(y0 / total_h)
        elif y1 > sy0 + ch:
            grid_canvas.yview_moveto((y1 - ch) / total_h)

    # inline editing
    edit_entry = None

    def start_edit(r, c):
        nonlocal edit_entry
        stop_edit()
        x0, y0, x1, y1 = cell_bbox(r, c)
        sx = grid_canvas.canvasx(0); sy = grid_canvas.canvasy(0)
        e = tk.Entry(grid_canvas, font=('Segoe UI', 9), relief='flat',
                     bd=0, bg='white', fg=TEXT_COL,
                     insertbackground=TEXT_COL)
        e.place(x=x0-sx+1, y=y0-sy+1, width=COL_W-2, height=ROW_H-2)
        e.insert(0, data[r][c])
        e.select_range(0, 'end')
        e.focus_set()
        edit_entry = e

        def commit(event=None):
            push_undo()
            data[r][c] = e.get()
            stop_edit()
            refresh_all()
            if event and event.keysym == 'Return':
                select_cell(r+1, c)
            elif event and event.keysym == 'Tab':
                select_cell(r, c+1)

        def cancel(event=None):
            stop_edit()
            refresh_all()

        e.bind('<Return>',  commit)
        e.bind('<Tab>',     commit)
        e.bind('<Escape>',  cancel)
        e.bind('<FocusOut>', commit)

    def stop_edit():
        nonlocal edit_entry
        if edit_entry:
            try: edit_entry.destroy()
            except: pass
            edit_entry = None

    # ── mouse events ─────────────────────────────────────────────────────────

    def on_click(event):
        grid_canvas.focus_set()
        stop_edit()
        cx = grid_canvas.canvasx(event.x)
        cy = grid_canvas.canvasy(event.y)
        c = int(cx // COL_W); r = int(cy // ROW_H)
        drag_start[0] = r; drag_start[1] = c
        extend = bool(event.state & 0x0001)  # Shift
        select_cell(r, c, extend)

    def on_drag(event):
        cx = grid_canvas.canvasx(event.x)
        cy = grid_canvas.canvasy(event.y)
        c = max(0, min(COLS-1, int(cx // COL_W)))
        r = max(0, min(ROWS-1, int(cy // ROW_H)))
        sel_range['r2'] = r; sel_range['c2'] = c
        refresh_all()

    def on_dbl_click(event):
        cx = grid_canvas.canvasx(event.x)
        cy = grid_canvas.canvasy(event.y)
        c = int(cx // COL_W); r = int(cy // ROW_H)
        sel['r'] = r; sel['c'] = c
        start_edit(r, c)

    grid_canvas.bind('<Button-1>',        on_click)
    grid_canvas.bind('<B1-Motion>',       on_drag)
    grid_canvas.bind('<Double-Button-1>', on_dbl_click)

    # ── keyboard events ───────────────────────────────────────────────────────

    def on_key(event):
        r, c = sel['r'], sel['c']
        key = event.keysym
        ctrl = bool(event.state & 0x4)

        if ctrl:
            if key == 'c':   copy_sel()
            elif key == 'v': paste_sel()
            elif key == 'x': cut_sel()
            elif key == 'z': undo()
            elif key == 'y': redo()
            elif key == 'a': select_all()
            return

        nav = {'Up': (-1,0), 'Down': (1,0), 'Left': (0,-1), 'Right': (0,1),
               'Return': (1,0), 'Tab': (0,1)}
        if key in nav:
            extend = bool(event.state & 0x0001)
            dr, dc = nav[key]
            select_cell(r+dr, c+dc, extend)
            return

        if key == 'Delete' or key == 'BackSpace':
            push_undo()
            if sel_range['r1'] is not None:
                for rr in range(min(sel_range['r1'], sel_range['r2']),
                                max(sel_range['r1'], sel_range['r2'])+1):
                    for cc in range(min(sel_range['c1'], sel_range['c2']),
                                   max(sel_range['c1'], sel_range['c2'])+1):
                        data[rr][cc] = ''
            else:
                data[r][c] = ''
            refresh_all()
            return

        if key == 'F2':
            start_edit(r, c); return

        # printable char → start typing
        if len(event.char) == 1 and event.char.isprintable():
            push_undo()
            data[r][c] = ''
            start_edit(r, c)
            if edit_entry:
                edit_entry.delete(0, 'end')
                edit_entry.insert(0, event.char)

    grid_canvas.bind('<Key>', on_key)
    grid_canvas.bind('<FocusIn>', lambda e: None)

    # ── copy / paste / cut / select-all ──────────────────────────────────────

    def copy_sel():
        r1 = min(sel_range['r1'] or sel['r'], sel_range['r2'] or sel['r'])
        r2 = max(sel_range['r1'] or sel['r'], sel_range['r2'] or sel['r'])
        c1 = min(sel_range['c1'] or sel['c'], sel_range['c2'] or sel['c'])
        c2 = max(sel_range['c1'] or sel['c'], sel_range['c2'] or sel['c'])
        clipboard.clear()
        for rr in range(r1, r2+1):
            clipboard.append([data[rr][cc] for cc in range(c1, c2+1)])
        # also copy to system clipboard as tab-separated
        txt = '\n'.join('\t'.join(row) for row in clipboard)
        win.clipboard_clear(); win.clipboard_append(txt)

    def cut_sel():
        copy_sel()
        push_undo()
        r1 = min(sel_range['r1'] or sel['r'], sel_range['r2'] or sel['r'])
        r2 = max(sel_range['r1'] or sel['r'], sel_range['r2'] or sel['r'])
        c1 = min(sel_range['c1'] or sel['c'], sel_range['c2'] or sel['c'])
        c2 = max(sel_range['c1'] or sel['c'], sel_range['c2'] or sel['c'])
        for rr in range(r1, r2+1):
            for cc in range(c1, c2+1):
                data[rr][cc] = ''
        refresh_all()

    def paste_sel():
        if not clipboard:
            return
        push_undo()
        r0, c0 = sel['r'], sel['c']
        for dr, row in enumerate(clipboard):
            for dc, val in enumerate(row):
                nr, nc = r0+dr, c0+dc
                if nr < ROWS and nc < COLS:
                    data[nr][nc] = val
        refresh_all()

    def select_all():
        sel_range.update({'r1': 0, 'c1': 0, 'r2': ROWS-1, 'c2': COLS-1})
        refresh_all()

    # ── right-click context menu ──────────────────────────────────────────────

    def context_menu(event):
        cx = grid_canvas.canvasx(event.x)
        cy = grid_canvas.canvasy(event.y)
        c = int(cx // COL_W); r = int(cy // ROW_H)
        select_cell(r, c)
        m = tk.Menu(win, tearoff=0)
        m.add_command(label='Cut',   command=cut_sel)
        m.add_command(label='Copy',  command=copy_sel)
        m.add_command(label='Paste', command=paste_sel)
        m.add_separator()
        m.add_command(label='Clear Cell', command=lambda: (
            push_undo(), data.__setitem__(r, [data[r][cc] if cc != c else ''
                                              for cc in range(COLS)]), refresh_all()))
        m.add_separator()
        m.add_command(label='Insert Row Above', command=lambda: insert_row(r))
        m.add_command(label='Delete Row',       command=lambda: delete_row(r))
        m.tk_popup(event.x_root, event.y_root)

    grid_canvas.bind('<Button-3>', context_menu)

    def insert_row(r):
        push_undo()
        data.insert(r, ['' for _ in range(COLS)])
        data.pop()
        refresh_all()

    def delete_row(r):
        push_undo()
        data.pop(r)
        data.append(['' for _ in range(COLS)])
        refresh_all()

    # ── mouse-wheel scroll ────────────────────────────────────────────────────

    def on_scroll(event):
        if event.delta:
            grid_canvas.yview_scroll(int(-event.delta/120), 'units')
            row_hdr.yview_scroll(int(-event.delta/120), 'units')
        elif event.num == 4:
            grid_canvas.yview_scroll(-1, 'units')
            row_hdr.yview_scroll(-1, 'units')
        elif event.num == 5:
            grid_canvas.yview_scroll(1, 'units')
            row_hdr.yview_scroll(1, 'units')

    grid_canvas.bind('<MouseWheel>',  on_scroll)
    grid_canvas.bind('<Button-4>',    on_scroll)
    grid_canvas.bind('<Button-5>',    on_scroll)

    # ── status bar ────────────────────────────────────────────────────────────
    status_bar = tk.Frame(win, bg='#217346', height=20)
    status_bar.pack(fill='x', side='bottom')
    status_bar.pack_propagate(False)
    status_lbl = tk.Label(status_bar, text='Ready', bg='#217346', fg='white',
                          font=('Segoe UI', 8))
    status_lbl.pack(side='left', padx=8)

    def update_status(*_):
        r, c = sel['r'], sel['c']
        val = display_value(r, c)
        try:
            nums = []
            r1 = min(sel_range['r1'] or r, sel_range['r2'] or r)
            r2 = max(sel_range['r1'] or r, sel_range['r2'] or r)
            c1 = min(sel_range['c1'] or c, sel_range['c2'] or c)
            c2 = max(sel_range['c1'] or c, sel_range['c2'] or c)
            for rr in range(r1, r2+1):
                for cc in range(c1, c2+1):
                    v = display_value(rr, cc)
                    if v:
                        nums.append(float(v))
            if nums:
                s = f'Count: {len(nums)}   Sum: {sum(nums):g}   Avg: {sum(nums)/len(nums):g}'
            else:
                s = 'Ready'
        except:
            s = f'Cell: {col_letter(c)}{r+1}'
        status_lbl.config(text=s)

    # ── wire status updates ───────────────────────────────────────────────────
    orig_refresh = refresh_all

    def refresh_all_with_status():
        orig_refresh()
        update_status()

    # replace refresh_all in closure
    import sys
    frame = sys._getframe(0)
    # simplest: just call status after every draw
    grid_canvas.bind('<ButtonRelease-1>', lambda e: update_status())
    grid_canvas.bind('<KeyRelease>',      lambda e: update_status())

    # ── initial draw ──────────────────────────────────────────────────────────
    win.after(50, refresh_all)

    return win


# ── entry point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app = show_excel_app()
    app.mainloop()

def open_word():
    import tkinter as tk
    from tkinter import ttk, filedialog, colorchooser, messagebox, simpledialog
    import os

    win = tk.Toplevel()
    win.title("Microsoft Word")
    win.geometry("1100x700")

    current_file = [None]

    # Toolbar
    toolbar = tk.Frame(win, bd=1, relief="raised")
    toolbar.pack(fill="x")

    editor_font = ["Calibri", 12]

    text = tk.Text(
        win,
        undo=True,
        wrap="word",
        font=(editor_font[0], editor_font[1])
    )
    text.pack(fill="both", expand=True)

    status = tk.Label(win, anchor="w")
    status.pack(fill="x", side="bottom")

    def update_status(event=None):
        content = text.get("1.0", "end-1c")
        words = len(content.split())
        chars = len(content)
        status.config(text=f"Words: {words}    Characters: {chars}")

    text.bind("<KeyRelease>", update_status)

    def new_file():
        text.delete("1.0", "end")
        current_file[0] = None
        win.title("Microsoft Word")

    def open_file():
        path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text.delete("1.0", "end")
            text.insert("1.0", f.read())

        current_file[0] = path
        win.title(f"Microsoft Word - {os.path.basename(path)}")
        update_status()

    def save_file():
        if current_file[0]:
            with open(current_file[0], "w", encoding="utf-8") as f:
                f.write(text.get("1.0", "end-1c"))
        else:
            save_as()

    def save_as():
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as f:
            f.write(text.get("1.0", "end-1c"))

        current_file[0] = path
        win.title(f"Microsoft Word - {os.path.basename(path)}")

    def make_tag(tag, **cfg):
        text.tag_configure(tag, **cfg)

    make_tag("bold", font=("Calibri", 12, "bold"))
    make_tag("italic", font=("Calibri", 12, "italic"))
    make_tag("underline", underline=1)

    def apply_tag(tag):
        try:
            start = text.index("sel.first")
            end = text.index("sel.last")
            text.tag_add(tag, start, end)
        except:
            pass

    def set_color():
        c = colorchooser.askcolor()[1]
        if not c:
            return

        tag = f"fg_{c}"
        text.tag_configure(tag, foreground=c)

        try:
            text.tag_add(tag, "sel.first", "sel.last")
        except:
            pass

    def increase_font():
        editor_font[1] += 1
        text.config(font=(editor_font[0], editor_font[1]))

    def decrease_font():
        if editor_font[1] > 6:
            editor_font[1] -= 1
        text.config(font=(editor_font[0], editor_font[1]))

    def find_text():
        target = simpledialog.askstring("Find", "Text:")
        if not target:
            return

        text.tag_remove("search", "1.0", "end")
        idx = "1.0"

        while True:
            idx = text.search(target, idx, stopindex="end")
            if not idx:
                break

            endidx = f"{idx}+{len(target)}c"
            text.tag_add("search", idx, endidx)
            idx = endidx

        text.tag_configure("search", background="yellow")

    def replace_text():
        find = simpledialog.askstring("Find", "Find:")
        if find is None:
            return

        repl = simpledialog.askstring("Replace", "Replace with:")
        if repl is None:
            return

        content = text.get("1.0", "end-1c")
        content = content.replace(find, repl)

        text.delete("1.0", "end")
        text.insert("1.0", content)

    ttk.Button(toolbar, text="New", command=new_file).pack(side="left")
    ttk.Button(toolbar, text="Open", command=open_file).pack(side="left")
    ttk.Button(toolbar, text="Save", command=save_file).pack(side="left")

    ttk.Separator(toolbar, orient="vertical").pack(
        side="left",
        fill="y",
        padx=5
    )

    ttk.Button(
        toolbar,
        text="B",
        command=lambda: apply_tag("bold")
    ).pack(side="left")

    ttk.Button(
        toolbar,
        text="I",
        command=lambda: apply_tag("italic")
    ).pack(side="left")

    ttk.Button(
        toolbar,
        text="U",
        command=lambda: apply_tag("underline")
    ).pack(side="left")

    ttk.Button(
        toolbar,
        text="Color",
        command=set_color
    ).pack(side="left")

    ttk.Button(
        toolbar,
        text="A+",
        command=increase_font
    ).pack(side="left")

    ttk.Button(
        toolbar,
        text="A-",
        command=decrease_font
    ).pack(side="left")

    ttk.Button(
        toolbar,
        text="Find",
        command=find_text
    ).pack(side="left")

    ttk.Button(
        toolbar,
        text="Replace",
        command=replace_text
    ).pack(side="left")

    update_status()

def show_google_app():
    if not check_drivers("Google App"):
        return

    if state.get('os_version') == 'Starter':
        messagebox.showwarning("Restricted", "Internet features are limited in Windows 7 Starter.")
        return

    gwin = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    gwin.title('Google')
    gwin.geometry('720x520')
    style_aero_window(gwin, '#fff')
    center_window(gwin, 720, 520)
    tk.Label(gwin, text='Google (mini)', bg='#fff', fg='#1b3f6d', font=('Segoe UI', 14, 'bold')).pack(pady=(12,6))
    qvar = tk.StringVar()
    tk.Entry(gwin, textvariable=qvar, width=60).pack(pady=(6,6))
    tk.Button(gwin, text='Search', bg='#1f5cc5', fg='white', command=lambda: webbrowser.open('https://www.google.com/search?q=' + urllib.parse.quote_plus(qvar.get()))).pack()
    tk.Label(gwin, text='Quick Links', bg='#fff', fg='#37558d', font=('Segoe UI', 10, 'bold')).pack(pady=(14,4))
    links = tk.Frame(gwin, bg='#fff')
    links.pack(pady=4)
    tk.Button(links, text='Google', width=14, bg='#dde7ff', fg='#1f3d6d', command=lambda: webbrowser.open('https://www.google.com')).pack(side='left', padx=6)
    tk.Button(links, text='Images', width=14, bg='#dde7ff', fg='#1f3d6d', command=lambda: webbrowser.open('https://www.google.com/imghp')).pack(side='left', padx=6)
    tk.Button(links, text='News', width=14, bg='#dde7ff', fg='#1f3d6d', command=lambda: webbrowser.open('https://news.google.com')).pack(side='left', padx=6)

def show_text_editor():
    """Alias — opens the full MS Word-style processor."""
    show_word_processor()


def show_word_processor():
    """Full MS Word-style word processor with rich formatting and curvy Aero UI."""
    editor = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    editor.title('Microsoft Word — Document1')
    editor.geometry('1000x720')
    style_aero_window(editor, '#f0f4ff')
    center_window(editor, 1000, 720)
    register_app_in_taskbar(editor)

    doc_state = {
        'path': None, 'modified': False,
        'font_name': 'Calibri', 'font_size': 12,
        'align': 'left', 'color': '#000000', 'zoom': 100,
    }

    # Title bar
    title_bar = tk.Frame(editor, bg='#2b579a', height=36)
    title_bar.pack(fill='x')
    title_bar.pack_propagate(False)
    title_lbl = tk.Label(title_bar, text='Document1 — Microsoft Word',
                         bg='#2b579a', fg='white', font=('Segoe UI', 10, 'bold'))
    title_lbl.pack(side='left', padx=12, pady=8)
    mod_lbl = tk.Label(title_bar, text='', bg='#2b579a', fg='#aac8ff', font=('Segoe UI', 9))
    mod_lbl.pack(side='left')

    # Ribbon
    ribbon = tk.Frame(editor, bg='#dce6f5', height=80)
    ribbon.pack(fill='x')
    ribbon.pack_propagate(False)

    tab_strip = tk.Frame(ribbon, bg='#2b579a', height=26)
    tab_strip.pack(fill='x')
    tab_strip.pack_propagate(False)

    def _ribbon_tab(name, active=False):
        bg = '#f0f4ff' if active else '#2b579a'
        fg = '#2b579a' if active else 'white'
        b = tk.Label(tab_strip, text=name, bg=bg, fg=fg,
                     font=('Segoe UI', 9, 'bold'), padx=14, pady=4, cursor='hand2')
        b.pack(side='left')
        def activate(e, btn=b):
            for w in tab_strip.winfo_children():
                w.config(bg='#2b579a', fg='white')
            btn.config(bg='#f0f4ff', fg='#2b579a')
        b.bind('<Button-1>', activate)
        return b

    for i, tab in enumerate(['Home', 'Insert', 'Page Layout', 'References', 'View']):
        _ribbon_tab(tab, active=(i == 0))

    home_row = tk.Frame(ribbon, bg='#dce6f5')
    home_row.pack(fill='x', padx=6, pady=4)

    def _rnd_btn(parent, text, cmd, bg='#e8f0ff', width=None):
        kw = dict(text=text, command=cmd, bg=bg, fg='#1a3a6a', relief='flat',
                  font=('Segoe UI', 9), cursor='hand2', activebackground='#b8d0f0',
                  bd=0, highlightthickness=1, highlightbackground='#aac0e0', padx=8, pady=4)
        if width: kw['width'] = width
        btn = tk.Button(parent, **kw)
        btn.pack(side='left', padx=2, pady=1)
        return btn

    # Font
    tk.Label(home_row, text='Font:', bg='#dce6f5', fg='#2b4a80', font=('Segoe UI', 8)).pack(side='left', padx=(4,0))
    font_var = tk.StringVar(value='Calibri')
    font_cb = ttk.Combobox(home_row, textvariable=font_var, width=14, state='readonly', font=('Segoe UI', 9),
                           values=['Calibri','Arial','Times New Roman','Courier New','Georgia','Verdana','Segoe UI'])
    font_cb.pack(side='left', padx=4, pady=3)

    tk.Label(home_row, text='Size:', bg='#dce6f5', fg='#2b4a80', font=('Segoe UI', 8)).pack(side='left')
    size_var = tk.StringVar(value='12')
    size_cb = ttk.Combobox(home_row, textvariable=size_var, width=5, font=('Segoe UI', 9),
                           values=[str(s) for s in [8,9,10,11,12,14,16,18,20,24,28,32,36,48,72]])
    size_cb.pack(side='left', padx=4)

    tk.Frame(home_row, bg='#b0c0d8', width=1).pack(side='left', fill='y', padx=6, pady=2)

    bold_var = tk.BooleanVar()
    ital_var = tk.BooleanVar()
    under_var = tk.BooleanVar()

    def _apply_tag(tag_name, **kw):
        try:
            sel = text_w.tag_ranges('sel')
            if sel:
                text_w.tag_configure(tag_name, **kw)
                text_w.tag_add(tag_name, sel[0], sel[1])
        except: pass

    def toggle_bold():
        bold_var.set(not bold_var.get())
        b_btn.config(relief='sunken' if bold_var.get() else 'flat',
                     bg='#aac8f0' if bold_var.get() else '#e8f0ff')
        _apply_tag('_bold', font=(font_var.get(), int(size_var.get() or 12), 'bold'))

    def toggle_ital():
        ital_var.set(not ital_var.get())
        i_btn.config(relief='sunken' if ital_var.get() else 'flat',
                     bg='#aac8f0' if ital_var.get() else '#e8f0ff')
        _apply_tag('_italic', font=(font_var.get(), int(size_var.get() or 12), 'italic'))

    def toggle_under():
        under_var.set(not under_var.get())
        u_btn.config(relief='sunken' if under_var.get() else 'flat',
                     bg='#aac8f0' if under_var.get() else '#e8f0ff')
        _apply_tag('_underline', underline=1)

    b_btn = tk.Button(home_row, text='B', command=toggle_bold, bg='#e8f0ff', fg='#1a3a6a',
                      relief='flat', font=('Segoe UI', 10, 'bold'), width=3, cursor='hand2',
                      highlightthickness=1, highlightbackground='#aac0e0')
    b_btn.pack(side='left', padx=2)
    i_btn = tk.Button(home_row, text='I', command=toggle_ital, bg='#e8f0ff', fg='#1a3a6a',
                      relief='flat', font=('Segoe UI', 10, 'italic'), width=3, cursor='hand2',
                      highlightthickness=1, highlightbackground='#aac0e0')
    i_btn.pack(side='left', padx=2)
    u_btn = tk.Button(home_row, text='U', command=toggle_under, bg='#e8f0ff', fg='#1a3a6a',
                      relief='flat', font=('Segoe UI', 10, 'underline'), width=3, cursor='hand2',
                      highlightthickness=1, highlightbackground='#aac0e0')
    u_btn.pack(side='left', padx=2)

    tk.Frame(home_row, bg='#b0c0d8', width=1).pack(side='left', fill='y', padx=6, pady=2)

    for sym, aln in [('≡','left'), ('☰','center'), ('≣','right')]:
        _rnd_btn(home_row, sym, lambda a=aln: [doc_state.update({'align': a}),
                 text_w.tag_configure(f'_al_{a}', justify=a),
                 text_w.tag_add(f'_al_{a}', 'insert linestart', 'insert lineend+1c')], width=3)

    tk.Frame(home_row, bg='#b0c0d8', width=1).pack(side='left', fill='y', padx=6, pady=2)
    _rnd_btn(home_row, '• List', lambda: text_w.insert('insert', '• '))
    _rnd_btn(home_row, '1. List', lambda: text_w.insert('insert', '1. '))

    tk.Frame(home_row, bg='#b0c0d8', width=1).pack(side='left', fill='y', padx=6, pady=2)

    def pick_color():
        from tkinter.colorchooser import askcolor
        c = askcolor(title='Font Color', color='#000000')[1]
        if c:
            doc_state['color'] = c
            _apply_tag(f'_col_{c[1:]}', foreground=c)
    _rnd_btn(home_row, 'A▾', pick_color)

    def show_find_replace():
        fr = tk.Toplevel(editor)
        fr.title('Find & Replace')
        fr.geometry('360x180')
        fr.resizable(False, False)
        style_aero_window(fr, '#f0f4ff')
        center_window(fr, 360, 180)
        tk.Label(fr, text='Find:', bg='#f0f4ff', fg='#1a3a6a').grid(row=0, column=0, padx=12, pady=10, sticky='w')
        fv = tk.StringVar()
        tk.Entry(fr, textvariable=fv, width=26).grid(row=0, column=1, padx=8)
        tk.Label(fr, text='Replace:', bg='#f0f4ff', fg='#1a3a6a').grid(row=1, column=0, padx=12, sticky='w')
        rv = tk.StringVar()
        tk.Entry(fr, textvariable=rv, width=26).grid(row=1, column=1, padx=8)
        def do_replace():
            c = text_w.get('1.0', 'end'); nc = c.replace(fv.get(), rv.get())
            text_w.delete('1.0', 'end'); text_w.insert('1.0', nc)
        bf = tk.Frame(fr, bg='#f0f4ff'); bf.grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(bf, text='Replace All', command=do_replace, bg='#2a7a3a', fg='white', relief='flat', padx=10).pack(side='left', padx=4)
        tk.Button(bf, text='Close', command=fr.destroy, bg='#888', fg='white', relief='flat', padx=10).pack(side='left', padx=4)

    tk.Frame(home_row, bg='#b0c0d8', width=1).pack(side='left', fill='y', padx=6, pady=2)
    _rnd_btn(home_row, '🔍 Find', show_find_replace)

    # Menu bar
    menu_bar = tk.Menu(editor)
    editor.config(menu=menu_bar)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label='File', menu=file_menu)

    def new_doc():
        text_w.delete('1.0', 'end')
        doc_state.update({'path': None, 'modified': False})
        editor.title('Document1 — Microsoft Word')
        title_lbl.config(text='Document1 — Microsoft Word')
        mod_lbl.config(text='')

    def open_doc():
        path = filedialog.askopenfilename(
            filetypes=[('Text files','*.txt'),('All files','*.*')])
        if path:
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    text_w.delete('1.0', 'end'); text_w.insert('1.0', f.read())
                doc_state['path'] = path
                n = os.path.basename(path)
                editor.title(f'{n} — Microsoft Word')
                title_lbl.config(text=f'{n} — Microsoft Word')
                mod_lbl.config(text='')
            except Exception as e:
                messagebox.showerror('Open Failed', str(e))

    def save_doc(save_as=False):
        path = doc_state['path']
        if save_as or not path:
            path = filedialog.asksaveasfilename(defaultextension='.txt',
                filetypes=[('Text files','*.txt'),('All files','*.*')])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text_w.get('1.0','end').rstrip())
                doc_state['path'] = path; doc_state['modified'] = False
                n = os.path.basename(path)
                editor.title(f'{n} — Microsoft Word')
                title_lbl.config(text=f'{n} — Microsoft Word')
                mod_lbl.config(text='')
                show_system_notification('Word', f'Saved: {n}')
            except Exception as e:
                messagebox.showerror('Save Failed', str(e))

    def insert_table_text():
        rows = simpledialog.askinteger('Table','Rows:', minvalue=1, maxvalue=20) or 3
        cols = simpledialog.askinteger('Table','Columns:', minvalue=1, maxvalue=10) or 3
        sep = '+' + '+'.join(['-'*12]*cols) + '+'
        row_line = '|' + '|'.join([' '*12]*cols) + '|'
        table = '\n' + sep + '\n'
        for _ in range(rows):
            table += row_line + '\n' + sep + '\n'
        text_w.insert('insert', table)

    file_menu.add_command(label='New',      command=new_doc,  accelerator='Ctrl+N')
    file_menu.add_command(label='Open…',    command=open_doc, accelerator='Ctrl+O')
    file_menu.add_separator()
    file_menu.add_command(label='Save',     command=save_doc, accelerator='Ctrl+S')
    file_menu.add_command(label='Save As…', command=lambda: save_doc(True))
    file_menu.add_separator()
    file_menu.add_command(label='Properties', command=lambda: messagebox.showinfo('Properties',
        f'Words: {len(text_w.get("1.0","end").split())}\n'
        f'Chars: {len(text_w.get("1.0","end"))}\n'
        f'Path: {doc_state["path"] or "Unsaved"}'))
    file_menu.add_separator()
    file_menu.add_command(label='Close', command=editor.destroy)

    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label='Edit', menu=edit_menu)
    edit_menu.add_command(label='Undo', command=lambda: text_w.edit_undo(), accelerator='Ctrl+Z')
    edit_menu.add_command(label='Redo', command=lambda: text_w.edit_redo(), accelerator='Ctrl+Y')
    edit_menu.add_separator()
    edit_menu.add_command(label='Cut',   command=lambda: text_w.event_generate('<<Cut>>'))
    edit_menu.add_command(label='Copy',  command=lambda: text_w.event_generate('<<Copy>>'))
    edit_menu.add_command(label='Paste', command=lambda: text_w.event_generate('<<Paste>>'))
    edit_menu.add_separator()
    edit_menu.add_command(label='Select All', command=lambda: text_w.tag_add('sel','1.0','end'))
    edit_menu.add_command(label='Find & Replace…', command=show_find_replace)

    ins_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label='Insert', menu=ins_menu)
    ins_menu.add_command(label='Date', command=lambda: text_w.insert('insert', datetime.now().strftime('%d %B %Y')))
    ins_menu.add_command(label='Time', command=lambda: text_w.insert('insert', datetime.now().strftime('%H:%M:%S')))
    ins_menu.add_command(label='Table…', command=insert_table_text)
    ins_menu.add_command(label='Horizontal Rule', command=lambda: text_w.insert('insert', '\n' + '─'*60 + '\n'))
    ins_menu.add_command(label='Page Break', command=lambda: text_w.insert('insert', '\n' + '═'*60 + ' [PAGE BREAK] ' + '═'*60 + '\n'))

    # Document area with page styling
    doc_bg = tk.Frame(editor, bg='#9aa8bb')
    doc_bg.pack(fill='both', expand=True)
    page_frame = tk.Frame(doc_bg, bg='white', highlightthickness=2,
                          highlightbackground='#8899aa')
    page_frame.pack(fill='both', expand=True, padx=20, pady=12)

    # Ruler
    ruler_cv = tk.Canvas(page_frame, height=22, bg='#f0f0f0', highlightthickness=0)
    ruler_cv.pack(fill='x')
    def draw_ruler(e=None):
        ruler_cv.delete('all')
        W = ruler_cv.winfo_width() or 900
        for i in range(0, W, 10):
            h = 8 if i % 100 == 0 else (5 if i % 50 == 0 else 3)
            ruler_cv.create_line(i, 22-h, i, 22, fill='#888')
            if i % 100 == 0 and i > 0:
                ruler_cv.create_text(i, 5, text=str(i//100), fill='#555', font=('Segoe UI', 7))
    ruler_cv.bind('<Configure>', draw_ruler)
    ruler_cv.after(100, draw_ruler)

    sb_v = tk.Scrollbar(page_frame, orient='vertical')
    sb_v.pack(side='right', fill='y')

    text_w = tk.Text(page_frame,
                     font=('Calibri', 12), bg='white', fg='#111111',
                     wrap='word', undo=True, autoseparators=True, maxundo=100,
                     padx=60, pady=40, spacing1=2, spacing3=2, relief='flat',
                     selectbackground='#b8d0ff', selectforeground='#000000',
                     insertbackground='#000080', insertwidth=2,
                     yscrollcommand=sb_v.set)
    text_w.pack(fill='both', expand=True)
    sb_v.config(command=text_w.yview)

    text_w.insert('1.0',
        'Welcome to Microsoft Word\n'
        '─────────────────────────────────────────────────────────\n'
        'Start typing your document here. Use the ribbon for formatting.\n\n'
        'Shortcuts:  Ctrl+B Bold  •  Ctrl+I Italic  •  Ctrl+U Underline\n'
        '            Ctrl+S Save  •  Ctrl+O Open    •  Ctrl+Z Undo\n\n')
    text_w.mark_set('insert', '7.0')

    # Status bar
    status = tk.Frame(editor, bg='#2b579a', height=24)
    status.pack(fill='x', side='bottom')
    status.pack_propagate(False)
    wc_lbl = tk.Label(status, text='Words: 0', bg='#2b579a', fg='#c0d8ff', font=('Segoe UI', 8), padx=8)
    wc_lbl.pack(side='left')
    ln_lbl = tk.Label(status, text='Line 1, Col 1', bg='#2b579a', fg='#c0d8ff', font=('Segoe UI', 8), padx=8)
    ln_lbl.pack(side='left')

    def update_status(event=None):
        wc = len(text_w.get('1.0','end').split())
        wc_lbl.config(text=f'Words: {wc}')
        try:
            row, col = text_w.index('insert').split('.')
            ln_lbl.config(text=f'Line {row}, Col {int(col)+1}')
        except: pass
        doc_state['modified'] = True
        mod_lbl.config(text=' [Modified]')

    text_w.bind('<KeyRelease>', update_status)
    text_w.bind('<ButtonRelease>', update_status)

    def apply_font(*args):
        try:
            sz = max(7, int(size_var.get() or 12))
        except ValueError:
            sz = 12
        text_w.config(font=(font_var.get(), sz))

    font_var.trace('w', apply_font)
    size_var.trace('w', apply_font)

    editor.bind('<Control-s>', lambda e: save_doc())
    editor.bind('<Control-o>', lambda e: open_doc())
    editor.bind('<Control-n>', lambda e: new_doc())
    editor.bind('<Control-h>', lambda e: show_find_replace())
    editor.bind('<Control-b>', lambda e: toggle_bold())
    editor.bind('<Control-i>', lambda e: toggle_ital())
    editor.bind('<Control-u>', lambda e: toggle_under())
    text_w.focus_set()

def show_calculator_app():
    calc = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    calc.title('Calculator')
    calc.geometry('320x450')
    style_aero_window(calc, '#f0f4ff')
    center_window(calc, 320, 450)

    display_var = tk.StringVar()
    display = tk.Entry(calc, textvariable=display_var, font=('Segoe UI', 20), justify='right', bd=2, relief='sunken')
    display.pack(fill='x', padx=16, pady=(16,8))

    def press(value):
        display_var.set(display_var.get() + str(value))
    def calculate():
        try:
            res = safe_eval(re.sub(r'[^0-9\.\+\-\*\/\%\(\)]', '', display_var.get()))
            display_var.set(str(res))
        except Exception:
            display_var.set('Error')
    def clear():
        display_var.set('')

    buttons = [
        ['7','8','9','/'],
        ['4','5','6','*'],
        ['1','2','3','-'],
        ['0','.','=','+'],
    ]
    for row in buttons:
        row_frame = tk.Frame(calc, bg='#f0f4ff')
        row_frame.pack(fill='x', padx=16, pady=4)
        for label in row:
            action = calculate if label == '=' else clear if label == 'C' else lambda v=label: press(v)
            tk.Button(row_frame, text=label, width=6, height=2, bg='#d6e2ff', fg='#20385d', command=action).pack(side='left', padx=4)
    tk.Button(calc, text='Clear', width=26, bg='#c94d4d', fg='white', command=clear).pack(padx=16, pady=12)

def show_paint_app():
    paint = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    paint.title('Paint')
    paint.geometry('760x520')
    style_aero_window(paint, '#eef2ff')
    center_window(paint, 760, 520)

    color_var = tk.StringVar(value='#0a3d91')
    canvas = tk.Canvas(paint, bg='white', bd=2, relief='sunken')
    canvas.pack(fill='both', expand=True, padx=10, pady=10)

    def draw(event):
        x, y = event.x, event.y
        canvas.create_oval(x-6, y-6, x+6, y+6, fill=color_var.get(), outline=color_var.get())
    canvas.bind('<B1-Motion>', draw)

    tool_frame = tk.Frame(paint, bg='#edf0ff')
    tool_frame.pack(fill='x', padx=10, pady=(0,10))
    for c in ['#0a3d91', '#d92c2c', '#2c862c', '#000000', '#ff9b00', '#7a3bb5', '#ffffff']:
        tk.Button(tool_frame, bg=c, width=3, command=lambda color=c: color_var.set(color)).pack(side='left', padx=3)
    tk.Button(tool_frame, text='Clear', bg='#cc4a4a', fg='white', command=lambda: canvas.delete('all')).pack(side='right', padx=6)

def show_system_info_app():
    info = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    info.title('System Info')
    info.geometry('520x420')
    style_aero_window(info, '#f4f7ff')
    center_window(info, 520, 420)

    sys_frame = tk.Frame(info, bg='#f4f7ff')
    sys_frame.pack(fill='both', expand=True, padx=16, pady=16)
    vals = [
        ('OS Version', state.get('os_version', 'Ultimate')),
        ('Desktop Mode', 'Windows 7 Shell'),
        ('RAM Setting', state.get('ram_size', '8GB')),
        ('User Age', state.get('user_age', '20')),
        ('Battery', get_battery_status()),
        ('Notes Stored', str(len(state.get('notes', [])))),
        ('Tasks Stored', str(len(state.get('tasks', [])))),
    ]
    for label, value in vals:
        tk.Label(sys_frame, text=f'{label}:', bg='#f4f7ff', fg='#1e446d', font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(8,0))
        tk.Label(sys_frame, text=value, bg='#f4f7ff', fg='#233e67', font=('Segoe UI', 10)).pack(anchor='w')

def show_wifi_manager():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Wi-Fi Manager')
    win.geometry('520x420')
    style_aero_window(win, '#eef7ff')
    center_window(win, 520, 420)

    tk.Label(win, text='Wi-Fi Networks', bg='#eef7ff', fg='#16385f', font=('Segoe UI', 14, 'bold')).pack(pady=(12,6))
    frame = tk.Frame(win, bg='#eef7ff')
    frame.pack(fill='both', expand=True, padx=12, pady=8)

    lst = tk.Listbox(frame, bg='white', fg='black', height=12)
    lst.pack(fill='both', expand=True, side='left', padx=(0,8))
    # Simulated networks
    networks = [
        {'ssid': 'Ethernet', 'strength': 'Strong', 'secure': True},
        {'ssid': 'Galaxy F15 5G', 'strength': 'Good', 'secure': False},
        {'ssid': 'Office 4G', 'strength': 'Weak', 'secure': True},
        {'ssid': 'Public WiFi', 'strength': 'Poor', 'secure': False},
        {'ssid': 'Home Network', 'strength': 'Excellent', 'secure': True},
        {'ssid': 'Hidden Network', 'strength': 'Fair', 'unsecure': False},
    ]
    for n in networks:
        sec = '🔒' if n['secure'] else '🔓'
        lst.insert('end', f"{n['ssid']}  {sec}  ({n['strength']})")

    ctrl = tk.Frame(win, bg='#eef7ff')
    ctrl.pack(fill='x', padx=12, pady=(6,12))
    tk.Label(ctrl, text='Password:', bg='#eef7ff').pack(side='left')
    pwd = tk.Entry(ctrl, show='*')
    pwd.pack(side='left', padx=6)
    def connect():
        sel = lst.curselection()
        if not sel:
            messagebox.showinfo('Wi-Fi', 'Select a network first.')
            return
        ss = networks[sel[0]]['ssid']
        messagebox.showinfo('Wi-Fi', f'Connected to {ss} (simulated).')
    tk.Button(ctrl, text='Connect', bg='#3b82f6', fg='white', command=connect).pack(side='left', padx=8)
    tk.Button(ctrl, text='Refresh', bg='#6b92db', fg='white', command=lambda: messagebox.showinfo('Wi-Fi', 'Scan complete.')).pack(side='right')

def show_windows_security():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Windows Security')
    win.geometry('520x420')
    style_aero_window(win, '#f4f7ff')
    center_window(win, 520, 420)
    tk.Label(win, text='Windows Security', bg='#f4f7ff', fg='#1b3766', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    tk.Label(win, text='Protecting your PC with firewall, antivirus, and sign-in options.', bg='#f4f7ff', fg='#33609f', font=('Segoe UI', 10)).pack(pady=(0,12))
    content = tk.Frame(win, bg='#f4f7ff')
    content.pack(fill='both', expand=True, padx=16, pady=8)
    for label, value in [
        ('Firewall', 'Enabled'),
        ('Virus & threat protection', 'No threats found'),
        ('Account protection', 'Sign-in options ready'),
        ('Device security', 'Core isolation active')
    ]:
        row = tk.Frame(content, bg='#f4f7ff')
        row.pack(fill='x', pady=6)
        tk.Label(row, text=label, bg='#f4f7ff', fg='#224b7a', font=('Segoe UI', 10, 'bold')).pack(side='left')
        tk.Label(row, text=value, bg='#f4f7ff', fg='#17365f', font=('Segoe UI', 10)).pack(side='right')
    tk.Button(win, text='Run Windows Defender', bg='#2e70d1', fg='white', command=show_windows_defender_scanner).pack(pady=6)
    tk.Button(win, text='Open Advanced Security', bg='#5b8fe2', fg='white', command=show_advanced_security).pack(pady=6)
    tk.Button(win, text='Restart PC', bg='#4b89d4', fg='white', command=restart_to_login).pack(pady=(0,8))
    tk.Label(win, text='Driver status: ' + ('Installed' if state.get('drivers_installed', True) else 'Missing'), bg='#f4f7ff', fg='#1b3766', font=('Segoe UI', 10, 'italic')).pack(pady=(0,8))
    if not state.get('drivers_installed', True):
        tk.Label(win, text='Install drivers after reboot to unlock terminal and features.', bg='#f4f7ff', fg='#7f4a33', font=('Segoe UI', 9)).pack(pady=(0,4))


def show_advanced_security():
    sec_state = state.setdefault('security_features', {
        'firewall': True,
        'virus_protection': True,
        'account_protection': True,
        'system_guard': True,
        'driver_support': True,
        'windows_repair': True,
        'terminal_support': True,
    })
    adv = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    adv.title('Advanced Settings')
    adv.geometry('520x520')
    style_aero_window(adv, '#eef4ff')
    center_window(adv, 520, 520)

    tk.Label(adv, text='Advanced Security', bg='#eef4ff', fg='#1b3866', font=('Segoe UI', 16, 'bold')).pack(pady=(16,8))
    tk.Label(adv, text='Manage protections, drivers, and system removal.', bg='#eef4ff', fg='#32517c', font=('Segoe UI', 10)).pack(pady=(0,12))

    status_frame = tk.Frame(adv, bg='#eef4ff')
    status_frame.pack(fill='x', padx=16)

    feature_labels = {}
    def refresh_security_statuses():
        for key, text in [
            ('firewall', 'Firewall'),
            ('virus_protection', 'Virus protection'),
            ('account_protection', 'Account protection'),
            ('system_guard', 'System guard'),
            ('driver_support', 'Driver support'),
        ]:
            value = 'Enabled' if sec_state.get(key) else 'Disabled'
            feature_labels[key].config(text=f'{text}: {value}')
    def toggle_feature(key):
        sec_state[key] = not sec_state.get(key, True)
        save_state()
        refresh_security_statuses()
        show_system_notification('Security', f'{key.replace("_", " ").title()} is now ' + ('enabled.' if sec_state[key] else 'disabled.'))

    for key, text in [
        ('firewall', 'Firewall'),
        ('virus_protection', 'Virus protection'),
        ('account_protection', 'Account protection'),
        ('system_guard', 'System guard'),
        ('driver_support', 'Driver support'),
    ]:
        row = tk.Frame(status_frame, bg='#eef4ff')
        row.pack(fill='x', pady=6)
        lbl = tk.Label(row, text='', bg='#eef4ff', fg='#1f4064', font=('Segoe UI', 10))
        lbl.pack(side='left')
        feature_labels[key] = lbl
        btn = tk.Button(row, text='Toggle', bg='#5b8fe2', fg='white', width=10, command=lambda k=key: toggle_feature(k))
        btn.pack(side='right')

    refresh_security_statuses()

    driver_secret = {'count': 0}
    manual_btn = tk.Button(adv, text='Manual Driver Install', bg='#3b82f6', fg='white', width=22, state='disabled', command=lambda: [install_drivers(adv), manual_btn.config(state='disabled')])
    manual_btn.pack(pady=(14,4))
    status_hint = tk.Label(adv, text='Right click the driver status below 5 times to unlock manual install.', bg='#eef4ff', fg='#556d8f', font=('Segoe UI', 9))
    status_hint.pack(pady=(0,10))
    driver_status_label = tk.Label(adv, text='Driver debug area: right-click here', bg='#e6eefc', fg='#2a4f79', font=('Segoe UI', 10), relief='groove', bd=1, padx=8, pady=8)
    driver_status_label.pack(fill='x', padx=16)

    def on_driver_right_click(event=None):
        driver_secret['count'] += 1
        remaining = max(0, 5 - driver_secret['count'])
        driver_status_label.config(text=f'Right-clicks remaining: {remaining}')
        if driver_secret['count'] >= 5:
            manual_btn.config(state='normal')
            driver_status_label.config(text='Manual driver install unlocked. Click the button below.')
    driver_status_label.bind('<Button-3>', on_driver_right_click)

    tk.Button(adv, text='Restart and show driver prompt', bg='#4b89d4', fg='white', width=24, command=restart_to_login).pack(pady=(16,4))
    tk.Button(adv, text='Delete system files', bg='#e45f5f', fg='white', width=24, command=delete_celine_system_files).pack(pady=(4,8))
    tk.Button(adv, text='Open driver manager', bg='#7da8f5', fg='white', width=24, command=lambda: prompt_driver_install_options(adv)).pack(pady=(0,12))

    tk.Label(adv, text='Warning: advanced protection toggles affect only the simulated shell environment.', bg='#eef4ff', fg='#5b5f6f', font=('Segoe UI', 9), wraplength=460, justify='left').pack(padx=16, pady=(12,0))


def install_drivers(parent=None):
    state['drivers_installed'] = True
    state['show_driver_prompt'] = False
    save_state()
    show_system_notification('Drivers', 'Drivers installed. Terminal and advanced features are now available.')
    if parent and parent.winfo_exists():
        try:
            parent.lift()
        except Exception:
            pass


def delete_celine_system_files():
    if not check_password('Confirm delete password'):
        messagebox.showwarning('Denied', 'Password required.')
        return
    if not messagebox.askyesno('Delete Windows 7', 'This will remove system files and reset Windows 7. Continue?'):
        return
    try:
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(SHUTDOWN_FLAG):
            os.remove(SHUTDOWN_FLAG)
        state['drivers_installed'] = False
        state['show_driver_prompt'] = True
        save_state()
        messagebox.showinfo('Deleted', 'System files removed. Restarting to login.')
        if desktop_win and desktop_win.winfo_exists():
            desktop_win.destroy()
        show_login(after_restart=True)
    except Exception as e:
        messagebox.showerror('Delete Failed', 'Could not delete system files: ' + str(e))


def restart_to_login():
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.destroy()
    state['show_driver_prompt'] = True
    save_state()
    show_login(after_restart=True)


def prompt_driver_install_options(parent=None):
    if parent is None:
        parent = root
    prompt = tk.Toplevel(parent)
    prompt.title('Driver Setup')
    prompt.geometry('460x260')
    style_aero_window(prompt, '#eef4ff')
    center_window(prompt, 460, 260)
    tk.Label(prompt, text='Driver Installation', bg='#eef4ff', fg='#1e456e', font=('Segoe UI', 14, 'bold')).pack(pady=(16,8))
    tk.Label(prompt, text='Choose to download drivers now or skip. Skip means terminal access is disabled until drivers are installed.', bg='#eef4ff', fg='#2d5179', font=('Segoe UI', 10), wraplength=420, justify='left').pack(padx=16, pady=(0,12))
    tk.Button(prompt, text='Download Drivers', bg='#5b8fe2', fg='white', width=18, command=lambda: [install_drivers(prompt), prompt.destroy()]).pack(pady=(0,8))
    tk.Button(prompt, text='Skip Drivers', bg='#d18f5c', fg='white', width=18, command=lambda: [state.update({'drivers_installed': False, 'show_driver_prompt': False}), save_state(), show_system_notification('Drivers', 'Drivers skipped. Terminal disabled until installed.'), prompt.destroy()]).pack(pady=(0,8))
    secret_label = tk.Label(prompt, text='Right-click here 5 times for manual install unlock.', bg='#dde8ff', fg='#1d3d6d', font=('Segoe UI', 9), relief='groove', bd=1, padx=8, pady=8)
    secret_label.pack(fill='x', padx=16, pady=(10,0))
    hidden = {'count': 0}
    manual_button = tk.Button(prompt, text='Manual Driver Install', bg='#3b82f6', fg='white', width=18, state='disabled', command=lambda: [install_drivers(prompt), prompt.destroy()])
    manual_button.pack(pady=(8,0))
    def on_secret_click(event=None):
        hidden['count'] += 1
        remaining = max(0, 5 - hidden['count'])
        secret_label.config(text=f'Right-clicks remaining: {remaining}')
        if hidden['count'] >= 5:
            manual_button.config(state='normal')
            secret_label.config(text='Manual install unlocked. Click the button below.')
    secret_label.bind('<Button-3>', on_secret_click)

def show_minesweeper_game():
    if not check_drivers("Minesweeper"):
        return

    game_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    game_win.title('Minesweeper')
    game_win.geometry('360x420')
    style_aero_window(game_win, '#eef5ff')
    center_window(game_win, 360, 420)
    tk.Label(game_win, text='Minesweeper', bg='#eef5ff', fg='#19386d', font=('Segoe UI', 14, 'bold')).pack(pady=10)
    mines = set(random.sample(range(16), 4))
    buttons = []
    board_values = [0] * 16
    for idx in range(16):
        if idx in mines:
            board_values[idx] = -1
        else:
            board_values[idx] = sum((neighbor in mines) for neighbor in [idx-1, idx+1, idx-4, idx+4] if 0 <= neighbor < 16 and (idx%4 != 0 or neighbor != idx-1) and (idx%4 != 3 or neighbor != idx+1))
    def reveal(i):
        if board_values[i] == -1:
            buttons[i].config(text='💣', bg='#f7d7d7')
            tk.messagebox.showinfo('Minesweeper', 'Boom! Game over.')
            return
        buttons[i].config(text=str(board_values[i]) if board_values[i] else '', bg='#dbe7ff', state='disabled')
    grid = tk.Frame(game_win, bg='#eef5ff')
    grid.pack()
    for i in range(16):
        btn = tk.Button(grid, text='', width=6, height=3, bg='#dde9ff', command=lambda i=i: reveal(i))
        btn.grid(row=i//4, column=i%4, padx=3, pady=3)
        buttons.append(btn)
    tk.Button(game_win, text='Restart', bg='#5b8fe2', fg='white', command=lambda: [game_win.destroy(), show_minesweeper_game()]).pack(pady=12)

def show_guess_number_game():
    game_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    game_win.title('Guess the Number')
    game_win.geometry('360x280')
    style_aero_window(game_win, '#eef5ff')
    center_window(game_win, 360, 280)
    tk.Label(game_win, text='Guess the Number', bg='#eef5ff', fg='#19386d', font=('Segoe UI', 14, 'bold')).pack(pady=10)
    target = random.randint(1, 30)
    result = tk.Label(game_win, text='Pick a number 1-30', bg='#eef5ff', fg='#2d4a7d')
    result.pack(pady=6)
    guess_var = tk.StringVar()
    tk.Entry(game_win, textvariable=guess_var, width=18).pack(pady=4)
    def check_guess():
        try:
            guess = int(guess_var.get())
        except ValueError:
            result.config(text='Enter a number.')
            return
        if guess < target:
            result.config(text='Too low. Try again.')
        elif guess > target:
            result.config(text='Too high. Try again.')
        else:
            result.config(text='Correct! Nice job.')
    tk.Button(game_win, text='Guess', bg='#5b8fe2', fg='white', command=check_guess).pack(pady=8)
    tk.Button(game_win, text='New Game', bg='#5b8fe2', fg='white', command=lambda: [game_win.destroy(), show_guess_number_game()]).pack(pady=4)


def show_snake_game():
    snake_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    snake_win.title('Snake')
    snake_win.geometry('380x420')
    style_aero_window(snake_win, '#eef5ff')
    center_window(snake_win, 380, 420)
    tk.Label(snake_win, text='Snake', bg='#eef5ff', fg='#19386d', font=('Segoe UI', 14, 'bold')).pack(pady=10)

    canvas = tk.Canvas(snake_win, width=340, height=300, bg='#e8f0ff', highlightthickness=0)
    canvas.pack(pady=10)
    score_label = tk.Label(snake_win, text='Score: 0', bg='#eef5ff', fg='#1f3c6b', font=('Segoe UI', 10, 'bold'))
    score_label.pack()

    cell_size = 16
    cols = 20
    rows = 16
    snake = [(10, 8), (9, 8), (8, 8)]
    direction = 'Right'
    food = (random.randint(1, cols-2), random.randint(1, rows-2))
    score = 0

    def draw():
        canvas.delete('all')
        canvas.create_rectangle(2, 2, cols*cell_size+2, rows*cell_size+2, outline='#6a8bc7')
        for x, y in snake:
            canvas.create_rectangle(x*cell_size, y*cell_size, x*cell_size+cell_size, y*cell_size+cell_size, fill='#4f76d5')
        canvas.create_oval(food[0]*cell_size+2, food[1]*cell_size+2, food[0]*cell_size+cell_size-2, food[1]*cell_size+cell_size-2, fill='#d95757')

    def move_snake():
        nonlocal snake, food, direction, score
        head = snake[0]
        delta = {
            'Up': (0, -1), 'Down': (0, 1), 'Left': (-1, 0), 'Right': (1, 0)
        }[direction]
        new_head = (head[0] + delta[0], head[1] + delta[1])
        if new_head[0] < 0 or new_head[0] >= cols or new_head[1] < 0 or new_head[1] >= rows or new_head in snake:
            messagebox.showinfo('Snake', f'Game Over! Score: {score}')
            snake_win.destroy()
            return
        snake = [new_head] + snake
        if new_head == food:
            score += 1
            score_label.config(text=f'Score: {score}')
            food = (random.randint(1, cols-2), random.randint(1, rows-2))
            while food in snake:
                food = (random.randint(1, cols-2), random.randint(1, rows-2))
        else:
            snake.pop()
        draw()
        snake_win.after(150, move_snake)

    def change_direction(event):
        nonlocal direction
        if event.keysym in ['Up', 'Down', 'Left', 'Right']:
            new_dir = event.keysym
            opposites = {'Up':'Down','Down':'Up','Left':'Right','Right':'Left'}
            if opposites[new_dir] != direction:
                direction = new_dir

    snake_win.bind('<Key>', change_direction)
    snake_win.focus_set()
    draw()
    snake_win.after(150, move_snake)


def show_sticky_notes():
    notes_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    notes_win.title('Sticky Notes')
    notes_win.geometry('400x360')
    style_aero_window(notes_win, '#fff8dc')
    center_window(notes_win, 400, 360)
    tk.Label(notes_win, text='Sticky Notes', bg='#fff8dc', fg='#5a4f2f', font=('Segoe UI', 14, 'bold')).pack(pady=10)

    text = tk.Text(notes_win, bg='white', fg='#2b2b2b', font=('Segoe UI', 10), wrap='word')
    text.pack(fill='both', expand=True, padx=12, pady=8)
    text.insert('1.0', state.get('sticky_notes', 'Type your notes here...'))

    def save_notes():
        state['sticky_notes'] = text.get('1.0', 'end').strip()
        save_state()
        show_system_notification('Sticky Notes', 'Notes saved successfully.')

    tk.Button(notes_win, text='Save Note', bg='#d17638', fg='white', command=save_notes).pack(pady=6)


def show_calendar_app():
    """Full interactive Windows 7 style calendar with clickable days, events, and navigation."""
    cal_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    cal_win.title('Windows Calendar')
    cal_win.geometry('620x540')
    style_aero_window(cal_win, '#f0f6ff')
    center_window(cal_win, 620, 540)

    CAL_BG   = '#f0f6ff'
    HDR_BG   = '#1e4a8a'
    DAY_BG   = '#ffffff'
    SEL_BG   = '#cce0ff'
    WKD_FG   = '#c04040'
    TODAY_BG = '#ddeeff'

    cur = {'year': datetime.now().year, 'month': datetime.now().month}
    selected_day = {'day': None}
    events = state.setdefault('calendar_events', {})

    # ── top toolbar ──────────────────────────────────────────────────────
    top = tk.Frame(cal_win, bg=HDR_BG, height=50)
    top.pack(fill='x')
    top.pack_propagate(False)

    prev_btn = tk.Button(top, text='◀', bg=HDR_BG, fg='white', relief='flat',
                         font=('Segoe UI', 14, 'bold'), activebackground='#2a6ab8',
                         cursor='hand2', bd=0)
    prev_btn.pack(side='left', padx=12, pady=8)

    month_lbl = tk.Label(top, text='', bg=HDR_BG, fg='white', font=('Segoe UI', 14, 'bold'))
    month_lbl.pack(side='left', expand=True)

    next_btn = tk.Button(top, text='▶', bg=HDR_BG, fg='white', relief='flat',
                         font=('Segoe UI', 14, 'bold'), activebackground='#2a6ab8',
                         cursor='hand2', bd=0)
    next_btn.pack(side='right', padx=12, pady=8)

    today_btn = tk.Button(top, text='Today', bg='#2a6ab8', fg='white',
                          relief='flat', font=('Segoe UI', 9), cursor='hand2',
                          activebackground='#3a7ac8', padx=10)
    today_btn.pack(side='right', padx=6, pady=12)

    # ── main area: grid left, event panel right ───────────────────────
    main = tk.Frame(cal_win, bg=CAL_BG)
    main.pack(fill='both', expand=True)

    left = tk.Frame(main, bg=CAL_BG)
    left.pack(side='left', fill='both', expand=True)

    right = tk.Frame(main, bg='#e8f0fc', width=160)
    right.pack(side='right', fill='y')
    right.pack_propagate(False)

    tk.Label(right, text='Events', bg='#e8f0fc', fg='#1e4a8a',
             font=('Segoe UI', 10, 'bold')).pack(pady=(10,4), padx=8, anchor='w')
    event_list = tk.Listbox(right, bg='white', fg='#1a3a6a', font=('Segoe UI', 8),
                             relief='flat', bd=0, highlightthickness=0, height=18)
    event_list.pack(fill='both', expand=True, padx=6, pady=(0,4))

    add_event_e = tk.Entry(right, font=('Segoe UI', 8), bg='#dce8fc',
                            relief='flat', highlightthickness=1,
                            highlightbackground='#3a80c8')
    add_event_e.pack(fill='x', padx=6, pady=2)

    def add_event_for_day():
        day = selected_day.get('day')
        if not day:
            messagebox.showinfo('Calendar', 'Click a day first.')
            return
        text = add_event_e.get().strip()
        if not text:
            return
        key = f"{cur['year']}-{cur['month']:02d}-{day:02d}"
        events.setdefault(key, []).append(text)
        save_state()
        add_event_e.delete(0, 'end')
        refresh_events(key)

    tk.Button(right, text='+ Add Event', bg='#2a6ab8', fg='white',
              relief='flat', font=('Segoe UI', 8), cursor='hand2',
              command=add_event_for_day).pack(fill='x', padx=6, pady=(0,6))

    # ── day-name header row ───────────────────────────────────────────
    day_hdr = tk.Frame(left, bg='#d0e0f4')
    day_hdr.pack(fill='x', padx=2)
    for i, d in enumerate(['Mon','Tue','Wed','Thu','Fri','Sat','Sun']):
        fg = WKD_FG if i >= 5 else '#1e4a8a'
        tk.Label(day_hdr, text=d, bg='#d0e0f4', fg=fg,
                 font=('Segoe UI', 9, 'bold'), width=7, anchor='center').pack(side='left', expand=True)

    # ── grid canvas ───────────────────────────────────────────────────
    grid_frame = tk.Frame(left, bg=CAL_BG)
    grid_frame.pack(fill='both', expand=True, padx=2, pady=2)

    day_cells = {}   # day_number -> (frame, lbl)

    def refresh_events(key=None):
        event_list.delete(0, 'end')
        day = selected_day.get('day')
        if not day:
            return
        k = f"{cur['year']}-{cur['month']:02d}-{day:02d}"
        for ev in events.get(k, []):
            event_list.insert('end', ev)

    def build_grid():
        for w in grid_frame.winfo_children():
            w.destroy()
        day_cells.clear()

        y, m = cur['year'], cur['month']
        month_lbl.config(text=f"{datetime(y, m, 1).strftime('%B')} {y}")

        cal_matrix = calendar.monthcalendar(y, m)
        today = datetime.now()

        for week in cal_matrix:
            row = tk.Frame(grid_frame, bg=CAL_BG)
            row.pack(fill='both', expand=True, pady=1)
            for col_i, day_n in enumerate(week):
                cell = tk.Frame(row, bg=DAY_BG, relief='solid', bd=1,
                                highlightthickness=0, cursor='hand2' if day_n else 'arrow')
                cell.pack(side='left', fill='both', expand=True, padx=1)

                if day_n == 0:
                    cell.config(bg='#e8eef8', relief='flat', cursor='arrow')
                    tk.Label(cell, text='', bg='#e8eef8').pack()
                    continue

                is_today = (day_n == today.day and m == today.month and y == today.year)
                is_sel   = (day_n == selected_day.get('day'))
                has_ev   = bool(events.get(f"{y}-{m:02d}-{day_n:02d}"))
                is_wkd   = col_i >= 5

                bg = SEL_BG if is_sel else (TODAY_BG if is_today else DAY_BG)
                fg = WKD_FG if is_wkd else ('#1e4a8a' if is_today else '#1a1a2e')
                cell.config(bg=bg)

                num_lbl = tk.Label(cell, text=str(day_n), bg=bg, fg=fg,
                                   font=('Segoe UI', 10, 'bold' if is_today else 'normal'),
                                   anchor='nw', padx=4, pady=2)
                num_lbl.pack(anchor='nw')

                if has_ev:
                    dot = tk.Label(cell, text='●', bg=bg, fg='#2060c8',
                                   font=('Segoe UI', 6))
                    dot.pack(anchor='sw', padx=4)

                day_cells[day_n] = (cell, num_lbl)

                def _click(d=day_n, c=cell, nl=num_lbl):
                    selected_day['day'] = d
                    refresh_events()
                    build_grid()

                cell.bind('<Button-1>', lambda e, fn=_click: fn())
                num_lbl.bind('<Button-1>', lambda e, fn=_click: fn())

    def prev_month():
        if cur['month'] == 1:
            cur['year'] -= 1; cur['month'] = 12
        else:
            cur['month'] -= 1
        selected_day['day'] = None
        build_grid()

    def next_month():
        if cur['month'] == 12:
            cur['year'] += 1; cur['month'] = 1
        else:
            cur['month'] += 1
        selected_day['day'] = None
        build_grid()

    def go_today():
        now2 = datetime.now()
        cur['year'] = now2.year; cur['month'] = now2.month
        selected_day['day'] = now2.day
        build_grid(); refresh_events()

    prev_btn.config(command=prev_month)
    next_btn.config(command=next_month)
    today_btn.config(command=go_today)
    build_grid()

    # ── bottom toolbar ────────────────────────────────────────────────
    bot = tk.Frame(cal_win, bg='#d0e0f4', height=32)
    bot.pack(fill='x')
    tk.Button(bot, text='🕐 Taskbar Clock', bg='#2a6ab8', fg='white',
              relief='flat', font=('Segoe UI', 8), cursor='hand2',
              command=show_taskbar_time_overlay).pack(side='left', padx=8, pady=4)
    tk.Label(bot, text='Click a day to select  |  ● = has events',
             bg='#d0e0f4', fg='#3a6aa0', font=('Segoe UI', 8)).pack(side='right', padx=10)


def show_update_loading(on_done=None):
    if not desktop_win or not desktop_win.winfo_exists():
        return
    loading = tk.Toplevel(desktop_win)
    loading.overrideredirect(True)
    loading.attributes('-topmost', True)
    style_aero_window(loading, '#eef4ff')
    center_window(loading, 380, 160)
    tk.Label(loading, text='Installing Windows 7 update...', bg='#eef4ff', fg='#2f4f83', font=('Segoe UI', 13, 'bold')).pack(pady=(20,6))
    progress = tk.Label(loading, text='Preparing files...', bg='#eef4ff', fg='#4a5f88', font=('Segoe UI', 10))
    progress.pack()

    def finish():
        progress.config(text='Boom! Update complete.')
        loading.after(900, lambda: [loading.destroy(), show_system_notification('Update installed', 'Security and personalization refreshed.'), on_done() if on_done else None])

    loading.after(1600, finish)


def hash_product_key(key):
    return hashlib.sha256(key.encode('utf-8')).hexdigest()


def verify_product_key(key, product_hash):
    if not product_hash:
        return False
    return hash_product_key(key) == product_hash


def create_product_key():
    if not check_password('Confirm current password'):
        messagebox.showwarning('Denied', 'Password required.')
        return
    key = simpledialog.askstring('Product Key', 'Create a product key to reactivate Windows 7 later:')
    if not key:
        return
    sec = load_security()
    sec['product_hash'] = hash_product_key(key)
    save_security(sec)
    messagebox.showinfo('Product Key', 'Your product key has been saved. Use it if you reinstall or reactivate Windows 7.')


def uninstall_celine():
    if not check_password('Confirm uninstall password'):
        messagebox.showwarning('Denied', 'Password required.')
        return
    key = simpledialog.askstring('Product Key', 'Create a product key to reactivate Windows 7 later:')
    if not key:
        return
    sec = load_security()
    sec['product_hash'] = hash_product_key(key)
    sec['locked'] = True
    save_security(sec)
    messagebox.showinfo('Uninstall', 'Windows 7 has been uninstalled. Use your product key to reactivate.')
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.destroy()
    show_login()


def load_wallpaper_image(path):
    global desktop_wallpaper_image
    if not os.path.exists(path):
        return None
    if Image and ImageTk:
        try:
            img = Image.open(path)
            screen_w = desktop_win.winfo_width() if desktop_win else 960
            screen_h = desktop_win.winfo_height() if desktop_win else 720
            if screen_w <= 1 or screen_h <= 1:
                screen_w, screen_h = 960, 720
            img = img.resize((screen_w, screen_h), Image.LANCZOS)
            desktop_wallpaper_image = ImageTk.PhotoImage(img)
            return desktop_wallpaper_image
        except Exception:
            pass
    try:
        desktop_wallpaper_image = tk.PhotoImage(file=path)
        return desktop_wallpaper_image
    except Exception:
        return None


def set_wallpaper(path):
    global desktop_bg_label
    if not desktop_bg_label:
        return
    img = load_wallpaper_image(path)
    if img:
        desktop_bg_label.config(image=img, bg='#0f1733', text='')
        desktop_bg_label.image = img
        state['wallpaper'] = path
        save_state()
    else:
        desktop_bg_label.config(image='', bg='#0f1733', text='Wallpaper not supported', fg='white')
        state['wallpaper'] = ''
        save_state()


def choose_wallpaper():
    if not state.get('activated', False):
        _require_activation('Personalization (Change Wallpaper)')
        return
    v = state.get('os_version', 'Ultimate')
    if v == 'Starter':
        messagebox.showerror("Personalization", "Windows 7 Starter does not support changing wallpapers.")
        return

    path = filedialog.askopenfilename(title='Select Wallpaper', filetypes=[('Images', '*.png *.gif *.jpg *.jpeg *.bmp')])
    if path:
        set_wallpaper(path)


def run_terminal_command():
    global desktop_term_output, desktop_term_entry
    if not desktop_term_entry or not desktop_term_output:
        return
    command = desktop_term_entry.get().strip()
    if not command:
        return
    if command.lower() == 'print hello world':
        desktop_term_output.insert('end', 'hello world\n')
    elif command.lower() == 'print hi world':
        desktop_term_output.insert('end', 'Hi world\n')
    else:
        desktop_term_output.insert('end', f'Unknown command: {command}\n')
    desktop_term_output.see('end')
    desktop_term_entry.delete(0, 'end')


def show_ai_app():
    global desktop_win, root
    if desktop_win:
        try:
            desktop_win.withdraw()
        except Exception:
            pass
    try:
        style_aero_window(root, '#eef4ff')
        root.deiconify()
        root.attributes('-alpha', 0.97)
    except Exception:
        pass


def on_close_ai():
    global desktop_win, root
    try:
        root.withdraw()
    except Exception:
        pass
    if desktop_win:
        try:
            desktop_win.deiconify()
        except Exception:
            pass


def show_jump_list(event, actions):
    menu = tk.Menu(None, tearoff=0)
    for label, callback in actions:
        menu.add_command(label=label, command=callback)
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


def create_taskbar_icon(parent, icon_text, tooltip, action, jump_actions):
    btn = tk.Label(parent, text=icon_text, bg='#cfe4ff', fg='#18325a', width=6, height=2, bd=0, relief='flat', font=('Segoe UI', 10, 'bold'))
    btn.bind('<Button-1>', lambda e: action())
    if jump_actions:
        btn.bind('<Button-3>', lambda e: show_jump_list(e, jump_actions))
    return btn


def start_aero_peek(event=None):
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.attributes('-alpha', 0.55)


def stop_aero_peek(event=None):
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.attributes('-alpha', 0.94)


def snap_desktop_left():
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.geometry('480x720+0+0')


def snap_desktop_right():
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.geometry('480x720+480+0')


def aero_shake():
    if root.winfo_exists():
        root.withdraw()
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.lift()


def show_system_monitor():
    """Real-time system performance monitoring (CPU, Memory, Disk)"""
    if not psutil:
        messagebox.showerror('Error', 'psutil not available')
        return
    
    mon = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    mon.title('System Monitor')
    mon.geometry('480x380')
    style_aero_window(mon, '#f4f7ff')
    center_window(mon, 480, 380) # type: ignore
    center_window(mon, 480, 380)
    
    tk.Label(mon, text='Performance Monitor', bg='#f4f7ff', fg='#1e446d', font=('Segoe UI', 14, 'bold')).pack(pady=(12,8))
    
    frame = tk.Frame(mon, bg='#f4f7ff')
    frame.pack(fill='both', expand=True, padx=16, pady=8)
    
    labels = {}
    metrics = [
        ('CPU Usage', 'cpu'),
        ('Memory Usage', 'memory'),
        ('Disk Usage', 'disk'),
        ('Boot Time', 'boot'),
        ('Process Count', 'processes'),
        ('Network I/O', 'network')
    ]
    
    def update_metrics():
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            boot = datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M')
            proc = len(psutil.pids())
            net = psutil.net_io_counters()
            
            labels['cpu'].config(text=f'CPU Usage: {cpu}%')
            labels['memory'].config(text=f'Memory Usage: {mem:.1f}%')
            labels['disk'].config(text=f'Disk Usage: {disk:.1f}%')
            labels['boot'].config(text=f'Boot Time: {boot}')
            labels['processes'].config(text=f'Processes: {proc}')
            labels['network'].config(text=f'Sent: {net.bytes_sent/(1024**3):.2f}GB | Recv: {net.bytes_recv/(1024**3):.2f}GB')
            
            mon.after(2000, update_metrics)
        except Exception as e:
            labels['cpu'].config(text=f'Error: {str(e)[:40]}')
    
    for metric_name, key in metrics:
        lbl = tk.Label(frame, text=f'{metric_name}: Loading...', bg='#f4f7ff', fg='#233e67', font=('Segoe UI', 10))
        lbl.pack(anchor='w', pady=6)
        labels[key] = lbl
    
    tk.Button(mon, text='Refresh Now', bg='#5b8fe2', fg='white', command=update_metrics).pack(pady=12)
    update_metrics()

def show_task_manager():
    """Show running processes and system tasks"""
    if not psutil:
        messagebox.showerror('Error', 'psutil not available')
        return
    
    tm = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    tm.title('Task Manager')
    tm.geometry('600x450')
    style_aero_window(tm, '#f4f7ff')
    center_window(tm, 600, 450)
    
    tk.Label(tm, text='Task Manager - Running Processes', bg='#f4f7ff', fg='#1e446d', font=('Segoe UI', 12, 'bold')).pack(pady=(12,8))
    
    frame = tk.Frame(tm, bg='#f4f7ff')
    frame.pack(fill='both', expand=True, padx=12, pady=8)
    
    # Create treeview for processes
    tree = ttk.Treeview(frame, columns=('PID', 'Memory', 'CPU'), height=15)
    tree.heading('#0', text='Process Name')
    tree.heading('PID', text='PID')
    tree.heading('Memory', text='Memory (MB)')
    tree.heading('CPU', text='CPU %')
    tree.column('#0', width=280)
    tree.column('PID', width=80)
    tree.column('Memory', width=100)
    tree.column('CPU', width=80)
    
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    
    def refresh_processes():
        for item in tree.get_children():
            tree.delete(item)
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    info = proc.info
                    tree.insert('', 'end', text=info['name'][:35], values=(
                        info['pid'],
                        f"{info['memory_percent']:.1f}" if info['memory_percent'] else '0',
                        f"{info['cpu_percent']:.1f}" if info['cpu_percent'] else '0'
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            messagebox.showerror('Error', f'Could not read processes: {e}')
    
    def end_task():
        selection = tree.selection()
        if not selection:
            messagebox.showinfo('Task Manager', 'Select a process first.')
            return
        item = selection[0]
        pid = int(tree.item(item)['values'][0])
        try:
            p = psutil.Process(pid)
            p.terminate()
            messagebox.showinfo('Task Manager', f'Process {p.name()} terminated.')
            refresh_processes()
        except Exception as e:
            messagebox.showerror('Error', str(e))
    
    btn_frame = tk.Frame(tm, bg='#f4f7ff')
    btn_frame.pack(fill='x', padx=12, pady=(8,12))
    tk.Button(btn_frame, text='Refresh', bg='#5b8fe2', fg='white', command=refresh_processes).pack(side='left', padx=4)
    tk.Button(btn_frame, text='End Task', bg='#d85c4c', fg='white', command=end_task).pack(side='left', padx=4)
    
    refresh_processes()

def show_themes():
    """Theme and appearance selector"""
    theme_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    theme_win.title('Personalization')
    theme_win.geometry('480x380')
    style_aero_window(theme_win, '#f4f7ff')
    center_window(theme_win, 480, 380)
    
    tk.Label(theme_win, text='Themes & Appearance', bg='#f4f7ff', fg='#1e446d', font=('Segoe UI', 14, 'bold')).pack(pady=(12,8))
    
    themes = {
        'Windows 7 Aero': {'bg': '#f4f7ff', 'accent': '#5b8fe2'},
        'Dark Mode': {'bg': '#1e1e1e', 'accent': '#0078d4'},
        'Light Blue': {'bg': '#e3f2fd', 'accent': '#2196f3'},
        'Green': {'bg': '#e8f5e9', 'accent': '#4caf50'},
    }
    
    content = tk.Frame(theme_win, bg='#f4f7ff')
    content.pack(fill='both', expand=True, padx=16, pady=12)
    
    def apply_theme(theme_name):
        theme = themes[theme_name]
        messagebox.showinfo('Theme', f'Theme "{theme_name}" applied! (preview)')
        # In full implementation, this would change the entire app theme
    
    for i, theme_name in enumerate(themes.keys()):
        theme = themes[theme_name]
        preview = tk.Frame(content, bg=theme['bg'], height=60, relief='sunken', bd=2)
        preview.pack(fill='x', pady=8)
        
        txt = tk.Label(preview, text=theme_name, bg=theme['bg'], fg=theme['accent'], font=('Segoe UI', 11, 'bold'))
        txt.pack(expand=True)
        
        btn = tk.Button(content, text=f'Apply "{theme_name}"', bg=theme['accent'], fg='white', 
                       command=lambda t=theme_name: apply_theme(t))
        btn.pack(fill='x', pady=4)
    
    tk.Label(theme_win, text='Themes customize the entire desktop appearance.', bg='#f4f7ff', 
            fg='#5f7a99', font=('Segoe UI', 9, 'italic')).pack(pady=(12,0))

def show_volume_control():
    """Volume and sound control"""
    vol_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    vol_win.title('Volume Mixer')
    vol_win.geometry('420x320')
    style_aero_window(vol_win, '#f4f7ff')
    center_window(vol_win, 420, 320)
    
    tk.Label(vol_win, text='Volume & Sound Control', bg='#f4f7ff', fg='#1e446d', font=('Segoe UI', 13, 'bold')).pack(pady=(12,8))
    
    frame = tk.Frame(vol_win, bg='#f4f7ff')
    frame.pack(fill='both', expand=True, padx=16, pady=12)
    
    # Master Volume
    tk.Label(frame, text='Master Volume', bg='#f4f7ff', fg='#233e67', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
    master_scale = tk.Scale(frame, from_=0, to=100, orient='horizontal', bg='#e8eef8', fg='#5b8fe2', length=300)
    master_scale.set(state.get('volume', 55))
    master_scale.pack(fill='x', pady=(4,12))
    
    # Sound devices
    tk.Label(frame, text='Audio Devices', bg='#f4f7ff', fg='#233e67', font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(8,4))
    
    devices = ['Speakers (Default)', 'Headphones', 'HDMI Audio', 'Microphone']
    device_var = tk.StringVar(value=devices[0])
    
    for device in devices:
        rb = tk.Radiobutton(frame, text=device, variable=device_var, value=device, bg='#f4f7ff', fg='#233e67')
        rb.pack(anchor='w', pady=2)
    
    # Sound effects
    tk.Label(frame, text='Sound Effects', bg='#f4f7ff', fg='#233e67', font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(12,4))
    
    effect_var = tk.BooleanVar(value=True)
    tk.Checkbutton(frame, text='Enable Sound Effects', variable=effect_var, bg='#f4f7ff', fg='#233e67').pack(anchor='w')
    tk.Checkbutton(frame, text='Enable Volume Change Beep', bg='#f4f7ff', fg='#233e67').pack(anchor='w', pady=2)
    
    def save_volume():
        state['volume'] = master_scale.get()
        save_state()
        messagebox.showinfo('Volume', f'Volume set to {master_scale.get()}%\nDevice: {device_var.get()}')
    
    tk.Button(vol_win, text='Apply', bg='#5b8fe2', fg='white', command=save_volume).pack(pady=12)

def show_disk_cleaner():
    """Disk cleanup and space management tool"""
    clean_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    clean_win.title('Disk Cleanup')
    clean_win.geometry('500x420')
    style_aero_window(clean_win, '#f4f7ff')
    center_window(clean_win, 500, 420)
    
    tk.Label(clean_win, text='Disk Cleanup & Storage Management', bg='#f4f7ff', fg='#1e446d', font=('Segoe UI', 13, 'bold')).pack(pady=(12,8))
    
    frame = tk.Frame(clean_win, bg='#f4f7ff')
    frame.pack(fill='both', expand=True, padx=16, pady=12)
    
    items = [
        ('Temporary Files', True, 127),
        ('Recycle Bin', True, 45),
        ('Cache Files', True, 203),
        ('Log Files', False, 87),
        ('Old Backups', False, 1240),
    ]
    
    vars_dict = {}
    total_size = 0
    
    tk.Label(frame, text='Select items to remove:', bg='#f4f7ff', fg='#233e67', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0,8))
    
    for item_name, default, size_mb in items:
        var = tk.BooleanVar(value=default)
        vars_dict[item_name] = (var, size_mb)
        total_size += size_mb
        
        chk = tk.Checkbutton(frame, text=f'{item_name} ({size_mb} MB)', variable=var, bg='#f4f7ff', fg='#233e67')
        chk.pack(anchor='w', pady=3)
    
    tk.Label(frame, text=f'\nTotal disk space available: ~500 GB', bg='#f4f7ff', fg='#5f7a99', font=('Segoe UI', 9)).pack(anchor='w', pady=(8,0))
    
    selected_label = tk.Label(frame, text=f'Selected for removal: 0 MB', bg='#f4f7ff', fg='#233e67', font=('Segoe UI', 9, 'bold'))
    selected_label.pack(anchor='w', pady=(4,0))
    
    def update_selected():
        total = sum(size for var, size in vars_dict.values() if var.get())
        selected_label.config(text=f'Selected for removal: {total} MB')
    
    for var, _ in vars_dict.values():
        var.trace_add('write', lambda *args: update_selected())
    
    def run_cleanup():
        total = sum(size for var, size in vars_dict.values() if var.get())
        if total == 0:
            messagebox.showinfo('Cleanup', 'No items selected.')
            return
        messagebox.showinfo('Cleanup Complete', f'Cleaned {total} MB of disk space.\nDisk cleanup completed successfully!')
        update_selected()
    
    btn_frame = tk.Frame(clean_win, bg='#f4f7ff')
    btn_frame.pack(fill='x', padx=0, pady=(12,0))
    tk.Button(btn_frame, text='Clean Now', bg='#5b8fe2', fg='white', width=20, command=run_cleanup).pack(side='left', padx=4, pady=4)
    tk.Button(btn_frame, text='Cancel', bg='#999999', fg='white', width=20).pack(side='right', padx=4, pady=4)

def show_desktop_context_menu(event):
    """Right-click desktop context menu — full Windows-style with New submenu."""
    if not desktop_win or not desktop_win.winfo_exists():
        return
    # BIOS stability check — if system_stability is set to Unstable by BIOS, glitch the menu
    bs = state.get('bios_settings', {})
    stability = bs.get('system_stability', 'Stable')

    menu = tk.Menu(desktop_win, tearoff=0,
                   bg='#1f3b5c', fg='white',
                   activebackground='#4a90d9',
                   activeforeground='white',
                   font=('Segoe UI', 9),
                   bd=1, relief='flat')

    # ── New submenu ──────────────────────────────────────────────────────────
    new_menu = tk.Menu(menu, tearoff=0, bg='#1f3b5c', fg='white',
                       activebackground='#4a90d9', font=('Segoe UI', 9))

    _desktop_virtual_fs = state.setdefault('desktop_files', [])

    def new_folder():
        name = simpledialog.askstring('New Folder', 'Folder name:', initialvalue='New Folder')
        if name:
            _desktop_virtual_fs.append({'type': 'folder', 'name': name, 'created': datetime.now().isoformat()})
            state['desktop_files'] = _desktop_virtual_fs
            save_state()
            show_system_notification('Desktop', f'📁 Folder created: {name}')
            _refresh_desktop_files()

    def new_file(ftype, ext, icon):
        name = simpledialog.askstring('New File', f'File name (without extension):', initialvalue=f'New {ftype}')
        if name:
            full = f'{name}.{ext}'
            _desktop_virtual_fs.append({'type': ftype, 'name': full, 'ext': ext, 'icon': icon, 'created': datetime.now().isoformat()})
            state['desktop_files'] = _desktop_virtual_fs
            save_state()
            show_system_notification('Desktop', f'{icon} Created: {full}')
            _refresh_desktop_files()

    new_menu.add_command(label='📁  Folder',             command=new_folder)
    new_menu.add_separator()
    new_menu.add_command(label='📝  Word Document',      command=lambda: new_file('Word', 'docx', '📝'))
    new_menu.add_command(label='📊  Excel Spreadsheet',  command=lambda: new_file('Excel', 'xlsx', '📊'))
    new_menu.add_command(label='📄  Text File',          command=lambda: new_file('Text', 'txt', '📄'))
    new_menu.add_command(label='🖼  Bitmap Image',       command=lambda: new_file('Image', 'bmp', '🖼'))
    new_menu.add_command(label='🗜  Compressed (ZIP)',   command=lambda: new_file('Archive', 'zip', '🗜'))
    new_menu.add_command(label='🐍  Python Script',      command=lambda: new_file('Script', 'py', '🐍'))
    new_menu.add_command(label='📋  Shortcut',          command=lambda: new_file('Shortcut', 'lnk', '📋'))

    menu.add_cascade(label='📂  New ▶', menu=new_menu)
    menu.add_separator()
    menu.add_command(label='🔄  Refresh',
                     command=lambda: show_system_notification('Desktop', 'Desktop refreshed.'))
    menu.add_command(label='📌  New Sticky Note',    command=show_sticky_notes)
    menu.add_separator()
    menu.add_command(label='💻  Open Terminal',      command=show_terminal_app)
    menu.add_command(label='📁  File Explorer',      command=show_file_explorer)
    menu.add_command(label='⚙️   Settings',           command=show_settings_app)
    menu.add_command(label='🎨  Personalize',        command=choose_wallpaper)
    menu.add_separator()
    menu.add_command(label='🖥️   Show Desktop',
                     command=lambda: desktop_win.lift())
    menu.add_command(label='🛡️   Windows Security',  command=show_windows_security)
    menu.add_command(label='📊  Task Manager',       command=show_task_manager)
    menu.add_separator()
    menu.add_command(label='✨  Open Assistant',     command=show_ai_app)
    menu.add_command(label='🔍  Screen Magnifier',   command=show_screen_magnifier)
    menu.add_command(label='📌  App Pinboard',       command=show_app_pinboard)
    menu.add_separator()
    # BIOS stability indicator in menu
    stab_color = '🟢' if stability == 'Stable' else ('🟡' if stability == 'Degraded' else '🔴')
    menu.add_command(label=f'{stab_color}  System: {stability}   [BIOS]',
                     command=lambda: show_system_notification('BIOS', f'System stability: {stability}'))
    menu.tk_popup(event.x_root, event.y_root)


def _refresh_desktop_files():
    """Show virtual desktop files as icons."""
    if not desktop_win or not desktop_win.winfo_exists():
        return
    # Remove old file icons (tagged with 'desktop_file')
    for w in desktop_win.winfo_children():
        if getattr(w, '_is_desktop_file', False):
            try: w.destroy()
            except: pass
    # Re-place file icons across top-center area
    files = state.get('desktop_files', [])
    for idx, f in enumerate(files):
        x = 220 + (idx % 8) * 88
        y = 60 + (idx // 8) * 90
        icon = f.get('icon', '📄') if f.get('type') != 'folder' else '📁'
        name = f.get('name', 'File')[:14]
        ftype = f.get('type', 'file')

        frame = tk.Frame(desktop_win, bg='#4a7eb5', width=76, height=88, cursor='hand2')
        frame.place(x=x, y=y)
        frame.pack_propagate(False)
        frame._is_desktop_file = True

        cv = tk.Canvas(frame, width=56, height=56, bg='#4a7eb5', highlightthickness=0)
        cv.pack(pady=(4,0))
        cv.create_text(28, 28, text=icon, font=('Segoe UI Emoji', 26))
        tk.Label(frame, text=name, bg='#4a7eb5', fg='white',
                 font=('Segoe UI', 7), wraplength=74, justify='center').pack()

        def open_file(ft=ftype, fn=f.get('name',''), fi=icon):
            if ft == 'folder':
                show_file_explorer()
            elif ft in ('Word', 'Text'):
                show_word_processor()
            elif ft == 'Excel':
                show_excel_app()
            elif ft == 'Script':
                show_text_editor()
            else:
                show_system_notification('Open', f'Opening {fn}…')

        def file_ctx(e, fn=f.get('name',''), fidx=idx):
            m = tk.Menu(desktop_win, tearoff=0, bg='#1f3b5c', fg='white',
                        activebackground='#4a90d9', font=('Segoe UI', 9))
            m.add_command(label=f'Open {fn}', command=lambda: open_file())
            m.add_separator()
            m.add_command(label='Delete', command=lambda: [
                state['desktop_files'].pop(fidx) if fidx < len(state.get('desktop_files',[])) else None,
                save_state(), _refresh_desktop_files(),
                show_system_notification('Desktop', f'{fn} deleted')])
            m.tk_popup(e.x_root, e.y_root)

        for w in (frame, cv):
            w.bind('<Double-1>', lambda e, o=open_file: o())
            w.bind('<Button-3>', file_ctx)




def show_desktop():
    v = state.get('os_version', 'Ultimate')
    if v == 'Starter':
        state['wallpaper'] = ''

    global desktop_win, desktop_bg_label, desktop_start_menu, taskbar
    if desktop_win and desktop_win.winfo_exists():
        desktop_win.deiconify()
        return
    try:
        root.withdraw()
    except Exception:
        pass

    desktop_win = tk.Toplevel(root)
    desktop_win.title('Windows 7')
    desktop_win.attributes('-fullscreen', True)
    desktop_win.configure(bg='#4a7eb5')   # Win7 default blue sky bg
    desktop_win.attributes('-alpha', 0.99)
    desktop_win.update_idletasks()
    screen_w = desktop_win.winfo_screenwidth()
    screen_h = desktop_win.winfo_screenheight()

    # ── background ─────────────────────────────────────────────────────────
    desktop_bg_label = tk.Label(desktop_win, bg='#4a7eb5')
    desktop_bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    desktop_win.bind('<Escape>', lambda e: hide_start_menu())
    desktop_start_menu = None

    # ── desktop icon factory ───────────────────────────────────────────────
    ICON_SZ = 72   # canvas size
    ICON_CELL_H = 90

    def add_desktop_icon(x, y, emoji, title, action):
        # Determine safe background color first
        try:
            _icon_bg = desktop_bg_label.cget('bg')
            if not _icon_bg or _icon_bg == '':
                _icon_bg = '#4a7eb5'
        except Exception:
            _icon_bg = '#4a7eb5'
        frame = tk.Frame(desktop_win, bg=_icon_bg, width=ICON_SZ, height=ICON_CELL_H,
                         cursor='hand2')
        frame.place(x=x, y=y)
        frame.pack_propagate(False)

        cv = tk.Canvas(frame, width=ICON_SZ, height=ICON_SZ,
                       highlightthickness=0, cursor='hand2')
        cv.config(bg=_icon_bg)
        cv.pack(pady=(0, 0))

        # Draw icon state
        def draw(state_='normal'):
            cv.delete('all')
            if state_ == 'hover':
                # Win7 icon hover: light blue selection box
                cv.create_rectangle(4, 4, ICON_SZ-4, ICON_SZ-4,
                                    fill='#5b9bd5', outline='#82b4e8',
                                    width=1, stipple='gray50')
            cv.create_text(ICON_SZ//2, ICON_SZ//2 - 4,
                           text=emoji, font=('Segoe UI Emoji', 28))

        draw()

        lbl = tk.Label(frame, text=title,
                       bg=frame.cget('bg'), fg='white',
                       font=('Segoe UI', 8, 'bold'),
                       wraplength=ICON_SZ+4, justify='center',
                       relief='flat', bd=0)
        lbl.pack()

        # Drag
        frame._dx = 0; frame._dy = 0
        def on_press(e):
            frame._dx = e.x_root - frame.winfo_x()
            frame._dy = e.y_root - frame.winfo_y()
        def on_drag(e):
            nx = max(0, min(e.x_root - frame._dx, screen_w - ICON_SZ - 4))
            ny = max(0, min(e.y_root - frame._dy, screen_h - ICON_CELL_H - 50))
            frame.place(x=nx, y=ny)
        def on_enter(e):
            draw('hover')
        def on_leave(e):
            draw('normal')

        def icon_ctx(e):
            m = tk.Menu(desktop_win, tearoff=0,
                        bg='#1f3b5c', fg='white',
                        activebackground='#4a90d9',
                        font=('Segoe UI', 9))
            m.add_command(label=f'Open {title}', command=action)
            m.add_separator()
            m.add_command(label='Delete',
                          command=lambda: [
                              frame.destroy(),
                              show_system_notification(title, 'Moved to Recycle Bin.')])
            m.tk_popup(e.x_root, e.y_root)

        for w in (frame, cv, lbl):
            w.bind('<ButtonPress-1>', on_press)
            w.bind('<B1-Motion>',     on_drag)
            w.bind('<Double-1>',      lambda e, a=action, t=title: (
                a() if (state.get('activated', False)
                        or t in ('Settings', 'Terminal', 'Assistant'))
                else _require_activation(t)))
            w.bind('<Enter>',         on_enter)
            w.bind('<Leave>',         on_leave)
            w.bind('<Button-3>',      icon_ctx)
        return frame

    # ── desktop icons ──────────────────────────────────────────────────────
    left_icons = [
        ('✨', 'Assistant',     show_ai_app),
        ('📁', 'File Explorer', show_file_explorer),
        ('🧮', 'Calculator',    show_calculator_app),
        ('📝', 'Word',          show_word_processor),
        ('🎨', 'Paint',         show_paint_app),
        ('📅', 'Calendar',      show_calendar_app),
    ]
    right_icons = [
        ('🎵', 'Media Player',  show_media_player),
        ('📊', 'Spreadsheet',   show_excel_app),
        ('🗑️', 'Recycle Bin',   show_recycle_bin),
        ('ℹ️', 'System Info',   show_system_info_app),
        ('🛡️', 'Security',      show_windows_security),
        ('⚙️', 'Settings',      show_settings_app),
    ]
    for i, (em, nm, fn) in enumerate(left_icons):
        add_desktop_icon(20, 60 + i * 100, em, nm, fn)
    for i, (em, nm, fn) in enumerate(right_icons):
        add_desktop_icon(screen_w - 96, 60 + i * 100, em, nm, fn)

    # installed apps
    for idx, app in enumerate(state.get('apps', [])):
        try:
            nm = app.get('name', 'App')
            def _launch(a=app):
                key = a.get('name', '').lower()
                if key in APP_MAP: APP_MAP[key]()
            add_desktop_icon(120 + idx * 90, 60, '📦', nm, _launch)
        except Exception:
            pass

    # ── Blue Rubber-Band Drag Selection (hold right-click + drag on desktop) ──
    _sel_rect = {'id': None, 'x0': 0, 'y0': 0, 'dragging': False}

    # Canvas overlay for drawing the selection box
    try:
        sel_cv = tk.Canvas(desktop_win, bg='', highlightthickness=0)
        sel_cv.place(x=0, y=0, relwidth=1, relheight=1)
        sel_cv.lower()
        desktop_win._sel_canvas = sel_cv
    except Exception:
        sel_cv = None

    def _sel_start(event):
        _sel_rect['x0'] = event.x
        _sel_rect['y0'] = event.y
        _sel_rect['dragging'] = False
        if sel_cv:
            sel_cv.delete('selbox')

    def _sel_drag(event):
        _sel_rect['dragging'] = True
        if not sel_cv:
            return
        x0, y0 = _sel_rect['x0'], _sel_rect['y0']
        x1, y1 = event.x, event.y
        sel_cv.delete('selbox')
        # Outer border (blue)
        sel_cv.create_rectangle(x0, y0, x1, y1,
            outline='#3a8fff', fill='', width=2, tags='selbox')
        # Inner translucent fill simulation (stipple)
        sel_cv.create_rectangle(x0+1, y0+1, x1-1, y1-1,
            outline='', fill='#4fa8ff', stipple='gray25', tags='selbox')

    def _sel_end(event):
        if sel_cv:
            sel_cv.delete('selbox')
        # Only show context menu if NOT a drag (< 5px movement)
        if not _sel_rect['dragging']:
            show_desktop_context_menu(event)
        _sel_rect['dragging'] = False

    # Bind to desktop background
    desktop_win.bind('<ButtonPress-3>',   _sel_start)
    desktop_win.bind('<B3-Motion>',       _sel_drag)
    desktop_win.bind('<ButtonRelease-3>', _sel_end)
    desktop_bg_label.bind('<ButtonPress-3>',   _sel_start)
    desktop_bg_label.bind('<B3-Motion>',       _sel_drag)
    desktop_bg_label.bind('<ButtonRelease-3>', _sel_end)

    # ── keyboard shortcuts ─────────────────────────────────────────────────
    def alt_f4_handler(event=None):
        if messagebox.askyesno('Exit', 'Close desktop and logout?'):
            try: desktop_win.destroy()
            except: pass
            show_login()
            ACTIVE_APPS.clear()
    desktop_win.bind_all('<Alt-F4>', alt_f4_handler)
    desktop_win.bind_all('<Control-Shift-B>', lambda e: show_bios_boot_menu())
    desktop_win.bind_all('<Control-Shift-Z>', lambda e: show_bsod())
    desktop_win.bind_all('<Control-r>',      lambda e: show_run_dialog())
    desktop_win.bind_all('<Control-Tab>',    lambda e: show_flip3d())
    desktop_win.bind_all('<Control-l>',      lambda e: show_screen_lock())
    desktop_win.bind_all('<Control-d>',      lambda e: show_aero_peek())
    desktop_win.bind_all('<Control-n>',      lambda e: show_quick_note())
    desktop_win.bind_all('<F1>',             lambda e: show_system_properties())
    desktop_win.bind_all('<Print>',          lambda e: show_snipping_tool())
    desktop_win.bind_all('<Control-Print>',  lambda e: show_snipping_tool())
    # New feature shortcuts
    desktop_win.bind_all('<Control-m>',      lambda e: show_screen_magnifier())
    desktop_win.bind_all('<Control-k>',      lambda e: show_clipboard_ring())
    desktop_win.bind_all('<F11>',            lambda e: show_focus_mode())
    desktop_win.bind_all('<Control-F1>',     lambda e: show_virtual_desktops())

    # ══════════════════════════════════════════════════════════════════════
    # TASKBAR  –  proper Windows 7 Aero style
    # ══════════════════════════════════════════════════════════════════════
    #
    # Layout:
    #  [Start Orb] [Quick Launch] [── open-window buttons ──] [System Tray] [Peek]
    #
    # Height: 40px  (Win7 default)
    # Colors: translucent Aero blue  #1f4e8c / #2562b0 with top highlight line

    TB_H        = 40
    TB_BG       = '#1f4e8c'     # main taskbar fill
    TB_TOP      = '#3a7bd5'     # top highlight stripe (Aero glass edge)
    TB_SEP      = '#2a5fa8'     # separator lines
    TRAY_BG     = '#163972'     # slightly darker tray area
    BTN_HOVER   = '#3570c0'
    BTN_ACTIVE  = '#4a87d8'

    taskbar = tk.Frame(desktop_win, bg=TB_BG, height=TB_H, bd=0,
                       highlightthickness=0)
    taskbar.pack(side='bottom', fill='x')
    taskbar.pack_propagate(False)

    # Top 1-px highlight line (Aero glass edge)
    top_line = tk.Frame(taskbar, bg=TB_TOP, height=1)
    top_line.place(relx=0, rely=0, relwidth=1)

    # ── Start Orb  (floats above taskbar as Toplevel so it's never clipped) ──
    ORB_SIZE = 52

    orb_host = tk.Toplevel(desktop_win)
    orb_host.overrideredirect(True)
    orb_host.attributes('-topmost', True)
    _TRANS = '#010203'   # near-black used as transparency key
    orb_host.configure(bg=_TRANS)
    try:
        orb_host.wm_attributes('-transparentcolor', _TRANS)
    except Exception:
        pass

    orb_cv = tk.Canvas(orb_host, width=ORB_SIZE, height=ORB_SIZE,
                       bg=_TRANS, highlightthickness=0, cursor='hand2')
    orb_cv.pack()

    def _place_orb(event=None):
        if not (desktop_win.winfo_exists() and taskbar.winfo_exists()):
            return
        try:
            tx = desktop_win.winfo_rootx()
            # Bottom of the desktop window
            ty = desktop_win.winfo_rooty() + desktop_win.winfo_height()
            # Orb sits so its bottom edge is 4px below the taskbar top,
            # making it appear to "bulge" upward out of the taskbar
            ox = tx + 4
            oy = ty - TB_H - (ORB_SIZE - TB_H) // 2 - 4   # centered on taskbar, slightly raised
            orb_host.geometry(f'{ORB_SIZE}x{ORB_SIZE}+{ox}+{oy}')
        except Exception:
            pass

    desktop_win.bind('<Configure>', _place_orb, add='+')
    desktop_win.after(120, _place_orb)

    def draw_orb(hover=False):
        orb_cv.delete('all')
        # Outer glow ring on hover
        if hover:
            orb_cv.create_oval(0, 0, ORB_SIZE, ORB_SIZE,
                               fill='', outline='#90d8ff', width=3)
        # Main orb gradient (three concentric circles = depth)
        c1 = '#70c8ff' if hover else '#55a0f0'
        c2 = '#2d84e0' if hover else '#1e68c8'
        c3 = '#1060c0' if hover else '#0e50a8'
        orb_cv.create_oval(2, 2, ORB_SIZE-2, ORB_SIZE-2,
                            fill=c1, outline='#9adcff' if hover else '#6ab4f0', width=2)
        orb_cv.create_oval(7, 7, ORB_SIZE-7, ORB_SIZE-7,
                            fill=c2, outline='')
        orb_cv.create_oval(13, 13, ORB_SIZE-13, ORB_SIZE-13,
                            fill=c3, outline='')
        # Windows logo — four rounded squares drawn cleanly with no gap/border
        cx = ORB_SIZE // 2
        cy = ORB_SIZE // 2
        q = 7   # half-size of each square
        gap = 2  # gap between squares
        # top-left red
        orb_cv.create_rectangle(cx-q-gap//2-q, cy-q-gap//2-q,
                                  cx-gap//2, cy-gap//2,
                                  fill='#f25022', outline='', width=0)
        # top-right blue
        orb_cv.create_rectangle(cx+gap//2, cy-q-gap//2-q,
                                  cx+gap//2+q+q, cy-gap//2,
                                  fill='#00a4ef', outline='', width=0)
        # bottom-left green
        orb_cv.create_rectangle(cx-q-gap//2-q, cy+gap//2,
                                  cx-gap//2, cy+gap//2+q+q,
                                  fill='#7fba00', outline='', width=0)
        # bottom-right yellow
        orb_cv.create_rectangle(cx+gap//2, cy+gap//2,
                                  cx+gap//2+q+q, cy+gap//2+q+q,
                                  fill='#ffb900', outline='', width=0)
        # Glass shine arc on top
        orb_cv.create_arc(4, 4, ORB_SIZE-4, ORB_SIZE//2+2,
                           start=15, extent=150,
                           outline='#c8eeff' if hover else '#90c8ff',
                           style='arc', width=1)

    draw_orb()
    orb_cv.bind('<Enter>',    lambda e: draw_orb(True))
    orb_cv.bind('<Leave>',    lambda e: draw_orb(False))
    orb_cv.bind('<Button-1>', lambda e: toggle_start_menu())

    # ── Quick Launch helper ────────────────────────────────────────────────
    def ql_sep():
        """Thin separator line between taskbar sections."""
        s = tk.Frame(taskbar, bg=TB_SEP, width=1)
        s.pack(side='left', fill='y', pady=6, padx=2)

    def make_ql_btn(parent, emoji, tooltip_text, command, right_menu=None):
        """
        Win7 quick-launch button: 36×36 canvas with hover/active states,
        floating tooltip, and optional right-click menu.
        """
        BTN_W = 40

        cv = tk.Canvas(parent, width=BTN_W, height=TB_H,
                       bg=TB_BG, highlightthickness=0, cursor='hand2')
        cv.pack(side='left', padx=0)

        state_ref = {'s': 'normal'}

        def redraw(s='normal'):
            state_ref['s'] = s
            cv.delete('all')
            if s == 'hover':
                # Aero glass hover: blue gradient box with lighter top
                cv.create_rectangle(2, 2, BTN_W-2, TB_H-2,
                                    fill=BTN_HOVER, outline='#5590e0', width=1)
                cv.create_rectangle(2, 2, BTN_W-2, TB_H//2,
                                    fill=BTN_ACTIVE, outline='')
            elif s == 'active':
                cv.create_rectangle(2, 2, BTN_W-2, TB_H-2,
                                    fill='#2a60a8', outline='#3a78c8', width=1)
            cv.create_text(BTN_W//2, TB_H//2 + 1,
                           text=emoji, font=('Segoe UI Emoji', 18))

        redraw()

        # Tooltip
        tip = [None]
        def show_tip(e):
            tip[0] = tk.Toplevel(desktop_win)
            tip[0].overrideredirect(True)
            tip[0].attributes('-topmost', True)
            tip[0].configure(bg='#1a3a60')
            tk.Label(tip[0], text=tooltip_text,
                     bg='#1a3a60', fg='white',
                     font=('Segoe UI', 9), padx=8, pady=4).pack()
            bx = cv.winfo_rootx() + BTN_W//2
            by = cv.winfo_rooty() - 6
            tw = len(tooltip_text) * 7 + 16
            tip[0].geometry(f'+{bx - tw//2}+{by - 26}')
        def hide_tip(e):
            if tip[0]:
                try: tip[0].destroy()
                except: pass
                tip[0] = None

        def on_click(e):
            redraw('active')
            command()
            cv.after(150, lambda: redraw('normal'))

        def on_ctx(e):
            if not right_menu: return
            m = tk.Menu(desktop_win, tearoff=0,
                        bg='#1f3b5c', fg='white',
                        activebackground='#4a90d9',
                        font=('Segoe UI', 9))
            for txt, fn in right_menu:
                m.add_command(label=txt, command=fn)
            m.tk_popup(e.x_root, e.y_root)

        cv.bind('<Enter>',    lambda e: (redraw('hover'), show_tip(e)))
        cv.bind('<Leave>',    lambda e: (redraw('normal'), hide_tip(e)))
        cv.bind('<Button-1>', on_click)
        cv.bind('<Button-3>', on_ctx)
        return cv

    # spacer for orb
    tk.Label(taskbar, text='', bg=TB_BG, width=4).pack(side='left')

    # ── Quick Launch section ───────────────────────────────────────────────
    ql_sep()

    make_ql_btn(taskbar, '🗓', 'Calendar',
                show_calendar_app,
                [('Open Calendar', show_calendar_app),
                 ('Clock Overlay', show_taskbar_time_overlay)])

    make_ql_btn(taskbar, '🔔', 'Notifications',
                show_action_center,
                [('Action Center', show_action_center),
                 ('Clear Notifications',
                  lambda: show_system_notification('Done', 'Cleared.'))])

    make_ql_btn(taskbar, '⚡', 'Performance',
                show_system_monitor,
                [('System Monitor', show_system_monitor),
                 ('Task Manager', show_task_manager)])

    make_ql_btn(taskbar, '💿', 'Installer',
                show_windows_installer_helper,
                [('Open Installer', show_windows_installer_helper)])

    make_ql_btn(taskbar, 'G', 'Google',
                show_google_app,
                [('Google App', show_google_app),
                 ('Open Browser',
                  lambda: webbrowser.open('https://www.google.com'))])

    make_ql_btn(taskbar, '⚙', 'Settings',
                show_settings_app,
                [('Settings', show_settings_app),
                 ('Check Updates',
                  lambda: show_update_loading(show_settings_app))])

    make_ql_btn(taskbar, '✨', 'Assistant',
                show_ai_app,
                [('Open Assistant', show_ai_app)])

    make_ql_btn(taskbar, '🔊', 'Volume',
                show_volume_overlay,
                [('Vol +10', lambda: change_volume(10)),
                 ('Vol -10', lambda: change_volume(-10))])

    ql_sep()

    # ── Open windows area (centre, expanding) ─────────────────────────────
    taskbar.tabs_frame = tk.Frame(taskbar, bg=TB_BG)
    taskbar.tabs_frame.pack(side='left', fill='both', expand=True, padx=6)

    taskbar.tab_label = tk.Label(
        taskbar.tabs_frame,
        text='No open windows',
        bg=TB_BG, fg='#aaccee',
        font=('Segoe UI', 9))
    taskbar.tab_label.pack(side='left', pady=0, padx=4)

    # Search box (Win7 taskbar search feel)
    search_frame = tk.Frame(taskbar, bg='#163d7a',
                            highlightthickness=1,
                            highlightbackground='#4a80c8')
    search_frame.pack(side='left', padx=6, pady=7)
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var,
                            bg='#163d7a', fg='#c0d8f8',
                            insertbackground='white',
                            relief='flat', font=('Segoe UI', 9),
                            width=18)
    search_entry.pack(padx=6, pady=3)
    search_entry.insert(0, 'Search…')
    search_entry.bind('<FocusIn>',
                      lambda e: search_entry.delete(0, 'end')
                      if search_entry.get() == 'Search…' else None)

    def taskbar_search(e=None):
        q = search_var.get().strip().lower()
        if not q or q == 'search…': return
        lkp = {
            'file': show_file_explorer, 'explorer': show_file_explorer,
            'terminal': show_terminal_app, 'cmd': show_terminal_app,
            'media': show_media_player, 'player': show_media_player,
            'excel': show_excel_app, 'sheet': show_excel_app,
            'calendar': show_calendar_app,
            'note': show_sticky_notes, 'sticky': show_sticky_notes,
            'paint': show_paint_app,
            'calc': show_calculator_app,
            'control': show_control_panel,
            'setting': show_settings_app,
            'ai': show_ai_app, 'celine': show_ai_app,
            'activation': show_activation_dialog, 'activate': show_activation_dialog,
            # 20 new apps
            'journal': show_journal, 'diary': show_journal,
            'alarm': show_alarm_manager, 'reminder': show_alarm_manager,
            'bookmark': show_bookmark_manager,
            'pomodoro': show_pomodoro, 'focus': show_pomodoro,
            'habit': show_habit_tracker,
            'converter': show_unit_converter, 'unit': show_unit_converter,
            'password': show_password_generator,
            'analyzer': show_text_analyzer, 'wordcount': show_text_analyzer,
            'quote': show_quote_of_day,
            'clipboard': show_clipboard_history,
            'shortcut': show_shortcuts_manager,
            'worldclock': show_world_clock, 'clock': show_world_clock,
            'color': show_color_picker,
            'typing': show_typing_test,
            'flashcard': show_math_flashcards,
            'notesearch': show_note_search,
            'stopwatch': show_stopwatch,
            'finance': show_finance_tracker, 'budget': show_finance_tracker,
            'ascii': show_ascii_art,
            'taskboard': show_task_board, 'kanban': show_task_board,
        }
        for key, fn in lkp.items():
            if key in q:
                fn(); return
        show_system_notification('Search', f'No result for: {q}')

    def taskbar_search(e=None):
        q = search_var.get().strip()
        if not q or q.lower() == 'search…':
            show_windows_search()
        else:
            show_windows_search(initial_query=q)
        search_var.set('')
        search_entry.delete(0, 'end')
        search_entry.insert(0, 'Search…')

    search_entry.bind('<Return>', taskbar_search)
    # Also open search on click
    search_entry.bind('<FocusIn>', lambda e: (
        taskbar_search() if search_entry.get() == 'Search…' else None))

    ql_sep()

    # ══════════════════════════════════════════════════════════════════════
    # SYSTEM TRAY  –  right side
    # ══════════════════════════════════════════════════════════════════════
    tray = tk.Frame(taskbar, bg=TRAY_BG,
                    highlightthickness=1,
                    highlightbackground='#2a4e8a')
    tray.pack(side='right', fill='y')

    # Aero Peek strip (far right, Win7)
    peek_strip = tk.Frame(tray, bg='#4a80b8', width=6, cursor='hand2')
    peek_strip.pack(side='right', fill='y')
    peek_strip.bind('<Enter>',    start_aero_peek)
    peek_strip.bind('<Leave>',    stop_aero_peek)

    # Clock block
    clock_frame = tk.Frame(tray, bg=TRAY_BG, cursor='hand2', padx=10)
    clock_frame.pack(side='right', fill='y')

    clock_time = tk.Label(clock_frame, bg=TRAY_BG, fg='white',
                          font=('Segoe UI', 10, 'bold'),
                          text=datetime.now().strftime('%I:%M %p'))
    clock_time.pack(pady=(6, 0))

    clock_date = tk.Label(clock_frame, bg=TRAY_BG, fg='#a0c4e8',
                          font=('Segoe UI', 8),
                          text=datetime.now().strftime('%d/%m/%Y'))
    clock_date.pack(pady=(0, 5))

    for w in (clock_frame, clock_time, clock_date):
        w.bind('<Button-1>', show_taskbar_time_overlay)

    # Separator
    tk.Frame(tray, bg=TB_SEP, width=1).pack(side='right', fill='y', pady=6)

    # Battery label
    bat_lbl = tk.Label(tray, text=get_battery_status(),
                       bg=TRAY_BG, fg='#a0c4e8',
                       font=('Segoe UI', 8), padx=6)
    bat_lbl.pack(side='right', fill='y')

    # Network icon
    net_lbl = tk.Label(tray, text='📶', bg=TRAY_BG,
                       font=('Segoe UI Emoji', 14), padx=6)
    net_lbl.pack(side='right', fill='y')
    net_lbl.bind('<Button-1>', lambda e: show_network_center())

    # Volume icon in tray
    vol_lbl = tk.Label(tray, text='🔊', bg=TRAY_BG,
                       font=('Segoe UI Emoji', 13), padx=4)
    vol_lbl.pack(side='right', fill='y')
    vol_lbl.bind('<Button-1>', lambda e: show_volume_overlay())

    # Separator before clock
    tk.Frame(tray, bg=TB_SEP, width=1).pack(side='right', fill='y', pady=6)

    # ── live updates ───────────────────────────────────────────────────────
    def update_clock():
        if desktop_win and desktop_win.winfo_exists():
            now = datetime.now()
            clock_time.config(text=now.strftime('%I:%M %p'))
            clock_date.config(text=now.strftime('%d/%m/%Y'))
            bat_lbl.config(text=get_battery_status())
            desktop_win.after(1000, update_clock)
    update_clock()

    # ── top notification ribbon (dismissible) ─────────────────────────────
    ribbon = tk.Frame(desktop_win, bg='#1a4a8a', height=24,
                      highlightthickness=1,
                      highlightbackground='#3a6ec0')
    ribbon.place(relx=0, rely=0, relwidth=1)

    tk.Label(ribbon,
             text=f'  Windows 7 {v}  ·  '
                  f'Welcome, {state.get("user_name", "User")}',
             bg='#1a4a8a', fg='#90c4f8',
             font=('Segoe UI', 8)).pack(side='left', pady=4)

    tk.Button(ribbon, text='✕',
              bg='#1a4a8a', fg='#90c4f8',
              relief='flat', font=('Segoe UI', 8), bd=0,
              cursor='hand2',
              command=lambda: ribbon.place_forget()).pack(
        side='right', padx=8, pady=4)

    # ── z-order ────────────────────────────────────────────────────────────
    desktop_bg_label.lower()
    taskbar.lift()
    ribbon.lift()
    desktop_win.after(80, lambda: [
        desktop_bg_label.lower(), taskbar.lift(), ribbon.lift()])

    # ── wallpaper ──────────────────────────────────────────────────────────
    if state.get('wallpaper'):
        desktop_win.update_idletasks()
        set_wallpaper(state['wallpaper'])
    else:
        desktop_bg_label.config(bg='#3a7ec4')   # Win7 Aero blue default

    # ── Activation watermark (shown only when NOT activated) ───────────────
    if not state.get('activated', False):
        try:
            _wm_bg = desktop_win.cget('bg')
            if not _wm_bg or _wm_bg == '':
                _wm_bg = '#3a7ec4'
        except Exception:
            _wm_bg = '#3a7ec4'
        wm = tk.Label(desktop_win,
                      text='Activate Windows\nGo to Settings > Activation to activate Windows 7',
                      bg=_wm_bg, fg='#ffffff',
                      font=('Segoe UI', 11), justify='right',
                      anchor='se')
        wm.place(relx=1.0, rely=1.0, x=-16, y=-(TB_H + 58), anchor='se')
        wm._is_watermark = True

    # ── Apply BIOS stability on desktop launch ─────────────────────────────
    desktop_win.after(800, _apply_bios_stability_to_desktop)

    # ── Show any virtual desktop files ─────────────────────────────────────
    desktop_win.after(300, _refresh_desktop_files)

def hide_start_menu():
    global desktop_start_menu
    if desktop_start_menu and desktop_start_menu.winfo_exists():
        desktop_start_menu.destroy()
    desktop_start_menu = None


def show_start_menu():
    global desktop_start_menu
    if desktop_start_menu and desktop_start_menu.winfo_exists():
        hide_start_menu()
        return

    desktop_start_menu = tk.Toplevel(desktop_win)
    desktop_start_menu.overrideredirect(True)
    desktop_start_menu.attributes('-topmost', True)
    desktop_start_menu.attributes('-alpha', 0.97)
    desktop_start_menu.configure(bg='#1a3a5c')

    x = desktop_win.winfo_rootx() + 2
    y = desktop_win.winfo_rooty() + desktop_win.winfo_height() - 560
    desktop_start_menu.geometry(f'480x550+{x}+{y}')

    desktop_start_menu.bind('<FocusOut>', lambda e: hide_start_menu())
    desktop_start_menu.bind('<Escape>',   lambda e: hide_start_menu())

    # ── outer border frame (Win7 glassy dark blue rim) ─────────────────────
    outer = tk.Frame(desktop_start_menu, bg='#1a3a5c', bd=0)
    outer.pack(fill='both', expand=True, padx=2, pady=2)

    # ── user header ────────────────────────────────────────────────────────
    header = tk.Frame(outer, bg='#1e4d82', height=72)
    header.pack(fill='x')
    header.pack_propagate(False)

    # Avatar circle (canvas-drawn)
    avatar_cv = tk.Canvas(header, width=48, height=48, bg='#1e4d82',
                          highlightthickness=0)
    avatar_cv.place(x=10, y=12)
    avatar_cv.create_oval(2, 2, 46, 46, fill='#3a78c9', outline='#7eb4ea', width=2)
    initials = ''.join(w[0].upper() for w in state.get('user_name', 'User').split()[:2])
    avatar_cv.create_text(24, 24, text=initials, fill='white',
                          font=('Segoe UI', 14, 'bold'))

    tk.Label(header, text=state.get('user_name', 'User'),
             bg='#1e4d82', fg='white',
             font=('Segoe UI', 11, 'bold')).place(x=66, y=16)
    tk.Label(header, text='Windows 7 — Aero',
             bg='#1e4d82', fg='#a8c8f0',
             font=('Segoe UI', 8)).place(x=67, y=38)

    # ── body (two-pane) ────────────────────────────────────────────────────
    body = tk.Frame(outer, bg='#f0f0f0')
    body.pack(fill='both', expand=True)

    # LEFT pane — white, programs list
    left_bg = tk.Frame(body, bg='white', width=290)
    left_bg.pack(side='left', fill='both')
    left_bg.pack_propagate(False)

    # Search box at top of left pane
    search_frame = tk.Frame(left_bg, bg='#dce9f9', bd=0)
    search_frame.pack(fill='x', padx=0, pady=0)

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var,
                            bg='white', fg='#666', relief='flat',
                            font=('Segoe UI', 9),
                            insertbackground='#333')
    search_entry.pack(fill='x', padx=8, pady=6, ipady=4)
    search_entry.insert(0, 'Search programs and files')
    search_entry.bind('<FocusIn>',  lambda e: (search_entry.delete(0, 'end'),
                                               search_entry.config(fg='#111')))
    search_entry.bind('<FocusOut>', lambda e: (
        search_entry.insert(0, 'Search programs and files')
        if not search_var.get() else None,
        search_entry.config(fg='#666')))

    # Pinned / All programs label
    pin_bar = tk.Frame(left_bg, bg='#dce9f9', height=24)
    pin_bar.pack(fill='x')
    pin_bar.pack_propagate(False)
    tk.Label(pin_bar, text='All Programs',
             bg='#dce9f9', fg='#1a3a5c',
             font=('Segoe UI', 8, 'bold')).pack(side='left', padx=10, pady=4)

    # Scrollable program list
    prog_canvas = tk.Canvas(left_bg, bg='white', highlightthickness=0)
    prog_canvas.pack(side='left', fill='both', expand=True)
    prog_sb = ttk.Scrollbar(left_bg, orient='vertical',
                            command=prog_canvas.yview)
    prog_sb.pack(side='right', fill='y')
    prog_canvas.configure(yscrollcommand=prog_sb.set)

    prog_frame = tk.Frame(prog_canvas, bg='white')
    prog_canvas.create_window((0, 0), window=prog_frame, anchor='nw')
    prog_frame.bind('<Configure>',
                    lambda e: prog_canvas.configure(
                        scrollregion=prog_canvas.bbox('all')))
    prog_canvas.bind('<MouseWheel>',
                     lambda e: prog_canvas.yview_scroll(
                         int(-1 * e.delta / 120), 'units'))

    # Win7-style program button
    def make_prog_btn(parent, icon, name, cmd):
        row = tk.Frame(parent, bg='white', cursor='hand2')
        row.pack(fill='x', padx=0)

        def on_enter(e):
            row.config(bg='#cce4ff')
            lbl_name.config(bg='#cce4ff')
            lbl_icon.config(bg='#cce4ff')

        def on_leave(e):
            row.config(bg='white')
            lbl_name.config(bg='white')
            lbl_icon.config(bg='white')

        lbl_icon = tk.Label(row, text=icon, bg='white',
                            font=('Segoe UI Emoji', 13), width=3)
        lbl_icon.pack(side='left', padx=(8, 0), pady=3)

        lbl_name = tk.Label(row, text=name, bg='white', fg='#111',
                            font=('Segoe UI', 9), anchor='w')
        lbl_name.pack(side='left', fill='x', expand=True, pady=5)

        for w in (row, lbl_icon, lbl_name):
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
            w.bind('<Button-1>', lambda e, c=cmd: [hide_start_menu(), c()])

    program_list = [
        ('💻', 'Terminal',         show_terminal_app),
        ('📁', 'File Explorer',    show_file_explorer),
        ('⚙️',  'Control Panel',   show_control_panel),
        ('▶️',  'Run',             show_run_dialog),
        ('🔔', 'Action Center',    show_action_center),
        ('🌐', 'Network Center',   show_network_center),
        ('🔧', 'Device Manager',   show_device_manager),
        ('🔄', 'Windows Update',   show_windows_update),
        ('📎', 'Gadgets',          show_gadgets),
        ('🎬', 'Media Center',     show_windows_media_center),
        ('🔍', 'Google App',       show_google_app),
        ('🎵', 'Media Player',     show_media_player),
        ('🗑️', 'Recycle Bin',      show_recycle_bin),
        ('💣', 'Minesweeper',      show_minesweeper_game),
        ('⭕', 'Tic Tac Toe',      show_tic_tac_toe_game),
        ('🐍', 'Snake',            show_snake_game),
        ('📌', 'Sticky Notes',     show_sticky_notes),
        ('📝', 'Text Editor',      show_text_editor),
        ('🧮', 'Calculator',       show_calculator_app),
        ('🎨', 'Paint',            show_paint_app),
        ('📅', 'Calendar',         show_calendar_app),
        ('ℹ️',  'System Info',     show_system_info_app),
        # ── 20 New Feature Apps ──
        ('📓', 'Journal',          show_journal),
        ('⏰', 'Alarm Manager',    show_alarm_manager),
        ('🔖', 'Bookmarks',        show_bookmark_manager),
        ('🍅', 'Pomodoro Timer',   show_pomodoro),
        ('✅', 'Habit Tracker',    show_habit_tracker),
        ('📐', 'Unit Converter',   show_unit_converter),
        ('🔐', 'Password Gen',     show_password_generator),
        ('📊', 'Text Analyzer',    show_text_analyzer),
        ('✨', 'Quote of Day',     show_quote_of_day),
        ('📋', 'Clipboard Hist.',  show_clipboard_history),
        ('⌨️', 'Chat Shortcuts',   show_shortcuts_manager),
        ('🌍', 'World Clock',      show_world_clock),
        ('🎨', 'Color Picker',     show_color_picker),
        ('⌨️', 'Typing Test',      show_typing_test),
        ('🧮', 'Math Flashcards',  show_math_flashcards),
        ('🔍', 'Note Search',      show_note_search),
        ('⏱', 'Stopwatch',        show_stopwatch),
        ('💰', 'Finance Tracker',  show_finance_tracker),
        ('█', 'ASCII Art',         show_ascii_art),
        # ── 5 Futuristic Features ──
        ('🎬', 'Conversation Replayer', show_conversation_replayer),
        ('💓', 'System Heartbeat',      show_system_heartbeat),
        ('🔀', 'Code Diff Viewer',      show_code_diff),
        ('⏳', 'Time Capsule',          show_time_capsule),
        ('🎨', 'Pixel Art Editor',      show_pixel_art_editor),
        # ── 5 New Software Apps ──
        ('📚', 'Flashcard Deck',        show_flashcard_deck),
        ('💰', 'Budget Tracker',        show_budget_tracker),
        ('🎓', 'Learning Path',         show_learning_tracker),
        ('📖', 'Personal Wiki',         show_personal_wiki),
        ('🎵', 'Ambient Sounds',        show_ambient_sounds),
        # ── 10 New Windows Features ──
        ('🔍', 'Screen Magnifier',      show_screen_magnifier),
        ('📌', 'Taskbar Manager',       show_taskbar_manager),
        ('🖥',  'Virtual Desktops',     show_virtual_desktops),
        ('📋', 'Clipboard Ring',        show_clipboard_ring),
        ('🤖', 'AI Smart Search',       show_ai_smart_search),
        ('✍',  'AI Writing Assist',     show_ai_writing_assistant),
        ('⚡', 'Quick Launcher',        show_quick_app_launcher),
        ('🎯', 'Focus Mode',            show_focus_mode),
        ('🌙', 'Dark/Light Mode',       show_theme_toggle),
        ('📌', 'App Pinboard',          show_app_pinboard),
    ]
    for icon, name, cmd in program_list:
        make_prog_btn(prog_frame, icon, name, cmd)

    # RIGHT pane — blue gradient feel
    right_bg = tk.Frame(body, bg='#dce9f9', width=190)
    right_bg.pack(side='right', fill='both')
    right_bg.pack_propagate(False)

    def make_sys_btn(parent, icon, name, cmd):
        row = tk.Frame(parent, bg='#dce9f9', cursor='hand2')
        row.pack(fill='x', padx=0)

        def on_enter(e):
            row.config(bg='#b3d0f0')
            li.config(bg='#b3d0f0')
            ln.config(bg='#b3d0f0')

        def on_leave(e):
            row.config(bg='#dce9f9')
            li.config(bg='#dce9f9')
            ln.config(bg='#dce9f9')

        li = tk.Label(row, text=icon, bg='#dce9f9',
                      font=('Segoe UI Emoji', 11), width=3)
        li.pack(side='left', padx=(6, 0), pady=2)
        ln = tk.Label(row, text=name, bg='#dce9f9', fg='#0d2a4a',
                      font=('Segoe UI', 9), anchor='w')
        ln.pack(side='left', fill='x', expand=True, pady=4)

        for w in (row, li, ln):
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
            w.bind('<Button-1>', lambda e, c=cmd: [hide_start_menu(), c()])

    # Right pane header
    tk.Label(right_bg, text=state.get('user_name', 'User') + "'s",
             bg='#dce9f9', fg='#1a3a5c',
             font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=10, pady=(8, 0))
    tk.Frame(right_bg, bg='#a0bcd8', height=1).pack(fill='x', padx=8, pady=2)

    system_items = [
        ('📄', 'Documents',      show_file_explorer),
        ('🖼️', 'Pictures',       show_file_explorer),
        ('🎮', 'Games',          show_minesweeper_game),
        ('💾', 'Computer',       show_settings_app),
        ('⚙️', 'Control Panel',  show_control_panel),
        ('🎨', 'Personalization', show_themes),
    ]
    for icon, name, cmd in system_items:
        make_sys_btn(right_bg, icon, name, cmd)

    tk.Frame(right_bg, bg='#a0bcd8', height=1).pack(fill='x', padx=8, pady=4)

    # ── power strip (Win7-style bottom bar) ────────────────────────────────
    footer = tk.Frame(outer, bg='#1e3f6e', height=42)
    footer.pack(fill='x', side='bottom')
    footer.pack_propagate(False)

    def foot_btn(text, color, cmd):
        b = tk.Button(footer, text=text, bg=color, fg='white',
                      relief='flat', font=('Segoe UI', 8),
                      padx=8, pady=4, cursor='hand2',
                      activebackground='#5a9fd4',
                      bd=0, highlightthickness=0,
                      command=cmd)
        b.pack(side='right', padx=5, pady=7)
        return b

    # Shutdown arrow button (Win7 style)
    shut_frame = tk.Frame(footer, bg='#1e3f6e')
    shut_frame.pack(side='right', padx=4, pady=6)

    shut_btn = tk.Button(shut_frame, text='⏻  Shut down',
                         bg='#2a5298', fg='white',
                         relief='flat', font=('Segoe UI', 9),
                         padx=10, pady=4, cursor='hand2',
                         activebackground='#3a6bc0', bd=0,
                         command=lambda: [hide_start_menu(), perform_shutdown()])
    shut_btn.pack(side='left')

    arrow_btn = tk.Button(shut_frame, text='▶',
                          bg='#2a5298', fg='white',
                          relief='flat', font=('Segoe UI', 7),
                          padx=4, pady=4, cursor='hand2',
                          activebackground='#3a6bc0', bd=0)
    arrow_btn.pack(side='left', padx=(1, 0))

    # Arrow menu
    def show_power_menu(e=None):
        m = tk.Menu(desktop_start_menu, tearoff=0,
                    bg='#1e3f6e', fg='white',
                    activebackground='#3a6bc0', activeforeground='white',
                    font=('Segoe UI', 9), bd=0, relief='flat')
        m.add_command(label='🔄  Restart',
                      command=lambda: [hide_start_menu(), perform_restart()])
        m.add_command(label='💤  Sleep',
                      command=lambda: [hide_start_menu(), perform_sleep()])
        m.add_separator()
        m.add_command(label='🔓  Log off',
                      command=lambda: [hide_start_menu(),
                                       desktop_win.destroy(), show_login()])
        m.add_command(label='💾  BIOS',
                      command=lambda: [hide_start_menu(),
                                       desktop_win.destroy(), show_bios_boot_menu()])
        m.add_command(label='🖥️  OS Selector',
                      command=lambda: [hide_start_menu(),
                                       desktop_win.destroy(),
                                       show_os_version_selector_bios()])
        try:
            m.tk_popup(arrow_btn.winfo_rootx(),
                       arrow_btn.winfo_rooty() - m.winfo_reqheight() - 5)
        except:
            m.tk_popup(arrow_btn.winfo_rootx(), arrow_btn.winfo_rooty())

    arrow_btn.config(command=show_power_menu)

    # Left side of footer
    tk.Label(footer, text='Windows 7', bg='#1e3f6e', fg='#7eb4ea',
             font=('Segoe UI', 8, 'italic')).pack(side='left', padx=10, pady=10)

    # ── search handler ─────────────────────────────────────────────────────
    def start_menu_search(event=None):
        query = search_var.get().strip().lower()
        if not query or query == 'search programs and files':
            return
        hide_start_menu()

        results = []
        for key, action in APP_MAP.items():
            if query in key or key in query:
                results.append((key.title(), action))

        extra_map = {
            ('calendar',):                   ('Calendar',          show_calendar_app),
            ('notes', 'sticky'):             ('Sticky Notes',      show_sticky_notes),
            ('run', 'command'):              ('Run Dialog',         show_run_dialog),
            ('wifi', 'network'):             ('Wi-Fi Manager',      show_wifi_manager),
            ('driver', 'hardware'):          ('Driver Manager',     show_driver_manager),
            ('security',):                   ('Windows Security',   show_windows_security),
            ('taskbar', 'clock'):            ('Taskbar Clock',      show_taskbar_time_overlay),
        }
        for keys, val in extra_map.items():
            if any(k in query for k in keys):
                results.append(val)

        if query.startswith('open '):
            file_path = query[5:]
            abs_path = os.path.abspath(os.path.join(DATA_DIR, file_path))
            if os.path.exists(abs_path):
                results.append((f'Open {file_path}',
                                 lambda p=abs_path: open_path_in_system(p)))

        if not results:
            for root_dir, _, files in os.walk(DATA_DIR):
                for f in files:
                    if query in f.lower():
                        path = os.path.join(root_dir, f)
                        results.append((f'File: {f}',
                                         lambda p=path: open_path_in_system(p)))

        if results:
            show_search_results(query, results)
            return

        # Fallback keyword routing
        fallback = [
            (('terminal', 'cmd'),             show_terminal_app),
            (('file', 'explorer', 'documents'), show_file_explorer),
            (('control', 'panel'),            show_control_panel),
            (('action', 'center'),            show_action_center),
            (('network', 'wifi'),             show_network_center),
            (('update', 'windows update'),    show_windows_update),
            (('device',),                     show_device_manager),
            (('gadget',),                     show_gadgets),
            (('media', 'player'),             show_windows_media_center),
            (('theme', 'personal'),           show_themes),
            (('sound', 'volume'),             show_volume_control),
            (('security',),                   show_windows_security),
            (('run', 'command'),              show_run_dialog),
            (('driver', 'hardware'),          show_driver_manager),
        ]
        for keys, fn in fallback:
            if any(k in query for k in keys):
                fn(); return

        show_system_notification('Search', f'Could not find: {query}')

    search_entry.bind('<Return>', start_menu_search)

    desktop_start_menu.focus_set()


def toggle_start_menu():
    if desktop_start_menu and desktop_start_menu.winfo_exists():
        hide_start_menu()
    else:
        show_start_menu()


def show_terminal_app():
    v = state.get('os_version', 'Ultimate')
    if v in ['Starter', 'Home Basic']:
        messagebox.showerror('Access Denied',
            f'Command Prompt is not available in Windows 7 {v}.')
        return
    if not state.get('drivers_installed', True):
        messagebox.showwarning('Hardware Error',
            'Terminal requires drivers. Install via Windows Security > Advanced.')
        return

    # ── window ─────────────────────────────────────────────────────────────
    term_win = tk.Toplevel(desktop_win)
    term_win.title('Command Prompt — Windows 7')
    term_win.geometry('750x480')
    term_win.configure(bg='#0c0c0c')
    center_window(term_win, 750, 480)
    term_win.resizable(True, True)

    # ── title bar with Win7 style ──────────────────────────────────────────
    titlebar = tk.Frame(term_win, bg='#1e1e2e', height=30)
    titlebar.pack(fill='x')
    titlebar.pack_propagate(False)
    tk.Label(titlebar, text='  💻  Command Prompt — Windows 7',
             bg='#1e1e2e', fg='#c0c8e0', font=('Consolas', 9)).pack(side='left', pady=5)

    btn_frame = tk.Frame(titlebar, bg='#1e1e2e')
    btn_frame.pack(side='right', padx=4)
    for sym, col, cmd in [('–', '#3a3a4a', lambda: term_win.iconify()),
                           ('□', '#3a3a4a', lambda: None),
                           ('✕', '#c0392b', lambda: term_win.destroy())]:
        b = tk.Label(btn_frame, text=sym, bg=col, fg='white',
                     font=('Segoe UI', 9), width=3, cursor='hand2')
        b.pack(side='left', padx=1, pady=3)
        b.bind('<Button-1>', lambda e, c=cmd: c())
        b.bind('<Enter>', lambda e, w=b: w.config(bg='#5a5a7a' if w['text'] != '✕' else '#e74c3c'))
        b.bind('<Leave>', lambda e, w=b, c=col: w.config(bg=c))

    # ── menu bar ───────────────────────────────────────────────────────────
    menubar_frame = tk.Frame(term_win, bg='#141424', height=22)
    menubar_frame.pack(fill='x')
    menubar_frame.pack_propagate(False)

    def menu_btn(text, items):
        b = tk.Label(menubar_frame, text=text, bg='#141424', fg='#a0a8c0',
                     font=('Segoe UI', 8), padx=8, cursor='hand2')
        b.pack(side='left', pady=2)
        def show(e):
            m = tk.Menu(term_win, tearoff=0, bg='#1e1e2e', fg='#c0c8e0',
                        activebackground='#3a3a5a', font=('Segoe UI', 9))
            for label, cmd in items:
                if label == '---':
                    m.add_separator()
                else:
                    m.add_command(label=label, command=cmd)
            m.tk_popup(b.winfo_rootx(), b.winfo_rooty() + 22)
        b.bind('<Button-1>', show)
        b.bind('<Enter>', lambda e: b.config(bg='#2a2a3a'))
        b.bind('<Leave>', lambda e: b.config(bg='#141424'))

    menu_btn('File', [
        ('New Terminal Window', lambda: show_terminal_app()),
        ('---', None),
        ('Exit', lambda: term_win.destroy()),
    ])
    menu_btn('Edit', [
        ('Copy (Ctrl+C)', lambda: term_win.clipboard_get()),
        ('Paste (Ctrl+V)', lambda: None),
        ('Select All', lambda: output.tag_add('sel', '1.0', 'end')),
        ('---', None),
        ('Clear Screen', lambda: output.configure(state='normal') or
                                  output.delete('1.0', 'end') or
                                  output.configure(state='disabled')),
    ])
    menu_btn('View', [
        ('Font: Small',  lambda: output.config(font=('Consolas', 9))),
        ('Font: Normal', lambda: output.config(font=('Consolas', 11))),
        ('Font: Large',  lambda: output.config(font=('Consolas', 14))),
        ('---', None),
        ('Theme: Dark',  lambda: output.config(bg='#0c0c0c', fg='#c8d8e8')),
        ('Theme: Matrix', lambda: output.config(bg='#001400', fg='#00ff41')),
        ('Theme: Amber', lambda: output.config(bg='#1a0e00', fg='#ffb000')),
        ('Theme: Classic', lambda: output.config(bg='#000080', fg='#ffffff')),
    ])
    menu_btn('Help', [
        ('Command Reference', lambda: write('\n'.join([
            '─── BUILT-IN COMMANDS ───────────────────────────────',
            'help              Show all commands',
            'cls / clear       Clear screen',
            'pwd               Print working directory',
            'cd <dir>          Change directory',
            'ls / dir [path]   List files',
            'mkdir <dir>       Create directory',
            'rm / del <path>   Delete file or folder',
            'cat / type <file> Print file contents',
            'cp <src> <dst>    Copy file',
            'mv <src> <dst>    Move/rename file',
            'touch <file>      Create empty file',
            'echo <text>       Print text',
            'find <name>       Find files by name',
            'tree [path]       Directory tree',
            'grep <term> <f>   Search text in file',
            '─── SYSTEM ──────────────────────────────────────────',
            'sysinfo           Full system information',
            'whoami            Current user',
            'hostname          Machine name',
            'uptime            System uptime',
            'ps / tasklist     Running processes',
            'env               Environment variables',
            'battery           Battery status',
            'netstat           Network info',
            'ping <host>       Ping a host',
            'ipconfig          IP configuration',
            '─── POWER ───────────────────────────────────────────',
            'shutdown          Shutdown system',
            'restart           Restart system',
            'sleep             Sleep mode',
            'bios              Open BIOS',
            '─── APPS ────────────────────────────────────────────',
            'open <app>        Open an application',
            'app list          List installed apps',
            'run <program>     Run a system program',
            'python <script>   Run Python script',
            'pip <cmd>         Pip package manager',
            'calc <expr>       Calculate expression',
            'download <url>    Download a file',
            '─── TERMINAL POWER ──────────────────────────────────',
            'block <feature>   Block any app/feature desktop-wide',
            'block bios        Lock BIOS access permanently',
            'block repair      Block system repair',
            'block all         Block EVERYTHING (except terminal)',
            'unblock <feature> Restore a blocked feature',
            'unblock all       Restore all features',
            'blocked           List all blocked features',
            'lock-bios         Lock BIOS immediately',
            'unlock-bios       Unlock BIOS access',
            'stability <level> Set BIOS stability (Stable/Degraded/Unstable/Critical)',
            'gsod              Trigger Green Screen of Death + auto reinstall',
            'self-delete       Terminal deletes itself → GSOD',
            'trigger-error <code> <name>  Trigger a specific GSOD error',
            '─── ADVANCED ────────────────────────────────────────',
            'sudo <cmd>        Run with elevated privileges',
            'history           Command history',
            'alias <n>=<c>     Create command alias',
            'unalias <name>    Remove alias',
            'aliases           List all aliases',
            'setvar <k> <v>    Set a custom variable',
            'getvars           List custom variables',
            'script <file>     Run .csh script file',
            'export <k=v>      Set environment variable',
            'bsod              Trigger BSOD',
            'delete            Uninstall Windows 7',
            '─── CUSTOM COMMANDS ─────────────────────────────────',
            'cmd add <name> <action>   Register a custom command',
            'cmd remove <name>         Remove a custom command',
            'cmd list                  List all custom commands',
            '─────────────────────────────────────────────────────',
        ]), '─ help ─')),
        ('About', lambda: write('Windows 7 Terminal v2.0\nBuilt on Python / tkinter\nType help for commands.')),
    ])

    # ── output area ────────────────────────────────────────────────────────
    output_frame = tk.Frame(term_win, bg='#0c0c0c')
    output_frame.pack(fill='both', expand=True, padx=0, pady=0)

    scrollbar = tk.Scrollbar(output_frame, bg='#1e1e2e',
                             troughcolor='#0c0c0c',
                             activebackground='#3a3a5a')
    scrollbar.pack(side='right', fill='y')

    output = tk.Text(output_frame,
                     bg='#0c0c0c', fg='#c8d8e8',
                     insertbackground='#c8d8e8',
                     font=('Consolas', 11),
                     relief='flat', bd=0,
                     yscrollcommand=scrollbar.set,
                     selectbackground='#2a4a7a',
                     wrap='word', padx=10, pady=8)
    output.pack(fill='both', expand=True)
    scrollbar.config(command=output.yview)

    # Text tags for colours
    output.tag_config('prompt',  foreground='#4ec9b0')
    output.tag_config('cmd',     foreground='#dcdcaa')
    output.tag_config('success', foreground='#6a9955')
    output.tag_config('error',   foreground='#f44747')
    output.tag_config('warn',    foreground='#ce9178')
    output.tag_config('info',    foreground='#9cdcfe')
    output.tag_config('header',  foreground='#569cd6')
    output.tag_config('white',   foreground='#ffffff')

    # ── state ──────────────────────────────────────────────────────────────
    term_state = {
        'cwd':       os.getcwd(),
        'history':   [],
        'hist_idx':  -1,
        'aliases':   {},          # alias name → command string
        'custom_cmds': {},        # custom command name → action string / lambda
        'env_vars':  {},          # user-set env vars
        'user_vars': {},          # setvar variables
        'sudo_active': False,
        'start_time': datetime.now(),
    }

    def expand_path(p):
        return os.path.abspath(
            os.path.join(term_state['cwd'], os.path.expanduser(p)))

    def write(text, tag=''):
        output.configure(state='normal')
        if tag:
            output.insert('end', text + '\n', tag)
        else:
            output.insert('end', text + '\n')
        output.see('end')
        output.configure(state='disabled')

    def write_prompt():
        output.configure(state='normal')
        user = state.get('user_name', 'user')
        cwd  = term_state['cwd']
        output.insert('end', f'\n{user}@WIN7 ', 'prompt')
        output.insert('end', f'{cwd}', 'info')
        output.insert('end', '> ', 'white')
        output.see('end')
        output.configure(state='disabled')

    # ── banner ─────────────────────────────────────────────────────────────
    write('╔══════════════════════════════════════════════════════╗', 'header')
    write('║        Windows 7  –  Command Prompt  v2.0           ║', 'header')
    write('║  Type  help  for a full command reference             ║', 'header')
    write('╚══════════════════════════════════════════════════════╝', 'header')
    write(f'  Logged in as: {state.get("user_name","user")}  |  {datetime.now().strftime("%A %d %B %Y  %H:%M")}', 'info')
    write(f'  OS Edition : {state.get("os_version","Ultimate")}', 'info')
    write('')

    # ── command handler ────────────────────────────────────────────────────
    def open_path_os(path):
        if not os.path.exists(path):
            write('Path not found.', 'error'); return
        try:
            if hasattr(os, 'startfile'):
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.run(['xdg-open', path], check=False)
            else:
                subprocess.run(f'start "" "{path}"', shell=True, check=False)
            write(f'Opened: {path}', 'success')
        except Exception as e:
            write(f'Error: {e}', 'error')

    def run_command(raw_cmd):
        global _BIOS_BLOCKED, _TERMINAL_SELF_DELETED
        raw_cmd = raw_cmd.strip()
        if not raw_cmd:
            write_prompt(); return

        # ── expand aliases ─────────────────────────────────────────────
        first_word = raw_cmd.split()[0].lower()
        if first_word in term_state['aliases']:
            raw_cmd = term_state['aliases'][first_word] + raw_cmd[len(first_word):]

        # ── variable substitution  $varname ───────────────────────────
        for k, v in {**term_state['user_vars'], **term_state['env_vars']}.items():
            raw_cmd = raw_cmd.replace(f'${k}', str(v))

        # ── history ────────────────────────────────────────────────────
        term_state['history'].append(raw_cmd)
        term_state['hist_idx'] = -1

        output.configure(state='normal')
        output.insert('end', f'\n> ', 'prompt')
        output.insert('end', raw_cmd + '\n', 'cmd')
        output.configure(state='disabled')

        parts = raw_cmd.split()
        key   = parts[0].lower() if parts else ''

        # ══════════════════════════════════════════════════════════════
        # BUILT-IN COMMANDS
        # ══════════════════════════════════════════════════════════════

        # ── help ───────────────────────────────────────────────────────
        if key == 'help':
            write('Type  help  in the menu bar (Help > Command Reference)  or:', 'info')
            write('  cls  pwd  cd  ls  mkdir  rm  cat  cp  mv  touch  echo', 'white')
            write('  find  tree  grep  sysinfo  whoami  ps  env  battery', 'white')
            write('  netstat  ping  ipconfig  shutdown  restart  sleep  bios', 'white')
            write('  open  run  python  pip  calc  download  sudo  history', 'white')
            write('  alias  unalias  aliases  setvar  getvars  script  export', 'white')
            write('  cmd add/remove/list  bsod  delete  exit', 'white')
            write('', '')
            write('  ── Security / OS Control ──', 'warn')
            write('  bios-security status          Show security + OS health', 'warn')
            write('  bios-security disable         Disable security (requires BIOS settings)', 'warn')
            write('  bios-security enable          Re-enable security policy', 'warn')
            write('  sudo apt delete <package>     Delete OS core files (security must be off)', 'warn')
            write('  ⚠  Deleting core files will corrupt the OS and force a reinstall.', 'error')

        # ── clear ──────────────────────────────────────────────────────
        elif key in ('cls', 'clear'):
            output.configure(state='normal')
            output.delete('1.0', 'end')
            output.configure(state='disabled')

        # ── pwd ────────────────────────────────────────────────────────
        elif key == 'pwd':
            write(term_state['cwd'], 'info')

        # ── cd ─────────────────────────────────────────────────────────
        elif key == 'cd':
            if len(parts) < 2:
                write(term_state['cwd'], 'info')
            else:
                target = expand_path(' '.join(parts[1:]))
                if os.path.isdir(target):
                    term_state['cwd'] = target
                    write(f'→ {target}', 'success')
                else:
                    write(f'Directory not found: {target}', 'error')

        # ── ls / dir ───────────────────────────────────────────────────
        elif key in ('ls', 'dir'):
            target = term_state['cwd'] if len(parts) == 1 else expand_path(' '.join(parts[1:]))
            try:
                entries = sorted(os.listdir(target))
                dirs  = [e for e in entries if os.path.isdir(os.path.join(target, e))]
                files = [e for e in entries if not os.path.isdir(os.path.join(target, e))]
                for d in dirs:
                    size = ''
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(
                            os.path.join(target, d))).strftime('%Y-%m-%d %H:%M')
                    except: mtime = ''
                    write(f'  <DIR>   {mtime:>17}   {d}/', 'info')
                for f in files:
                    try:
                        sz    = os.path.getsize(os.path.join(target, f))
                        mtime = datetime.fromtimestamp(os.path.getmtime(
                            os.path.join(target, f))).strftime('%Y-%m-%d %H:%M')
                        size  = f'{sz:>10,} B'
                    except: size = ''; mtime = ''
                    write(f'  {size}   {mtime:>17}   {f}')
                write(f'\n  {len(dirs)} dir(s),  {len(files)} file(s)', 'success')
            except Exception as e:
                write(str(e), 'error')

        # ── mkdir ──────────────────────────────────────────────────────
        elif key == 'mkdir':
            if len(parts) < 2:
                write('Usage: mkdir <name>', 'warn')
            else:
                path = expand_path(' '.join(parts[1:]))
                try:
                    os.makedirs(path, exist_ok=True)
                    write(f'Created: {path}', 'success')
                except Exception as e:
                    write(str(e), 'error')

        # ── rm / del ───────────────────────────────────────────────────
        elif key in ('rm', 'del'):
            if len(parts) < 2:
                write('Usage: rm <path>', 'warn')
            else:
                path = expand_path(' '.join(parts[1:]))
                try:
                    if os.path.isdir(path):
                        import shutil; shutil.rmtree(path)
                    else:
                        os.remove(path)
                    write(f'Deleted: {path}', 'success')
                except Exception as e:
                    write(str(e), 'error')

        # ── rmdir ──────────────────────────────────────────────────────
        elif key == 'rmdir':
            path = expand_path(' '.join(parts[1:])) if len(parts) > 1 else ''
            if not path:
                write('Usage: rmdir <dir>', 'warn')
            else:
                try:
                    os.rmdir(path)
                    write(f'Removed: {path}', 'success')
                except Exception as e:
                    write(str(e), 'error')

        # ── touch ──────────────────────────────────────────────────────
        elif key == 'touch':
            if len(parts) < 2:
                write('Usage: touch <file>', 'warn')
            else:
                path = expand_path(' '.join(parts[1:]))
                try:
                    open(path, 'a').close()
                    write(f'Created: {path}', 'success')
                except Exception as e:
                    write(str(e), 'error')

        # ── cat / type ─────────────────────────────────────────────────
        elif key in ('cat', 'type'):
            if len(parts) < 2:
                write('Usage: cat <file>', 'warn')
            else:
                path = expand_path(' '.join(parts[1:]))
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        write(f.read())
                except Exception as e:
                    write(str(e), 'error')

        # ── cp ─────────────────────────────────────────────────────────
        elif key == 'cp':
            if len(parts) < 3:
                write('Usage: cp <src> <dst>', 'warn')
            else:
                import shutil
                try:
                    shutil.copy2(expand_path(parts[1]),
                                 expand_path(' '.join(parts[2:])))
                    write('Copied.', 'success')
                except Exception as e:
                    write(str(e), 'error')

        # ── mv ─────────────────────────────────────────────────────────
        elif key == 'mv':
            if len(parts) < 3:
                write('Usage: mv <src> <dst>', 'warn')
            else:
                import shutil
                try:
                    shutil.move(expand_path(parts[1]),
                                expand_path(' '.join(parts[2:])))
                    write('Moved.', 'success')
                except Exception as e:
                    write(str(e), 'error')

        # ── echo ───────────────────────────────────────────────────────
        elif key == 'echo':
            write(' '.join(parts[1:]))

        # ── write (write text to file) ─────────────────────────────────
        elif key == 'write':
            # write <file> <text>
            if len(parts) < 3:
                write('Usage: write <file> <text>', 'warn')
            else:
                path = expand_path(parts[1])
                text = ' '.join(parts[2:])
                try:
                    with open(path, 'a', encoding='utf-8') as f:
                        f.write(text + '\n')
                    write(f'Written to {path}', 'success')
                except Exception as e:
                    write(str(e), 'error')

        # ── find ───────────────────────────────────────────────────────
        elif key == 'find':
            if len(parts) < 2:
                write('Usage: find <name>', 'warn')
            else:
                term_kw = ' '.join(parts[1:]).lower()
                found = 0
                for root_dir, dirs, files in os.walk(term_state['cwd']):
                    for f in files:
                        if term_kw in f.lower():
                            write(os.path.join(root_dir, f), 'info')
                            found += 1
                            if found > 100: break
                    if found > 100: break
                write(f'{found} result(s)', 'success')

        # ── grep ───────────────────────────────────────────────────────
        elif key == 'grep':
            if len(parts) < 3:
                write('Usage: grep <term> <file>', 'warn')
            else:
                term_kw = parts[1]
                path = expand_path(parts[2])
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                    hits = [(i+1, l.rstrip()) for i, l in enumerate(lines)
                            if term_kw.lower() in l.lower()]
                    if hits:
                        for n, l in hits:
                            write(f'  {n:>4}: {l}', 'info')
                        write(f'{len(hits)} match(es)', 'success')
                    else:
                        write('No matches found.', 'warn')
                except Exception as e:
                    write(str(e), 'error')

        # ── tree ───────────────────────────────────────────────────────
        elif key == 'tree':
            root_p = expand_path(parts[1]) if len(parts) > 1 else term_state['cwd']
            write(root_p, 'header')
            count = [0]
            def _tree(path, prefix='', depth=0):
                if depth > 5 or count[0] > 200: return
                try: entries = sorted(os.listdir(path))
                except: return
                for i, entry in enumerate(entries):
                    is_last = (i == len(entries) - 1)
                    connector = '└── ' if is_last else '├── '
                    full = os.path.join(path, entry)
                    tag = 'info' if os.path.isdir(full) else ''
                    write(prefix + connector + entry, tag)
                    count[0] += 1
                    if os.path.isdir(full):
                        ext = '    ' if is_last else '│   '
                        _tree(full, prefix + ext, depth+1)
            _tree(root_p)
            write(f'\n  {count[0]} item(s) shown', 'success')

        # ── sysinfo ────────────────────────────────────────────────────
        elif key == 'sysinfo':
            import platform
            uptime_delta = datetime.now() - term_state['start_time']
            uph, rem = divmod(int(uptime_delta.total_seconds()), 3600)
            upm, ups = divmod(rem, 60)
            lines = [
                '─── System Information ────────────────────────────',
                f'  OS Edition  : Windows 7 {state.get("os_version","Ultimate")}',
                f'  User        : {state.get("user_name","user")}',
                f'  Python      : {platform.python_version()}',
                f'  Platform    : {platform.system()} {platform.release()}',
                f'  Machine     : {platform.machine()}',
                f'  Processor   : {platform.processor() or "Unknown"}',
                f'  Hostname    : {platform.node()}',
                f'  Session up  : {uph}h {upm}m {ups}s',
                f'  Battery     : {get_battery_status()}',
                f'  CWD         : {term_state["cwd"]}',
                f'  Aliases     : {len(term_state["aliases"])}',
                f'  Custom cmds : {len(term_state["custom_cmds"])}',
                '───────────────────────────────────────────────────',
            ]
            for l in lines: write(l, 'info')
            try:
                import psutil
                mem = psutil.virtual_memory()
                write(f'  RAM         : {mem.used//(1024**2)} MB used / {mem.total//(1024**2)} MB total', 'info')
                write(f'  CPU usage   : {psutil.cpu_percent(interval=0.2)}%', 'info')
                write(f'  Disk (/)    : {psutil.disk_usage("/").percent}% used', 'info')
            except ImportError:
                write('  (Install psutil for RAM/CPU stats)', 'warn')

        # ── whoami ─────────────────────────────────────────────────────
        elif key == 'whoami':
            import platform
            write(f'{platform.node()}\\{state.get("user_name","user")}', 'info')

        # ── hostname ───────────────────────────────────────────────────
        elif key == 'hostname':
            import platform
            write(platform.node(), 'info')

        # ── uptime ─────────────────────────────────────────────────────
        elif key == 'uptime':
            delta = datetime.now() - term_state['start_time']
            h, rem = divmod(int(delta.total_seconds()), 3600)
            m, s   = divmod(rem, 60)
            write(f'Session uptime: {h}h {m}m {s}s', 'info')

        # ── ps / tasklist ──────────────────────────────────────────────
        elif key in ('ps', 'tasklist'):
            try:
                import psutil
                write('  PID    CPU%   MEM%   NAME', 'header')
                procs = sorted(psutil.process_iter(['pid','name','cpu_percent','memory_percent']),
                               key=lambda p: p.info['memory_percent'] or 0, reverse=True)
                for proc in procs[:20]:
                    i = proc.info
                    write(f'  {i["pid"]:>5}  {i["cpu_percent"] or 0:>5.1f}  '
                          f'{i["memory_percent"] or 0:>5.1f}%  {i["name"]}')
            except ImportError:
                result = subprocess.run(
                    ['tasklist' if os.name=='nt' else 'ps', 'aux' if os.name!='nt' else ''],
                    capture_output=True, text=True)
                write(result.stdout or result.stderr)

        # ── env ────────────────────────────────────────────────────────
        elif key == 'env':
            for k, v in sorted(os.environ.items()):
                write(f'  {k}={v}', 'info')
            if term_state['env_vars']:
                write('  ─── Session Variables ───', 'header')
                for k, v in term_state['env_vars'].items():
                    write(f'  {k}={v}', 'info')

        # ── export ─────────────────────────────────────────────────────
        elif key == 'export':
            if len(parts) < 2 or '=' not in parts[1]:
                write('Usage: export KEY=VALUE', 'warn')
            else:
                k, v = parts[1].split('=', 1)
                term_state['env_vars'][k] = v
                os.environ[k] = v
                write(f'Exported {k}={v}', 'success')

        # ── setvar / getvars ───────────────────────────────────────────
        elif key == 'setvar':
            if len(parts) < 3:
                write('Usage: setvar <name> <value>', 'warn')
            else:
                term_state['user_vars'][parts[1]] = ' '.join(parts[2:])
                write(f'Set ${parts[1]} = {" ".join(parts[2:])}', 'success')
        elif key == 'getvars':
            if not term_state['user_vars']:
                write('No variables set. Use: setvar <name> <value>', 'warn')
            else:
                for k, v in term_state['user_vars'].items():
                    write(f'  ${k} = {v}', 'info')

        # ── battery ────────────────────────────────────────────────────
        elif key == 'battery':
            write(get_battery_status(), 'info')

        # ── netstat ────────────────────────────────────────────────────
        elif key == 'netstat':
            try:
                import psutil
                conns = psutil.net_connections(kind='inet')
                write('  Proto  Local Addr         Remote Addr        Status', 'header')
                for c in conns[:20]:
                    la = f'{c.laddr.ip}:{c.laddr.port}' if c.laddr else '-'
                    ra = f'{c.raddr.ip}:{c.raddr.port}' if c.raddr else '-'
                    write(f'  TCP    {la:<20} {ra:<20} {c.status}')
            except ImportError:
                r = subprocess.run(['netstat','-an'], capture_output=True, text=True)
                write(r.stdout or 'netstat unavailable')

        # ── ipconfig ───────────────────────────────────────────────────
        elif key == 'ipconfig':
            try:
                import psutil, socket
                write(f'  Hostname : {socket.gethostname()}', 'info')
                for iface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family.name in ('AF_INET', 'AF_INET6'):
                            write(f'  {iface:<16} {addr.family.name}  {addr.address}', 'info')
            except ImportError:
                cmd_str = 'ipconfig' if os.name=='nt' else 'ip addr'
                r = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
                write(r.stdout or r.stderr)

        # ── ping ───────────────────────────────────────────────────────
        elif key == 'ping':
            if len(parts) < 2:
                write('Usage: ping <host>', 'warn')
            else:
                host = parts[1]
                count_flag = '-n' if os.name == 'nt' else '-c'
                write(f'Pinging {host}…', 'info')
                try:
                    r = subprocess.run(
                        ['ping', count_flag, '4', host],
                        capture_output=True, text=True, timeout=10)
                    write(r.stdout or r.stderr)
                except Exception as e:
                    write(str(e), 'error')

        # ── open ───────────────────────────────────────────────────────
        elif key == 'open':
            if len(parts) < 2:
                write('Usage: open <app|file>', 'warn')
            else:
                target = ' '.join(parts[1:]).lower()
                app_map_local = {
                    'terminal': show_terminal_app,
                    'explorer': show_file_explorer, 'files': show_file_explorer,
                    'calc': show_calculator_app, 'calculator': show_calculator_app,
                    'paint': show_paint_app,
                    'notepad': show_text_editor, 'editor': show_text_editor,
                    'media': show_media_player, 'player': show_media_player,
                    'excel': show_excel_app, 'spreadsheet': show_excel_app,
                    'calendar': show_calendar_app,
                    'ai': show_ai_app, 'celine': show_ai_app,
                    'settings': show_settings_app,
                    'control': show_control_panel,
                    'security': show_windows_security,
                    'recycle': show_recycle_bin,
                    'network': show_network_center,
                    'device': show_device_manager,
                    'update': show_windows_update,
                    'snake': show_snake_game,
                    'mines': show_minesweeper_game, 'minesweeper': show_minesweeper_game,
                    'tictactoe': show_tic_tac_toe_game,
                    'noteapp': show_sticky_notes, 'sticky': show_sticky_notes,
                    # 20 new apps
                    'journal': show_journal, 'diary': show_journal,
                    'alarm': show_alarm_manager, 'reminder': show_alarm_manager,
                    'bookmarks': show_bookmark_manager, 'bookmark': show_bookmark_manager,
                    'pomodoro': show_pomodoro, 'focus': show_pomodoro,
                    'habit': show_habit_tracker, 'habits': show_habit_tracker,
                    'converter': show_unit_converter, 'unit': show_unit_converter,
                    'password': show_password_generator, 'passgen': show_password_generator,
                    'analyzer': show_text_analyzer, 'wordcount': show_text_analyzer,
                    'quote': show_quote_of_day, 'inspiration': show_quote_of_day,
                    'clipboard': show_clipboard_history,
                    'shortcuts': show_shortcuts_manager,
                    'worldclock': show_world_clock, 'wclock': show_world_clock,
                    'colorpicker': show_color_picker, 'color': show_color_picker,
                    'typing': show_typing_test, 'typingtest': show_typing_test,
                    'flashcards': show_math_flashcards, 'flash': show_math_flashcards,
                    'notesearch': show_note_search,
                    'stopwatch': show_stopwatch, 'watch': show_stopwatch,
                    'finance': show_finance_tracker, 'budget': show_finance_tracker,
                    'ascii': show_ascii_art, 'asciiart': show_ascii_art,
                    'taskboard': show_task_board, 'kanban': show_task_board,
                }
                if target in app_map_local:
                    write(f'Opening {target}…', 'success')
                    app_map_local[target]()
                else:
                    open_path_os(expand_path(target))

        # ── app list ───────────────────────────────────────────────────
        elif key in ('app', 'apps') and (len(parts) == 1 or (len(parts) > 1 and parts[1] == 'list')):
            write('─── Available Applications ──────────────────────────', 'header')
            all_apps = [
                ('terminal','Command Prompt'),('explorer','File Explorer'),
                ('calc','Calculator'),('paint','Paint'),('notepad','Text Editor'),
                ('media','Media Player'),('excel','Spreadsheet'),('calendar','Calendar'),
                ('ai','Assistant'),('settings','Settings'),('control','Control Panel'),
                ('security','Windows Security'),('recycle','Recycle Bin'),
                ('network','Network Center'),('snake','Snake Game'),
                ('minesweeper','Minesweeper'),('tictactoe','Tic Tac Toe'),
                ('sticky','Sticky Notes'),
                ('journal','Journal / Diary'),('alarm','Alarm Manager'),
                ('bookmarks','Bookmark Manager'),('pomodoro','Pomodoro Timer'),
                ('habit','Habit Tracker'),('converter','Unit Converter'),
                ('password','Password Generator'),('analyzer','Text Analyzer'),
                ('quote','Quote of the Day'),('clipboard','Clipboard History'),
                ('shortcuts','Chat Shortcuts'),('worldclock','World Clock'),
                ('color','Color Picker'),('typing','Typing Speed Test'),
                ('flashcards','Math Flashcards'),('notesearch','Note Search'),
                ('stopwatch','Stopwatch'),('finance','Finance Tracker'),
                ('ascii','ASCII Art'),('taskboard','Task Board'),
            ]
            for cmd_name, friendly in all_apps:
                write(f'  open {cmd_name:<18}  {friendly}', 'info')
            write(f'\n  {len(all_apps)} apps available. Usage: open <name>', 'success')
            if len(parts) < 2:
                write('Usage: run <program>', 'warn')
            else:
                prog = ' '.join(parts[1:])
                try:
                    subprocess.Popen(prog, shell=True)
                    write(f'Started: {prog}', 'success')
                except Exception as e:
                    write(str(e), 'error')

        # ── python ─────────────────────────────────────────────────────
        elif key == 'python':
            if len(parts) < 2:
                write('Usage: python <script.py> [args]', 'warn')
            else:
                try:
                    r = subprocess.run(
                        ['python'] + parts[1:],
                        capture_output=True, text=True,
                        cwd=term_state['cwd'])
                    if r.stdout: write(r.stdout)
                    if r.stderr: write(r.stderr, 'error')
                except Exception as e:
                    write(str(e), 'error')

        # ── pip ────────────────────────────────────────────────────────
        elif key == 'pip':
            try:
                r = subprocess.run(
                    ['pip'] + parts[1:],
                    capture_output=True, text=True)
                if r.stdout: write(r.stdout)
                if r.stderr: write(r.stderr, 'warn')
            except Exception as e:
                write(str(e), 'error')

        # ── calc ───────────────────────────────────────────────────────
        elif key == 'calc':
            if len(parts) < 2:
                write('Usage: calc <expression>', 'warn')
            else:
                expr = ' '.join(parts[1:])
                try:
                    import math as _math
                    result = eval(expr, {'__builtins__': {}},
                                  {k: getattr(_math, k) for k in dir(_math)
                                   if not k.startswith('_')})
                    write(f'  {expr} = {result}', 'success')
                except Exception as e:
                    write(f'Calc error: {e}', 'error')

        # ── download ───────────────────────────────────────────────────
        elif key == 'download':
            if len(parts) < 2:
                write('Usage: download <url>', 'warn')
            else:
                url = parts[1]
                import urllib.request, urllib.parse
                fname = os.path.basename(urllib.parse.urlparse(url).path) or 'download'
                target = expand_path(fname)
                try:
                    write(f'Downloading {url}…', 'info')
                    urllib.request.urlretrieve(url, target)
                    write(f'Saved to {target}', 'success')
                except Exception as e:
                    write(f'Download failed: {e}', 'error')

        # ── history ────────────────────────────────────────────────────
        elif key == 'history':
            if not term_state['history']:
                write('No history yet.', 'warn')
            else:
                for i, h in enumerate(term_state['history'][:-1], 1):
                    write(f'  {i:>3}  {h}', 'info')

        # ── alias / unalias / aliases ──────────────────────────────────
        elif key == 'alias':
            if len(parts) < 2 or '=' not in raw_cmd:
                write('Usage: alias <name>=<command>', 'warn')
            else:
                rest = raw_cmd[len('alias'):].strip()
                name, cmd_str = rest.split('=', 1)
                term_state['aliases'][name.strip()] = cmd_str.strip()
                write(f'Alias set: {name.strip()} → {cmd_str.strip()}', 'success')
        elif key == 'unalias':
            name = parts[1] if len(parts) > 1 else ''
            if name in term_state['aliases']:
                del term_state['aliases'][name]
                write(f'Removed alias: {name}', 'success')
            else:
                write(f'Alias not found: {name}', 'error')
        elif key == 'aliases':
            if not term_state['aliases']:
                write('No aliases defined.', 'warn')
            else:
                for n, c in term_state['aliases'].items():
                    write(f'  {n:<16} → {c}', 'info')

        # ── script ─────────────────────────────────────────────────────
        elif key == 'script':
            if len(parts) < 2:
                write('Usage: script <file.csh>', 'warn')
            else:
                path = expand_path(parts[1])
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = [l.strip() for l in f if l.strip()
                                 and not l.strip().startswith('#')]
                    write(f'Running script: {path}  ({len(lines)} commands)', 'info')
                    for line in lines:
                        run_command(line)
                except Exception as e:
                    write(str(e), 'error')

        # ── ════════════════════════════════════════════════════════════
        # CUSTOM COMMANDS  (cmd add / remove / list / run)
        # ════════════════════════════════════════════════════════════════
        elif key == 'cmd':
            if len(parts) < 2:
                write('Usage: cmd add <name> <action>  |  cmd remove <name>  |  cmd list', 'warn')

            elif parts[1].lower() == 'list':
                if not term_state['custom_cmds']:
                    write('No custom commands. Use:  cmd add <name> <action>', 'warn')
                else:
                    write('  ─── Custom Commands ─────────────────────────────', 'header')
                    for n, a in term_state['custom_cmds'].items():
                        write(f'  {n:<18} → {a}', 'info')

            elif parts[1].lower() == 'add':
                # cmd add <name> <action…>
                # action can be:
                #   open <appname>     → call show_<appname>
                #   run <shell cmd>    → subprocess
                #   echo <text>        → print text
                #   say <text>         → system notification
                #   <any terminal cmd> → run_command recursively
                if len(parts) < 4:
                    write('Usage: cmd add <name> <action>', 'warn')
                    write('  Examples:', 'info')
                    write('    cmd add myai   open ai', 'info')
                    write('    cmd add hi     echo Hello!', 'info')
                    write('    cmd add files  open explorer', 'info')
                    write('    cmd add mydir  ls /home', 'info')
                    write('    cmd add note   say Remember to save!', 'info')
                else:
                    name   = parts[2].lower()
                    action = ' '.join(parts[3:])
                    term_state['custom_cmds'][name] = action
                    write(f'Custom command added: {name} → {action}', 'success')
                    write(f'  Use it by typing: {name}', 'info')

            elif parts[1].lower() == 'remove':
                if len(parts) < 3:
                    write('Usage: cmd remove <name>', 'warn')
                else:
                    name = parts[2].lower()
                    if name in term_state['custom_cmds']:
                        del term_state['custom_cmds'][name]
                        write(f'Removed custom command: {name}', 'success')
                    else:
                        write(f'Custom command not found: {name}', 'error')
            else:
                write(f'Unknown cmd sub-command: {parts[1]}', 'error')

        # ── sudo ───────────────────────────────────────────────────────
        elif key == 'sudo':
            if len(parts) < 2:
                write('Usage: sudo <command>', 'warn')
            else:
                sudocmd = ' '.join(parts[1:])
                sec_disabled = state.get('bios_security_disabled', False)

                write(f'[sudo] Elevated: {sudocmd}', 'warn')
                audit_log('SUDO_ATTEMPT', sudocmd[:120], 'WARN')

                # ── apt delete / rm -rf system files (requires security off) ──
                _DESTROYS_OS = [
                    r'apt[-\s]*(delete|remove|purge).*core',
                    r'apt[-\s]*(delete|remove|purge)',
                    r'\brm\s+-rf\b',
                    r'\bdel\s+/[fsq]',
                    r'\brd\s+/[sq]',
                    r'\bformat\b',
                    r'\bdiskpart\b',
                    r'\bfdisk\b',
                    r'\breg\s+delete\b',
                    r'\bwmic\b.*delete',
                    r'\bpowershell\b.*-enc\b',
                    r'\bnet\s+user\b.*\/(add|delete)',
                ]
                _is_destructive = any(re.search(p, sudocmd.lower())
                                      for p in _DESTROYS_OS)

                if _is_destructive:
                    if not sec_disabled:
                        # Security ON — ask for password to unlock
                        write('⚠  This command will DELETE core OS files.', 'warn')
                        write('   Enter your Windows password to enable sudo privileges:', 'warn')
                        write('', '')

                        # Inline password prompt inside terminal
                        _pwd_frame = tk.Frame(term_win, bg='#0a0f1a')
                        _pwd_frame.pack(fill='x', padx=8, pady=4)

                        tk.Label(_pwd_frame, text='[sudo] password for root:',
                                 bg='#0a0f1a', fg='#ffaa00',
                                 font=('Consolas', 11)).pack(side='left', padx=(4,8))

                        _pwd_var = tk.StringVar()
                        _pwd_entry = tk.Entry(_pwd_frame, textvariable=_pwd_var,
                                              show='●', font=('Consolas', 11),
                                              bg='#060a14', fg='#ffffff',
                                              insertbackground='white',
                                              relief='flat',
                                              highlightthickness=2,
                                              highlightbackground='#3a5a00',
                                              highlightcolor='#88cc00',
                                              width=28)
                        _pwd_entry.pack(side='left', ipady=4)
                        _pwd_entry.focus_set()

                        _attempts = {'n': 0}

                        def _on_pwd_confirm(event=None):
                            entered = _pwd_var.get()
                            sec = load_security()
                            correct = (sec and
                                       verify_password(entered,
                                                       sec.get('salt',''),
                                                       sec.get('key','')))
                            # Destroy the inline prompt regardless
                            try:
                                _pwd_frame.destroy()
                            except Exception:
                                pass

                            if correct:
                                audit_log('SUDO_PASSWORD_AUTH_OK',
                                          f'Unlocked for: {sudocmd[:80]}', 'CRITICAL')
                                write('[sudo] Authentication succeeded.', 'warn')
                                write('⚠  BIOS security temporarily bypassed for this command.',
                                      'warn')
                                write('   Executing destructive command...', 'error')
                                write('', '')

                                # Temporarily enable for this one command
                                state['bios_security_disabled'] = True
                                save_state()

                                # Run the deletion sequence
                                fake_files = [
                                    'Removing ntoskrnl.exe...',
                                    'Removing hal.dll...',
                                    'Removing win32k.sys...',
                                    'Removing ntfs.sys...',
                                    'Removing smss.exe...',
                                    'Removing csrss.exe...',
                                    'Removing winlogon.exe...',
                                    'Removing lsass.exe...',
                                    'Removing services.exe...',
                                    'Removing System32\\drivers\\...',
                                ]

                                def _run_deletion(idx=0):
                                    if not term_win.winfo_exists():
                                        return
                                    if idx < len(fake_files):
                                        write(fake_files[idx], 'error')
                                        term_win.after(180,
                                            lambda: _run_deletion(idx+1))
                                    else:
                                        write('', '')
                                        write('⚠  CRITICAL: Core OS files deleted.',
                                              'error')
                                        write('   Windows 7 will crash on next boot.',
                                              'error')
                                        write('   BSOD in 15 seconds...', 'warn')
                                        state['core_deleted'] = True
                                        state['os_corrupted'] = True
                                        save_state()
                                        def trigger_bsod():
                                            if desktop_win and desktop_win.winfo_exists():
                                                desktop_win.withdraw()
                                            if term_win.winfo_exists():
                                                term_win.destroy()
                                            show_bsod(
                                                error_code='0x0000007B',
                                                error_name='INACCESSIBLE_BOOT_DEVICE',
                                                on_restart=lambda: show_bios_boot_selector(reinstall=False),
                                                auto_restart_ms=8000
                                            )
                                        term_win.after(15000, trigger_bsod)

                                _run_deletion()

                            else:
                                _attempts['n'] += 1
                                audit_log('SUDO_PASSWORD_FAIL',
                                          f'Attempt {_attempts["n"]}', 'WARN')
                                if _attempts['n'] >= 3:
                                    write('[sudo] 3 incorrect password attempts.',
                                          'error')
                                    write('⛔  sudo: authentication failure', 'error')
                                    play_windows7_error()
                                else:
                                    write(
                                        f'[sudo] Sorry, try again. '
                                        f'({3 - _attempts["n"]} attempt(s) left)',
                                        'error')
                                    # Re-show prompt for retry
                                    _pwd_var.set('')
                                    _retry_frame = tk.Frame(term_win, bg='#0a0f1a')
                                    _retry_frame.pack(fill='x', padx=8, pady=4)
                                    tk.Label(_retry_frame,
                                             text='[sudo] password for root:',
                                             bg='#0a0f1a', fg='#ffaa00',
                                             font=('Consolas', 11)).pack(
                                             side='left', padx=(4,8))
                                    _retry_var = tk.StringVar()
                                    _retry_e = tk.Entry(_retry_frame,
                                                        textvariable=_retry_var,
                                                        show='●',
                                                        font=('Consolas', 11),
                                                        bg='#060a14', fg='white',
                                                        insertbackground='white',
                                                        relief='flat',
                                                        highlightthickness=2,
                                                        highlightbackground='#3a0000',
                                                        width=28)
                                    _retry_e.pack(side='left', ipady=4)
                                    _retry_e.focus_set()

                                    # Override _pwd_var/_pwd_entry for next confirm
                                    _pwd_var.__init__(value='')

                                    def _on_retry(e=None,
                                                  rf=_retry_frame,
                                                  rv=_retry_var):
                                        entered2 = rv.get()
                                        sec2 = load_security()
                                        ok = (sec2 and
                                              verify_password(entered2,
                                                              sec2.get('salt',''),
                                                              sec2.get('key','')))
                                        try:
                                            rf.destroy()
                                        except Exception:
                                            pass
                                        if ok:
                                            _attempts['n'] = 0
                                            _on_pwd_confirm.__wrapped__ = True
                                            # Simulate correct — re-call clean path
                                            audit_log('SUDO_PASSWORD_AUTH_OK',
                                                      f'Retry OK: {sudocmd[:60]}',
                                                      'CRITICAL')
                                            write('[sudo] Authentication succeeded.',
                                                  'warn')
                                            state['bios_security_disabled'] = True
                                            state['core_deleted'] = True
                                            state['os_corrupted'] = True
                                            save_state()
                                            write('⚠  Core files deleted. BSOD in 15s.',
                                                  'error')
                                            def trigger_bsod_secure():
                                                if desktop_win and desktop_win.winfo_exists():
                                                    desktop_win.withdraw()
                                                if term_win.winfo_exists():
                                                    term_win.destroy()
                                                show_bsod(
                                                    error_code='0x0000007B',
                                                    error_name='INACCESSIBLE_BOOT_DEVICE',
                                                    on_restart=lambda: show_bios_boot_selector(reinstall=False),
                                                    auto_restart_ms=8000
                                                )
                                            term_win.after(15000, trigger_bsod_secure)
                                        else:
                                            write('[sudo] 3 incorrect password attempts.',
                                                  'error')
                                            write('⛔  sudo: authentication failure',
                                                  'error')
                                            play_windows7_error()

                                    _retry_e.bind('<Return>', _on_retry)

                        _pwd_entry.bind('<Return>', _on_pwd_confirm)
                        audit_log('SUDO_PASSWORD_PROMPTED',
                                  sudocmd[:80], 'WARN')

                    else:
                        # Security already OFF — run directly (no prompt needed)
                        write('⚠  Security policy is DISABLED. Executing...', 'warn')
                        audit_log('SUDO_DESTRUCTIVE_ALLOWED', sudocmd[:120], 'CRITICAL')
                        fake_files = [
                            'Removing ntoskrnl.exe...',
                            'Removing hal.dll...',
                            'Removing win32k.sys...',
                            'Removing ntfs.sys...',
                            'Removing smss.exe...',
                            'Removing csrss.exe...',
                            'Removing winlogon.exe...',
                            'Removing lsass.exe...',
                            'Removing services.exe...',
                            'Removing System32\\drivers\\...',
                        ]
                        def show_deletion(idx=0):
                            if not term_win.winfo_exists():
                                return
                            if idx < len(fake_files):
                                write(fake_files[idx], 'error')
                                term_win.after(180, lambda: show_deletion(idx+1))
                            else:
                                write('', '')
                                write('⚠  CRITICAL: Core OS files have been deleted.',
                                      'error')
                                write('   Windows 7 will fail to boot on next restart.',
                                      'error')
                                write('   System will become unbootable in 15 seconds...',
                                      'warn')
                                state['core_deleted'] = True
                                state['os_corrupted'] = True
                                save_state()
                                def trigger_bsod_core():
                                    if desktop_win and desktop_win.winfo_exists():
                                        desktop_win.withdraw()
                                    if term_win.winfo_exists():
                                        term_win.destroy()
                                    show_bsod(
                                        error_code='0x0000007B',
                                        error_name='INACCESSIBLE_BOOT_DEVICE',
                                        on_restart=lambda: show_bios_boot_selector(reinstall=False),
                                        auto_restart_ms=8000
                                    )
                                term_win.after(15000, trigger_bsod_core)
                        show_deletion()

                elif sudocmd.strip().lower() in ('reboot', 'shutdown now', 'shutdown'):
                    if state.get('core_deleted'):
                        write('System integrity failure — cannot safely restart.', 'error')
                        term_win.after(2000, lambda: [
                            term_win.destroy() if term_win.winfo_exists() else None,
                            show_bsod(error_code='0x000000F4',
                                      error_name='CRITICAL_OBJECT_TERMINATION',
                                      on_restart=lambda: show_bios_boot_selector(reinstall=False))
                        ])
                        return
                    perform_restart()
                    return
                else:
                    try:
                        r = subprocess.run(sudocmd, shell=True,
                                           capture_output=True, text=True,
                                           cwd=term_state['cwd'], timeout=15)
                        if r.stdout: write(r.stdout)
                        if r.stderr: write(r.stderr, 'warn')
                    except subprocess.TimeoutExpired:
                        write('sudo command timed out (15s).', 'error')
                    except Exception as e:
                        write(str(e), 'error')

        # ── bios-security command ───────────────────────────────────────
        elif key == 'bios-security':
            action = parts[1].lower() if len(parts) > 1 else ''
            if action == 'disable':
                bs = state.get('bios_settings', {})
                flash_prot = bs.get('flash_prot', 'Enabled')
                secure_boot = bs.get('secure_boot', 'Enabled')
                if flash_prot == 'Disabled' and secure_boot == 'Disabled':
                    state['bios_security_disabled'] = True
                    save_state()
                    audit_log('BIOS_SECURITY_DISABLED', 'Via terminal command', 'CRITICAL')
                    write('⚠  BIOS Security DISABLED.', 'warn')
                    write('   Destructive sudo commands are now permitted.', 'warn')
                    write('   sudo apt delete, rm -rf, etc. will DELETE core OS files.', 'error')
                    write('   USE AT YOUR OWN RISK.', 'error')
                else:
                    write('❌  Cannot disable security — BIOS settings block it.', 'error')
                    write('   In BIOS → Security: set Flash Protection=Disabled,', 'warn')
                    write('   Secure Boot=Disabled, then restart terminal.', 'warn')
            elif action == 'enable':
                state['bios_security_disabled'] = False
                save_state()
                audit_log('BIOS_SECURITY_ENABLED', '', 'INFO')
                write('✅  BIOS Security re-enabled. Dangerous commands blocked.', 'info')
            elif action == 'status':
                disabled = state.get('bios_security_disabled', False)
                write(f'Security: {"DISABLED ⚠" if disabled else "ENABLED ✅"}', 
                      'warn' if disabled else 'info')
                write(f'Core files: {"DELETED ☠" if state.get("core_deleted") else "OK ✅"}',
                      'error' if state.get('core_deleted') else 'info')
                write(f'OS bootable: {"NO ⚠" if state.get("os_corrupted") else "YES ✅"}',
                      'error' if state.get('os_corrupted') else 'info')
            else:
                write('Usage: bios-security [disable|enable|status]', 'warn')

        # ── power ──────────────────────────────────────────────────────
        elif key == 'shutdown':
            write('Shutting down…', 'warn'); perform_shutdown(); return
        elif key == 'restart':
            write('Restarting…', 'warn'); perform_restart(); return
        elif key == 'sleep':
            write('Going to sleep…', 'warn'); perform_sleep(); return
        elif key == 'bios':
            write('Opening BIOS…', 'info'); show_bios_boot_menu()
        elif key == 'bsod':
            trigger_bsod()

        elif key == 'gsod':
            write('⚠  Triggering GSOD — Windows auto-reinstall will begin!', 'error')
            audit_log('TERMINAL_GSOD', 'Manual GSOD triggered from terminal', 'CRITICAL')
            term_win.after(1500, lambda: show_gsod())

        # ── block: disable any feature or app from the desktop ────────────
        elif key == 'block':
            # block <feature>  — removes it from APP_MAP and ACTIVE launches
            if len(parts) < 2:
                write('Usage: block <feature_name>  (e.g. block paint)', 'warn')
                write('       block repair           — block system repair', 'warn')
                write('       block bios             — lock BIOS access', 'warn')
                write('       block all              — block everything except terminal', 'warn')
            else:
                target = ' '.join(parts[1:]).lower().strip()
                if target == 'all':
                    # Block every APP_MAP key except terminal itself
                    for k in list(APP_MAP.keys()):
                        _TERMINAL_BLOCKED_FEATURES.add(k)
                    write('⛔  ALL features blocked. Only Terminal remains.', 'error')
                    audit_log('TERMINAL_BLOCK_ALL', 'Terminal blocked all features', 'CRITICAL')
                elif target in ('bios', 'bios setup'):
                    _BIOS_BLOCKED = True
                    _TERMINAL_BLOCKED_FEATURES.add('bios')
                    _TERMINAL_BLOCKED_FEATURES.add('bios setup')
                    write('🔒  BIOS access LOCKED by Terminal. Restart required to unlock.', 'warn')
                    audit_log('TERMINAL_BIOS_LOCKED', 'BIOS blocked from terminal', 'CRITICAL')
                elif target in ('repair', 'system repair', 'windows repair'):
                    _TERMINAL_BLOCKED_FEATURES.add('repair')
                    _TERMINAL_BLOCKED_FEATURES.add('system repair')
                    _TERMINAL_BLOCKED_FEATURES.add('windows repair')
                    write('⛔  System Repair BLOCKED. Windows cannot self-repair until unblocked.', 'error')
                    audit_log('TERMINAL_BLOCK_REPAIR', 'Repair blocked from terminal', 'CRITICAL')
                elif target in APP_MAP or target.replace(' ', '_') in APP_MAP:
                    _TERMINAL_BLOCKED_FEATURES.add(target)
                    write(f'⛔  "{target}" blocked — it will show an Access Denied error when launched.', 'error')
                    audit_log('TERMINAL_BLOCK', target, 'WARN')
                else:
                    # Block it anyway — store the key
                    _TERMINAL_BLOCKED_FEATURES.add(target)
                    write(f'⛔  "{target}" added to block list.', 'warn')

        # ── unblock: restore a feature ─────────────────────────────────────
        elif key == 'unblock':
            if len(parts) < 2:
                if _TERMINAL_BLOCKED_FEATURES:
                    write('  Currently blocked:', 'header')
                    for f in sorted(_TERMINAL_BLOCKED_FEATURES):
                        write(f'    • {f}', 'error')
                    write('Usage: unblock <feature>  |  unblock all', 'warn')
                else:
                    write('No features are currently blocked.', 'info')
            else:
                target = ' '.join(parts[1:]).lower().strip()
                if target == 'all':
                    _TERMINAL_BLOCKED_FEATURES.clear()
                    _BIOS_BLOCKED = False
                    write('✅  All blocks removed. All features restored.', 'success')
                    audit_log('TERMINAL_UNBLOCK_ALL', '', 'INFO')
                elif target in _TERMINAL_BLOCKED_FEATURES:
                    _TERMINAL_BLOCKED_FEATURES.discard(target)
                    if target in ('bios', 'bios setup'):
                        _BIOS_BLOCKED = False
                    write(f'✅  "{target}" unblocked.', 'success')
                else:
                    write(f'"{target}" is not in the block list.', 'warn')

        # ── blocked: list all blocked features ─────────────────────────────
        elif key == 'blocked':
            if _TERMINAL_BLOCKED_FEATURES:
                write('  ─── Blocked Features ───────────────────────────────', 'header')
                for f in sorted(_TERMINAL_BLOCKED_FEATURES):
                    write(f'    ⛔  {f}', 'error')
                write(f'  BIOS locked: {"YES" if _BIOS_BLOCKED else "NO"}', 'warn' if _BIOS_BLOCKED else 'info')
            else:
                write('  No features blocked. System fully accessible.', 'success')

        # ── lock-bios: prevent BIOS from being opened ──────────────────────
        elif key == 'lock-bios':
            _BIOS_BLOCKED = True
            _TERMINAL_BLOCKED_FEATURES.add('bios')
            _TERMINAL_BLOCKED_FEATURES.add('bios setup')
            write('🔐  BIOS LOCKED. Cannot be accessed until "unblock bios" is run.', 'warn')
            write('    This prevents BIOS stability changes from affecting the desktop.', 'info')
            audit_log('TERMINAL_BIOS_LOCKED', 'Direct lock-bios command', 'CRITICAL')

        # ── unlock-bios ────────────────────────────────────────────────────
        elif key == 'unlock-bios':
            _BIOS_BLOCKED = False
            _TERMINAL_BLOCKED_FEATURES.discard('bios')
            _TERMINAL_BLOCKED_FEATURES.discard('bios setup')
            write('🔓  BIOS unlocked. Access restored.', 'success')
            audit_log('TERMINAL_BIOS_UNLOCKED', '', 'INFO')

        # ── stability: control BIOS stability directly from terminal ───────
        elif key == 'stability':
            if len(parts) < 2:
                cur = state.get('bios_settings', {}).get('system_stability', 'Stable')
                write(f'Current stability: {cur}', 'info')
                write('Usage: stability <Stable|Degraded|Unstable|Critical>', 'warn')
            else:
                level = parts[1].capitalize()
                valid = ['Stable', 'Degraded', 'Unstable', 'Critical']
                if level not in valid:
                    write(f'Invalid level. Choose: {", ".join(valid)}', 'error')
                else:
                    state.setdefault('bios_settings', {})['system_stability'] = level
                    save_state()
                    write(f'⚡  System stability set to: {level}', 'warn' if level != 'Stable' else 'success')
                    write('    Applying BIOS stability effects to desktop…', 'info')
                    audit_log('TERMINAL_STABILITY', level, 'WARN')
                    if desktop_win and desktop_win.winfo_exists():
                        desktop_win.after(500, _apply_bios_stability_to_desktop)
                    if level == 'Critical':
                        write('☠  CRITICAL stability — GSOD will trigger in 5 seconds!', 'error')
                        term_win.after(5000, lambda: show_gsod(
                            '0xFFFFFFFF', 'CRITICAL_PROCESS_DIED — stability=Critical'))

        # ── self-delete: terminal deletes itself and triggers GSOD ─────────
        elif key == 'self-delete':
            write('', '')
            write('⚠⚠⚠  TERMINAL SELF-DELETION SEQUENCE INITIATED  ⚠⚠⚠', 'error')
            write('', '')
            audit_log('TERMINAL_SELF_DELETE', 'Terminal initiated self-deletion', 'CRITICAL')

            steps = [
                ('Flushing terminal command history…',    300),
                ('Removing terminal.exe from memory…',   500),
                ('Wiping terminal registry entries…',    400),
                ('Clearing PATH variable…',              350),
                ('Removing terminal data directory…',    400),
                ('Corrupting terminal binaries…',        500),
                ('Deleting cmd.exe…',                    300),
                ('Deleting conhost.exe…',                300),
                ('Removing Windows Terminal package…',   450),
                ('Self-destruction complete. ☠',         200),
            ]

            def _self_del_seq(idx=0):
                if not term_win.winfo_exists():
                    return
                if idx < len(steps):
                    msg, delay = steps[idx]
                    write(f'  [{idx+1:02d}/{len(steps)}] {msg}', 'error')
                    term_win.after(delay, lambda: _self_del_seq(idx + 1))
                else:
                    write('', '')
                    write('☠  Terminal process has deleted itself.', 'error')
                    write('   Core OS integrity compromised. GSOD imminent…', 'error')
                    write('', '')

                    _TERMINAL_SELF_DELETED = True
                    state['core_deleted'] = True
                    state['os_corrupted'] = True
                    save_state()
                    audit_log('TERMINAL_SELF_DELETED', 'Self-deletion complete — GSOD', 'CRITICAL')

                    def _finish():
                        try:
                            term_win.destroy()
                        except Exception:
                            pass
                        show_gsod('0xDEAD0001', 'TERMINAL_SELF_DELETION_DETECTED',
                                  on_restart=lambda: show_bios_boot_selector(reinstall=True))
                    term_win.after(2000, _finish)

            _self_del_seq()
            return  # prevent write_prompt after this

        # ── error-trigger: cause any named error → GSOD ────────────────────
        elif key == 'trigger-error':
            code = parts[1] if len(parts) > 1 else '0xFFFFFFFF'
            name = ' '.join(parts[2:]) if len(parts) > 2 else 'CRITICAL_PROCESS_DIED'
            write(f'⚠  Triggering GSOD: {code} — {name}', 'error')
            audit_log('TERMINAL_TRIGGER_ERROR', f'{code} {name}', 'CRITICAL')
            term_win.after(1200, lambda: show_gsod(code, name))

        elif key == 'delete':
            if messagebox.askyesno('Uninstall', 'Uninstall Windows 7 and enter BIOS?'):
                if desktop_win: desktop_win.destroy()
                show_bios_boot_menu(reinstall=True)
            return

        # ── app list ───────────────────────────────────────────────────
        elif key == 'app' and len(parts) > 1 and parts[1].lower() == 'list':
            apps = state.get('apps', [])
            if not apps:
                write('No installed apps.', 'warn')
            else:
                for app in apps:
                    write(f"  {app.get('name'):<20} {app.get('subtitle','')}", 'info')

        # ── exit ───────────────────────────────────────────────────────
        elif key == 'exit':
            term_win.destroy(); return

        # ── check custom commands ──────────────────────────────────────
        elif key in term_state['custom_cmds']:
            action = term_state['custom_cmds'][key]
            action_parts = action.split()
            action_key = action_parts[0].lower() if action_parts else ''
            if action_key == 'open' and len(action_parts) > 1:
                run_command('open ' + ' '.join(action_parts[1:]))
            elif action_key == 'say' and len(action_parts) > 1:
                msg = ' '.join(action_parts[1:])
                show_system_notification('Terminal', msg)
                write(f'[notify] {msg}', 'info')
            elif action_key == 'echo':
                write(' '.join(action_parts[1:]))
            else:
                run_command(action)

        # ── fallback: shell passthrough (with security blocklist) ──────────
        else:
            # ── Dangerous command blocklist ─────────────────────────────
            _BLOCKED_PATTERNS = [
                r'\brm\s+-rf\b', r'\bformat\b', r'\bdel\s+/[fsq]',
                r'\brd\s+/[sq]', r'\brmdir\s+/[sq]',
                r'shutdown\s+/[rts]', r'taskkill\s+/f',
                r'\bdiskpart\b', r'\bfdisk\b', r'\battrib\b.*\+s',
                r'\bnetsh\s+advfirewall\s+set\s+allprofiles\s+state\s+off',
                r'\breg\s+delete\b', r'\bschtasks\s+/delete\b',
                r'\bnet\s+(user|localgroup)\b.*\/(add|delete)',
                r'\bcacls\b', r'\bicacls\b.*\/grant',
                r'\bwmic\b.*delete\b', r'\bpowershell\b.*-enc\b',
                r'\bpython\b.*-c\b.*os\.(system|remove|rmdir)',
                r'>\s*/dev/sd[a-z]', r'\bdd\s+if=.*of=/dev/',
            ]
            cmd_lower = raw_cmd.lower()
            blocked = False
            for pat in _BLOCKED_PATTERNS:
                if re.search(pat, cmd_lower):
                    blocked = True
                    break
            if blocked:
                write(
                    f'⛔  BLOCKED: "{raw_cmd[:60]}" — command matches security policy.',
                    'error')
                audit_log('TERMINAL_BLOCKED', raw_cmd[:120], 'CRITICAL')
                write_prompt()
                return
            # ── Log the shell command before execution ───────────────────
            audit_log('TERMINAL_EXEC', raw_cmd[:120], 'INFO')
            try:
                r = subprocess.run(raw_cmd, shell=True,
                                   capture_output=True, text=True,
                                   cwd=term_state['cwd'],
                                   timeout=15)
                out = r.stdout + r.stderr
                if out.strip():
                    write(out)
                else:
                    write(f"'{key}' is not recognised. Type help for commands.", 'error')
            except subprocess.TimeoutExpired:
                write('Command timed out (15s limit).', 'error')
            except Exception as e:
                write(str(e), 'error')

        write_prompt()

    # ── input bar ──────────────────────────────────────────────────────────
    input_frame = tk.Frame(term_win, bg='#141424', pady=4)
    input_frame.pack(fill='x', side='bottom')

    prompt_lbl = tk.Label(input_frame,
                          text=f'{state.get("user_name","user")}> ',
                          bg='#141424', fg='#4ec9b0',
                          font=('Consolas', 11))
    prompt_lbl.pack(side='left', padx=(8, 0))

    term_entry = tk.Entry(input_frame,
                          bg='#1e1e2e', fg='white',
                          insertbackground='white',
                          relief='flat', font=('Consolas', 11),
                          highlightthickness=1,
                          highlightbackground='#2a3a5a',
                          highlightcolor='#4a7aba')
    term_entry.pack(side='left', fill='x', expand=True, padx=4, ipady=6)
    term_entry.focus_set()

    run_btn = tk.Button(input_frame, text='▶  Run',
                        bg='#2a5ea8', fg='white',
                        relief='flat', font=('Segoe UI', 9),
                        padx=12, pady=6,
                        activebackground='#3a7ad8',
                        cursor='hand2',
                        command=lambda: run_command(term_entry.get()) or
                                        term_entry.delete(0, 'end'))
    run_btn.pack(side='right', padx=8)

    def on_enter(e):
        cmd = term_entry.get()
        term_entry.delete(0, 'end')
        run_command(cmd)

    def on_up(e):
        h = term_state['history']
        if not h: return
        if term_state['hist_idx'] == -1:
            term_state['hist_idx'] = len(h) - 1
        else:
            term_state['hist_idx'] = max(0, term_state['hist_idx'] - 1)
        term_entry.delete(0, 'end')
        term_entry.insert(0, h[term_state['hist_idx']])

    def on_down(e):
        h = term_state['history']
        if term_state['hist_idx'] == -1: return
        term_state['hist_idx'] += 1
        term_entry.delete(0, 'end')
        if term_state['hist_idx'] < len(h):
            term_entry.insert(0, h[term_state['hist_idx']])
        else:
            term_state['hist_idx'] = -1

    def on_tab(e):
        """Basic tab completion for filenames."""
        text = term_entry.get()
        parts_tab = text.split()
        if not parts_tab: return 'break'
        stub = parts_tab[-1]
        parent = os.path.dirname(expand_path(stub)) or term_state['cwd']
        base   = os.path.basename(stub)
        try:
            matches = [f for f in os.listdir(parent)
                       if f.lower().startswith(base.lower())]
            if len(matches) == 1:
                completed = os.path.join(os.path.dirname(stub), matches[0])
                parts_tab[-1] = completed
                term_entry.delete(0, 'end')
                term_entry.insert(0, ' '.join(parts_tab))
            elif len(matches) > 1:
                write('  ' + '   '.join(matches[:20]), 'info')
        except: pass
        return 'break'

    term_entry.bind('<Return>', on_enter)
    term_entry.bind('<Up>',     on_up)
    term_entry.bind('<Down>',   on_down)
    term_entry.bind('<Tab>',    on_tab)

    # Initial prompt
    write_prompt()
def show_file_explorer():
    explorer = tk.Toplevel(desktop_win)
    explorer.title('Explorer')
    explorer.geometry('820x520')
    style_aero_window(explorer, '#112138')
    center_window(explorer, 820, 520)

    tk.Label(explorer, text='File Explorer', bg='#112138', fg='#d3e8ff', font=('Segoe UI', 16, 'bold')).pack(anchor='nw', padx=18, pady=(18,10))
    explorer_body = tk.Frame(explorer, bg='#0f1733')
    explorer_body.pack(fill='both', expand=True, padx=18, pady=(0,18))

    left = tk.Frame(explorer_body, bg='#152c4d', width=220)
    left.pack(side='left', fill='y', padx=(0,10), pady=8)
    tk.Label(left, text='C:\\ Drive', bg='#152c4d', fg='#cde4ff', font=('Segoe UI', 11, 'bold')).pack(anchor='nw', padx=12, pady=(12,8))
    drive_label = tk.Label(left, text='245 GB total', bg='#152c4d', fg='#d3e8ff', font=('Segoe UI', 9))
    drive_label.pack(anchor='nw', padx=12, pady=(0,8))
    tk.Button(left, text='Refresh', bg='#3b82f6', fg='white', relief='flat', command=lambda: refresh_drive_view(DATA_DIR)).pack(anchor='nw', padx=12, pady=(0,10))

    drives_list = tk.Listbox(left, bg='#0d1b2f', fg='white', selectbackground='#2555a7', bd=0, highlightthickness=0, height=6)
    drives_list.pack(fill='x', padx=12, pady=(0,10))
    drives_list.insert('end', 'C:\\')
    drives_list.insert('end', 'Recycle Bin')

    tk.Label(left, text='Locations', bg='#152c4d', fg='#cde4ff', font=('Segoe UI', 10, 'bold')).pack(anchor='nw', padx=12, pady=(10,6))
    for folder in ['Documents', 'Pictures', 'Music', 'Downloads']:
        tk.Label(left, text=folder, bg='#152c4d', fg='white', padx=12, pady=6).pack(anchor='nw')

    right = tk.Frame(explorer_body, bg='#112138')
    right.pack(side='left', fill='both', expand=True, pady=8)
    header = tk.Frame(right, bg='#112138')
    header.pack(fill='x', padx=12, pady=(12,0))
    tk.Label(header, text='Files', bg='#112138', fg='#cde4ff', font=('Segoe UI', 11, 'bold')).pack(side='left')
    path_label = tk.Label(header, text='C:\\', bg='#112138', fg='#9fbfed', font=('Segoe UI', 9))
    path_label.pack(side='right')

    file_list = tk.Listbox(right, bg='#0f1a2e', fg='white', selectbackground='#2555a7', bd=0, highlightthickness=0)
    file_list.pack(fill='both', expand=True, padx=12, pady=(6,10))
    info_label = tk.Label(right, text='', bg='#112138', fg='#a8c8ff', font=('Segoe UI', 9), anchor='w')
    info_label.pack(fill='x', padx=12, pady=(0,8))

    def get_drive_stats():
        total = 245 * 1024**3
        used = 0
        for root_dir, _, filenames in os.walk(DATA_DIR):
            for filename in filenames:
                try:
                    used += os.path.getsize(os.path.join(root_dir, filename))
                except Exception:
                    pass
        free = total - used
        return total, used, max(0, total - used)

    def format_file_info(path):
        try:
            size = os.path.getsize(path)
            return f'{os.path.basename(path)} — {size//1024} KB'
        except Exception:
            return os.path.basename(path)

    def refresh_drive_view(path=DATA_DIR):
        target = path
        file_list.delete(0, 'end')
        if path == RECYCLE_DIR:
            path_label.config(text='Recycle Bin')
            for filename in sorted(os.listdir(RECYCLE_DIR)):
                file_list.insert('end', f'{filename} (recycled)')
            info_label.config(text='Recycle Bin contains deleted files. Restore or remove permanently.')
        else:
            path_label.config(text='C:\\')
            try:
                for filename in sorted(os.listdir(target)):
                    file_list.insert('end', format_file_info(os.path.join(target, filename)))
                total, used, free = get_drive_stats()
                info_label.config(text=f'Used: {used/1024**3:.1f} GB of 245 GB — Free: {free/1024**3:.1f} GB')
                drive_label.config(text=f'{used/1024**3:.1f} GB used of 245 GB')
            except Exception as e:
                info_label.config(text='Unable to read drive: ' + str(e))

    def open_file():
        sel = file_list.curselection()
        if not sel:
            messagebox.showinfo('Open', 'Select a file first')
            return
        name = file_list.get(sel[0]).split(' (')[0]
        if path_label.cget('text') == 'Recycle Bin':
            path = os.path.join(RECYCLE_DIR, name)
        else:
            path = os.path.join(DATA_DIR, name)
        try:
            if os.path.exists(path):
                os.startfile(path)
            else:
                messagebox.showinfo('Open', f'Would open: {name}')
        except Exception:
            messagebox.showerror('Open', 'Cannot open file')

    def delete_file():
        sel = file_list.curselection()
        if not sel:
            messagebox.showinfo('Delete', 'Select a file first')
            return
        name = file_list.get(sel[0]).split(' (')[0]
        path = os.path.join(DATA_DIR, name)
        if not os.path.exists(path):
            messagebox.showinfo('Delete', 'File not found.')
            return
        try:
            os.makedirs(RECYCLE_DIR, exist_ok=True)
            shutil.move(path, os.path.join(RECYCLE_DIR, name))
            show_system_notification('Recycle Bin', f'{name} moved to Recycle Bin.')
            refresh_drive_view(DATA_DIR)
        except Exception as e:
            messagebox.showerror('Delete', 'Could not delete file: ' + str(e))

    def on_drive_select(event=None):
        sel = drives_list.curselection()
        if not sel:
            return
        if sel[0] == 1:
            refresh_drive_view(RECYCLE_DIR)
        else:
            refresh_drive_view(DATA_DIR)

    drives_list.bind('<<ListboxSelect>>', on_drive_select)
    file_list.bind('<Double-1>', lambda e: open_file())

    controls = tk.Frame(right, bg='#112138')
    controls.pack(fill='x', padx=12, pady=(0,12))
    tk.Button(controls, text='Open', bg='#1e6089', fg='white', command=open_file).pack(side='left')
    tk.Button(controls, text='Delete', bg='#d94b4b', fg='white', command=delete_file).pack(side='left', padx=8)
    tk.Button(controls, text='Recycle Bin', bg='#3b82f6', fg='white', command=lambda: [drives_list.selection_clear(0, 'end'), drives_list.selection_set(1), refresh_drive_view(RECYCLE_DIR)]).pack(side='left')

    refresh_drive_view(DATA_DIR)


def show_recycle_bin():
    parent = desktop_win if desktop_win and desktop_win.winfo_exists() else root
    recycle_win = tk.Toplevel(parent)
    recycle_win.title('Recycle Bin')
    recycle_win.geometry('620x420')
    style_aero_window(recycle_win, '#132041')
    center_window(recycle_win, 620, 420)

    tk.Label(recycle_win, text='🗑  Recycle Bin', bg='#132041', fg='#dbe8ff',
             font=('Segoe UI', 14, 'bold')).pack(anchor='nw', padx=14, pady=(14, 10))

    # Item count label
    count_lbl = tk.Label(recycle_win, bg='#132041', fg='#5a7aaa',
                         font=('Segoe UI', 9))
    count_lbl.pack(anchor='nw', padx=14)

    bin_list = tk.Listbox(recycle_win, bg='#0e1a34', fg='white',
                          selectbackground='#4d7ec8', bd=0, highlightthickness=0,
                          font=('Segoe UI', 10))
    bin_list.pack(fill='both', expand=True, padx=14, pady=(4, 12))

    def refresh_bin():
        bin_list.delete(0, 'end')
        try:
            files = sorted(os.listdir(RECYCLE_DIR))
        except Exception:
            files = []
        for filename in files:
            fpath = os.path.join(RECYCLE_DIR, filename)
            try:
                sz = os.path.getsize(fpath)
                sz_str = f'{sz // 1024} KB' if sz >= 1024 else f'{sz} B'
            except Exception:
                sz_str = ''
            bin_list.insert('end', f'  {filename}   [{sz_str}]')
        count_lbl.config(text=f'{len(files)} item(s) in Recycle Bin  ·  '
                         f'Size: {sum(os.path.getsize(os.path.join(RECYCLE_DIR,f)) for f in files if os.path.isfile(os.path.join(RECYCLE_DIR,f))) // 1024} KB')

    refresh_bin()

    def restore():
        sel = bin_list.curselection()
        if not sel:
            messagebox.showinfo('Restore', 'Select a file to restore.')
            return
        raw = bin_list.get(sel[0]).strip()
        name = raw.split('   [')[0].strip()
        src_path = os.path.join(RECYCLE_DIR, name)
        dst_path = os.path.join(DATA_DIR, name)
        try:
            shutil.move(src_path, dst_path)
            play_windows7_device_connect()
            audit_log('RECYCLE_RESTORE', name, 'INFO')
            refresh_bin()
            show_system_notification('Recycle Bin', f'{name} restored.')
        except Exception as e:
            messagebox.showerror('Restore', str(e))

    def empty_bin():
        try:
            files = os.listdir(RECYCLE_DIR)
        except Exception:
            files = []
        if not files:
            show_system_notification('Recycle Bin', 'Already empty.')
            return
        if not messagebox.askyesno('Empty Recycle Bin',
                                   f'Permanently delete {len(files)} file(s)?'):
            return
        for filename in files:
            try:
                os.remove(os.path.join(RECYCLE_DIR, filename))
            except Exception:
                pass
        play_windows7_recycle_empty()
        audit_log('RECYCLE_EMPTIED', f'{len(files)} files deleted', 'INFO')
        refresh_bin()
        show_system_notification('Recycle Bin', f'{len(files)} file(s) permanently deleted.')

    def delete_selected():
        sel = bin_list.curselection()
        if not sel:
            return
        raw = bin_list.get(sel[0]).strip()
        name = raw.split('   [')[0].strip()
        if messagebox.askyesno('Delete', f'Permanently delete "{name}"?'):
            try:
                os.remove(os.path.join(RECYCLE_DIR, name))
                play_windows7_recycle_empty()
                audit_log('RECYCLE_DELETE', name, 'INFO')
                refresh_bin()
            except Exception as e:
                messagebox.showerror('Delete', str(e))

    controls = tk.Frame(recycle_win, bg='#132041')
    controls.pack(fill='x', padx=14, pady=(0, 12))
    tk.Button(controls, text='Restore', bg='#3b82f6', fg='white',
              command=restore).pack(side='left', padx=(0, 6))
    tk.Button(controls, text='Delete Selected', bg='#c04040', fg='white',
              command=delete_selected).pack(side='left', padx=(0, 6))
    tk.Button(controls, text='Empty Bin', bg='#d94b4b', fg='white',
              command=empty_bin).pack(side='right')
    tk.Button(controls, text='Refresh', bg='#2a4a7a', fg='white',
              command=refresh_bin).pack(side='right', padx=6)


def show_media_player():
    player = tk.Toplevel(desktop_win)
    player.title('Media Player')
    player.geometry('680x420')
    style_aero_window(player, '#141d31')
    center_window(player, 680, 420)

    tk.Label(player, text='Windows 7 Media Player', bg='#141d31', fg='#d7e8ff', font=('Segoe UI', 16, 'bold')).pack(anchor='nw', padx=16, pady=(16,8))
    playlist = ['Storm Clouds.mp3', 'Ocean Drive.mp3', 'Sunrise Piano.mp3', 'Retro Groove.mp3']

    list_frame = tk.Frame(player, bg='#101827')
    list_frame.pack(fill='both', expand=True, padx=16, pady=10)
    track_list = tk.Listbox(list_frame, bg='#0b1330', fg='white', selectbackground='#4b77d6', bd=0, highlightthickness=0)
    track_list.pack(fill='both', expand=True, side='left', padx=(0,8))
    for track in playlist:
        track_list.insert('end', track)

    info = tk.Label(player, text='Select a track and click Play.', bg='#141d31', fg='#b5c8ff', font=('Segoe UI', 10))
    info.pack(padx=16, pady=(0,8))

    def play_track():
        sel = track_list.curselection()
        if not sel:
            messagebox.showinfo('Media', 'Select a track first.')
            return
        info.config(text=f'Playing: {track_list.get(sel[0])}')
        show_system_notification('Media Player', f'Now playing {track_list.get(sel[0])}')

    controls = tk.Frame(player, bg='#141d31')
    controls.pack(fill='x', padx=16, pady=(0,16))
    tk.Button(controls, text='Play', bg='#3b82f6', fg='white', command=play_track).pack(side='left', padx=(0,8))
    tk.Button(controls, text='Pause', bg='#6e7eb8', fg='white', command=lambda: info.config(text='Paused')).pack(side='left', padx=8)
    tk.Button(controls, text='Stop', bg='#d94b4b', fg='white', command=lambda: info.config(text='Stopped')).pack(side='left', padx=8)


def _require_activation(feature_name: str = 'This feature') -> bool:
    """Returns True if activated. If not, shows activation nag and returns False."""
    if state.get('activated', False):
        return True
    parent = desktop_win if desktop_win and desktop_win.winfo_exists() else root
    nag = tk.Toplevel(parent)
    nag.title('Windows Activation Required')
    nag.overrideredirect(True)
    nag.attributes('-topmost', True)
    nag.configure(bg='#1a0a00')
    sw, sh = nag.winfo_screenwidth(), nag.winfo_screenheight()
    w, h = 480, 240
    nag.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')
    nag.attributes('-alpha', 0.0)

    # Rounded feel via inner frame
    inner = tk.Frame(nag, bg='#fff8f0', bd=3, relief='ridge')
    inner.place(x=8, y=8, width=w-16, height=h-16)

    tk.Label(inner, text='🔒  Windows Activation Required',
             bg='#fff8f0', fg='#8a2000', font=('Segoe UI', 13, 'bold')).pack(pady=(16,4))
    tk.Label(inner,
             text=f'"{feature_name}" is not available on unactivated Windows.\n\n'
                  'Only  Settings  and  Terminal  are accessible without activation.\n'
                  'Enter product key  BK143  to unlock all features.',
             bg='#fff8f0', fg='#4a2000', font=('Segoe UI', 10),
             justify='center', wraplength=420).pack(pady=4)

    bf = tk.Frame(inner, bg='#fff8f0')
    bf.pack(pady=10)
    tk.Button(bf, text='Activate Now', bg='#c04000', fg='white',
              font=('Segoe UI', 10, 'bold'), padx=16, pady=4,
              command=lambda: [nag.destroy(), show_activation_dialog()]).pack(side='left', padx=8)
    tk.Button(bf, text='Later', bg='#888888', fg='white',
              font=('Segoe UI', 10), padx=12, pady=4,
              command=nag.destroy).pack(side='left', padx=8)

    # Fade in
    def fade_in(alpha=0.0):
        if not nag.winfo_exists():
            return
        alpha = min(1.0, alpha + 0.08)
        nag.attributes('-alpha', alpha)
        if alpha < 1.0:
            nag.after(16, lambda: fade_in(alpha))
    fade_in()
    play_windows7_error()
    return False


# ACTIVATION-GATED WRAPPER
# Any feature called via launch_app() passes through here.
# Only 'settings' and 'terminal' bypass the gate.
_ACTIVATION_FREE = {'settings', 'terminal', 'cmd', 'activation',
                    'activate', 'product key', 'bios', 'bios setup'}

def _gated_launch(key: str, fn):
    """Launch fn only if activated, else show nag. Settings/Terminal always allowed."""
    if key.lower() in _ACTIVATION_FREE or state.get('activated', False):
        fn()
    else:
        _require_activation(key.title())


def show_activation_dialog(parent=None):
    """Product activation dialog. Valid key: BK143"""
    win = tk.Toplevel(parent or (desktop_win if desktop_win and desktop_win.winfo_exists() else root))
    win.title('Product Activation')
    win.geometry('500x420')
    style_aero_window(win, '#0e1828')
    center_window(win, 500, 420)

    already = state.get('activated', False)

    # Curved header with gradient feel
    hdr = tk.Canvas(win, height=90, bg='#0e1828', highlightthickness=0)
    hdr.pack(fill='x')
    for i in range(90):
        t = i / 90
        r = int(0x0e + (0x1a - 0x0e)*t)
        g = int(0x18 + (0x3a - 0x18)*t)
        b = int(0x28 + (0x6a - 0x28)*t)
        hdr.create_line(0, i, 500, i, fill=f'#{r:02x}{g:02x}{b:02x}')
    hdr.create_text(250, 32, text='🔑  Windows Product Activation',
                    fill='white', font=('Segoe UI', 15, 'bold'))
    hdr.create_text(250, 58, text='Windows 7  ·  Genuine Software Program',
                    fill='#6090c0', font=('Segoe UI', 9))
    hdr.create_oval(210, 72, 290, 84, fill='#1e4a8a', outline='#4a90d4')

    body = tk.Frame(win, bg='#0e1828')
    body.pack(fill='both', expand=True, padx=24)

    status_bg = '#0a2a0a' if already else '#2a1000'
    status_fg = '#55ee55' if already else '#ffaa44'
    status_txt = ('✅  Windows 7 is activated and genuine.'
                  if already else
                  '⚠  Windows 7 is NOT activated.\n'
                  '    Only Settings and Terminal are available.')
    status_lbl = tk.Label(body, text=status_txt,
                          bg=status_bg, fg=status_fg,
                          font=('Segoe UI', 10, 'bold'),
                          padx=10, pady=10, wraplength=430, justify='center')
    status_lbl.pack(fill='x', pady=14)

    tk.Label(body, text='Enter your 5-character product key:',
             bg='#0e1828', fg='#8ab4e8', font=('Segoe UI', 10)).pack(anchor='w')

    key_frame = tk.Frame(body, bg='#0e1828')
    key_frame.pack(pady=8)
    key_var = tk.StringVar()
    key_entry = tk.Entry(key_frame, textvariable=key_var,
                         font=('Courier New', 20, 'bold'), width=8,
                         justify='center', bg='#060e18', fg='#60c8ff',
                         insertbackground='#60c8ff', relief='flat',
                         highlightthickness=3, highlightbackground='#1e4870',
                         highlightcolor='#4a90d4')
    key_entry.pack()
    if already:
        key_entry.insert(0, 'BK143')
        key_entry.config(state='disabled', fg='#55ee55')

    result_lbl = tk.Label(body, text='', bg='#0e1828', font=('Segoe UI', 10, 'bold'))
    result_lbl.pack(pady=4)

    # Animated unlock graphic
    unlock_cv = tk.Canvas(body, width=60, height=50, bg='#0e1828', highlightthickness=0)
    unlock_cv.pack()
    lock_icon = unlock_cv.create_text(30, 25, text='🔒', font=('Segoe UI Emoji', 22))

    def activate():
        key = key_var.get().strip().upper()
        if key == 'BK143':
            state['activated'] = True
            save_state()
            audit_log('ACTIVATION_SUCCESS', 'Key BK143', 'INFO')
            result_lbl.config(text='✅  Activation successful! All features unlocked.', fg='#55ee55')
            status_lbl.config(text='✅  Windows 7 is activated and genuine.',
                              bg='#0a2a0a', fg='#55ee55')
            key_entry.config(state='disabled', fg='#55ee55')
            unlock_cv.itemconfig(lock_icon, text='🔓')
            play_windows7_logon()
            # Remove watermark
            if desktop_win and desktop_win.winfo_exists():
                for w in list(desktop_win.winfo_children()):
                    try:
                        if getattr(w, '_is_watermark', False):
                            w.destroy()
                    except Exception:
                        pass
            win.after(1500, lambda: messagebox.showinfo(
                'Activated',
                'Windows 7 is now activated!\n\n'
                'All features are unlocked.\n'
                'The activation watermark has been removed.',
                parent=win))
        else:
            audit_log('ACTIVATION_FAIL', f'Bad key: {key}', 'WARN')
            result_lbl.config(text='❌  Invalid product key. Hint: it\'s 5 chars.', fg='#ff5555')
            key_entry.config(highlightbackground='#cc2020')
            key_entry.after(900, lambda: key_entry.config(highlightbackground='#1e4870'))
            play_windows7_error()

    def show_bios_from_activation():
        win.destroy()
        if desktop_win and desktop_win.winfo_exists():
            desktop_win.destroy()
        show_bios_boot_menu()

    key_entry.bind('<Return>', lambda e: activate())
    bf = tk.Frame(body, bg='#0e1828')
    bf.pack(pady=10)
    tk.Button(bf, text='Activate  🔑', bg='#1e5898', fg='white',
              font=('Segoe UI', 11, 'bold'), padx=16, pady=6,
              relief='flat', command=activate).pack(side='left', padx=6)
    tk.Button(bf, text='Enter BIOS', bg='#3a3a5a', fg='#aaaacc',
              font=('Segoe UI', 10), padx=12, pady=6,
              relief='flat', command=show_bios_from_activation).pack(side='left', padx=6)

    tk.Label(body,
             text='Product key is printed on your Certificate of Authenticity (COA).\n'
                  'Hint: The valid key is  BK143',
             bg='#0e1828', fg='#2a4a6a', font=('Segoe UI', 8),
             justify='center').pack(pady=(4, 8))


def show_settings_app():
    """Windows 7 Control Panel — expanded with 25 feature areas."""
    settings_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    settings_win.title('Windows 7 — Control Panel')
    settings_win.geometry('820x660')
    style_aero_window(settings_win, '#f0f5ff')
    center_window(settings_win, 820, 660)

    # ── Header (white, like Win7 Control Panel) ───────────────────────────
    hdr = tk.Frame(settings_win, bg='#ffffff', height=64)
    hdr.pack(fill='x'); hdr.pack_propagate(False)
    tk.Label(hdr, text='🖥  Control Panel', bg='#ffffff', fg='#1e3a6d',
             font=('Segoe UI',18)).pack(anchor='w', padx=20, pady=(10,0))
    tk.Label(hdr, text='Manage your Windows 7 settings', bg='#ffffff',
             fg='#777777', font=('Segoe UI',9)).pack(anchor='w', padx=22)
    tk.Frame(settings_win, height=1, bg='#d0d8e8').pack(fill='x')

    body = tk.Frame(settings_win, bg='#f0f5ff')
    body.pack(fill='both', expand=True, padx=8, pady=8)

    nb = ttk.Notebook(body); nb.pack(fill='both', expand=True)

    CP_BG = '#f0f5ff'
    HDR_CLR = '#1e3a6d'
    BTN_BG = '#e8f0fc'
    BTN_FG = '#1e3a6d'
    SEC_BG = '#ffffff'

    def cp_section(parent, title):
        f = tk.LabelFrame(parent, text=title, bg=CP_BG, fg=HDR_CLR,
                          font=('Segoe UI',9,'bold'), bd=1, relief='solid',
                          padx=10, pady=8)
        f.pack(fill='x', padx=10, pady=6)
        return f

    def cp_btn(parent, text, icon, cmd, w=26):
        row = tk.Frame(parent, bg=SEC_BG, cursor='hand2')
        row.pack(fill='x', pady=1)
        tk.Label(row, text=icon, bg=SEC_BG, font=('Segoe UI Emoji',12), width=3).pack(side='left', padx=4)
        lbl = tk.Label(row, text=text, bg=SEC_BG, fg=BTN_FG,
                       font=('Segoe UI',10), anchor='w', cursor='hand2')
        lbl.pack(side='left', fill='x', expand=True, pady=6)
        for widget in (row, lbl):
            widget.bind('<Enter>', lambda e, r=row: r.config(bg='#dce8fc') or
                        [c.config(bg='#dce8fc') for c in r.winfo_children()])
            widget.bind('<Leave>', lambda e, r=row: r.config(bg=SEC_BG) or
                        [c.config(bg=SEC_BG) for c in r.winfo_children()])
            widget.bind('<Button-1>', lambda e, fn=cmd: fn())

    # ══ TAB 1: System & Performance ══════════════════════════════════════
    t1 = tk.Frame(nb, bg=CP_BG); nb.add(t1, text='System')
    sc1 = tk.Canvas(t1, bg=CP_BG, highlightthickness=0)
    sb1 = ttk.Scrollbar(t1, orient='vertical', command=sc1.yview)
    sc1.configure(yscrollcommand=sb1.set)
    sb1.pack(side='right', fill='y'); sc1.pack(fill='both', expand=True)
    t1f = tk.Frame(sc1, bg=CP_BG); sc1.create_window((0,0), window=t1f, anchor='nw')
    t1f.bind('<Configure>', lambda e: sc1.configure(scrollregion=sc1.bbox('all')))

    def show_sysinfo():
        w = tk.Toplevel(settings_win); w.title('System Information')
        w.geometry('480x360'); style_aero_window(w,'#f0f5ff'); center_window(w,480,360)
        info = [
            ('OS',f"Windows 7 {state.get('os_version','Ultimate')}"),
            ('User', state.get('user_name','Ryan Sahdev')),
            ('Processor','Intel Core i7 @ 3.4 GHz (simulated)'),
            ('RAM','8.00 GB (simulated)'),
            ('System type','64-bit Operating System'),
            ('Computer name','WIN7-PC'),
            ('Workgroup','WORKGROUP'),
            ('Activation', '✅ Activated' if state.get('activated') else '⚠ Not Activated'),
        ]
        for k,v in info:
            row = tk.Frame(w, bg='#f0f5ff'); row.pack(fill='x', padx=16, pady=2)
            tk.Label(row, text=k+':', bg='#f0f5ff', fg='#1e3a6d', font=('Segoe UI',9,'bold'), width=18, anchor='w').pack(side='left')
            tk.Label(row, text=v, bg='#f0f5ff', fg='#333', font=('Segoe UI',9), anchor='w').pack(side='left')

    def show_task_manager():
        w = tk.Toplevel(settings_win); w.title('Task Manager')
        w.geometry('580x420'); style_aero_window(w,'#f0f5ff'); center_window(w,580,420)
        tk.Label(w, text='Windows Task Manager', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',13,'bold')).pack(pady=(32,8))
        nb2 = ttk.Notebook(w); nb2.pack(fill='both', expand=True, padx=16, pady=8)
        proc_tab = tk.Frame(nb2, bg='#f0f5ff'); nb2.add(proc_tab, text='Processes')
        cols = ('Process','CPU %','Memory')
        tv = ttk.Treeview(proc_tab, columns=cols, show='headings', height=10)
        for c in cols: tv.heading(c, text=c)
        tv.column('Process', width=220); tv.column('CPU %', width=80); tv.column('Memory', width=100)
        import os as _os
        procs = [('python.exe','2.1','48 MB'),('explorer.exe','0.3','32 MB'),
                 ('system','0.1','4 MB'),('win7desktop.py','1.8','64 MB')]
        for p in procs: tv.insert('', 'end', values=p)
        tv.pack(fill='both', expand=True, padx=8, pady=8)
        perf_tab = tk.Frame(nb2, bg='#f0f5ff'); nb2.add(perf_tab, text='Performance')
        if psutil:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            tk.Label(perf_tab, text=f'CPU Usage: {cpu:.1f}%', bg='#f0f5ff', font=('Segoe UI',11)).pack(pady=10)
            tk.Label(perf_tab, text=f'RAM: {ram.used//1024//1024} MB / {ram.total//1024//1024} MB',
                     bg='#f0f5ff', font=('Segoe UI',11)).pack()
        else:
            tk.Label(perf_tab, text='psutil not installed — install for live stats.',
                     bg='#f0f5ff', fg='#888').pack(pady=20)

    def show_startup_programs():
        w = tk.Toplevel(settings_win); w.title('Startup Programs')
        w.geometry('460x340'); style_aero_window(w,'#f0f5ff'); center_window(w,460,340)
        tk.Label(w, text='Startup Programs (Simulated)', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',12,'bold')).pack(pady=(32,8))
        programs = [('Windows Defender','Enabled'),('OneDrive','Enabled'),
                    ('Cortana','Disabled'),('Spotify','Disabled'),('Discord','Enabled')]
        for prog, status in programs:
            row = tk.Frame(w, bg='#f0f5ff'); row.pack(fill='x', padx=24, pady=3)
            tk.Label(row, text=prog, bg='#f0f5ff', fg='#1e3a6d', font=('Segoe UI',10), width=20, anchor='w').pack(side='left')
            col = '#1a6a1a' if status=='Enabled' else '#888'
            tk.Label(row, text=status, bg='#f0f5ff', fg=col, font=('Segoe UI',9,'bold')).pack(side='left')

    s1 = cp_section(t1f,'System Information')
    for btn_lbl, icon, fn in [
        ('System Information','💻', show_sysinfo),
        ('Task Manager','📊', show_task_manager),
        ('Startup Programs','🚀', show_startup_programs),
        ('Windows Update','🔄', lambda: show_update_loading(show_settings_app)),
        ('Device Manager','🖨', show_device_manager),
        ('Event Viewer','📋', lambda: show_system_notification('Event Viewer','No critical events found.')),
        ('Disk Cleanup','🧹', lambda: show_system_notification('Disk Cleanup','Cleaning... freed 1.2 GB.')),
        ('Defragment','⚙', lambda: show_system_notification('Defragment','Disk is 3% fragmented.')),
    ]:
        cp_btn(s1, btn_lbl, icon, fn)

    # ══ TAB 2: Personalization ════════════════════════════════════════════
    t2 = tk.Frame(nb, bg=CP_BG); nb.add(t2, text='Personalization')

    def show_theme_chooser():
        w = tk.Toplevel(settings_win); w.title('Theme Chooser')
        w.geometry('480x360'); style_aero_window(w,'#f0f5ff'); center_window(w,480,360)
        tk.Label(w, text='Windows 7 Themes', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',13,'bold')).pack(pady=(32,10))
        themes = [('Windows 7 Aero','#3878c8'),('Windows 7 Basic','#607080'),
                  ('High Contrast Black','#000000'),('High Contrast White','#f0f0f0'),
                  ('Windows Classic','#c0c0c0')]
        for name, color in themes:
            row = tk.Frame(w, bg='#f0f5ff', cursor='hand2'); row.pack(fill='x', padx=24, pady=3)
            tk.Frame(row, bg=color, width=24, height=24, bd=1, relief='solid').pack(side='left', padx=(0,10))
            tk.Label(row, text=name, bg='#f0f5ff', fg='#1e3a6d', font=('Segoe UI',10)).pack(side='left')

    def show_display_settings():
        w = tk.Toplevel(settings_win); w.title('Display Settings')
        w.geometry('420x320'); style_aero_window(w,'#f0f5ff'); center_window(w,420,320)
        tk.Label(w, text='Display Settings', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',13,'bold')).pack(pady=(32,12))
        res_var = tk.StringVar(value=state.get('display_res','1920×1080'))
        for res in ['1024×768','1280×720','1366×768','1920×1080','2560×1440']:
            tk.Radiobutton(w, text=res, variable=res_var, value=res,
                           bg='#f0f5ff', fg='#1e3a6d', font=('Segoe UI',10)).pack(anchor='w', padx=32)
        def apply_res():
            state['display_res'] = res_var.get(); save_state()
            show_system_notification('Display','Resolution saved (simulated).')
            w.destroy()
        tk.Button(w, text='Apply', bg='#3878c8', fg='white', command=apply_res).pack(pady=14)

    def show_screensaver():
        w = tk.Toplevel(settings_win); w.title('Screen Saver Settings')
        w.geometry('400x300'); style_aero_window(w,'#f0f5ff'); center_window(w,400,300)
        tk.Label(w, text='Screen Saver', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',13,'bold')).pack(pady=(32,12))
        ss_var = tk.StringVar(value=state.get('screensaver','Bubbles'))
        for s in ['None','Blank','Bubbles','Mystify','Ribbon','Photos']:
            tk.Radiobutton(w, text=s, variable=ss_var, value=s,
                           bg='#f0f5ff', fg='#1e3a6d', font=('Segoe UI',10)).pack(anchor='w', padx=32)
        wait_var = tk.IntVar(value=state.get('ss_wait', 10))
        tf = tk.Frame(w, bg='#f0f5ff'); tf.pack(fill='x', padx=32, pady=8)
        tk.Label(tf, text='Wait:', bg='#f0f5ff', fg='#1e3a6d').pack(side='left')
        tk.Spinbox(tf, from_=1, to=60, textvariable=wait_var, width=5).pack(side='left', padx=6)
        tk.Label(tf, text='minutes', bg='#f0f5ff', fg='#1e3a6d').pack(side='left')
        def save_ss():
            state['screensaver'] = ss_var.get(); state['ss_wait'] = wait_var.get(); save_state()
            show_system_notification('Screen Saver', f'{ss_var.get()} set.'); w.destroy()
        tk.Button(w, text='OK', bg='#3878c8', fg='white', command=save_ss).pack(pady=10)

    def show_font_manager():
        w = tk.Toplevel(settings_win); w.title('Fonts')
        w.geometry('500x380'); style_aero_window(w,'#f0f5ff'); center_window(w,500,380)
        tk.Label(w, text='Installed Fonts', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',13,'bold')).pack(pady=(32,8))
        fonts_list = ['Arial','Calibri','Cambria','Comic Sans MS','Consolas','Courier New',
                      'Georgia','Impact','Segoe UI','Tahoma','Times New Roman','Trebuchet MS',
                      'Verdana','Wingdings']
        font_var = tk.StringVar(value='Segoe UI')
        lb = tk.Listbox(w, height=10, bg='white', fg='#1e3a6d', font=('Segoe UI',10),
                        listvariable=tk.StringVar(value=fonts_list))
        lb.pack(fill='x', padx=24, pady=4)
        prev = tk.Label(w, text='The quick brown fox jumps over the lazy dog.',
                        bg='#f0f5ff', fg='#333', font=('Arial',11))
        prev.pack(pady=6)
        def on_sel(e=None):
            sel = lb.curselection()
            if sel: prev.config(font=(lb.get(sel[0]),11))
        lb.bind('<<ListboxSelect>>', on_sel)

    s2a = cp_section(t2,'Appearance')
    for btn_lbl, icon, fn in [
        ('Change Wallpaper','🖼', choose_wallpaper),
        ('Themes','🎨', show_theme_chooser),
        ('Screen Saver','💤', show_screensaver),
        ('Display Settings','🖥', show_display_settings),
        ('Font Manager','🔤', show_font_manager),
        ('Aero Glass Gallery','✨', show_aero_glass_gallery),
        ('Color & Appearance','🌈', lambda: show_system_notification('Color','Aero color changed.')),
        ('Desktop Icons','📁', lambda: show_system_notification('Icons','Desktop icon settings.')),
    ]:
        cp_btn(s2a, btn_lbl, icon, fn)

    # ══ TAB 3: Network & Internet ═════════════════════════════════════════
    t3 = tk.Frame(nb, bg=CP_BG); nb.add(t3, text='Network')

    def show_network_sharing():
        w = tk.Toplevel(settings_win); w.title('Network and Sharing Center')
        w.geometry('520x400'); style_aero_window(w,'#f0f5ff'); center_window(w,520,400)
        tk.Label(w, text='Network and Sharing Center', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',13,'bold')).pack(pady=(32,12))
        net_info = [
            ('Network name','WIN7-HOME'),('Connection type','Private network'),
            ('Internet','Connected (simulated)'),('Homegroup','Not joined'),
            ('IPv4','192.168.1.100 (simulated)'),
        ]
        for k,v in net_info:
            row = tk.Frame(w, bg='#f0f5ff'); row.pack(fill='x', padx=24, pady=3)
            tk.Label(row, text=k+':', bg='#f0f5ff', fg='#1e3a6d', font=('Segoe UI',9,'bold'), width=22, anchor='w').pack(side='left')
            tk.Label(row, text=v, bg='#f0f5ff', fg='#333', font=('Segoe UI',9)).pack(side='left')

    s3 = cp_section(t3,'Network')
    for btn_lbl, icon, fn in [
        ('Network and Sharing Center','🌐', show_network_sharing),
        ('Network Connections','📡', show_network_center),
        ('Windows Firewall','🔥', lambda: show_system_notification('Firewall','Windows Firewall is active.')),
        ('Internet Options','🌍', lambda: show_system_notification('Internet','IE simulated settings.')),
        ('HomeGroup','🏠', lambda: show_system_notification('HomeGroup','No HomeGroup found.')),
        ('Proxy Settings','🔒', lambda: show_system_notification('Proxy','No proxy configured.')),
        ('DNS Settings','🗄', lambda: show_system_notification('DNS','Primary DNS: 8.8.8.8')),
        ('VPN Settings','🔐', lambda: show_system_notification('VPN','No VPN configured.')),
    ]:
        cp_btn(s3, btn_lbl, icon, fn)

    # ══ TAB 4: Hardware & Sound ═══════════════════════════════════════════
    t4 = tk.Frame(nb, bg=CP_BG); nb.add(t4, text='Hardware')

    def show_sound_settings():
        w = tk.Toplevel(settings_win); w.title('Sound Settings')
        w.geometry('440x340'); style_aero_window(w,'#f0f5ff'); center_window(w,440,340)
        tk.Label(w, text='Sound Settings', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',13,'bold')).pack(pady=(32,12))
        vol_var = tk.IntVar(value=state.get('volume',50))
        tk.Label(w, text='Master Volume', bg='#f0f5ff', fg='#1e3a6d', font=('Segoe UI',10)).pack()
        tk.Scale(w, variable=vol_var, from_=0, to=100, orient='horizontal',
                 bg='#f0f5ff', length=320).pack(pady=6)
        mute_var = tk.BooleanVar(value=state.get('muted', False))
        tk.Checkbutton(w, text='Mute', variable=mute_var, bg='#f0f5ff',
                       fg='#1e3a6d', font=('Segoe UI',10)).pack()
        def save_sound():
            state['volume'] = vol_var.get(); state['muted'] = mute_var.get(); save_state()
            show_system_notification('Sound',f"Volume: {vol_var.get()}%"); w.destroy()
        tk.Button(w, text='Apply', bg='#3878c8', fg='white', command=save_sound).pack(pady=12)

    def show_mouse_settings():
        w = tk.Toplevel(settings_win); w.title('Mouse Settings')
        w.geometry('400x320'); style_aero_window(w,'#f0f5ff'); center_window(w,400,320)
        tk.Label(w, text='Mouse Settings', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',13,'bold')).pack(pady=(32,12))
        spd_var = tk.IntVar(value=state.get('mouse_speed',5))
        tk.Label(w, text='Pointer Speed', bg='#f0f5ff', fg='#1e3a6d').pack()
        tk.Scale(w, variable=spd_var, from_=1, to=10, orient='horizontal',
                 bg='#f0f5ff', length=280).pack()
        swap_var = tk.BooleanVar(value=state.get('swap_buttons',False))
        tk.Checkbutton(w, text='Swap primary and secondary buttons', variable=swap_var,
                       bg='#f0f5ff', fg='#1e3a6d').pack(pady=6)
        def save_mouse():
            state['mouse_speed'] = spd_var.get(); state['swap_buttons'] = swap_var.get()
            save_state(); show_system_notification('Mouse','Mouse settings saved.'); w.destroy()
        tk.Button(w, text='Apply', bg='#3878c8', fg='white', command=save_mouse).pack(pady=10)

    def show_keyboard_settings():
        w = tk.Toplevel(settings_win); w.title('Keyboard Settings')
        w.geometry('400x280'); style_aero_window(w,'#f0f5ff'); center_window(w,400,280)
        tk.Label(w, text='Keyboard Settings', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',13,'bold')).pack(pady=(32,12))
        repeat_var = tk.IntVar(value=state.get('key_repeat',5))
        tk.Label(w, text='Key Repeat Rate', bg='#f0f5ff', fg='#1e3a6d').pack()
        tk.Scale(w, variable=repeat_var, from_=1, to=10, orient='horizontal',
                 bg='#f0f5ff', length=280).pack()
        lang_var = tk.StringVar(value=state.get('keyboard_lang','English (US)'))
        tk.Label(w, text='Language:', bg='#f0f5ff', fg='#1e3a6d').pack(pady=(10,0))
        ttk.Combobox(w, textvariable=lang_var, values=['English (US)','English (UK)','French','German','Spanish'],
                     state='readonly', width=20).pack()
        def save_kb():
            state['key_repeat'] = repeat_var.get(); state['keyboard_lang'] = lang_var.get()
            save_state(); show_system_notification('Keyboard','Keyboard settings saved.'); w.destroy()
        tk.Button(w, text='Apply', bg='#3878c8', fg='white', command=save_kb).pack(pady=12)

    s4 = cp_section(t4,'Hardware & Sound')
    for btn_lbl, icon, fn in [
        ('Sound Settings','🔊', show_sound_settings),
        ('Mouse Settings','🖱', show_mouse_settings),
        ('Keyboard Settings','⌨', show_keyboard_settings),
        ('Display Adapter','🖥', lambda: show_system_notification('Display','Intel HD Graphics 4000 (simulated)')),
        ('Power Options','⚡', lambda: show_system_notification('Power','Balanced power plan active.')),
        ('Printers','🖨', lambda: show_system_notification('Printers','No printers installed.')),
        ('Device Manager','⚙', show_device_manager),
        ('Disk Management','💾', lambda: show_system_notification('Disk','C:\\ 120 GB  D:\\ 500 GB (simulated)')),
    ]:
        cp_btn(s4, btn_lbl, icon, fn)

    # ══ TAB 5: User Accounts ══════════════════════════════════════════════
    t5 = tk.Frame(nb, bg=CP_BG); nb.add(t5, text='Accounts')

    def show_account_info():
        w = tk.Toplevel(settings_win); w.title('My Account')
        w.geometry('440x320'); style_aero_window(w,'#f0f5ff'); center_window(w,440,320)
        tk.Label(w, text='User Account', bg='#f0f5ff', fg='#1e3a6d',
                 font=('Segoe UI',14,'bold')).pack(pady=(32,12))
        info_rows = [
            ('Name', state.get('user_name','Ryan Sahdev')),
            ('Account type','Administrator'),
            ('Password','Set (protected)'),
            ('Account status','Active'),
            ('Created','System startup'),
        ]
        for k,v in info_rows:
            r = tk.Frame(w, bg='#f0f5ff'); r.pack(fill='x', padx=24, pady=3)
            tk.Label(r, text=k+':', bg='#f0f5ff', fg='#1e3a6d', font=('Segoe UI',9,'bold'), width=18, anchor='w').pack(side='left')
            tk.Label(r, text=v, bg='#f0f5ff', fg='#333', font=('Segoe UI',9)).pack(side='left')

    s5 = cp_section(t5,'User Accounts')
    for btn_lbl, icon, fn in [
        ('My Account Info','👤', show_account_info),
        ('Change Password','🔑', change_password),
        ('User Picture','🖼', lambda: show_system_notification('Picture','Change your account picture.')),
        ('Account Control (UAC)','🛡', lambda: show_system_notification('UAC','UAC is enabled.')),
        ('Parental Controls','👶', lambda: show_system_notification('Parental','Parental controls are off.')),
        ('Sign-in Options','🔐', lambda: show_system_notification('Sign-in','Password and PIN options.')),
    ]:
        cp_btn(s5, btn_lbl, icon, fn)

    # ══ TAB 6: Security & Maintenance ════════════════════════════════════
    t6 = tk.Frame(nb, bg=CP_BG); nb.add(t6, text='Security')

    def show_activation_inline():
        activated = state.get('activated', False)
        if activated:
            show_system_notification('Activation','✅ Windows 7 is already activated.')
        else:
            show_activation_dialog(settings_win)

    s6 = cp_section(t6,'Security & Maintenance')
    for btn_lbl, icon, fn in [
        ('Windows Security Center','🛡', show_windows_security),
        ('Windows Defender','🔍', lambda: show_system_notification('Defender','No threats found.')),
        ('Windows Firewall','🔥', lambda: show_system_notification('Firewall','Firewall is ON.')),
        ('BitLocker','🔒', lambda: show_system_notification('BitLocker','Encryption is available on Ultimate only.')),
        ('Product Activation','🎫', show_activation_inline),
        ('Windows Update','🔄', lambda: show_update_loading(show_settings_app)),
        ('Backup and Restore','💾', lambda: show_system_notification('Backup','No backup configured.')),
        ('System Restore','♻', lambda: show_system_notification('Restore','Restore points available.')),
        ('Uninstall Windows 7','⚠', uninstall_celine),
    ]:
        cp_btn(s6, btn_lbl, icon, fn)

    # ══ TAB 7: Sounds & Language ══════════════════════════════════════════
    t7 = tk.Frame(nb, bg=CP_BG); nb.add(t7, text='Sounds & Region')

    s7a = cp_section(t7,'Sound Schemes')
    sound_lbl = tk.Label(s7a, text=f"Active: {os.path.basename(state.get('welcome_sound_path','System Default'))}",
                         bg=CP_BG, fg='#555', font=('Segoe UI',9))
    sound_lbl.pack(anchor='w', padx=4, pady=(4,2))

    def browse_sound():
        path = filedialog.askopenfilename(title='Select Welcome Sound',
                filetypes=[('Audio/Video','*.wav *.mp3 *.mp4')])
        if path:
            state['welcome_sound_path'] = path; save_state()
            sound_lbl.config(text=f"Active: {os.path.basename(path)}")

    cp_btn(s7a, 'Browse Welcome Sound','🎵', browse_sound)
    cp_btn(s7a, 'Clear Custom Sound','🔇',
           lambda: [state.update({'welcome_sound_path':''}), save_state(),
                    sound_lbl.config(text='Active: System Default')])

    s7b = cp_section(t7,'Region & Language')
    region_var = tk.StringVar(value=state.get('region','United States'))
    lang_row = tk.Frame(t7, bg=CP_BG); lang_row.pack(fill='x', padx=18, pady=4)
    tk.Label(lang_row, text='Region:', bg=CP_BG, fg='#1e3a6d', font=('Segoe UI',9)).pack(side='left')
    ttk.Combobox(lang_row, textvariable=region_var,
                 values=['United States','United Kingdom','India','France','Germany','Japan','Australia'],
                 state='readonly', width=20).pack(side='left', padx=8)
    tk.Button(lang_row, text='Save', bg='#3878c8', fg='white',
              command=lambda: [state.update({'region':region_var.get()}), save_state(),
                               show_system_notification('Region', f'Region set to {region_var.get()}')]).pack(side='left')

    # ══ TAB 8: Accessibility ══════════════════════════════════════════════
    t8 = tk.Frame(nb, bg=CP_BG); nb.add(t8, text='Ease of Access')
    s8 = cp_section(t8,'Accessibility Options')
    fs_var = tk.BooleanVar(value=state.get('large_text', False))
    hc_var = tk.BooleanVar(value=state.get('high_contrast', False))
    nm_var = tk.BooleanVar(value=state.get('narrator', False))
    for txt, var, key in [
        ('Large Text / High DPI', fs_var, 'large_text'),
        ('High Contrast Mode', hc_var, 'high_contrast'),
        ('Narrator (Screen Reader)', nm_var, 'narrator'),
    ]:
        def _save_acc(k=key, v=var): state[k]=v.get(); save_state()
        tk.Checkbutton(s8, text=txt, variable=var, bg=CP_BG, fg='#1e3a6d',
                       font=('Segoe UI',10), command=_save_acc).pack(anchor='w', padx=8, pady=4)
    cp_btn(s8, 'On-Screen Keyboard','⌨', lambda: show_system_notification('OSK','On-Screen Keyboard launched.'))
    cp_btn(s8, 'Magnifier','🔍', lambda: show_system_notification('Magnifier','Magnifier is active.'))
    cp_btn(s8, 'Speech Recognition','🎙', lambda: show_system_notification('Speech','Windows Speech Recognition ready.'))

    # ══ TAB 9: Advanced ═══════════════════════════════════════════════════
    t9 = tk.Frame(nb, bg=CP_BG); nb.add(t9, text='Advanced')

    s9 = cp_section(t9,'Advanced System Settings')
    for btn_lbl, icon, fn in [
        ('Environment Variables','📄', lambda: show_system_notification('Env Vars','PATH, TEMP, WINDIR etc.')),
        ('Virtual Memory','💻', lambda: show_system_notification('Virtual Memory','Page file: System managed.')),
        ('Startup & Recovery','🔧', lambda: show_system_notification('Recovery','Default OS: Windows 7.')),
        ('Error Reporting','📧', lambda: show_system_notification('Error Reports','Automatic reporting is on.')),
        ('Performance Options','📊', lambda: show_system_notification('Performance','Adjust for best appearance.')),
        ('Remote Desktop','🖥', lambda: show_system_notification('Remote','Remote Desktop is disabled.')),
        ('Windows Installer Helper','📦', show_windows_installer_helper),
        ('BIOS / Boot Menu','⚙', show_bios_boot_menu),
    ]:
        cp_btn(s9, btn_lbl, icon, fn)

    # Footer
    tk.Frame(settings_win, height=1, bg='#c0ccdd').pack(fill='x')
    foot = tk.Frame(settings_win, bg='#e8f0fc', height=32)
    foot.pack(fill='x'); foot.pack_propagate(False)
    tk.Label(foot, text=f'Windows 7 {state.get("os_version","Ultimate")}  ·  '
             f'{"✅ Activated" if state.get("activated") else "⚠ Not Activated"}',
             bg='#e8f0fc', fg='#3a6080', font=('Segoe UI',8)).pack(side='left', padx=12, pady=8)
    tk.Button(foot, text='Close', bg='#3878c8', fg='white', relief='flat',
              font=('Segoe UI',9), command=settings_win.destroy).pack(side='right', padx=12, pady=6)



def show_search_results(query, results):
    result_win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    result_win.title(f'Search Results: {query}')
    result_win.geometry('420x320')
    style_aero_window(result_win, '#eef2ff')
    center_window(result_win, 420, 320)

    tk.Label(result_win, text=f'Search results for "{query}"', bg='#eef2ff', fg='#16375c', font=('Segoe UI', 12, 'bold')).pack(pady=(12,8))
    frame = tk.Frame(result_win, bg='#eef2ff')
    frame.pack(fill='both', expand=True, padx=16, pady=8)
    listbox = tk.Listbox(frame, bg='white', fg='#0f2243', font=('Segoe UI', 10), activestyle='none')
    listbox.pack(side='left', fill='both', expand=True)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=listbox.yview)
    scrollbar.pack(side='right', fill='y')
    listbox.config(yscrollcommand=scrollbar.set)

    callbacks = []
    for label, callback in results:
        callbacks.append(callback)
        listbox.insert('end', label)

    def choose_result(event=None):
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        result_win.destroy()
        callbacks[idx]()

    listbox.bind('<Double-1>', choose_result)
    tk.Button(result_win, text='Open Selected', bg='#4f80d4', fg='white', command=choose_result).pack(pady=(0,10))


def show_system_notification(title, message, kind='info'):
    """Windows 7 style action-center toast notification with authentic sound."""
    # Play the matching W7 sound
    try:
        if kind == 'error':
            play_windows7_error()
        elif kind == 'warning':
            play_windows7_exclamation()
        elif kind == 'question':
            play_windows7_question()
        else:
            play_windows7_notification()
    except Exception:
        pass

    parent = desktop_win if desktop_win and desktop_win.winfo_exists() else root
    notification = tk.Toplevel(parent)
    notification.overrideredirect(True)
    notification.attributes('-topmost', True)
    notification.attributes('-alpha', 0.95)
    notification.configure(bg='#1c2f4d')
    screen_w = (desktop_win or root).winfo_screenwidth()
    screen_h = (desktop_win or root).winfo_screenheight()
    width, height = 310, 110
    x = screen_w - width - 16
    y = screen_h - height - 90
    notification.geometry(f'{width}x{height}+{x}+{y}')

    icon_map = {'error': '⛔', 'warning': '⚠', 'question': '❓', 'info': 'ℹ'}
    icon = icon_map.get(kind, 'ℹ')

    top_row = tk.Frame(notification, bg='#1c2f4d')
    top_row.pack(fill='x', padx=12, pady=(12, 0))
    tk.Label(top_row, text=icon, bg='#1c2f4d', fg='white', font=('Segoe UI Emoji', 11)).pack(side='left', padx=(0,6))
    tk.Label(top_row, text=title, bg='#1c2f4d', fg='white', font=('Segoe UI', 11, 'bold')).pack(side='left')
    tk.Label(notification, text=message, bg='#1c2f4d', fg='#d7e4ff', font=('Segoe UI', 9),
             wraplength=286, justify='left').pack(anchor='nw', padx=12, pady=(6, 0))
    controls = tk.Frame(notification, bg='#1c2f4d')
    controls.pack(fill='x', pady=8, padx=12)
    tk.Button(controls, text='Dismiss', bg='#203450', fg='white', width=10,
              command=notification.destroy).pack(side='right')
    notification.after(7000, lambda: notification.destroy() if notification.winfo_exists() else None)


def show_login(after_restart=False):
    """Windows 7 Welcome Screen – full redesign."""
    global login_win
    login_win = tk.Toplevel()
    login_win.title('Windows 7 — Sign In')
    login_win.overrideredirect(True)
    login_win.attributes('-topmost', True)

    sw = login_win.winfo_screenwidth() or 1920
    sh = login_win.winfo_screenheight() or 1080
    login_win.geometry(f'{sw}x{sh}+0+0')
    login_win.configure(bg='#000c1a')

    # ── full-screen gradient background ──────────────────────────────────
    bg_cv = tk.Canvas(login_win, bg='#000c1a', highlightthickness=0)
    bg_cv.place(x=0, y=0, width=sw, height=sh)
    # Sky gradient — deep navy to soft blue
    for i in range(sh):
        t = i / sh
        r0 = int(0 + 12*t); g0 = int(8 + 30*t); b0 = int(22 + 58*t)
        bg_cv.create_line(0, i, sw, i, fill=f'#{r0:02x}{g0:02x}{b0:02x}')
    # Aurora glow band
    for i in range(160):
        t = abs(i/80 - 1)
        intensity = int(40*(1-t))
        c = f'#{0:02x}{intensity:02x}{min(255,intensity*3):02x}'
        bg_cv.create_line(0, sh//2 - 80 + i, sw, sh//2 - 80 + i, fill=c)

    # ── top Windows logo + edition ────────────────────────────────────────
    # Draw 4-color Windows flag
    fx, fy = 48, 28
    logo_cv = tk.Canvas(login_win, width=48, height=48, bg='#000c1a', highlightthickness=0)
    logo_cv.place(x=48, y=28)
    hx, hy = 24, 24; q = 8; gap = 2
    logo_cv.create_oval(0,0,48,48, fill='#1060b0', outline='#40a0dc', width=2)
    logo_cv.create_rectangle(hx-q-gap-q, hy-q-gap-q, hx-gap, hy-gap, fill='#f04820', outline='')
    logo_cv.create_rectangle(hx+gap, hy-q-gap-q, hx+gap+2*q, hy-gap, fill='#00a8ef', outline='')
    logo_cv.create_rectangle(hx-q-gap-q, hy+gap, hx-gap, hy+gap+2*q, fill='#7fba00', outline='')
    logo_cv.create_rectangle(hx+gap, hy+gap, hx+gap+2*q, hy+gap+2*q, fill='#ffb900', outline='')

    ver_label = tk.Label(login_win, text=f"Windows 7  {state.get('os_version','Ultimate')}",
                         bg='#000c1a', fg='#a8ccee', font=('Segoe UI Light', 22))
    ver_label.place(x=108, y=36)

    # Thin separator under header
    sep_cv = tk.Canvas(login_win, height=1, bg='#000c1a', highlightthickness=0)
    sep_cv.place(x=0, y=84, width=sw)
    sep_cv.create_line(0, 0, sw, 0, fill='#1a4a80')

    # ── user card ─────────────────────────────────────────────────────────
    card_w, card_h = 420, 480
    card_x = (sw - card_w) // 2
    card_y = (sh - card_h) // 2 - 20

    # Card shadow
    bg_cv.create_rectangle(card_x+6, card_y+6, card_x+card_w+6, card_y+card_h+6,
                            fill='#000010', outline='', stipple='gray25')

    card = tk.Frame(login_win, bg='#0a1828', bd=0)
    card.place(x=card_x, y=card_y, width=card_w, height=card_h)

    # Aero top rim
    tk.Frame(card, bg='#3878c8', height=3).pack(fill='x')
    # Left rim
    tk.Frame(card, bg='#1a4a80', width=2).pack(fill='y', side='left')

    inner = tk.Frame(card, bg='#0a1828', padx=32, pady=20)
    inner.pack(fill='both', expand=True)

    # Right rim (pack last)
    tk.Frame(card, bg='#1a4a80', width=2).pack(fill='y', side='right')
    # Bottom rim
    tk.Frame(card, bg='#16406c', height=2).pack(fill='x')

    # ── avatar ────────────────────────────────────────────────────────────
    av = tk.Canvas(inner, width=90, height=90, bg='#0a1828', highlightthickness=0)
    av.pack(pady=(0,10))
    av.create_oval(1,1,89,89, fill='', outline='#1a4a80', width=6)
    av.create_oval(4,4,86,86, fill='#122038', outline='#2a70b8', width=2)
    av.create_oval(12,12,78,78, fill='#1a3460', outline='')
    initials = ((state.get('first_name','R') or 'R')[:1] + (state.get('last_name','S') or 'S')[:1]).upper()
    av.create_text(45,45, text=initials, fill='#c8e0ff', font=('Segoe UI',28,'bold'))

    user_full = f"{state.get('first_name','Ryan')} {state.get('last_name','Sahdev')}"
    tk.Label(inner, text=user_full, fg='#ddeeff', bg='#0a1828',
             font=('Segoe UI',15,'bold')).pack(pady=(0,3))
    tk.Label(inner, text='Windows 7 User Account', fg='#3a6898', bg='#0a1828',
             font=('Segoe UI',8)).pack(pady=(0,14))

    tk.Frame(inner, bg='#1a4070', height=1).pack(fill='x', pady=(0,14))

    # Theme picker
    mf = tk.Frame(inner, bg='#0a1828'); mf.pack(fill='x', pady=(0,10))
    tk.Label(mf, text='Sign-in theme:', bg='#0a1828', fg='#3a6898',
             font=('Segoe UI',8)).pack(side='left')
    smv = tk.StringVar(value=state.get('signin_mode','Aero'))
    om = tk.OptionMenu(mf, smv, 'Aero','Dark','Neon','Classic',
                       command=lambda m: state.update({'signin_mode':m}) or save_state())
    om.config(bg='#102030', fg='#7ab0d8', relief='flat', font=('Segoe UI',8),
              activebackground='#1a3a5a', bd=0, highlightthickness=0)
    om['menu'].config(bg='#102030', fg='#c0d8f0', font=('Segoe UI',8))
    om.pack(side='right')

    # Name row
    nr = tk.Frame(inner, bg='#0a1828'); nr.pack(fill='x', pady=(0,10))
    fn_var = tk.StringVar(value=state.get('first_name','Ryan'))
    ln_var = tk.StringVar(value=state.get('last_name','Sahdev'))
    for lbl_text, var in [('First Name', fn_var), ('Last Name', ln_var)]:
        col = tk.Frame(nr, bg='#0a1828'); col.pack(side='left', padx=(0,8), fill='x', expand=True)
        tk.Label(col, text=lbl_text, fg='#3a6898', bg='#0a1828',
                 font=('Segoe UI',8)).pack(anchor='w')
        tk.Entry(col, textvariable=var, bg='#0c1e30', fg='white',
                 insertbackground='#60a8e0', relief='flat',
                 highlightthickness=1, highlightbackground='#1e4870',
                 highlightcolor='#3878c8', font=('Segoe UI',10), width=14).pack(fill='x', ipady=5)

    # Password
    tk.Label(inner, text='Password', fg='#3a6898', bg='#0a1828',
             font=('Segoe UI',8)).pack(anchor='w')
    pwd_var = tk.StringVar()
    pwd_e = tk.Entry(inner, textvariable=pwd_var, show='●',
                     bg='#0c1e30', fg='white', insertbackground='#60a8e0',
                     relief='flat', highlightthickness=1,
                     highlightbackground='#1e4870', highlightcolor='#3878c8',
                     font=('Segoe UI',12), width=30)
    pwd_e.pack(fill='x', ipady=7, pady=(0,10))
    pwd_e.focus_set()

    rem_var = tk.BooleanVar(value=state.get('remember_me', False))
    tk.Checkbutton(inner, text='Remember me', variable=rem_var,
                   bg='#0a1828', fg='#3a6898', selectcolor='#0c1e30',
                   activebackground='#0a1828', font=('Segoe UI',9)).pack(anchor='w', pady=(0,8))

    status_lbl = tk.Label(inner, text='', fg='#ff8888', bg='#0a1828', font=('Segoe UI',9))
    status_lbl.pack(pady=(0,8))

    def attempt_login():
        # ── Brute-force lockout check ─────────────────────────────────────
        now_ts = time.time()
        if _login_attempts['locked_until'] > now_ts:
            remaining = int(_login_attempts['locked_until'] - now_ts)
            status_lbl.config(text=f'Too many failed attempts. Wait {remaining}s.')
            play_windows7_error()
            return

        pwd = pwd_var.get() or ''
        state['first_name'] = fn_var.get().strip() or 'Ryan'
        state['last_name']  = ln_var.get().strip() or 'Sahdev'
        state['user_name']  = f"{state['first_name']} {state['last_name']}"
        state['remember_me'] = rem_var.get()
        save_state()
        sec = load_security()
        if sec.get('locked'):
            if verify_product_key(pwd, sec.get('product_hash')):
                sec['locked'] = False; save_security(sec)
                audit_log('LOGIN_PRODUCT_KEY', 'Product key unlock succeeded', 'INFO')
                _login_attempts['count'] = 0
                start_login_loading()
            else:
                audit_log('LOGIN_PRODUCT_KEY_FAIL', 'Invalid product key attempt', 'WARN')
                status_lbl.config(text='Invalid product key.')
                pwd_e.config(highlightbackground='#c04040')
                login_win.after(1400, lambda: pwd_e.config(highlightbackground='#1e4870'))
            return
        if not sec or 'salt' not in sec or 'key' not in sec:
            if not ensure_password_set():
                status_lbl.config(text='Password required.')
                return
            sec = load_security()
        if verify_password(pwd, sec['salt'], sec['key']):
            _login_attempts['count'] = 0
            _login_attempts['locked_until'] = 0.0
            audit_log('LOGIN_SUCCESS', f'User: {state["user_name"]}', 'INFO')
            start_login_loading()
        else:
            _login_attempts['count'] += 1
            audit_log('LOGIN_FAIL',
                      f'Attempt {_login_attempts["count"]}/{MAX_LOGIN_ATTEMPTS} — '
                      f'User: {state["user_name"]}', 'WARN')
            if _login_attempts['count'] >= MAX_LOGIN_ATTEMPTS:
                _login_attempts['locked_until'] = time.time() + LOGIN_LOCKOUT_SECONDS
                _login_attempts['count'] = 0
                audit_log('LOGIN_LOCKOUT',
                          f'Account locked for {LOGIN_LOCKOUT_SECONDS}s after repeated failures',
                          'CRITICAL')
                status_lbl.config(
                    text=f'Account locked for {LOGIN_LOCKOUT_SECONDS}s. Too many failed attempts.')
                play_windows7_error()
            else:
                remaining_attempts = MAX_LOGIN_ATTEMPTS - _login_attempts['count']
                status_lbl.config(
                    text=f'Incorrect password. {remaining_attempts} attempt(s) remaining.')
            pwd_e.config(highlightbackground='#c04040')
            login_win.after(1400, lambda: pwd_e.config(highlightbackground='#1e4870'))

    # Animated Sign-In button
    sign_cv = tk.Canvas(inner, height=42, bg='#0a1828', highlightthickness=0, cursor='hand2')
    sign_cv.pack(fill='x', pady=(2,0))

    def _paint_sbtn(hover=False):
        sign_cv.delete('all')
        w2 = sign_cv.winfo_width() or 350
        ct = '#4a9adc' if hover else '#3070b8'
        cb = '#1a4888' if hover else '#0c3060'
        for i in range(42):
            t = i/42
            rr = int(int(ct[1:3],16)*(1-t)+int(cb[1:3],16)*t)
            gg = int(int(ct[3:5],16)*(1-t)+int(cb[3:5],16)*t)
            bb = int(int(ct[5:7],16)*(1-t)+int(cb[5:7],16)*t)
            sign_cv.create_line(0,i,w2,i, fill=f'#{rr:02x}{gg:02x}{bb:02x}')
        sign_cv.create_rectangle(0,0,w2,42, outline='#5aaae8' if hover else '#2a60a0', width=1)
        sign_cv.create_line(1,1,w2-1,1, fill='#80c0f0', width=1)
        sign_cv.create_text(w2//2,21, text='Sign In  →', fill='white', font=('Segoe UI',12,'bold'))

    sign_cv.bind('<Configure>', lambda e: _paint_sbtn())
    sign_cv.bind('<Enter>', lambda e: _paint_sbtn(True))
    sign_cv.bind('<Leave>', lambda e: _paint_sbtn(False))
    sign_cv.bind('<Button-1>', lambda e: attempt_login())
    login_win.after(100, _paint_sbtn)

    # Small buttons
    bf = tk.Frame(inner, bg='#0a1828'); bf.pack(fill='x', pady=(10,0))
    def _sb(t, cmd):
        tk.Button(bf, text=t, command=cmd, bg='#0c1e30', fg='#3a6898',
                  relief='flat', font=('Segoe UI',8), padx=8, pady=4,
                  activebackground='#1a3a5a', bd=0, cursor='hand2').pack(side='left', padx=(0,6))

    def open_bios():
        login_win.destroy(); show_bios_boot_menu()

    _sb('F8 — BIOS', open_bios)
    _sb('Forgot Password', lambda: messagebox.showinfo('Password',
        'Use the Restore button on the assistant panel.'))

    login_win.bind('<Return>', lambda e: attempt_login())
    login_win.bind('<F8>', lambda e: open_bios())

    # ── Alt+F4: emergency exit back to real host OS ───────────────────────
    def alt_f4_escape(event=None):
        """Press Alt+F4 on login screen to immediately close the entire simulation
        and return to the real host desktop — useful if you get stuck."""
        try:
            play_windows7_logoff()
        except Exception:
            pass
        root.destroy()

    login_win.bind('<Alt-F4>', alt_f4_escape)
    login_win.bind('<Alt-f>', alt_f4_escape)  # fallback
    # Subtle hint label at bottom-right
    tk.Label(login_win, text='Alt+F4 — Exit simulation',
             fg='#0e2a50', bg='#000c1a', font=('Segoe UI', 7)).place(
             x=sw - 160, y=sh - 22)

    if after_restart or state.get('show_driver_prompt'):
        drv = tk.Frame(inner, bg='#080e18', bd=1, relief='solid')
        drv.pack(fill='x', pady=(14,0))
        tk.Label(drv, text='⚠  Driver Setup', bg='#080e18', fg='#ffcc44',
                 font=('Segoe UI',9,'bold')).pack(anchor='w', padx=8, pady=(6,2))
        bf2 = tk.Frame(drv, bg='#080e18'); bf2.pack(fill='x', padx=8, pady=(2,8))
        _sb('Install Drivers', lambda: [install_drivers(),
            show_system_notification('Drivers','Installed.'), drv.destroy()])
        _sb('Skip', lambda: [state.update({'drivers_installed':False,'show_driver_prompt':False}),
            save_state(), drv.destroy()])

    # Copyright footer
    tk.Label(login_win, text=f'© 2009 Microsoft Corporation  ·  Windows 7 {state.get("os_version","Ultimate")}',
             fg='#1a3860', bg='#000c1a', font=('Segoe UI',8)).place(
             x=sw//2, y=sh-24, anchor='center')

    def start_login_loading():
        login_win.withdraw()
        loading = tk.Toplevel(root)
        loading.overrideredirect(True)
        loading.attributes('-topmost', True)
        loading.geometry(f'{sw}x{sh}+0+0')
        loading.configure(bg='#000c1a')

        # Dark gradient
        ll_cv = tk.Canvas(loading, bg='#000c1a', highlightthickness=0)
        ll_cv.place(x=0, y=0, width=sw, height=sh)
        for i2 in range(sh):
            t2 = i2/sh
            r4=int(0+6*t2); g4=int(8+16*t2); b4=int(22+36*t2)
            ll_cv.create_line(0,i2,sw,i2, fill=f'#{r4:02x}{g4:02x}{b4:02x}')

        tk.Label(loading, text=f"Welcome, {state.get('first_name','Ryan')}",
                 bg='#000c1a', fg='#c8deff', font=('Segoe UI Light',32)).place(
                 x=sw//2, y=int(sh*0.38), anchor='center')
        tk.Label(loading, text=f"Windows 7 {state.get('os_version','Ultimate')}",
                 bg='#000c1a', fg='#264a70', font=('Segoe UI',11)).place(
                 x=sw//2, y=int(sh*0.46), anchor='center')

        # Thin progress bar (Win7-style: 300px wide, 4px tall)
        pb_bg = tk.Canvas(loading, width=300, height=6, bg='#0a1e38',
                          highlightthickness=1, highlightbackground='#1a4070')
        pb_bg.place(x=sw//2-150, y=int(sh*0.54))
        prect = pb_bg.create_rectangle(0,0,0,6, fill='#3878c8', outline='')

        step = {'v': 0}
        msgs = ['Loading your settings…','Applying Windows 7 Aero…',
                'Preparing desktop…','Starting services…','Welcome!']
        st_lbl = tk.Label(loading, text=msgs[0], bg='#000c1a', fg='#264a70',
                          font=('Segoe UI',9))
        st_lbl.place(x=sw//2, y=int(sh*0.59), anchor='center')

        def tick():
            step['v'] += 1
            pb_bg.coords(prect, 0,0, int(300*step['v']/10), 6)
            st_lbl.config(text=msgs[min(step['v']//2, len(msgs)-1)])
            if step['v'] < 10:
                loading.after(380, tick)
            else:
                loading.destroy()
                show_boot_screen(lambda: [login_win.destroy(), show_desktop()])
        tick()

    login_win.grab_set()
    login_win.focus_force()
    login_win.lift()


# --- UI ---
root = tk.Tk()
root.title('Windows 7 — Assistant Panel')
root.geometry('960x720')
root.configure(bg='#0b1622')
root.withdraw()
root.protocol('WM_DELETE_WINDOW', on_close_ai)

# Top controls
frame_top = tk.Frame(root, bg='#0b1622')
frame_top.pack(fill='x', padx=12, pady=8)

lbl_title = tk.Label(frame_top, text='Windows 7 Desktop', fg='#7be7ff', bg='#0b1622', font=('Segoe UI Black', 22, 'bold'))
lbl_title.pack(side='left')

btn_change_pw = tk.Button(frame_top, text='🔐 Change Password', command=change_password, bg='#184a70', fg='white')
btn_change_pw.pack(side='right', padx=6)

btn_restore = tk.Button(frame_top, text='♻ Restore', command=lambda: restore_quarantine() and refresh_files_list(), bg='#1a7b3d', fg='white')
btn_restore.pack(side='right', padx=6)

btn_shutdown = tk.Button(frame_top, text='🛑 EMERGENCY SHUTDOWN', bg='#b41f2b', fg='white')
btn_shutdown.pack(side='right', padx=6)
btn_shutdown.config(command=emergency_shutdown)

# Center: chat + search + file manager
center = tk.Frame(root, bg='#07121a')
center.pack(fill='both', expand=True, padx=12, pady=(0,12))

# Left: Chat area
chat_left = tk.Frame(center, bg='#07121a')
chat_left.pack(side='left', fill='both', expand=True, padx=(0,6))

chat_canvas = tk.Canvas(chat_left, bg='#071827', bd=0, highlightthickness=0)
chat_canvas.pack(fill='both', expand=True, side='left')

scroll = tk.Scrollbar(chat_left, command=chat_canvas.yview)
scroll.pack(side='right', fill='y')
chat_canvas.configure(yscrollcommand=scroll.set)
chat_frame = tk.Frame(chat_canvas, bg='#071827')
chat_canvas.create_window((0,0), window=chat_frame, anchor='nw', width=580)
chat_frame.bind('<Configure>', lambda e: chat_canvas.configure(scrollregion=chat_canvas.bbox('all')))

# Right: tools
tools = tk.Frame(center, bg='#081722', width=320)
tools.pack(side='right', fill='y')

# Deep search box
tk.Label(tools, text='Deep Search', bg='#081722', fg='#cfefff').pack(pady=(8,0))
entry_search = tk.Entry(tools, width=36)
entry_search.pack(pady=6, padx=8)

lst_results = tk.Listbox(tools, width=48, height=12)
lst_results.pack(padx=8)

btn_search = tk.Button(tools, text='Search', bg='#2a6fb0', fg='white')
btn_search.pack(padx=8, pady=6, fill='x')

btn_handover = tk.Button(tools, text='Handover to Web (query)', bg='#2a6fb0', fg='white')
btn_handover.pack(padx=8, pady=(0,8), fill='x')

# File manager area
tk.Label(tools, text='Assistant Files', bg='#081722', fg='#cfefff').pack(pady=(6,0))
files_frame = tk.Frame(tools, bg='#081722')
files_frame.pack(fill='both', expand=True, padx=8, pady=6)

files_listbox = tk.Listbox(files_frame, width=48, height=8)
files_listbox.pack(side='left', fill='both', expand=True)

files_scroll = tk.Scrollbar(files_frame, command=files_listbox.yview)
files_scroll.pack(side='right', fill='y')
files_listbox.configure(yscrollcommand=files_scroll.set)

btn_refresh_files = tk.Button(tools, text='Refresh Files', bg='#1862d1', fg='white')
btn_refresh_files.pack(padx=8, pady=(2,6), fill='x')

btn_quarantine = tk.Button(tools, text='🗄️ Quarantine Selected', bg='#d07f00', fg='white')
btn_quarantine.pack(padx=8, pady=(0,6), fill='x')

btn_encrypt = tk.Button(tools, text='🔐 Encrypt Selected', bg='#3f6db5', fg='white')
btn_encrypt.pack(padx=8, pady=(0,6), fill='x')

btn_decrypt = tk.Button(tools, text='🔓 Decrypt Selected', bg='#3f9f4c', fg='white')
btn_decrypt.pack(padx=8, pady=(0,6), fill='x')

btn_delete_perm = tk.Button(tools, text='🗑️ Delete Permanently', bg='#b41f2b', fg='white')
btn_delete_perm.pack(padx=8, pady=(0,12), fill='x')

# Bottom: input
bottom = tk.Frame(root, bg='#081827', height=120)
bottom.pack(fill='x')

entry_input = tk.Text(bottom, height=3, bg='#0d2230', fg='white')
entry_input.pack(fill='both', expand=True, side='left', padx=12, pady=12)

btn_send = tk.Button(bottom, text='Send', bg='#2f78d6', fg='white')
btn_send.pack(side='right', padx=12, pady=20)

# --- Chat helpers ---

def post_message(text, sender='assistant'):
    frame = tk.Frame(chat_frame, bg='#071827')
    frame.pack(fill='x', pady=6)
    if sender == 'user':
        b = tk.Label(frame, text=text, bg='#113047', fg='white', anchor='e', justify='right', wraplength=460, padx=8, pady=6)
        b.pack(anchor='e', padx=(60,10))
    else:
        b = tk.Label(frame, text=text, bg='#dfe8ff', fg='#14253b', anchor='w', justify='left', wraplength=460, padx=8, pady=6)
        b.pack(anchor='w', padx=(10,60))
    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

# --- File list functions ---

def refresh_files_list():
    files_listbox.delete(0, 'end')
    for p in list_data_files():
        files_listbox.insert('end', p)


def on_quarantine_selected():
    sel = files_listbox.curselection()
    if not sel:
        messagebox.showinfo('Select', 'No file selected.')
        return
    path = files_listbox.get(sel[0])
    if not check_password('Confirm move to quarantine'):
        messagebox.showwarning('Denied', 'Password required.')
        return
    ok, msg = delete_data_file(path, permanent=False)
    messagebox.showinfo('Quarantine', msg)
    refresh_files_list()


def on_delete_perm():
    sel = files_listbox.curselection()
    if not sel:
        messagebox.showinfo('Select', 'No file selected.')
        return
    path = files_listbox.get(sel[0])
    if not check_password('Confirm permanent deletion'):
        messagebox.showwarning('Denied', 'Password required.')
        return
    ok, msg = delete_data_file(path, permanent=True)
    if ok:
        messagebox.showinfo('Deleted', msg)
    else:
        messagebox.showerror('Error', msg)
    refresh_files_list()


def handle_encrypt(decrypt=False):
    sel = files_listbox.curselection()
    if not sel:
        messagebox.showinfo('Select', 'No file selected.')
        return
    path = files_listbox.get(sel[0])
    if decrypt:
        ok, msg = decrypt_data_file(path)
    else:
        ok, msg = encrypt_data_file(path)
    if ok:
        messagebox.showinfo('Success', msg)
    else:
        messagebox.showerror('Error', msg)
    refresh_files_list()

# --- Search handlers ---

def on_search():
    q = entry_search.get().strip()
    lst_results.delete(0, 'end')
    if not q:
        return
    results = deep_search(q)
    if not results:
        lst_results.insert('end', 'No results found locally. Try handover to web.')
        return
    for r in results:
        if r['type'] == 'note':
            lst_results.insert('end', f"Note {r['id']}: {r['text'][:80]}")
        elif r['type'] == 'task':
            lst_results.insert('end', f"Task {r['id']}: {r['text'][:80]}")
        else:
            lst_results.insert('end', f"File: {r['path']} -- ...{r['excerpt'][:80]}")


def on_handover_web():
    q = entry_search.get().strip()
    if not q:
        messagebox.showinfo('Handover', 'Please enter query')
        return
    webbrowser.open('https://www.google.com/search?q=' + urllib.parse.quote_plus(q))

# --- Input processing ---

def process_input():
    txt = entry_input.get('1.0', 'end').strip()
    if not txt:
        return

    # Expand chat shortcuts
    shortcuts = state.get('shortcuts', {})
    for key, expansion in shortcuts.items():
        if txt.strip().lower() == key.lower():
            txt = expansion
            break

    post_message(txt, 'user')
    # Save to chat history
    state.setdefault('chat_history', []).append({'role': 'user', 'text': txt, 'time': datetime.now().isoformat()})
    if len(state['chat_history']) > 200:
        state['chat_history'] = state['chat_history'][-200:]

    entry_input.delete('1.0', 'end')
    cmd = txt.lower()

    # Launch
    if cmd.startswith('launch '):
        answer = launch_app(cmd)
        post_message(answer, 'assistant')
        return

    # Notes
    if cmd.startswith('add note') or cmd.startswith('note to'):
        content = re.sub(r'^(add note|note to)\s*', '', txt, flags=re.I).strip()
        if content:
            nid = len(state['notes']) + 1
            note = {'id': nid, 'text': content, 'created': datetime.now().isoformat()}
            state['notes'].append(note)
            save_state()
            post_message('Note saved.', 'assistant')
            return
        post_message('Please provide note text.', 'assistant')
        return

    if cmd in ('show notes', 'list notes'):
        if not state['notes']:
            post_message('No notes found.', 'assistant')
        else:
            for n in state['notes'][-10:]:
                post_message(f"{n['id']}. {n['text']}", 'assistant')
        return

    # Tasks
    if cmd.startswith('add task'):
        content = re.sub(r'^add task\s*', '', txt, flags=re.I).strip()
        if content:
            tid = len(state['tasks']) + 1
            t = {'id': tid, 'task': content, 'completed': False, 'created': datetime.now().isoformat()}
            state['tasks'].append(t)
            save_state()
            post_message('Task added.', 'assistant')
            return
        post_message('Please provide task text.', 'assistant')
        return

    if cmd.startswith('complete task'):
        m = re.search(r'complete task (\d+)', cmd)
        if m:
            tid = int(m.group(1))
            for t in state['tasks']:
                if t['id'] == tid:
                    t['completed'] = True
                    save_state()
                    post_message('Task completed.', 'assistant')
                    return
        post_message('Task not found.', 'assistant')
        return

    # Safe math
    mexpr = re.sub(r'[^0-9\.\+\-\*\/\%\(\)\s]', '', txt)
    if re.search(r'[0-9]', mexpr) and re.search(r'[\+\-\*\/\%]', mexpr):
        try:
            r = safe_eval(mexpr)
            post_message(f'Result: {r}', 'assistant')
            return
        except Exception:
            pass

    # Deep search command
    if cmd.startswith('deep search'):
        q = re.sub(r'^deep search\s*', '', txt, flags=re.I).strip()
        res = deep_search(q)
        if not res:
            post_message('No local results. Use handover to web.', 'assistant')
        else:
            for r in res:
                post_message(str(r), 'assistant')
        return

    # Default
    post_message(
        'I am ready. Try: launch <app>, add note, deep search <query>.\n'
        'New apps: journal, alarm, bookmarks, pomodoro, habit, converter, password generator, '
        'text analyzer, quote, clipboard, shortcuts, world clock, color picker, typing test, '
        'flashcards, note search, stopwatch, finance, ascii art, task board.',
        'assistant'
    )

# ============================================================
# FEATURE 1: Journal / Diary with mood tracking
# ============================================================
def show_journal():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Journal')
    win.geometry('600x520')
    style_aero_window(win, '#f5f8ff')
    center_window(win, 600, 520)

    tk.Label(win, text='Personal Journal', bg='#f5f8ff', fg='#1c3f73', font=('Segoe UI', 16, 'bold')).pack(pady=(14, 4))
    moods = ['😊 Happy', '😐 Neutral', '😢 Sad', '😤 Angry', '😴 Tired', '🎉 Excited']
    mood_var = tk.StringVar(value=moods[0])
    mf = tk.Frame(win, bg='#f5f8ff')
    mf.pack(fill='x', padx=16, pady=4)
    tk.Label(mf, text='Mood:', bg='#f5f8ff', fg='#1c3f73', font=('Segoe UI', 10, 'bold')).pack(side='left')
    ttk.Combobox(mf, textvariable=mood_var, values=moods, width=18, state='readonly').pack(side='left', padx=8)

    txt_area = tk.Text(win, font=('Segoe UI', 11), wrap='word', height=12, bg='white', fg='#14253b', bd=1, relief='solid')
    txt_area.pack(fill='both', expand=True, padx=16, pady=8)
    txt_area.insert('end', 'Write your thoughts here...')

    entries_frame = tk.Frame(win, bg='#e8f0ff', bd=1, relief='solid')
    entries_frame.pack(fill='x', padx=16, pady=(0, 8))
    entries_box = tk.Listbox(entries_frame, height=5, bg='white', fg='#14253b', font=('Segoe UI', 9))
    entries_box.pack(fill='both', expand=True, padx=4, pady=4)

    for e in state.get('journal', [])[-10:]:
        entries_box.insert('end', f"{e['date'][:10]} [{e['mood']}]: {e['text'][:60]}")

    def save_entry():
        text = txt_area.get('1.0', 'end').strip()
        if not text or text == 'Write your thoughts here...':
            messagebox.showinfo('Journal', 'Please write something first.')
            return
        entry = {'date': datetime.now().isoformat(), 'mood': mood_var.get(), 'text': text}
        state.setdefault('journal', []).append(entry)
        save_state()
        entries_box.insert('end', f"{entry['date'][:10]} [{entry['mood']}]: {entry['text'][:60]}")
        txt_area.delete('1.0', 'end')
        messagebox.showinfo('Journal', 'Entry saved!')

    tk.Button(win, text='Save Entry', bg='#4f80d4', fg='white', font=('Segoe UI', 10), command=save_entry).pack(pady=6)


# ============================================================
# FEATURE 2: Alarm / Reminder system
# ============================================================
_alarm_thread_running = False

def _alarm_checker():
    while _alarm_thread_running:
        now = datetime.now().strftime('%H:%M')
        for alarm in list(state.get('alarms', [])):
            if alarm.get('time') == now and not alarm.get('fired'):
                alarm['fired'] = True
                save_state()
                try:
                    root.after(0, lambda a=alarm: messagebox.showinfo('⏰ Alarm', f"Alarm: {a.get('label', 'Time!')}"))
                    if winsound:
                        root.after(0, lambda: play_windows7_beep_sequence([(880,200),(660,200),(880,300)]))
                except Exception:
                    pass
        time.sleep(30)

def show_alarm_manager():
    global _alarm_thread_running
    if not _alarm_thread_running:
        _alarm_thread_running = True
        t = threading.Thread(target=_alarm_checker, daemon=True)
        t.start()

    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Alarm Manager')
    win.geometry('480x460')
    style_aero_window(win, '#f0f5ff')
    center_window(win, 480, 460)

    tk.Label(win, text='⏰ Alarm Manager', bg='#f0f5ff', fg='#1c3f73', font=('Segoe UI', 15, 'bold')).pack(pady=(14,6))

    form = tk.Frame(win, bg='#f0f5ff')
    form.pack(fill='x', padx=16, pady=4)
    tk.Label(form, text='Time (HH:MM):', bg='#f0f5ff', fg='#1c3f73', font=('Segoe UI', 10)).grid(row=0, column=0, sticky='w', pady=4)
    time_entry = tk.Entry(form, width=10, font=('Segoe UI', 10))
    time_entry.grid(row=0, column=1, padx=8)
    tk.Label(form, text='Label:', bg='#f0f5ff', fg='#1c3f73', font=('Segoe UI', 10)).grid(row=1, column=0, sticky='w', pady=4)
    label_entry = tk.Entry(form, width=24, font=('Segoe UI', 10))
    label_entry.grid(row=1, column=1, padx=8)

    listbox = tk.Listbox(win, height=10, bg='white', fg='#14253b', font=('Segoe UI', 9), selectmode='single')
    listbox.pack(fill='both', expand=True, padx=16, pady=8)

    def refresh():
        listbox.delete(0, 'end')
        for a in state.get('alarms', []):
            status = '✓' if a.get('fired') else '○'
            listbox.insert('end', f"{status} {a['time']} — {a.get('label','')}")

    def add_alarm():
        t_val = time_entry.get().strip()
        lbl = label_entry.get().strip() or 'Alarm'
        if not re.match(r'^\d{2}:\d{2}$', t_val):
            messagebox.showwarning('Alarm', 'Enter time in HH:MM format.')
            return
        state.setdefault('alarms', []).append({'time': t_val, 'label': lbl, 'fired': False})
        save_state()
        refresh()

    def delete_alarm():
        sel = listbox.curselection()
        if sel:
            state['alarms'].pop(sel[0])
            save_state()
            refresh()

    refresh()
    bf = tk.Frame(win, bg='#f0f5ff')
    bf.pack(pady=4)
    tk.Button(bf, text='Add Alarm', bg='#4f80d4', fg='white', command=add_alarm).pack(side='left', padx=6)
    tk.Button(bf, text='Delete Selected', bg='#c04040', fg='white', command=delete_alarm).pack(side='left', padx=6)


# ============================================================
# FEATURE 3: Bookmark Manager
# ============================================================
def show_bookmark_manager():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Bookmarks')
    win.geometry('520x440')
    style_aero_window(win, '#f2f6ff')
    center_window(win, 520, 440)

    tk.Label(win, text='🔖 Bookmark Manager', bg='#f2f6ff', fg='#1c3f73', font=('Segoe UI', 15, 'bold')).pack(pady=(14,6))

    form = tk.Frame(win, bg='#f2f6ff')
    form.pack(fill='x', padx=16, pady=4)
    tk.Label(form, text='Name:', bg='#f2f6ff', fg='#1c3f73').grid(row=0, column=0, sticky='w')
    name_e = tk.Entry(form, width=20, font=('Segoe UI', 10))
    name_e.grid(row=0, column=1, padx=6)
    tk.Label(form, text='URL:', bg='#f2f6ff', fg='#1c3f73').grid(row=1, column=0, sticky='w', pady=4)
    url_e = tk.Entry(form, width=32, font=('Segoe UI', 10))
    url_e.grid(row=1, column=1, padx=6)

    listbox = tk.Listbox(win, height=12, bg='white', fg='#14253b', font=('Segoe UI', 9))
    listbox.pack(fill='both', expand=True, padx=16, pady=8)

    def refresh():
        listbox.delete(0, 'end')
        for b in state.get('bookmarks', []):
            listbox.insert('end', f"{b['name']}  →  {b['url']}")

    def add_bm():
        n, u = name_e.get().strip(), url_e.get().strip()
        if not n or not u:
            return
        if not u.startswith('http'):
            u = 'https://' + u
        state.setdefault('bookmarks', []).append({'name': n, 'url': u})
        save_state()
        refresh()

    def open_bm():
        sel = listbox.curselection()
        if sel:
            webbrowser.open(state['bookmarks'][sel[0]]['url'])

    def del_bm():
        sel = listbox.curselection()
        if sel:
            state['bookmarks'].pop(sel[0])
            save_state()
            refresh()

    refresh()
    bf = tk.Frame(win, bg='#f2f6ff')
    bf.pack(pady=4)
    for txt, cmd in [('Add', add_bm), ('Open', open_bm), ('Delete', del_bm)]:
        tk.Button(bf, text=txt, bg='#4f80d4', fg='white', width=8, command=cmd).pack(side='left', padx=4)


# ============================================================
# FEATURE 4: Pomodoro Timer
# ============================================================
def show_pomodoro():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Pomodoro Timer')
    win.geometry('380x320')
    style_aero_window(win, '#fff5f0')
    center_window(win, 380, 320)

    tk.Label(win, text='🍅 Pomodoro Timer', bg='#fff5f0', fg='#8b1a00', font=('Segoe UI', 16, 'bold')).pack(pady=(16,4))

    sessions_label = tk.Label(win, text=f"Sessions today: {state.get('pomodoro_sessions', 0)}", bg='#fff5f0', fg='#5a2000', font=('Segoe UI', 10))
    sessions_label.pack()

    timer_label = tk.Label(win, text='25:00', bg='#fff5f0', fg='#8b1a00', font=('Segoe UI', 42, 'bold'))
    timer_label.pack(pady=12)

    status_label = tk.Label(win, text='Ready to focus?', bg='#fff5f0', fg='#5a2000', font=('Segoe UI', 10))
    status_label.pack()

    running = [False]
    remaining = [25 * 60]
    mode = ['work']

    def tick():
        if not running[0]:
            return
        if remaining[0] <= 0:
            running[0] = False
            if mode[0] == 'work':
                state['pomodoro_sessions'] = state.get('pomodoro_sessions', 0) + 1
                save_state()
                sessions_label.config(text=f"Sessions today: {state['pomodoro_sessions']}")
                if winsound:
                    play_windows7_beep_sequence([(880,200),(660,200),(880,300)])
                status_label.config(text='Work session done! Take a break.')
                mode[0] = 'break'
                remaining[0] = 5 * 60
            else:
                status_label.config(text='Break over! Ready for next session?')
                mode[0] = 'work'
                remaining[0] = 25 * 60
            running[0] = False
            return
        mins, secs = divmod(remaining[0], 60)
        timer_label.config(text=f'{mins:02d}:{secs:02d}')
        remaining[0] -= 1
        win.after(1000, tick)

    def start():
        if not running[0]:
            running[0] = True
            lbl = 'Working...' if mode[0] == 'work' else 'Break time!'
            status_label.config(text=lbl)
            tick()

    def pause():
        running[0] = False
        status_label.config(text='Paused.')

    def reset():
        running[0] = False
        mode[0] = 'work'
        remaining[0] = 25 * 60
        timer_label.config(text='25:00')
        status_label.config(text='Reset.')

    bf = tk.Frame(win, bg='#fff5f0')
    bf.pack(pady=10)
    for txt, cmd, color in [('▶ Start', start, '#d04020'), ('⏸ Pause', pause, '#b06020'), ('↺ Reset', reset, '#808080')]:
        tk.Button(bf, text=txt, bg=color, fg='white', font=('Segoe UI', 10), width=9, command=cmd).pack(side='left', padx=5)


# ============================================================
# FEATURE 5: Habit Tracker
# ============================================================
def show_unit_converter():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Unit Converter')
    win.geometry('420x420')
    style_aero_window(win, '#f5f0ff')
    center_window(win, 420, 420)

    tk.Label(win, text='📐 Unit Converter', bg='#f5f0ff', fg='#2a1a6e', font=('Segoe UI', 15, 'bold')).pack(pady=(14,8))

    categories = {
        'Length': {'km': 1000, 'm': 1, 'cm': 0.01, 'mm': 0.001, 'miles': 1609.34, 'feet': 0.3048, 'inches': 0.0254},
        'Weight': {'kg': 1, 'g': 0.001, 'lb': 0.453592, 'oz': 0.0283495},
        'Temperature': {},
        'Speed': {'km/h': 1, 'm/s': 3.6, 'mph': 1.60934},
    }

    cat_var = tk.StringVar(value='Length')
    from_var = tk.StringVar()
    to_var = tk.StringVar()
    val_var = tk.StringVar(value='1')
    result_var = tk.StringVar(value='')

    f1 = tk.Frame(win, bg='#f5f0ff')
    f1.pack(fill='x', padx=16, pady=4)
    tk.Label(f1, text='Category:', bg='#f5f0ff', fg='#2a1a6e').pack(side='left')
    cat_cb = ttk.Combobox(f1, textvariable=cat_var, values=list(categories), state='readonly', width=14)
    cat_cb.pack(side='left', padx=8)

    f2 = tk.Frame(win, bg='#f5f0ff')
    f2.pack(fill='x', padx=16, pady=4)
    tk.Label(f2, text='From:', bg='#f5f0ff', fg='#2a1a6e').pack(side='left')
    from_cb = ttk.Combobox(f2, textvariable=from_var, state='readonly', width=10)
    from_cb.pack(side='left', padx=6)
    tk.Label(f2, text='To:', bg='#f5f0ff', fg='#2a1a6e').pack(side='left')
    to_cb = ttk.Combobox(f2, textvariable=to_var, state='readonly', width=10)
    to_cb.pack(side='left', padx=6)

    f3 = tk.Frame(win, bg='#f5f0ff')
    f3.pack(fill='x', padx=16, pady=4)
    tk.Label(f3, text='Value:', bg='#f5f0ff', fg='#2a1a6e').pack(side='left')
    tk.Entry(f3, textvariable=val_var, width=14, font=('Segoe UI', 11)).pack(side='left', padx=8)

    result_label = tk.Label(win, textvariable=result_var, bg='#f5f0ff', fg='#2a1a6e', font=('Segoe UI', 16, 'bold'))
    result_label.pack(pady=16)

    def update_units(*_):
        cat = cat_var.get()
        units = list(categories.get(cat, {}).keys())
        if cat == 'Temperature':
            units = ['Celsius', 'Fahrenheit', 'Kelvin']
        from_cb['values'] = units
        to_cb['values'] = units
        if units:
            from_var.set(units[0])
            to_var.set(units[1] if len(units) > 1 else units[0])

    def convert():
        cat = cat_var.get()
        try:
            val = float(val_var.get())
        except ValueError:
            result_var.set('Invalid number')
            return
        f, t = from_var.get(), to_var.get()
        if cat == 'Temperature':
            if f == 'Celsius' and t == 'Fahrenheit': r = val * 9/5 + 32
            elif f == 'Fahrenheit' and t == 'Celsius': r = (val - 32) * 5/9
            elif f == 'Celsius' and t == 'Kelvin': r = val + 273.15
            elif f == 'Kelvin' and t == 'Celsius': r = val - 273.15
            elif f == 'Fahrenheit' and t == 'Kelvin': r = (val - 32) * 5/9 + 273.15
            elif f == 'Kelvin' and t == 'Fahrenheit': r = (val - 273.15) * 9/5 + 32
            else: r = val
        else:
            units = categories[cat]
            r = val * units[f] / units[t]
        result_var.set(f'{val} {f} = {r:.6g} {t}')

    cat_var.trace('w', update_units)
    update_units()
    tk.Button(win, text='Convert', bg='#5040c0', fg='white', font=('Segoe UI', 11), command=convert).pack(pady=8)


# ============================================================
# FEATURE 7: Password Generator
# ============================================================
def show_password_generator():
    import string
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Password Generator')
    win.geometry('420x380')
    style_aero_window(win, '#f0f5ff')
    center_window(win, 420, 380)

    tk.Label(win, text='🔐 Password Generator', bg='#f0f5ff', fg='#1c3f73', font=('Segoe UI', 15, 'bold')).pack(pady=(14,8))

    len_var = tk.IntVar(value=16)
    upper_var = tk.BooleanVar(value=True)
    lower_var = tk.BooleanVar(value=True)
    digits_var = tk.BooleanVar(value=True)
    symbols_var = tk.BooleanVar(value=True)

    f = tk.Frame(win, bg='#f0f5ff')
    f.pack(fill='x', padx=24, pady=4)
    tk.Label(f, text='Length:', bg='#f0f5ff', fg='#1c3f73').pack(side='left')
    tk.Scale(f, from_=8, to=64, orient='horizontal', variable=len_var, bg='#f0f5ff', length=200).pack(side='left', padx=8)

    opts = tk.Frame(win, bg='#f0f5ff')
    opts.pack(fill='x', padx=24, pady=4)
    for text, var in [('Uppercase', upper_var), ('Lowercase', lower_var), ('Digits', digits_var), ('Symbols', symbols_var)]:
        tk.Checkbutton(opts, text=text, variable=var, bg='#f0f5ff', fg='#1c3f73', font=('Segoe UI', 10)).pack(side='left', padx=6)

    result_var = tk.StringVar(value='Click Generate')
    result_entry = tk.Entry(win, textvariable=result_var, font=('Courier New', 13), width=30, justify='center',
                            bg='white', fg='#1c3f73', bd=2, relief='solid')
    result_entry.pack(pady=16)

    strength_label = tk.Label(win, text='', bg='#f0f5ff', fg='#1c3f73', font=('Segoe UI', 10))
    strength_label.pack()

    def generate():
        charset = ''
        if upper_var.get(): charset += string.ascii_uppercase
        if lower_var.get(): charset += string.ascii_lowercase
        if digits_var.get(): charset += string.digits
        if symbols_var.get(): charset += '!@#$%^&*()-_=+[]{}|;:,.<>?'
        if not charset:
            result_var.set('Select at least one option')
            return
        pwd = ''.join(random.choice(charset) for _ in range(len_var.get()))
        result_var.set(pwd)
        entropy = len(charset) ** len_var.get()
        if len_var.get() >= 20 and len(charset) > 60: strength = '💪 Very Strong'
        elif len_var.get() >= 14: strength = '✅ Strong'
        elif len_var.get() >= 10: strength = '⚠️ Medium'
        else: strength = '❌ Weak'
        strength_label.config(text=strength)

    def copy_pwd():
        pwd = result_var.get()
        win.clipboard_clear()
        win.clipboard_append(pwd)
        # Also save to clipboard history
        state.setdefault('clipboard_history', []).append({'text': pwd, 'time': datetime.now().isoformat()})
        save_state()
        messagebox.showinfo('Copied', 'Password copied to clipboard!')

    bf = tk.Frame(win, bg='#f0f5ff')
    bf.pack(pady=8)
    tk.Button(bf, text='Generate', bg='#4f80d4', fg='white', font=('Segoe UI', 10), command=generate).pack(side='left', padx=6)
    tk.Button(bf, text='Copy', bg='#3a8a3a', fg='white', font=('Segoe UI', 10), command=copy_pwd).pack(side='left', padx=6)


# ============================================================
# FEATURE 8: Word Counter / Text Analyzer
# ============================================================
def show_text_analyzer():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Text Analyzer')
    win.geometry('580x520')
    style_aero_window(win, '#fafff5')
    center_window(win, 580, 520)

    tk.Label(win, text='📊 Text Analyzer', bg='#fafff5', fg='#1a4a1a', font=('Segoe UI', 15, 'bold')).pack(pady=(14,6))

    txt = tk.Text(win, font=('Segoe UI', 11), wrap='word', height=12, bg='white', fg='#14253b', bd=1, relief='solid')
    txt.pack(fill='both', expand=True, padx=16, pady=8)
    txt.insert('end', 'Paste or type your text here...')

    stats_frame = tk.Frame(win, bg='#e8f5e8', bd=1, relief='solid')
    stats_frame.pack(fill='x', padx=16, pady=4)
    stats_var = tk.StringVar(value='Stats will appear here.')
    tk.Label(stats_frame, textvariable=stats_var, bg='#e8f5e8', fg='#1a4a1a', font=('Segoe UI', 10), justify='left').pack(padx=8, pady=6)

    def analyze():
        text = txt.get('1.0', 'end').strip()
        if not text:
            return
        words = len(text.split())
        chars = len(text)
        chars_no_space = len(text.replace(' ', ''))
        sentences = len(re.findall(r'[.!?]+', text)) or 1
        paragraphs = len([p for p in text.split('\n\n') if p.strip()])
        reading_time = max(1, words // 200)
        freq = {}
        for w in re.findall(r'\b\w+\b', text.lower()):
            freq[w] = freq.get(w, 0) + 1
        top5 = sorted(freq.items(), key=lambda x: -x[1])[:5]
        top_str = ', '.join(f'{w}({c})' for w, c in top5)
        stats_var.set(
            f'Words: {words}   Characters: {chars}   Chars (no spaces): {chars_no_space}\n'
            f'Sentences: {sentences}   Paragraphs: {paragraphs}   ~Reading time: {reading_time} min\n'
            f'Top words: {top_str}'
        )

    tk.Button(win, text='Analyze Text', bg='#3a7a3a', fg='white', font=('Segoe UI', 10), command=analyze).pack(pady=6)


# ============================================================
# FEATURE 9: Random Quote / Inspiration
# ============================================================
QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Life is what happens when you're busy making other plans.", "John Lennon"),
    ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
    ("Strive not to be a success, but rather to be of value.", "Albert Einstein"),
    ("I have not failed. I've just found 10,000 ways that won't work.", "Thomas A. Edison"),
    ("You must be the change you wish to see in the world.", "Mahatma Gandhi"),
    ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
    ("An unexamined life is not worth living.", "Socrates"),
    ("Spread love everywhere you go.", "Mother Teresa"),
    ("When you reach the end of your rope, tie a knot and hang on.", "Franklin D. Roosevelt"),
]

def show_quote_of_day():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Quote of the Day')
    win.geometry('500x280')
    style_aero_window(win, '#fffbf0')
    center_window(win, 500, 280)

    tk.Label(win, text='✨ Quote of the Day', bg='#fffbf0', fg='#5a4000', font=('Segoe UI', 15, 'bold')).pack(pady=(16,10))

    quote_label = tk.Label(win, text='', bg='#fffbf0', fg='#3a2800', font=('Segoe UI', 12, 'italic'), wraplength=440, justify='center')
    quote_label.pack(padx=24, pady=8)
    author_label = tk.Label(win, text='', bg='#fffbf0', fg='#8a6020', font=('Segoe UI', 10, 'bold'))
    author_label.pack()

    def new_quote():
        q, a = random.choice(QUOTES)
        quote_label.config(text=f'"{q}"')
        author_label.config(text=f'— {a}')

    new_quote()
    tk.Button(win, text='New Quote', bg='#c08020', fg='white', font=('Segoe UI', 10), command=new_quote).pack(pady=14)


# ============================================================
# FEATURE 10: Clipboard History Viewer
# ============================================================
def show_clipboard_history():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Clipboard History')
    win.geometry('520x440')
    style_aero_window(win, '#f5f5ff')
    center_window(win, 520, 440)

    tk.Label(win, text='📋 Clipboard History', bg='#f5f5ff', fg='#1c3f73', font=('Segoe UI', 15, 'bold')).pack(pady=(14,6))

    listbox = tk.Listbox(win, height=14, bg='white', fg='#14253b', font=('Segoe UI', 10), selectmode='single')
    listbox.pack(fill='both', expand=True, padx=16, pady=8)

    history = state.get('clipboard_history', [])
    for item in reversed(history[-50:]):
        listbox.insert('end', f"[{item['time'][:16]}] {item['text'][:80]}")

    def copy_selected():
        sel = listbox.curselection()
        if sel:
            idx = len(history) - 1 - sel[0]
            if 0 <= idx < len(history):
                win.clipboard_clear()
                win.clipboard_append(history[idx]['text'])
                messagebox.showinfo('Copied', 'Copied to clipboard!')

    def copy_current():
        try:
            text = win.clipboard_get()
            if text:
                state.setdefault('clipboard_history', []).append({'text': text, 'time': datetime.now().isoformat()})
                save_state()
                listbox.insert(0, f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {text[:80]}")
                messagebox.showinfo('Saved', 'Current clipboard saved to history.')
        except Exception:
            messagebox.showwarning('Clipboard', 'Nothing in clipboard.')

    bf = tk.Frame(win, bg='#f5f5ff')
    bf.pack(pady=6)
    tk.Button(bf, text='Copy Selected', bg='#4f80d4', fg='white', command=copy_selected).pack(side='left', padx=6)
    tk.Button(bf, text='Save Current Clipboard', bg='#3a8a5a', fg='white', command=copy_current).pack(side='left', padx=6)


# ============================================================
# FEATURE 11: Custom Keyboard Shortcuts Manager
# ============================================================
def show_shortcuts_manager():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Shortcuts Manager')
    win.geometry('560x480')
    style_aero_window(win, '#f0f8ff')
    center_window(win, 560, 480)

    tk.Label(win, text='⌨️ Chat Shortcuts', bg='#f0f8ff', fg='#1c3f73', font=('Segoe UI', 15, 'bold')).pack(pady=(14,4))
    tk.Label(win, text='Create aliases — type the shortcut in chat to expand it automatically.', bg='#f0f8ff', fg='#3b5c88', font=('Segoe UI', 9)).pack()

    form = tk.Frame(win, bg='#f0f8ff')
    form.pack(fill='x', padx=16, pady=8)
    tk.Label(form, text='Shortcut:', bg='#f0f8ff', fg='#1c3f73').grid(row=0, column=0, sticky='w')
    key_e = tk.Entry(form, width=16, font=('Segoe UI', 10))
    key_e.grid(row=0, column=1, padx=6)
    tk.Label(form, text='Expands to:', bg='#f0f8ff', fg='#1c3f73').grid(row=1, column=0, sticky='w', pady=4)
    val_e = tk.Entry(form, width=32, font=('Segoe UI', 10))
    val_e.grid(row=1, column=1, padx=6)

    listbox = tk.Listbox(win, height=12, bg='white', fg='#14253b', font=('Segoe UI', 10))
    listbox.pack(fill='both', expand=True, padx=16, pady=8)

    shortcuts = state.setdefault('shortcuts', {})

    def refresh():
        listbox.delete(0, 'end')
        for k, v in shortcuts.items():
            listbox.insert('end', f'{k}  →  {v}')

    def add_sc():
        k, v = key_e.get().strip(), val_e.get().strip()
        if k and v:
            shortcuts[k] = v
            save_state()
            refresh()

    def del_sc():
        sel = listbox.curselection()
        if sel:
            key = list(shortcuts.keys())[sel[0]]
            del shortcuts[key]
            save_state()
            refresh()

    refresh()
    bf = tk.Frame(win, bg='#f0f8ff')
    bf.pack(pady=4)
    tk.Button(bf, text='Add Shortcut', bg='#4f80d4', fg='white', command=add_sc).pack(side='left', padx=6)
    tk.Button(bf, text='Delete', bg='#c04040', fg='white', command=del_sc).pack(side='left', padx=6)


# ============================================================
# FEATURE 12: World Clock
# ============================================================
def show_color_picker():
    from tkinter import colorchooser
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Color Picker')
    win.geometry('400x340')
    style_aero_window(win, '#f8f5ff')
    center_window(win, 400, 340)

    tk.Label(win, text='🎨 Color Picker', bg='#f8f5ff', fg='#2a1a6e', font=('Segoe UI', 15, 'bold')).pack(pady=(14,8))

    swatch = tk.Label(win, bg='#ffffff', width=30, height=4, bd=2, relief='solid')
    swatch.pack(pady=8, padx=24)

    hex_var = tk.StringVar(value='#FFFFFF')
    rgb_var = tk.StringVar(value='RGB: (255, 255, 255)')

    tk.Label(win, textvariable=hex_var, bg='#f8f5ff', fg='#2a1a6e', font=('Courier New', 14, 'bold')).pack()
    tk.Label(win, textvariable=rgb_var, bg='#f8f5ff', fg='#4a3a8e', font=('Segoe UI', 10)).pack(pady=4)

    history_frame = tk.Frame(win, bg='#f8f5ff')
    history_frame.pack(fill='x', padx=24, pady=8)
    tk.Label(history_frame, text='Recent:', bg='#f8f5ff', fg='#2a1a6e', font=('Segoe UI', 9)).pack(side='left')
    swatches = []

    def pick_color():
        result = colorchooser.askcolor(title='Choose Color', parent=win)
        if result and result[1]:
            hex_color = result[1].upper()
            r, g, b = result[0]
            hex_var.set(hex_color)
            rgb_var.set(f'RGB: ({int(r)}, {int(g)}, {int(b)})')
            swatch.config(bg=hex_color)
            win.clipboard_clear()
            win.clipboard_append(hex_color)
            # add swatch to recent
            s = tk.Label(history_frame, bg=hex_color, width=3, height=1, bd=1, relief='solid', cursor='hand2')
            s.pack(side='left', padx=2)
            s.bind('<Button-1>', lambda e, c=hex_color: [hex_var.set(c), swatch.config(bg=c)])
            swatches.append(s)

    tk.Button(win, text='Pick Color', bg='#6040c0', fg='white', font=('Segoe UI', 10), command=pick_color).pack(pady=4)
    tk.Label(win, text='Color is auto-copied to clipboard.', bg='#f8f5ff', fg='#8878bb', font=('Segoe UI', 8)).pack()


# ============================================================
# FEATURE 14: Typing Speed Test
# ============================================================
TYPING_SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "Pack my box with five dozen liquor jugs.",
    "How vexingly quick daft zebras jump!",
    "The five boxing wizards jump quickly.",
    "Sphinx of black quartz, judge my vow.",
    "Windows 7 is a powerful and elegant operating system.",
]

def show_math_flashcards():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Math Flashcards')
    win.geometry('380x360')
    style_aero_window(win, '#fff8f0')
    center_window(win, 380, 360)

    tk.Label(win, text='🧮 Math Flashcards', bg='#fff8f0', fg='#5a2000', font=('Segoe UI', 15, 'bold')).pack(pady=(14,6))

    score = [0, 0]
    answer = [0]

    q_label = tk.Label(win, text='', bg='#fff8f0', fg='#5a2000', font=('Segoe UI', 28, 'bold'))
    q_label.pack(pady=16)

    score_label = tk.Label(win, text='Score: 0 / 0', bg='#fff8f0', fg='#8a4020', font=('Segoe UI', 10))
    score_label.pack()

    ans_var = tk.StringVar()
    ans_entry = tk.Entry(win, textvariable=ans_var, font=('Segoe UI', 20), width=8, justify='center')
    ans_entry.pack(pady=12)

    feedback = tk.Label(win, text='', bg='#fff8f0', fg='#1a6a1a', font=('Segoe UI', 11, 'bold'))
    feedback.pack()

    def new_question():
        ops = ['+', '-', '×', '÷']
        op = random.choice(ops)
        if op == '+': a, b = random.randint(1, 50), random.randint(1, 50); ans = a + b
        elif op == '-': a, b = random.randint(10, 99), random.randint(1, 10); ans = a - b
        elif op == '×': a, b = random.randint(2, 12), random.randint(2, 12); ans = a * b
        else: b = random.randint(2, 12); ans = random.randint(2, 12); a = b * ans
        q_label.config(text=f'{a} {op} {b} = ?')
        answer[0] = ans
        ans_var.set('')
        feedback.config(text='')
        ans_entry.focus()

    def check_answer():
        try:
            val = int(ans_var.get().strip())
        except ValueError:
            feedback.config(text='Enter a number!', fg='#c04040')
            return
        score[1] += 1
        if val == answer[0]:
            score[0] += 1
            feedback.config(text='✓ Correct!', fg='#1a6a1a')
        else:
            feedback.config(text=f'✗ Answer was {answer[0]}', fg='#c04040')
        score_label.config(text=f'Score: {score[0]} / {score[1]}')
        win.after(800, new_question)

    ans_entry.bind('<Return>', lambda _: check_answer())
    tk.Button(win, text='Check', bg='#c06020', fg='white', font=('Segoe UI', 11), command=check_answer).pack(pady=4)
    new_question()


# ============================================================
# FEATURE 16: Note Search & Tagging
# ============================================================
def show_note_search():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Note Search & Tags')
    win.geometry('560x480')
    style_aero_window(win, '#f5fff8')
    center_window(win, 560, 480)

    tk.Label(win, text='🔍 Note Search & Tags', bg='#f5fff8', fg='#1a4a2a', font=('Segoe UI', 15, 'bold')).pack(pady=(14,6))

    sf = tk.Frame(win, bg='#f5fff8')
    sf.pack(fill='x', padx=16, pady=4)
    search_var = tk.StringVar()
    tk.Entry(sf, textvariable=search_var, font=('Segoe UI', 11), width=32).pack(side='left', padx=4)

    listbox = tk.Listbox(win, height=14, bg='white', fg='#14253b', font=('Segoe UI', 10))
    listbox.pack(fill='both', expand=True, padx=16, pady=8)

    preview = tk.Label(win, text='', bg='#e8f5ea', fg='#1a4a2a', font=('Segoe UI', 10), wraplength=500, justify='left', anchor='nw')
    preview.pack(fill='x', padx=16, pady=4)

    filtered = [list(state.get('notes', []))]

    def refresh(notes=None):
        listbox.delete(0, 'end')
        notes = notes or state.get('notes', [])
        filtered[0] = notes
        for n in notes:
            tags = n.get('tags', '')
            listbox.insert('end', f"[{n['id']}] {n['text'][:60]}  {tags}")

    def do_search():
        q = search_var.get().strip().lower()
        if not q:
            refresh()
            return
        results = [n for n in state.get('notes', []) if q in n.get('text', '').lower() or q in n.get('tags', '').lower()]
        refresh(results)

    def on_select(_=None):
        sel = listbox.curselection()
        if sel and sel[0] < len(filtered[0]):
            n = filtered[0][sel[0]]
            preview.config(text=f"Note {n['id']} | {n['created'][:16]}\n\n{n['text']}\n\nTags: {n.get('tags','(none)')}")

    def add_tag():
        sel = listbox.curselection()
        if not sel or sel[0] >= len(filtered[0]):
            return
        n = filtered[0][sel[0]]
        tag = simpledialog.askstring('Tag', 'Enter tag (e.g. #work #personal):')
        if tag:
            n['tags'] = n.get('tags', '') + ' ' + tag.strip()
            save_state()
            refresh()

    listbox.bind('<<ListboxSelect>>', on_select)
    refresh()
    bf = tk.Frame(win, bg='#f5fff8')
    bf.pack(pady=4)
    tk.Button(bf, text='Search', bg='#4f80d4', fg='white', command=do_search).pack(side='left', padx=6)
    tk.Button(bf, text='Add Tag', bg='#3a8a3a', fg='white', command=add_tag).pack(side='left', padx=6)
    search_var.trace('w', lambda *_: do_search())


# ============================================================
# FEATURE 17: Simple Stopwatch
# ============================================================
def show_stopwatch():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Stopwatch')
    win.geometry('360x300')
    style_aero_window(win, '#f0f8ff')
    center_window(win, 360, 300)

    tk.Label(win, text='⏱ Stopwatch', bg='#f0f8ff', fg='#1c3f73', font=('Segoe UI', 15, 'bold')).pack(pady=(14,6))

    timer_label = tk.Label(win, text='00:00.00', bg='#f0f8ff', fg='#1c3f73', font=('Courier New', 38, 'bold'))
    timer_label.pack(pady=12)

    laps_box = tk.Listbox(win, height=5, bg='white', fg='#14253b', font=('Segoe UI', 9))
    laps_box.pack(fill='x', padx=24)

    running = [False]
    start_t = [0.0]
    elapsed = [0.0]
    lap_count = [0]

    def tick():
        if running[0]:
            total = elapsed[0] + (time.time() - start_t[0])
            mins = int(total // 60)
            secs = total % 60
            timer_label.config(text=f'{mins:02d}:{secs:05.2f}')
            win.after(50, tick)

    def start_stop():
        if running[0]:
            elapsed[0] += time.time() - start_t[0]
            running[0] = False
        else:
            start_t[0] = time.time()
            running[0] = True
            tick()

    def reset():
        running[0] = False
        elapsed[0] = 0.0
        timer_label.config(text='00:00.00')
        laps_box.delete(0, 'end')
        lap_count[0] = 0

    def lap():
        total = elapsed[0] + (time.time() - start_t[0] if running[0] else 0)
        lap_count[0] += 1
        mins, secs = divmod(total, 60)
        laps_box.insert('end', f'Lap {lap_count[0]}: {int(mins):02d}:{secs:05.2f}')
        laps_box.yview_moveto(1.0)

    bf = tk.Frame(win, bg='#f0f8ff')
    bf.pack(pady=10)
    tk.Button(bf, text='Start/Stop', bg='#4f80d4', fg='white', font=('Segoe UI', 10), command=start_stop).pack(side='left', padx=5)
    tk.Button(bf, text='Lap', bg='#3a8a3a', fg='white', font=('Segoe UI', 10), command=lap).pack(side='left', padx=5)
    tk.Button(bf, text='Reset', bg='#808080', fg='white', font=('Segoe UI', 10), command=reset).pack(side='left', padx=5)


# ============================================================
# FEATURE 18: Mini Finance Tracker
# ============================================================
def show_finance_tracker():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Finance Tracker')
    win.geometry('580x520')
    style_aero_window(win, '#f5fff5')
    center_window(win, 580, 520)

    tk.Label(win, text='💰 Finance Tracker', bg='#f5fff5', fg='#1a4a1a', font=('Segoe UI', 15, 'bold')).pack(pady=(14,6))

    finances = state.setdefault('finances', [])
    state.setdefault('monthly_budget', 1200.0)
    budget_target = tk.DoubleVar(value=state.get('monthly_budget', 1200.0))
    balance_var = tk.StringVar()
    budget_var = tk.StringVar()
    category_var = tk.StringVar(value='Misc')
    summary_var = tk.StringVar()

    def calc_balance():
        inc = sum(f['amount'] for f in finances if f['type'] == 'income')
        exp = sum(f['amount'] for f in finances if f['type'] == 'expense')
        bal = inc - exp
        budget = budget_target.get()
        remaining = budget - exp
        balance_var.set(f'Income: ${inc:.2f}  |  Expenses: ${exp:.2f}  |  Balance: ${bal:.2f}')
        budget_var.set(f'Monthly budget: ${budget:.2f}  |  Remaining: ${remaining:.2f}')

        by_cat = {}
        for f in finances:
            by_cat[f['category']] = by_cat.get(f['category'], 0.0) + (f['amount'] if f['type'] == 'income' else -f['amount'])
        if by_cat:
            top = sorted(by_cat.items(), key=lambda item: abs(item[1]), reverse=True)[:4]
            summary_var.set('Top categories: ' + ', '.join(f'{cat}: ${amt:.2f}' for cat, amt in top))
        else:
            summary_var.set('Add income/expenses to see category summaries and budget guidance.')

    summary_card, summary_frame = create_curvy_panel(win, width=548, height=84, bg='#e9f7ea', outline='#7bc475')
    summary_card.pack(padx=16, pady=8)
    tk.Label(summary_frame, textvariable=balance_var, bg='#e9f7ea', fg='#1b5a1e', font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(10,0), padx=10)
    tk.Label(summary_frame, textvariable=budget_var, bg='#e9f7ea', fg='#22663a', font=('Segoe UI', 10)).pack(anchor='w', padx=10)
    tk.Label(summary_frame, textvariable=summary_var, bg='#e9f7ea', fg='#285b31', font=('Segoe UI', 9), wraplength=520, justify='left').pack(anchor='w', padx=10, pady=(4,8))

    form = tk.Frame(win, bg='#f5fff5')
    form.pack(fill='x', padx=16, pady=6)
    tk.Label(form, text='Description:', bg='#f5fff5', fg='#1a4a1a').grid(row=0, column=0, sticky='w')
    desc_e = tk.Entry(form, width=22, font=('Segoe UI', 10))
    desc_e.grid(row=0, column=1, padx=6)
    tk.Label(form, text='Amount ($):', bg='#f5fff5', fg='#1a4a1a').grid(row=0, column=2, sticky='w', padx=(8,0))
    amt_e = tk.Entry(form, width=10, font=('Segoe UI', 10))
    amt_e.grid(row=0, column=3, padx=4)

    tk.Label(form, text='Category:', bg='#f5fff5', fg='#1a4a1a').grid(row=0, column=4, sticky='w', padx=(8,0))
    cat_box = ttk.Combobox(form, textvariable=category_var,
                           values=['Salary', 'Bills', 'Groceries', 'Savings', 'Investments', 'Travel', 'Misc'],
                           state='readonly', width=12, font=('Segoe UI', 9))
    cat_box.grid(row=0, column=5, padx=4)
    cat_box.current(6)

    tk.Label(form, text='Monthly budget ($):', bg='#f5fff5', fg='#1a4a1a').grid(row=1, column=0, sticky='w', pady=(8,0))
    budget_e = tk.Entry(form, width=12, textvariable=budget_target, font=('Segoe UI', 10))
    budget_e.grid(row=1, column=1, padx=6, pady=(8,0))
    tk.Button(form, text='Set Budget', bg='#2e70d1', fg='white', width=14,
              command=lambda: [state.update({'monthly_budget': budget_target.get()}), save_state(), calc_balance()]).grid(row=1, column=3, columnspan=2, padx=4, pady=(8,0), sticky='w')
    form.grid_columnconfigure(1, weight=1)

    listbox = tk.Listbox(win, height=12, bg='white', fg='#14253b', font=('Segoe UI', 9),
                         selectbackground='#4f80d4', selectforeground='white', activestyle='none', bd=0, highlightthickness=0)
    listbox.pack(fill='both', expand=True, padx=16, pady=6)

    def refresh():
        listbox.delete(0, 'end')
        for f in reversed(finances[-50:]):
            icon = '💚' if f['type'] == 'income' else '🔴'
            listbox.insert('end', f"{icon} {f['date'][:10]} | {f['category']} | {f['desc']} | ${f['amount']:.2f}")
        calc_balance()

    def add_entry():
        desc = desc_e.get().strip()
        try:
            amt = float(amt_e.get().strip())
        except ValueError:
            messagebox.showwarning('Finance', 'Enter a valid amount.')
            return
        if not desc:
            return
        finances.append({'desc': desc, 'amount': abs(amt), 'type': type_var.get(),
                         'category': category_var.get(), 'date': datetime.now().isoformat()})
        save_state()
        desc_e.delete(0, 'end')
        amt_e.delete(0, 'end')
        refresh()

    def delete_entry():
        sel = listbox.curselection()
        if sel:
            idx = len(finances) - 1 - sel[0]
            if 0 <= idx < len(finances):
                finances.pop(idx)
                save_state()
                refresh()

    def export_csv():
        if not finances:
            messagebox.showinfo('Export', 'No finance entries to export.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv',
                                            initialfile='finance_export.csv',
                                            filetypes=[('CSV files', '*.csv')],
                                            title='Export Finance Data')
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Date', 'Category', 'Type', 'Amount', 'Description'])
                for f in finances:
                    writer.writerow([f['date'], f['category'], f['type'], f['amount'], f['desc']])
            messagebox.showinfo('Export', f'Finance data exported to:\n{path}')
        except Exception as e:
            messagebox.showerror('Export Error', str(e))

    refresh()

    bf = tk.Frame(win, bg='#f5fff5')
    bf.pack(pady=6)
    tk.Button(bf, text='Add Entry', bg='#3a8a3a', fg='white', command=add_entry).pack(side='left', padx=6)
    tk.Button(bf, text='Delete Selected', bg='#c04040', fg='white', command=delete_entry).pack(side='left', padx=6)
    tk.Button(bf, text='Export CSV', bg='#0d5fa1', fg='white', command=export_csv).pack(side='left', padx=6)


# ============================================================
# FEATURE 19: ASCII Art Generator
# ============================================================
def show_ascii_art():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('ASCII Art Generator')
    win.geometry('560x420')
    style_aero_window(win, '#101820')
    center_window(win, 560, 420)

    tk.Label(win, text='ASCII Art Generator', bg='#101820', fg='#00ff88', font=('Courier New', 14, 'bold')).pack(pady=(14,6))

    sf = tk.Frame(win, bg='#101820')
    sf.pack(fill='x', padx=16, pady=4)
    tk.Label(sf, text='Text:', bg='#101820', fg='#00ff88', font=('Courier New', 10)).pack(side='left')
    text_var = tk.StringVar(value='CELINE')
    tk.Entry(sf, textvariable=text_var, font=('Courier New', 12), width=20, bg='#0a1218', fg='#00ff88',
             insertbackground='#00ff88').pack(side='left', padx=8)

    styles = {'Block': None, 'Shadow': None, 'Thin': None}
    style_var = tk.StringVar(value='Block')
    ttk.Combobox(sf, textvariable=style_var, values=list(styles), state='readonly', width=10).pack(side='left', padx=4)

    output = tk.Text(win, font=('Courier New', 9), bg='#0a1218', fg='#00ff88', height=14, bd=0,
                     insertbackground='#00ff88')
    output.pack(fill='both', expand=True, padx=16, pady=8)

    BLOCK_FONT = {
        'A': [' ██ ', '████', '█  █'], 'B': ['███ ', '███ ', '███ '],
        'C': [' ██ ', '█   ', ' ██ '], 'D': ['███ ', '█  █', '███ '],
        'E': ['████', '███ ', '████'], 'I': ['████', ' ██ ', '████'],
        'L': ['█   ', '█   ', '████'], 'N': ['█  █', '████', '█  █'],
        'R': ['███ ', '███ ', '█  █'], 'S': [' ███', '███ ', '███ '],
    }

    def generate():
        text = text_var.get().upper()[:12]
        lines = ['', '', '']
        for ch in text:
            glyph = BLOCK_FONT.get(ch, ['?? ', '?? ', '?? '])
            for i in range(3):
                lines[i] += glyph[i] + '  '
        result = '\n'.join(lines)
        output.delete('1.0', 'end')
        output.insert('end', result)

    def copy_art():
        art = output.get('1.0', 'end').strip()
        win.clipboard_clear()
        win.clipboard_append(art)
        messagebox.showinfo('Copied', 'ASCII art copied!')

    bf = tk.Frame(win, bg='#101820')
    bf.pack(pady=4)
    tk.Button(bf, text='Generate', bg='#006644', fg='#00ff88', font=('Courier New', 10), command=generate).pack(side='left', padx=6)
    tk.Button(bf, text='Copy', bg='#004433', fg='#00ff88', font=('Courier New', 10), command=copy_art).pack(side='left', padx=6)
    generate()


# ============================================================
# FEATURE 20: Task Priority Board (Kanban-lite)
# ============================================================
def show_task_board():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Task Board')
    win.geometry('680x520')
    style_aero_window(win, '#f0f4ff')
    center_window(win, 680, 520)

    tk.Label(win, text='📌 Task Priority Board', bg='#f0f4ff', fg='#1c3f73', font=('Segoe UI', 15, 'bold')).pack(pady=(14,6))

    boards = state.setdefault('task_board', {'Todo': [], 'In Progress': [], 'Done': []})

    col_frame = tk.Frame(win, bg='#f0f4ff')
    col_frame.pack(fill='both', expand=True, padx=10, pady=4)

    col_colors = {'Todo': '#ffe8e8', 'In Progress': '#fff8e0', 'Done': '#e8ffe8'}
    col_header_colors = {'Todo': '#d04040', 'In Progress': '#d08020', 'Done': '#3a8a3a'}
    listboxes = {}

    for i, col_name in enumerate(['Todo', 'In Progress', 'Done']):
        col = tk.Frame(col_frame, bg=col_colors[col_name], bd=1, relief='solid')
        col.grid(row=0, column=i, sticky='nsew', padx=6, pady=4)
        col_frame.columnconfigure(i, weight=1)
        col_frame.rowconfigure(0, weight=1)
        tk.Label(col, text=col_name, bg=col_header_colors[col_name], fg='white',
                 font=('Segoe UI', 11, 'bold')).pack(fill='x', padx=0, pady=0)
        lb = tk.Listbox(col, bg=col_colors[col_name], fg='#14253b', font=('Segoe UI', 9),
                        selectmode='single', relief='flat', bd=0, height=16)
        lb.pack(fill='both', expand=True, padx=4, pady=4)
        listboxes[col_name] = lb
        for item in boards.get(col_name, []):
            lb.insert('end', item)

    def add_task_board():
        task = simpledialog.askstring('New Task', 'Task description:')
        if task:
            boards.setdefault('Todo', []).append(task)
            listboxes['Todo'].insert('end', task)
            save_state()

    def move_task(direction):
        cols = ['Todo', 'In Progress', 'Done']
        for i, col in enumerate(cols):
            sel = listboxes[col].curselection()
            if sel:
                item = listboxes[col].get(sel[0])
                target_i = i + direction
                if 0 <= target_i < len(cols):
                    target = cols[target_i]
                    listboxes[col].delete(sel[0])
                    boards[col].remove(item)
                    boards[target].append(item)
                    listboxes[target].insert('end', item)
                    save_state()
                return

    def del_task():
        cols = ['Todo', 'In Progress', 'Done']
        for col in cols:
            sel = listboxes[col].curselection()
            if sel:
                item = listboxes[col].get(sel[0])
                listboxes[col].delete(sel[0])
                if item in boards[col]:
                    boards[col].remove(item)
                save_state()
                return

    bf = tk.Frame(win, bg='#f0f4ff')
    bf.pack(pady=6)
    tk.Button(bf, text='+ Add Task', bg='#4f80d4', fg='white', command=add_task_board).pack(side='left', padx=5)
    tk.Button(bf, text='◀ Move Back', bg='#8060c0', fg='white', command=lambda: move_task(-1)).pack(side='left', padx=5)
    tk.Button(bf, text='Move Forward ▶', bg='#3a8a3a', fg='white', command=lambda: move_task(1)).pack(side='left', padx=5)
    tk.Button(bf, text='Delete', bg='#c04040', fg='white', command=del_task).pack(side='left', padx=5)


# ============================================================
# FEATURE 21: Screen Lock (Win+L)
# ============================================================
def show_screen_lock():
    """Windows 7 Screen Lock — full-screen lock overlay."""
    if not desktop_win or not desktop_win.winfo_exists():
        return
    lock = tk.Toplevel(root)
    lock.overrideredirect(True)
    lock.attributes('-topmost', True)
    sw = lock.winfo_screenwidth(); sh = lock.winfo_screenheight()
    lock.geometry(f'{sw}x{sh}+0+0')
    lock.configure(bg='#000814')

    cv = tk.Canvas(lock, bg='#000814', highlightthickness=0)
    cv.place(x=0, y=0, width=sw, height=sh)
    for i in range(sh):
        t = i / sh
        r = int(0 + 8*t); g = int(5 + 12*t); b = int(14 + 28*t)
        cv.create_line(0, i, sw, i, fill=f'#{r:02x}{g:02x}{b:02x}')

    # Windows logo
    lx, ly = sw // 2, sh // 2 - 80
    cv.create_oval(lx-28, ly-28, lx+28, ly+28, fill='#0d3a6e', outline='#1a6ab8', width=2)
    cv.create_rectangle(lx-14, ly-14, lx-2, ly-2, fill='#f04820', outline='')
    cv.create_rectangle(lx+2, ly-14, lx+14, ly-2, fill='#00a8ef', outline='')
    cv.create_rectangle(lx-14, ly+2, lx-2, ly+14, fill='#7fba00', outline='')
    cv.create_rectangle(lx+2, ly+2, lx+14, ly+14, fill='#ffb900', outline='')

    name_lbl = tk.Label(lock, text=state.get('user_name', 'Ryan Sahdev'),
                        bg='#000814', fg='#c8deff', font=('Segoe UI Light', 24))
    name_lbl.place(x=sw//2, y=sh//2-20, anchor='center')
    tk.Label(lock, text='Click or press any key to unlock', bg='#000814',
             fg='#2a4a70', font=('Segoe UI', 10)).place(x=sw//2, y=sh//2+20, anchor='center')

    # Live clock on lock screen
    clock_lbl = tk.Label(lock, bg='#000814', fg='#4a7ab8', font=('Segoe UI Light', 48))
    clock_lbl.place(x=sw//2, y=sh//2-180, anchor='center')
    date_lbl = tk.Label(lock, bg='#000814', fg='#1e3a5c', font=('Segoe UI', 12))
    date_lbl.place(x=sw//2, y=sh//2-120, anchor='center')

    def tick_lock():
        if lock.winfo_exists():
            now = datetime.now()
            clock_lbl.config(text=now.strftime('%H:%M'))
            date_lbl.config(text=now.strftime('%A, %B %d'))
            lock.after(1000, tick_lock)
    tick_lock()

    def unlock(event=None):
        pwd = simpledialog.askstring('Unlock', 'Enter password to unlock:', show='●', parent=lock)
        if pwd is None:
            return
        sec = load_security()
        if sec and verify_password(pwd, sec.get('salt',''), sec.get('key','')):
            play_windows7_device_connect()
            lock.destroy()
            if desktop_win and desktop_win.winfo_exists():
                desktop_win.lift()
        else:
            play_windows7_error()
            show_system_notification('Locked', 'Incorrect password.', kind='error')

    lock.bind('<Button-1>', unlock)
    lock.bind('<Key>', unlock)
    play_windows7_asterisk()


# ============================================================
# FEATURE 22: Run Dialog (Win+R)
# ============================================================
def show_run_dialog():
    """Windows 7 Run dialog — type app names to launch."""
    if not desktop_win or not desktop_win.winfo_exists():
        return
    run = tk.Toplevel(desktop_win)
    run.title('Run')
    run.overrideredirect(True)
    run.attributes('-topmost', True)
    run.configure(bg='#eef4ff', highlightthickness=2,
                  highlightbackground='#2060a8', highlightcolor='#4a9ad4')

    sw = run.winfo_screenwidth(); sh = run.winfo_screenheight()
    w, h = 440, 160
    run.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2+80}')

    tk.Label(run, text='Run', bg='#eef4ff', fg='#1c3f73',
             font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=18, pady=(14,0))
    tk.Label(run, text='Type the name of a program or app to open it.',
             bg='#eef4ff', fg='#3b5c88', font=('Segoe UI', 9)).pack(anchor='w', padx=18)

    row = tk.Frame(run, bg='#eef4ff'); row.pack(fill='x', padx=18, pady=12)
    tk.Label(row, text='Open:', bg='#eef4ff', fg='#1c3f73', font=('Segoe UI', 10)).pack(side='left')
    cmd_var = tk.StringVar()
    cmd_e = tk.Entry(row, textvariable=cmd_var, font=('Segoe UI', 10), width=26,
                     bg='white', fg='#14253b', relief='flat',
                     highlightthickness=1, highlightbackground='#aac9eb')
    cmd_e.pack(side='left', padx=8, ipady=4)
    cmd_e.focus_set()

    history = state.get('run_history', [])

    def execute(event=None):
        cmd = cmd_var.get().strip().lower()
        if not cmd:
            run.destroy(); return
        history_list = state.setdefault('run_history', [])
        if cmd not in history_list:
            history_list.insert(0, cmd)
            history_list[:] = history_list[:12]
        save_state()
        run.destroy()
        play_windows7_menu_popup()
        result = launch_app(cmd)
        if 'Unknown' in result:
            show_system_notification('Run', f'Cannot find "{cmd}". Check spelling.', kind='warning')

    bf = tk.Frame(run, bg='#eef4ff'); bf.pack(fill='x', padx=18, pady=(0,10))
    tk.Button(bf, text='OK', bg='#4f80d4', fg='white', width=10, command=execute).pack(side='left', padx=(0,6))
    tk.Button(bf, text='Cancel', bg='#9ab0cc', fg='white', width=10, command=run.destroy).pack(side='left')

    cmd_e.bind('<Return>', execute)
    run.bind('<Escape>', lambda e: run.destroy())


# ============================================================
# FEATURE 23: Flip 3D Window Switcher (Win+Tab simulation)
# ============================================================
def show_flip3d():
    """Windows 7 Flip 3D — cascading 2D simulation of open windows."""
    if not desktop_win or not desktop_win.winfo_exists():
        return
    open_wins = [w for w in ACTIVE_APPS if w.winfo_exists() and w.state() != 'withdrawn']
    if not open_wins:
        show_system_notification('Flip 3D', 'No open windows to switch.'); return

    flip = tk.Toplevel(desktop_win)
    flip.overrideredirect(True)
    flip.attributes('-topmost', True)
    flip.attributes('-alpha', 0.93)
    sw = flip.winfo_screenwidth(); sh = flip.winfo_screenheight()
    flip.geometry(f'{sw}x{sh}+0+0')
    flip.configure(bg='#05101a')

    # Dark gradient backdrop
    cv = tk.Canvas(flip, bg='#05101a', highlightthickness=0)
    cv.place(x=0, y=0, width=sw, height=sh)
    for i in range(sh):
        t = i / sh
        b = int(10 + 20*t)
        cv.create_line(0, i, sw, i, fill=f'#000{b:x}1{b:x}')

    tk.Label(flip, text='Win + Tab  —  Window Switcher',
             bg='#05101a', fg='#4a7ab8', font=('Segoe UI', 11)).place(
             x=sw//2, y=sh-60, anchor='center')
    tk.Label(flip, text='Click a card or press Escape to close',
             bg='#05101a', fg='#1e3a5c', font=('Segoe UI', 9)).place(
             x=sw//2, y=sh-38, anchor='center')

    sel = {'i': 0}
    cards = []
    N = len(open_wins)
    cx, cy = sw // 2, sh // 2 - 20
    CARD_W, CARD_H = 260, 160

    def draw_cards():
        for c in cards:
            try: c.destroy()
            except: pass
        cards.clear()
        for idx, win in enumerate(open_wins):
            offset = idx - sel['i']
            x = cx + offset * 90 - CARD_W // 2
            y = cy + abs(offset) * 18 - CARD_H // 2
            alpha_scale = max(0.3, 1.0 - abs(offset) * 0.15)
            card_cv = tk.Canvas(flip, width=CARD_W, height=CARD_H,
                                bg='#1a3a6a', highlightthickness=2,
                                highlightbackground='#3878c8' if offset == 0 else '#1a4060')
            card_cv.place(x=x, y=y)
            cards.append(card_cv)
            # Draw aero glass gradient on card
            for row in range(CARD_H):
                t = row / CARD_H
                r = int(0x1a + (0x3a-0x1a)*t)
                g = int(0x3a + (0x6a-0x3a)*t)
                b2 = int(0x6a + (0xa0-0x6a)*t)
                card_cv.create_line(0, row, CARD_W, row, fill=f'#{r:02x}{g:02x}{b2:02x}')
            card_cv.create_text(CARD_W//2, 22, text=win.title()[:28],
                                fill='white', font=('Segoe UI', 9, 'bold'))
            card_cv.create_rectangle(10, 36, CARD_W-10, CARD_H-20,
                                     fill='#ffffff', outline='#8ab0d8', width=1)
            card_cv.create_text(CARD_W//2, (36+CARD_H-20)//2,
                                text=win.title()[:20], fill='#3a5480',
                                font=('Segoe UI', 9))
            # Click to bring to front
            def on_card_click(e, w=win):
                flip.destroy()
                w.deiconify(); w.lift(); w.focus_force()
                play_windows7_maximize()
            card_cv.bind('<Button-1>', on_card_click)
            if offset == 0:
                card_cv.lift()

    draw_cards()

    def on_key(event):
        if event.keysym in ('Right', 'Tab'):
            sel['i'] = (sel['i'] + 1) % N
            draw_cards(); play_windows7_menu_popup()
        elif event.keysym == 'Left':
            sel['i'] = (sel['i'] - 1) % N
            draw_cards(); play_windows7_menu_popup()
        elif event.keysym in ('Return', 'space'):
            w = open_wins[sel['i']]
            flip.destroy(); w.deiconify(); w.lift(); w.focus_force()
            play_windows7_maximize()
        elif event.keysym == 'Escape':
            flip.destroy()

    flip.bind('<Key>', on_key)
    flip.bind('<MouseWheel>', lambda e: on_key(type('E', (), {'keysym': 'Right' if e.delta < 0 else 'Left'})()))
    flip.focus_force()
    play_windows7_menu_popup()


# ============================================================
# FEATURE 24: Desktop Gadgets Overlay (live floating widgets)
# ============================================================
def show_desktop_gadgets_overlay():
    """Live floating gadget sidebar — clock, CPU, date."""
    if not desktop_win or not desktop_win.winfo_exists():
        return
    gw = tk.Toplevel(desktop_win)
    gw.overrideredirect(True)
    gw.attributes('-topmost', True)
    gw.attributes('-alpha', 0.88)
    sw = gw.winfo_screenwidth(); sh = gw.winfo_screenheight()
    gw.geometry(f'160x{sh-80}+{sw-168}+0')
    gw.configure(bg='#0a1828')

    # ── Analog Clock gadget ──────────────────────────────────────────────
    clock_frame = tk.Frame(gw, bg='#0e2038', bd=1, relief='solid')
    clock_frame.pack(fill='x', padx=4, pady=(8, 4))
    tk.Label(clock_frame, text='Clock', bg='#0e2038', fg='#4a80b8',
             font=('Segoe UI', 8, 'bold')).pack(pady=(4, 0))
    clock_cv = tk.Canvas(clock_frame, width=120, height=120,
                         bg='#0e2038', highlightthickness=0)
    clock_cv.pack(padx=16, pady=4)

    def draw_clock():
        clock_cv.delete('all')
        now = datetime.now()
        cx, cy, r = 60, 60, 52
        clock_cv.create_oval(cx-r, cy-r, cx+r, cy+r, outline='#2060a8', width=3, fill='#122040')
        clock_cv.create_oval(cx-r+4, cy-r+4, cx+r-4, cy+r-4, outline='#1a4a80', width=1)
        pass  # math already imported globally
        # Hour marks
        for i in range(12):
            angle = math.radians(i * 30 - 90)
            x1 = cx + (r-6) * math.cos(angle); y1 = cy + (r-6) * math.sin(angle)
            x2 = cx + (r-2) * math.cos(angle); y2 = cy + (r-2) * math.sin(angle)
            clock_cv.create_line(x1, y1, x2, y2, fill='#3878c8', width=2)
        # Hands
        h_angle = math.radians((now.hour % 12 + now.minute/60) * 30 - 90)
        m_angle = math.radians(now.minute * 6 - 90)
        s_angle = math.radians(now.second * 6 - 90)
        clock_cv.create_line(cx, cy, cx+30*math.cos(h_angle), cy+30*math.sin(h_angle),
                             fill='#c8deff', width=3)
        clock_cv.create_line(cx, cy, cx+42*math.cos(m_angle), cy+42*math.sin(m_angle),
                             fill='#8ab4e8', width=2)
        clock_cv.create_line(cx, cy, cx+46*math.cos(s_angle), cy+46*math.sin(s_angle),
                             fill='#ff6060', width=1)
        clock_cv.create_oval(cx-3, cy-3, cx+3, cy+3, fill='#4a80b8', outline='')
        if gw.winfo_exists():
            clock_frame.after(1000, draw_clock)
    draw_clock()

    # ── CPU Meter gadget ─────────────────────────────────────────────────
    cpu_frame = tk.Frame(gw, bg='#0e2038', bd=1, relief='solid')
    cpu_frame.pack(fill='x', padx=4, pady=4)
    tk.Label(cpu_frame, text='CPU Meter', bg='#0e2038', fg='#4a80b8',
             font=('Segoe UI', 8, 'bold')).pack(pady=(4, 0))
    cpu_cv = tk.Canvas(cpu_frame, width=130, height=70, bg='#0e2038', highlightthickness=0)
    cpu_cv.pack(padx=4, pady=4)
    cpu_history = [0] * 26

    def draw_cpu():
        val = psutil.cpu_percent(interval=None) if psutil else random.randint(5, 35)
        cpu_history.append(val); cpu_history.pop(0)
        cpu_cv.delete('all')
        cpu_cv.create_rectangle(0, 0, 130, 70, fill='#060e1a', outline='#1a4060')
        for i in range(1, 26):
            x1 = (i-1) * 5; x2 = i * 5
            y1 = 68 - int(cpu_history[i-1] * 0.64)
            y2 = 68 - int(cpu_history[i] * 0.64)
            cpu_cv.create_line(x1, y1, x2, y2, fill='#3a9adc', width=2)
        cpu_cv.create_text(65, 35, text=f'{int(val)}%',
                           fill='#6ab4e8', font=('Segoe UI', 16, 'bold'))
        if gw.winfo_exists():
            cpu_frame.after(1500, draw_cpu)
    draw_cpu()

    # ── Calendar snippet ─────────────────────────────────────────────────
    cal_frame = tk.Frame(gw, bg='#0e2038', bd=1, relief='solid')
    cal_frame.pack(fill='x', padx=4, pady=4)
    now = datetime.now()
    tk.Label(cal_frame, text=now.strftime('%b %Y'), bg='#0e2038', fg='#4a80b8',
             font=('Segoe UI', 8, 'bold')).pack(pady=(4, 0))
    tk.Label(cal_frame, text=now.strftime('%d'), bg='#0e2038', fg='#c8deff',
             font=('Segoe UI', 28, 'bold')).pack()
    tk.Label(cal_frame, text=now.strftime('%A'), bg='#0e2038', fg='#3a6898',
             font=('Segoe UI', 8)).pack(pady=(0, 6))

    # Close button
    tk.Button(gw, text='✕ Close Gadgets', bg='#0a1828', fg='#3a6898',
              relief='flat', font=('Segoe UI', 7), command=gw.destroy).pack(
              side='bottom', pady=6)

    # Drag gadget panel
    def start_drag(e): gw._dx = e.x; gw._dy = e.y
    def do_drag(e):
        gw.geometry(f'+{gw.winfo_x()+(e.x-gw._dx)}+{gw.winfo_y()+(e.y-gw._dy)}')
    gw.bind('<ButtonPress-1>', start_drag)
    gw.bind('<B1-Motion>', do_drag)


# ============================================================
# FEATURE 25: Quick Notes (Desktop Post-it, Win+N)
# ============================================================
def show_quick_note():
    """Borderless sticky note that sits on the desktop."""
    if not desktop_win or not desktop_win.winfo_exists():
        return
    colors = ['#fff9a0', '#a8e6cf', '#ffd3b6', '#d4a5f5', '#a0d8ff']
    col = random.choice(colors)
    note = tk.Toplevel(desktop_win)
    note.overrideredirect(True)
    note.attributes('-topmost', True)
    sw = note.winfo_screenwidth(); sh = note.winfo_screenheight()
    w, h = 220, 200
    note.geometry(f'{w}x{h}+{random.randint(60, sw-300)}+{random.randint(60, sh-300)}')
    note.configure(bg=col)

    title_bar = tk.Frame(note, bg=col, height=24)
    title_bar.pack(fill='x')
    tk.Label(title_bar, text='📝 Quick Note', bg=col, fg='#4a4a2a',
             font=('Segoe UI', 8, 'bold')).pack(side='left', padx=6, pady=3)
    tk.Button(title_bar, text='✕', bg=col, fg='#8a4a4a', relief='flat',
              font=('Segoe UI', 8), command=note.destroy).pack(side='right', padx=4)

    txt = tk.Text(note, bg=col, fg='#3a3a2a', font=('Segoe UI', 10),
                  relief='flat', bd=0, wrap='word', insertbackground='#3a3a2a')
    txt.pack(fill='both', expand=True, padx=6, pady=4)
    txt.insert('1.0', 'Type your note here...')
    txt.bind('<FocusIn>', lambda e: txt.delete('1.0','end')
             if txt.get('1.0','end').strip()=='Type your note here...' else None)

    def start_drag(e): note._dx = e.x; note._dy = e.y
    def do_drag(e):
        note.geometry(f'+{note.winfo_x()+(e.x-note._dx)}+{note.winfo_y()+(e.y-note._dy)}')
    title_bar.bind('<ButtonPress-1>', start_drag)
    title_bar.bind('<B1-Motion>', do_drag)
    play_windows7_asterisk()


# ============================================================
# FEATURE 26: System Properties (like right-click My Computer)
# ============================================================
def show_system_properties():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('System Properties')
    win.geometry('580x480')
    style_aero_window(win, '#eef5ff')
    center_window(win, 580, 480)

    tk.Label(win, text='System Properties', bg='#eef5ff', fg='#1c3f73',
             font=('Segoe UI', 16, 'bold')).pack(pady=(22, 4))
    tk.Frame(win, bg='#bdd5f0', height=1).pack(fill='x', padx=20)

    info_frame = tk.Frame(win, bg='#eef5ff')
    info_frame.pack(fill='both', expand=True, padx=24, pady=12)

    # Windows edition block
    ed_frame = tk.Frame(info_frame, bg='#d8ecff', bd=1, relief='solid')
    ed_frame.pack(fill='x', pady=6)
    tk.Label(ed_frame, text=f"Windows 7  {state.get('os_version','Ultimate')}",
             bg='#d8ecff', fg='#1a4070', font=('Segoe UI', 13, 'bold')).pack(
             anchor='w', padx=14, pady=(10,0))
    tk.Label(ed_frame, text='© 2009 Microsoft Corporation. All rights reserved.',
             bg='#d8ecff', fg='#5a7aa0', font=('Segoe UI', 8)).pack(
             anchor='w', padx=14, pady=(2,10))

    # Specs
    specs = [
        ('Processor', 'Intel® Core™ i7  4× 2.80 GHz'),
        ('Installed memory (RAM)', state.get('ram_size', '8 GB')),
        ('System type', '64-bit Operating System'),
        ('Computer name', 'RYAN-PC'),
        ('Workgroup', 'WORKGROUP'),
        ('Windows activation', '✅ Activated — Product ID: 00426-OEM-8992752'),
    ]
    for label, value in specs:
        row = tk.Frame(info_frame, bg='#eef5ff')
        row.pack(fill='x', pady=3)
        tk.Label(row, text=label+':', bg='#eef5ff', fg='#1c3f73',
                 font=('Segoe UI', 10, 'bold'), width=28, anchor='w').pack(side='left')
        tk.Label(row, text=value, bg='#eef5ff', fg='#3a5480',
                 font=('Segoe UI', 10)).pack(side='left')

    bf = tk.Frame(win, bg='#eef5ff')
    bf.pack(pady=10)
    for txt, fn in [('Device Manager', show_device_manager),
                    ('Advanced Settings', show_settings_app),
                    ('Close', win.destroy)]:
        tk.Button(bf, text=txt, bg='#4f80d4', fg='white', width=16,
                  command=fn).pack(side='left', padx=5)


# FEATURE 28: Windows Magnifier
# ============================================================
def show_magnifier():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Magnifier')
    win.geometry('400x120')
    style_aero_window(win, '#eef5ff')
    center_window(win, 400, 120)

    tk.Label(win, text='🔍 Windows Magnifier', bg='#eef5ff', fg='#1c3f73',
             font=('Segoe UI', 12, 'bold')).pack(pady=(14, 4))

    zoom_var = tk.IntVar(value=2)
    row = tk.Frame(win, bg='#eef5ff'); row.pack(pady=6)
    tk.Label(row, text='Zoom level:', bg='#eef5ff', fg='#3a5480',
             font=('Segoe UI', 10)).pack(side='left', padx=8)
    for z in [2, 3, 4, 6, 8]:
        tk.Radiobutton(row, text=f'{z}×', variable=zoom_var, value=z,
                       bg='#eef5ff', fg='#1c3f73', activebackground='#eef5ff',
                       font=('Segoe UI', 10), selectcolor='#d0e8ff').pack(side='left', padx=4)

    def apply_zoom():
        z = zoom_var.get()
        if desktop_win and desktop_win.winfo_exists():
            desktop_win.tk.call('tk', 'scaling', z * 0.75)
        show_system_notification('Magnifier', f'Zoom set to {z}×')
    def reset_zoom():
        if desktop_win and desktop_win.winfo_exists():
            desktop_win.tk.call('tk', 'scaling', 1.0)
        show_system_notification('Magnifier', 'Zoom reset to normal')

    bf = tk.Frame(win, bg='#eef5ff'); bf.pack(pady=4)
    tk.Button(bf, text='Apply', bg='#4f80d4', fg='white', command=apply_zoom).pack(side='left', padx=6)
    tk.Button(bf, text='Reset', bg='#9ab0cc', fg='white', command=reset_zoom).pack(side='left', padx=6)


# ============================================================
# FEATURE 29: Screenshot Tool (Snipping Tool simulation)
# ============================================================
def show_snipping_tool():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Snipping Tool')
    win.geometry('460x340')
    style_aero_window(win, '#f0f4ff')
    center_window(win, 460, 340)

    tk.Label(win, text='✂ Snipping Tool', bg='#f0f4ff', fg='#1c3f73',
             font=('Segoe UI', 14, 'bold')).pack(pady=(16, 4))
    tk.Label(win, text='Capture any area of your screen.',
             bg='#f0f4ff', fg='#3b5c88', font=('Segoe UI', 10)).pack()

    mode_var = tk.StringVar(value='Full Screen')
    modes = ['Free-form Snip', 'Rectangular Snip', 'Window Snip', 'Full Screen']
    row = tk.Frame(win, bg='#f0f4ff'); row.pack(pady=10)
    tk.Label(row, text='Mode:', bg='#f0f4ff', fg='#1c3f73', font=('Segoe UI', 10)).pack(side='left')
    ttk.Combobox(row, textvariable=mode_var, values=modes,
                 state='readonly', width=18).pack(side='left', padx=8)

    preview = tk.Canvas(win, bg='#d4e4f8', width=400, height=160,
                        highlightthickness=1, highlightbackground='#aac9eb')
    preview.pack(padx=20, pady=8)
    preview.create_text(200, 80, text='[ Screenshot preview will appear here ]',
                        fill='#6080a8', font=('Segoe UI', 10))

    def take_snip():
        preview.delete('all')
        # Simulate a capture with the window title and time
        preview.create_rectangle(10, 10, 390, 150, fill='#eaf4ff', outline='#5a90c8')
        preview.create_text(200, 50, text=f'Snip captured — {mode_var.get()}',
                            fill='#1c3f73', font=('Segoe UI', 11, 'bold'))
        preview.create_text(200, 80,
                            text=datetime.now().strftime('%Y-%m-%d  %H:%M:%S'),
                            fill='#4a6890', font=('Segoe UI', 10))
        preview.create_text(200, 110, text='Desktop — Windows 7 Aero',
                            fill='#6080a8', font=('Segoe UI', 9))
        play_windows7_asterisk()
        show_system_notification('Snipping Tool', f'{mode_var.get()} captured.')

    def save_snip():
        path = filedialog.asksaveasfilename(defaultextension='.txt',
                                            filetypes=[('Text files','*.txt')],
                                            initialfile='snip.txt',
                                            title='Save Snip As')
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'Snip — {mode_var.get()}\nCaptured: {datetime.now()}\n')
            show_system_notification('Snipping Tool', f'Saved to {os.path.basename(path)}')

    bf = tk.Frame(win, bg='#f0f4ff'); bf.pack(pady=4)
    tk.Button(bf, text='New', bg='#4f80d4', fg='white', width=12, command=take_snip).pack(side='left', padx=6)
    tk.Button(bf, text='Save Snip', bg='#3a8a3a', fg='white', width=12, command=save_snip).pack(side='left', padx=6)


# ============================================================
# FEATURE 30: Printer & Fax (simulated)
# ============================================================
def show_printer_fax():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Devices and Printers')
    win.geometry('540x380')
    style_aero_window(win, '#eef5ff')
    center_window(win, 540, 380)

    tk.Label(win, text='🖨 Devices and Printers', bg='#eef5ff', fg='#1c3f73',
             font=('Segoe UI', 15, 'bold')).pack(pady=(18, 8))

    devices = [
        ('HP LaserJet 1018', '🖨', 'Ready', True),
        ('Canon PIXMA MX490', '🖨', 'Offline', False),
        ('Microsoft XPS Writer', '📄', 'Ready', True),
        ('Fax', '📠', 'Ready', True),
    ]

    frame = tk.Frame(win, bg='#eef5ff')
    frame.pack(fill='both', expand=True, padx=20, pady=8)

    for name, icon, status, online in devices:
        card = tk.Frame(frame, bg='white', bd=1, relief='solid')
        card.pack(fill='x', pady=4)
        row = tk.Frame(card, bg='white'); row.pack(fill='x', padx=10, pady=8)
        tk.Label(row, text=icon, bg='white', font=('Segoe UI Emoji', 16)).pack(side='left')
        col = tk.Frame(row, bg='white'); col.pack(side='left', padx=10)
        tk.Label(col, text=name, bg='white', fg='#1c3f73',
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        tk.Label(col, text=status, bg='white',
                 fg='#3a8a3a' if online else '#c04040',
                 font=('Segoe UI', 9)).pack(anchor='w')
        tk.Button(row, text='Print Test', bg='#4f80d4', fg='white',
                  command=lambda n=name: show_system_notification('Printer',
                  f'Test page sent to {n}.')).pack(side='right')

    tk.Button(win, text='Add a printer', bg='#3a8a3a', fg='white',
              command=lambda: show_system_notification('Printer',
              'Searching for available printers...')).pack(pady=8)


# ============================================================
# FEATURE 31: Aero Peek (show desktop)
# ============================================================
def show_aero_peek():
    """Show Desktop — hides all windows temporarily (Aero Peek)."""
    if not desktop_win or not desktop_win.winfo_exists():
        return
    any_visible = any(
        w.winfo_exists() and w.state() != 'withdrawn'
        for w in ACTIVE_APPS
    )
    if any_visible:
        for w in list(ACTIVE_APPS.keys()):
            if w.winfo_exists() and w.state() != 'withdrawn':
                w.withdraw()
        show_system_notification('Aero Peek', 'Desktop revealed. Click again to restore.')
    else:
        for w in list(ACTIVE_APPS.keys()):
            if w.winfo_exists():
                w.deiconify()
        show_system_notification('Aero Peek', 'Windows restored.')
    play_windows7_minimize()


# ============================================================
# SECURITY FEATURE A: Security Audit Log Viewer
# ============================================================
def show_audit_log_viewer():
    """View the full security audit log with color-coded severity."""
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Security Audit Log')
    win.geometry('760x520')
    style_aero_window(win, '#0a1018')
    center_window(win, 760, 520)

    tk.Label(win, text='🔒 Security Audit Log', bg='#0a1018', fg='#00cc88',
             font=('Consolas', 14, 'bold')).pack(pady=(16, 4))
    tk.Label(win, text=f'Log file: {AUDIT_LOG_FILE}', bg='#0a1018', fg='#2a5a40',
             font=('Consolas', 8)).pack()

    log_frame = tk.Frame(win, bg='#0a1018')
    log_frame.pack(fill='both', expand=True, padx=16, pady=10)

    log_text = tk.Text(log_frame, bg='#060e0a', fg='#00cc88',
                       font=('Consolas', 9), wrap='word', bd=0,
                       state='disabled', selectbackground='#0a3a20')
    sb = ttk.Scrollbar(log_frame, command=log_text.yview)
    log_text.config(yscrollcommand=sb.set)
    sb.pack(side='right', fill='y')
    log_text.pack(fill='both', expand=True)

    log_text.tag_config('CRITICAL', foreground='#ff4444')
    log_text.tag_config('WARN',     foreground='#ffaa00')
    log_text.tag_config('INFO',     foreground='#00cc88')
    log_text.tag_config('ts',       foreground='#2a6a44')

    def refresh_log():
        entries = read_audit_log(300)
        log_text.config(state='normal')
        log_text.delete('1.0', 'end')
        for line in entries:
            if '[CRITICAL]' in line:
                tag = 'CRITICAL'
            elif '[WARN' in line:
                tag = 'WARN'
            else:
                tag = 'INFO'
            log_text.insert('end', line + '\n', tag)
        log_text.see('end')
        log_text.config(state='disabled')

    refresh_log()

    def export_log():
        path = filedialog.asksaveasfilename(
            defaultextension='.log',
            filetypes=[('Log files', '*.log'), ('Text', '*.txt')],
            initialfile='security_audit.log', title='Export Audit Log')
        if path:
            try:
                import shutil as _shutil
                _shutil.copy2(AUDIT_LOG_FILE, path)
                show_system_notification('Audit Log', f'Exported to {os.path.basename(path)}')
            except Exception as e:
                messagebox.showerror('Export', str(e))

    def clear_log():
        if not check_password('Enter password to clear audit log'):
            show_system_notification('Audit Log', 'Password required to clear log.', kind='error')
            return
        if messagebox.askyesno('Clear Log', 'Permanently clear all audit log entries?'):
            try:
                open(AUDIT_LOG_FILE, 'w').close()
                audit_log('AUDIT_LOG_CLEARED', 'Log cleared by user', 'WARN')
                refresh_log()
            except Exception:
                pass

    bf = tk.Frame(win, bg='#0a1018')
    bf.pack(pady=6)
    tk.Button(bf, text='Refresh', bg='#0a3a20', fg='#00cc88', width=12,
              command=refresh_log).pack(side='left', padx=5)
    tk.Button(bf, text='Export', bg='#0a3a20', fg='#00cc88', width=12,
              command=export_log).pack(side='left', padx=5)
    tk.Button(bf, text='Clear Log', bg='#4a0a0a', fg='#ff8888', width=12,
              command=clear_log).pack(side='left', padx=5)


# ============================================================
# SECURITY FEATURE B: Windows Defender Scanner
# ============================================================
def show_windows_defender_scanner():
    """Full animated Windows Defender scan simulation."""
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Windows Defender')
    win.geometry('640x500')
    style_aero_window(win, '#f0f8ff')
    center_window(win, 640, 500)

    # Header
    header = tk.Frame(win, bg='#0d4a9e')
    header.pack(fill='x')
    tk.Label(header, text='🛡  Windows Defender', bg='#0d4a9e', fg='white',
             font=('Segoe UI', 16, 'bold')).pack(side='left', padx=16, pady=14)
    tk.Label(header, text='Real-time protection: ON', bg='#0d4a9e', fg='#80d8ff',
             font=('Segoe UI', 9)).pack(side='right', padx=16)

    body = tk.Frame(win, bg='#f0f8ff')
    body.pack(fill='both', expand=True, padx=20, pady=14)

    status_lbl = tk.Label(body, text='System is protected.', bg='#f0f8ff', fg='#1a5c1a',
                          font=('Segoe UI', 13, 'bold'))
    status_lbl.pack(pady=(0, 6))

    # Progress bar
    pb_frame = tk.Frame(body, bg='#dde8f8', bd=1, relief='solid')
    pb_frame.pack(fill='x', pady=6)
    pb_cv = tk.Canvas(pb_frame, height=22, bg='#dde8f8', highlightthickness=0)
    pb_cv.pack(fill='x')
    pb_rect = pb_cv.create_rectangle(0, 0, 0, 22, fill='#0d6a3e', outline='')

    scan_lbl = tk.Label(body, text='', bg='#f0f8ff', fg='#3a5a80',
                        font=('Consolas', 8))
    scan_lbl.pack(anchor='w')

    results_frame = tk.Frame(body, bg='white', bd=1, relief='solid')
    results_frame.pack(fill='both', expand=True, pady=8)
    results_text = tk.Text(results_frame, bg='white', fg='#1a2a3a',
                           font=('Consolas', 8), wrap='word', bd=0, state='disabled')
    results_scroll = ttk.Scrollbar(results_frame, command=results_text.yview)
    results_text.config(yscrollcommand=results_scroll.set)
    results_scroll.pack(side='right', fill='y')
    results_text.pack(fill='both', expand=True, padx=4, pady=4)

    results_text.tag_config('ok',    foreground='#1a5c1a')
    results_text.tag_config('warn',  foreground='#bb6600')
    results_text.tag_config('clean', foreground='#3a6898')

    scan_running = {'v': False}

    # Simulated scan targets
    SCAN_PATHS = [
        'C:\\Windows\\System32', 'C:\\Users\\Ryan\\AppData\\Roaming',
        'C:\\Program Files', 'C:\\Program Files (x86)',
        'C:\\Users\\Ryan\\Documents', 'C:\\Users\\Ryan\\Downloads',
        'C:\\Windows\\Temp', 'C:\\Users\\Ryan\\Desktop',
        'C:\\Windows\\SysWOW64', 'C:\\ProgramData',
        'C:\\Users\\Ryan\\AppData\\Local\\Temp',
        'C:\\Windows\\System32\\drivers',
    ]
    FAKE_FILES = [
        'explorer.exe', 'svchost.exe', 'winlogon.exe', 'lsass.exe',
        'services.exe', 'csrss.exe', 'smss.exe', 'ntoskrnl.exe',
        'kernel32.dll', 'user32.dll', 'advapi32.dll', 'shell32.dll',
        'ntdll.dll', 'msvcrt.dll', 'setupapi.dll', 'wininet.dll',
    ]

    scan_stats = {'scanned': 0, 'threats': 0, 'start': None}

    def append_result(line, tag='clean'):
        results_text.config(state='normal')
        results_text.insert('end', line + '\n', tag)
        results_text.see('end')
        results_text.config(state='disabled')

    def run_scan(scan_type='Quick'):
        if scan_running['v']:
            return
        scan_running['v'] = True
        scan_stats['scanned'] = 0
        scan_stats['threats'] = 0
        scan_stats['start'] = time.time()
        status_lbl.config(text=f'{scan_type} Scan in progress...', fg='#1a4a9e')
        results_text.config(state='normal')
        results_text.delete('1.0', 'end')
        results_text.config(state='disabled')
        audit_log('DEFENDER_SCAN_START', f'Type={scan_type}', 'INFO')

        paths = SCAN_PATHS[:4] if scan_type == 'Quick' else SCAN_PATHS
        total_steps = len(paths) * 6

        def step(idx=0):
            if idx >= total_steps:
                finish_scan()
                return
            path_i = idx // 6
            file_i = idx % 6
            if path_i < len(paths):
                path = paths[path_i]
                fname = FAKE_FILES[idx % len(FAKE_FILES)]
                scan_stats['scanned'] += 1
                full = f'{path}\\{fname}'
                scan_lbl.config(text=f'Scanning: {full[:70]}')
                pct = int(idx / total_steps * 100)
                try:
                    w = pb_cv.winfo_width() or 580
                    pb_cv.coords(pb_rect, 0, 0, int(w * pct / 100), 22)
                except Exception:
                    pass
                # Rarely flag something
                if idx == total_steps // 3 and scan_type == 'Full':
                    append_result(
                        f'  ⚠  Suspicious: {full}  [PUA:Win32/Presenoker]', 'warn')
                    scan_stats['threats'] += 1
                else:
                    if idx % 8 == 0:
                        append_result(f'  ✔  {full}', 'ok')
            win.after(80 if scan_type == 'Quick' else 40, lambda: step(idx + 1))

        def finish_scan():
            scan_running['v'] = False
            elapsed = int(time.time() - scan_stats['start'])
            scan_lbl.config(text='')
            try:
                w = pb_cv.winfo_width() or 580
                pb_cv.coords(pb_rect, 0, 0, w, 22)
            except Exception:
                pass
            if scan_stats['threats'] == 0:
                status_lbl.config(text='✅  No threats found. System is clean.', fg='#1a5c1a')
                play_windows7_asterisk()
            else:
                status_lbl.config(
                    text=f'⚠  {scan_stats["threats"]} threat(s) detected. See below.', fg='#cc4400')
                play_windows7_exclamation()
            append_result(
                f'\n─── Scan complete ─── '
                f'{scan_stats["scanned"]} items scanned  ·  '
                f'{scan_stats["threats"]} threats  ·  {elapsed}s elapsed ───', 'clean')
            audit_log('DEFENDER_SCAN_DONE',
                      f'Scanned={scan_stats["scanned"]} Threats={scan_stats["threats"]}', 'INFO')

        step()

    bf_top = tk.Frame(body, bg='#f0f8ff')
    bf_top.pack(fill='x', pady=(0, 6))
    tk.Button(bf_top, text='Quick Scan', bg='#0d4a9e', fg='white', width=14,
              command=lambda: threading.Thread(target=lambda: run_scan('Quick'), daemon=True).start()
              ).pack(side='left', padx=4)
    tk.Button(bf_top, text='Full Scan', bg='#0d6a4e', fg='white', width=14,
              command=lambda: threading.Thread(target=lambda: run_scan('Full'), daemon=True).start()
              ).pack(side='left', padx=4)
    tk.Button(bf_top, text='View Audit Log', bg='#4a3a70', fg='white', width=14,
              command=show_audit_log_viewer).pack(side='right', padx=4)


# ============================================================
# SECURITY FEATURE C: Secure Encrypted Vault
# ============================================================
def show_secure_vault():
    """Password-protected, encrypted personal notes vault."""
    # Require password before opening
    sec = load_security()
    if not sec or 'salt' not in sec:
        messagebox.showwarning('Vault', 'Set up an assistant password first.')
        return
    vault_pwd = simpledialog.askstring('Secure Vault', '🔒 Enter vault password:', show='●')
    if vault_pwd is None:
        return
    if not verify_password(vault_pwd, sec['salt'], sec['key']):
        play_windows7_error()
        audit_log('VAULT_ACCESS_DENIED', 'Wrong password', 'WARN')
        messagebox.showerror('Vault', 'Incorrect password. Access denied.')
        return
    audit_log('VAULT_OPENED', f'User: {state.get("user_name","?")}', 'INFO')

    # Load or decrypt vault contents
    vault_data = []
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'rb') as f:
                raw = f.read()
            decrypted = decrypt_bytes(raw, vault_pwd)
            vault_data = json.loads(decrypted.decode('utf-8', errors='replace'))
        except Exception:
            vault_data = []

    def save_vault():
        try:
            raw = json.dumps(vault_data, indent=2).encode('utf-8')
            enc = encrypt_bytes(raw, vault_pwd)
            with open(VAULT_FILE, 'wb') as f:
                f.write(enc)
            audit_log('VAULT_SAVED', f'{len(vault_data)} entries', 'INFO')
        except Exception as e:
            messagebox.showerror('Vault', f'Save failed: {e}')

    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('🔒 Secure Vault')
    win.geometry('680x520')
    style_aero_window(win, '#0e1820')
    center_window(win, 680, 520)

    header = tk.Frame(win, bg='#0a1228')
    header.pack(fill='x')
    tk.Label(header, text='🔒 Secure Vault', bg='#0a1228', fg='#c8deff',
             font=('Segoe UI', 14, 'bold')).pack(side='left', padx=16, pady=12)
    tk.Label(header, text='AES-XTEA encrypted  ·  Password protected',
             bg='#0a1228', fg='#2a4a70', font=('Segoe UI', 8)).pack(side='right', padx=16)

    # Entries list on left
    list_frame = tk.Frame(win, bg='#0a1020', width=200)
    list_frame.pack(side='left', fill='y', padx=(10,0), pady=10)
    list_frame.pack_propagate(False)

    tk.Label(list_frame, text='Vault Entries', bg='#0a1020', fg='#4a80b8',
             font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=8, pady=(8, 4))

    lb = tk.Listbox(list_frame, bg='#060e18', fg='#8ab8e8', font=('Segoe UI', 9),
                    selectmode='single', relief='flat', bd=0,
                    selectbackground='#1a3a6a', selectforeground='white',
                    activestyle='none')
    lb.pack(fill='both', expand=True, padx=4, pady=4)

    # Editor on right
    edit_frame = tk.Frame(win, bg='#0e1820')
    edit_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

    tk.Label(edit_frame, text='Title:', bg='#0e1820', fg='#4a80b8',
             font=('Segoe UI', 9)).pack(anchor='w')
    title_var = tk.StringVar()
    title_e = tk.Entry(edit_frame, textvariable=title_var, bg='#0c1828', fg='white',
                       insertbackground='#60a8e0', relief='flat',
                       highlightthickness=1, highlightbackground='#1e4870',
                       font=('Segoe UI', 11))
    title_e.pack(fill='x', ipady=5, pady=(0, 10))

    tk.Label(edit_frame, text='Content (encrypted):', bg='#0e1820', fg='#4a80b8',
             font=('Segoe UI', 9)).pack(anchor='w')
    content_e = tk.Text(edit_frame, bg='#080e18', fg='#c8deff',
                        font=('Segoe UI', 10), wrap='word', relief='flat',
                        insertbackground='#60a8e0',
                        highlightthickness=1, highlightbackground='#1e4870')
    content_e.pack(fill='both', expand=True, pady=(0, 8))

    current = {'idx': -1}

    def refresh_list():
        lb.delete(0, 'end')
        for entry in vault_data:
            lb.insert('end', f"  🔐  {entry.get('title', 'Untitled')[:28]}")

    def on_select(event=None):
        sel = lb.curselection()
        if not sel:
            return
        current['idx'] = sel[0]
        entry = vault_data[sel[0]]
        title_var.set(entry.get('title', ''))
        content_e.delete('1.0', 'end')
        content_e.insert('1.0', entry.get('content', ''))

    def new_entry():
        vault_data.append({'title': 'New Entry', 'content': '',
                           'created': datetime.now().isoformat()})
        current['idx'] = len(vault_data) - 1
        refresh_list()
        lb.selection_clear(0, 'end')
        lb.selection_set(current['idx'])
        title_var.set('New Entry')
        content_e.delete('1.0', 'end')
        title_e.focus_set()

    def save_entry():
        idx = current['idx']
        if idx < 0 or idx >= len(vault_data):
            new_entry(); idx = current['idx']
        vault_data[idx]['title'] = title_var.get().strip() or 'Untitled'
        vault_data[idx]['content'] = content_e.get('1.0', 'end').strip()
        vault_data[idx]['modified'] = datetime.now().isoformat()
        save_vault()
        refresh_list()
        show_system_notification('Vault', 'Entry saved and encrypted.')

    def delete_entry():
        idx = current['idx']
        if idx < 0 or idx >= len(vault_data):
            return
        if messagebox.askyesno('Vault', 'Delete this vault entry?'):
            vault_data.pop(idx)
            current['idx'] = -1
            title_var.set('')
            content_e.delete('1.0', 'end')
            save_vault()
            refresh_list()

    lb.bind('<<ListboxSelect>>', on_select)
    refresh_list()

    bf = tk.Frame(edit_frame, bg='#0e1820')
    bf.pack(fill='x')
    tk.Button(bf, text='New', bg='#1a4880', fg='white', width=9, command=new_entry).pack(side='left', padx=3)
    tk.Button(bf, text='Save 🔒', bg='#1a5838', fg='white', width=9, command=save_entry).pack(side='left', padx=3)
    tk.Button(bf, text='Delete', bg='#6a1a1a', fg='white', width=9, command=delete_entry).pack(side='left', padx=3)

    def on_close():
        audit_log('VAULT_CLOSED', '', 'INFO')
        win.destroy()
    win.protocol('WM_DELETE_WINDOW', on_close)


# ============================================================
# SECURITY FEATURE D: Two-Factor Authentication Setup
# ============================================================
def show_2fa_setup():
    """Simulated TOTP two-factor authentication setup."""
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Two-Factor Authentication')
    win.geometry('500x460')
    style_aero_window(win, '#f0f4ff')
    center_window(win, 500, 460)

    tk.Label(win, text='🔐 Two-Factor Authentication', bg='#f0f4ff', fg='#1c3f73',
             font=('Segoe UI', 14, 'bold')).pack(pady=(18, 4))
    tk.Label(win, text='Add an extra layer of security to your Windows 7 account.',
             bg='#f0f4ff', fg='#3a5c88', font=('Segoe UI', 9)).pack()

    enabled = state.get('2fa_enabled', False)
    status_lbl = tk.Label(win,
                          text='✅ 2FA is ENABLED' if enabled else '⚠  2FA is DISABLED',
                          bg='#f0f4ff',
                          fg='#1a6a1a' if enabled else '#aa4400',
                          font=('Segoe UI', 11, 'bold'))
    status_lbl.pack(pady=10)

    # QR code simulation (drawn as a canvas pattern)
    qr_frame = tk.Frame(win, bg='white', bd=2, relief='solid')
    qr_frame.pack(pady=8)
    qr_cv = tk.Canvas(qr_frame, width=140, height=140, bg='white', highlightthickness=0)
    qr_cv.pack(padx=8, pady=8)

    # Draw a fake QR code pattern
    random.seed(42)
    for row in range(14):
        for col in range(14):
            x1, y1 = col * 10, row * 10
            # Corner finder patterns
            if (row < 3 and col < 3) or (row < 3 and col > 10) or (row > 10 and col < 3):
                fill = '#000000'
            elif random.random() > 0.45:
                fill = '#000000'
            else:
                fill = '#ffffff'
            qr_cv.create_rectangle(x1, y1, x1+10, y1+10, fill=fill, outline='')

    secret_key = state.get('2fa_secret', '')
    if not secret_key:
        # Generate a fake base32-like secret
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
        secret_key = ''.join(random.choices(chars, k=32))
        state['2fa_secret'] = secret_key
        save_state()

    tk.Label(win, text='Secret key (save this):', bg='#f0f4ff', fg='#1c3f73',
             font=('Segoe UI', 9)).pack()
    tk.Label(win, text=f'{secret_key[:16]}  {secret_key[16:]}',
             bg='#e8f0ff', fg='#1a3a8a',
             font=('Consolas', 11, 'bold'),
             relief='solid', bd=1, padx=10, pady=6).pack(pady=4)

    tk.Label(win, text='Scan with Google Authenticator, Authy, or any TOTP app.',
             bg='#f0f4ff', fg='#3a5c88', font=('Segoe UI', 8),
             wraplength=460).pack(pady=4)

    code_frame = tk.Frame(win, bg='#f0f4ff')
    code_frame.pack(pady=8)
    tk.Label(code_frame, text='Enter 6-digit code to verify:', bg='#f0f4ff',
             fg='#1c3f73', font=('Segoe UI', 10)).pack(side='left', padx=6)
    code_var = tk.StringVar()
    code_e = tk.Entry(code_frame, textvariable=code_var, width=10,
                      font=('Consolas', 14, 'bold'), bg='white', fg='#1a3a70',
                      justify='center', relief='flat',
                      highlightthickness=2, highlightbackground='#4a80b8')
    code_e.pack(side='left')
    code_e.focus_set()

    verify_lbl = tk.Label(win, text='', bg='#f0f4ff', font=('Segoe UI', 10))
    verify_lbl.pack()

    def verify_code():
        code = code_var.get().strip()
        if len(code) != 6 or not code.isdigit():
            verify_lbl.config(text='Enter exactly 6 digits.', fg='#cc4400')
            return
        # Simulated TOTP — accept any 6-digit code for demo, but log it
        # In a real impl: pyotp.TOTP(secret_key).verify(code)
        demo_valid_code = str(int(time.time()) // 30 % 1000000).zfill(6)
        if code == demo_valid_code or len(code) == 6:  # demo: any 6-digit code works
            state['2fa_enabled'] = True
            save_state()
            status_lbl.config(text='✅ 2FA is ENABLED', fg='#1a6a1a')
            verify_lbl.config(text='✅ 2FA enabled successfully!', fg='#1a6a1a')
            play_windows7_device_connect()
            audit_log('2FA_ENABLED', f'User: {state.get("user_name","?")}', 'INFO')
        else:
            verify_lbl.config(text='❌ Invalid code. Try again.', fg='#cc4400')
            play_windows7_error()

    def disable_2fa():
        if not check_password('Enter password to disable 2FA'):
            return
        state['2fa_enabled'] = False
        save_state()
        status_lbl.config(text='⚠  2FA is DISABLED', fg='#aa4400')
        verify_lbl.config(text='2FA has been disabled.', fg='#aa4400')
        audit_log('2FA_DISABLED', f'User: {state.get("user_name","?")}', 'WARN')

    bf = tk.Frame(win, bg='#f0f4ff')
    bf.pack(pady=8)
    tk.Button(bf, text='Verify & Enable', bg='#1a5898', fg='white', width=16,
              command=verify_code).pack(side='left', padx=5)
    tk.Button(bf, text='Disable 2FA', bg='#8a3030', fg='white', width=14,
              command=disable_2fa).pack(side='left', padx=5)
    code_e.bind('<Return>', lambda e: verify_code())


# ============================================================
# SECURITY FEATURE E: Intrusion Detection System Monitor
# ============================================================
def show_ids_monitor():
    """Real-time simulated Intrusion Detection System monitor."""
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('IDS Monitor')
    win.geometry('700x540')
    style_aero_window(win, '#08100a')
    center_window(win, 700, 540)

    tk.Label(win, text='🔎 Intrusion Detection System', bg='#08100a', fg='#00e060',
             font=('Consolas', 13, 'bold')).pack(pady=(14, 2))
    tk.Label(win, text='Live network and system event monitor', bg='#08100a',
             fg='#1a4a28', font=('Consolas', 8)).pack()

    # Stats bar
    stats_frame = tk.Frame(win, bg='#0a180c')
    stats_frame.pack(fill='x', padx=12, pady=6)
    stats = {'packets': 0, 'blocked': 0, 'alerts': 0, 'uptime': 0}
    stat_labels = {}
    for key, label in [('packets', 'Packets Inspected'),
                       ('blocked', 'Blocked'),
                       ('alerts',  'Alerts'),
                       ('uptime',  'Uptime (s)')]:
        col = tk.Frame(stats_frame, bg='#0a180c')
        col.pack(side='left', expand=True)
        tk.Label(col, text=label, bg='#0a180c', fg='#1a5a2a',
                 font=('Consolas', 7)).pack()
        lbl = tk.Label(col, text='0', bg='#0a180c', fg='#00e060',
                       font=('Consolas', 14, 'bold'))
        lbl.pack()
        stat_labels[key] = lbl

    # Alert feed
    feed_frame = tk.Frame(win, bg='#060e08')
    feed_frame.pack(fill='both', expand=True, padx=12, pady=(0, 6))
    feed_text = tk.Text(feed_frame, bg='#030a04', fg='#00cc50',
                        font=('Consolas', 8), wrap='word', bd=0,
                        state='disabled')
    feed_sb = ttk.Scrollbar(feed_frame, command=feed_text.yview)
    feed_text.config(yscrollcommand=feed_sb.set)
    feed_sb.pack(side='right', fill='y')
    feed_text.pack(fill='both', expand=True)

    feed_text.tag_config('alert',   foreground='#ff4444', background='#1a0000')
    feed_text.tag_config('block',   foreground='#ffaa00')
    feed_text.tag_config('ok',      foreground='#00cc50')
    feed_text.tag_config('ts',      foreground='#1a4a2a')

    running = {'v': True}
    start_time = time.time()

    # Simulated event templates
    NORMAL_EVENTS = [
        'TCP SYN {ip} → 192.168.1.42:443 [HTTPS] — ALLOWED',
        'DNS query google.com → 142.250.80.46 — OK',
        'ARP reply 192.168.1.1 — gateway confirmed',
        'TCP ACK {ip} → 192.168.1.42:80 — ALLOWED',
        'ICMP echo {ip} — OK',
        'TLS 1.3 handshake {ip} → 443 — ENCRYPTED',
    ]
    SUSPICIOUS_EVENTS = [
        'PORT SCAN detected from {ip} — 22 ports in 0.3s — ALERT',
        'Repeated auth failures from {ip} — BRUTE FORCE SUSPECTED',
        'Outbound connection to {ip}:4444 — UNUSUAL PORT — BLOCKED',
        'Large data exfiltration attempt {ip} — 48 MB burst — BLOCKED',
        'SQL injection pattern in HTTP header from {ip} — BLOCKED',
        'Malformed packet from {ip} — fragmentation exploit attempt',
    ]

    def random_ip():
        return f'{random.randint(10,220)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}'

    def append_feed(line, tag='ok'):
        feed_text.config(state='normal')
        ts = datetime.now().strftime('%H:%M:%S')
        feed_text.insert('end', f'[{ts}] ', 'ts')
        feed_text.insert('end', line + '\n', tag)
        feed_text.see('end')
        feed_text.config(state='disabled')

    def ids_tick():
        if not running['v'] or not win.winfo_exists():
            return
        stats['uptime'] = int(time.time() - start_time)
        stats['packets'] += random.randint(12, 80)

        # Occasionally generate an alert
        if random.random() < 0.18:
            event = random.choice(SUSPICIOUS_EVENTS).replace('{ip}', random_ip())
            stats['alerts'] += 1
            is_blocked = 'BLOCKED' in event
            if is_blocked:
                stats['blocked'] += 1
            append_feed(event, 'alert' if not is_blocked else 'block')
            if stats['alerts'] % 5 == 0:
                play_windows7_exclamation()
        else:
            if random.random() < 0.3:
                event = random.choice(NORMAL_EVENTS).replace('{ip}', random_ip())
                append_feed(event, 'ok')

        for key, lbl in stat_labels.items():
            try:
                lbl.config(text=str(stats[key]))
            except Exception:
                pass

        win.after(1400, ids_tick)

    ids_tick()
    audit_log('IDS_MONITOR_OPENED', '', 'INFO')

    def stop_ids():
        running['v'] = False
        audit_log('IDS_MONITOR_CLOSED', '', 'INFO')
        win.destroy()

    bf = tk.Frame(win, bg='#08100a')
    bf.pack(pady=4)
    tk.Button(bf, text='Stop & Close', bg='#3a0a0a', fg='#ff8888', width=14,
              command=stop_ids).pack(side='left', padx=6)
    tk.Button(bf, text='Export Alerts', bg='#0a2a14', fg='#00cc50', width=14,
              command=lambda: [
                  audit_log('IDS_EXPORT', f'Alerts={stats["alerts"]}', 'INFO'),
                  show_system_notification('IDS', f'{stats["alerts"]} alerts exported to audit log.')
              ]).pack(side='left', padx=6)

    win.protocol('WM_DELETE_WINDOW', stop_ids)


# ─── Register new features in APP_MAP ──────────────────────────────────────
APP_MAP.update({
    'lock screen': lambda: show_screen_lock(),
    'lock':        lambda: show_screen_lock(),
    'run':         lambda: show_run_dialog(),
    'flip 3d':     lambda: show_flip3d(),
    'flip3d':      lambda: show_flip3d(),
    'gadget overlay': lambda: show_desktop_gadgets_overlay(),
    'quick note':  lambda: show_quick_note(),
    'system properties': lambda: show_system_properties(),
    'computer properties': lambda: show_system_properties(),
    'recycle bin': lambda: show_recycle_bin(),
    'recycle':     lambda: show_recycle_bin(),
    'magnifier':   lambda: show_magnifier(),
    'zoom':        lambda: show_magnifier(),
    'snipping tool': lambda: show_snipping_tool(),
    'screenshot':  lambda: show_snipping_tool(),
    'snip':        lambda: show_snipping_tool(),
    'printer':     lambda: show_printer_fax(),
    'print':       lambda: show_printer_fax(),
    'fax':         lambda: show_printer_fax(),
    'peek':        lambda: show_aero_peek(),
    'show desktop': lambda: show_aero_peek(),
    # New security features
    'audit log':   lambda: show_audit_log_viewer(),
    'security log': lambda: show_audit_log_viewer(),
    'defender':    lambda: show_windows_defender_scanner(),
    'antivirus':   lambda: show_windows_defender_scanner(),
    'scan':        lambda: show_windows_defender_scanner(),
    'vault':       lambda: show_secure_vault(),
    'secure vault': lambda: show_secure_vault(),
    '2fa':         lambda: show_2fa_setup(),
    'two factor':  lambda: show_2fa_setup(),
    'ids':         lambda: show_ids_monitor(),
    'intrusion':   lambda: show_ids_monitor(),
    # BIOS / install features
    'bios':        lambda: show_bios_setup(),
    'bios setup':  lambda: show_bios_setup(),
    'uefi':        lambda: show_bios_setup(),
    'ez mode':     lambda: show_bios_setup(start_tab=0),
    'usb boot':    lambda: show_usb_boot_sequence(),
    'reinstall':   lambda: show_usb_boot_sequence(),
    'fresh install': lambda: show_usb_boot_sequence(),
    'oobe':        lambda: show_oobe_sequence(),
    # New bonus features
    'pomodoro':    lambda: show_pomodoro_timer(),
    'timer':       lambda: show_pomodoro_timer(),
    'habit':       lambda: show_habit_tracker(),
    'habits':      lambda: show_habit_tracker(),
    'markdown':    lambda: show_markdown_editor(),
    'md editor':   lambda: show_markdown_editor(),
    'ascii art':   lambda: show_ascii_art_studio(),
    'ascii':       lambda: show_ascii_art_studio(),
    'network map': lambda: show_network_map(),
    'network':     lambda: show_network_map(),
})


# ============================================================
# BONUS FEATURE I: Pomodoro / Focus Timer
# — A productivity timer that actually feels satisfying to use
# ============================================================
def show_pomodoro_timer():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Focus Timer')
    win.geometry('340x400')
    style_aero_window(win, '#0e1428')
    center_window(win, 340, 400)

    PRESETS = [
        ('Pomodoro',  25, '#e05050'),
        ('Short Break', 5, '#50a850'),
        ('Long Break', 15, '#5090e0'),
        ('Custom',    45, '#a850e0'),
    ]
    timer_state = {
        'running': False,
        'remaining': 25 * 60,
        'total':    25 * 60,
        'sessions': 0,
        'label':    'Pomodoro',
        'color':    '#e05050',
        'job':      None,
    }

    # Header
    tk.Label(win, text='⏱  Focus Timer', bg='#0e1428', fg='#c8deff',
             font=('Segoe UI', 15, 'bold')).pack(pady=(16, 4))

    sessions_lbl = tk.Label(win, text='Sessions today: 0', bg='#0e1428',
                            fg='#2a4a8a', font=('Segoe UI', 9))
    sessions_lbl.pack()

    # Arc canvas for circular timer
    cv = tk.Canvas(win, width=200, height=200, bg='#0e1428', highlightthickness=0)
    cv.pack(pady=8)

    def draw_arc():
        cv.delete('all')
        pct = timer_state['remaining'] / max(timer_state['total'], 1)
        color = timer_state['color']
        # Background ring
        cv.create_oval(20, 20, 180, 180, outline='#1a2a4a', width=14)
        # Progress arc — tkinter arc: 0=3 o'clock, goes counterclockwise
        extent = -pct * 359.9
        cv.create_arc(20, 20, 180, 180, start=90, extent=extent,
                      outline=color, width=14, style='arc')
        # Time text
        mins = timer_state['remaining'] // 60
        secs = timer_state['remaining'] % 60
        cv.create_text(100, 92, text=f'{mins:02d}:{secs:02d}',
                       fill=color, font=('Segoe UI Light', 28, 'bold'))
        cv.create_text(100, 126, text=timer_state['label'],
                       fill='#3a6898', font=('Segoe UI', 10))

    draw_arc()

    # Preset buttons
    preset_frame = tk.Frame(win, bg='#0e1428')
    preset_frame.pack(fill='x', padx=16, pady=4)

    def set_preset(label, minutes, color):
        if timer_state['job']:
            win.after_cancel(timer_state['job'])
        timer_state.update({
            'running': False, 'remaining': minutes * 60,
            'total': minutes * 60, 'label': label, 'color': color, 'job': None
        })
        draw_arc()
        start_btn.config(text='▶  Start')

    for label, minutes, color in PRESETS:
        btn = tk.Button(preset_frame, text=label, bg='#1a2a4a', fg=color,
                        font=('Segoe UI', 8), relief='flat', bd=0,
                        command=lambda l=label, m=minutes, c=color: set_preset(l, m, c))
        btn.pack(side='left', expand=True, fill='x', padx=2, ipady=4)

    # Control buttons
    ctrl_frame = tk.Frame(win, bg='#0e1428')
    ctrl_frame.pack(fill='x', padx=20, pady=8)

    def tick():
        if not timer_state['running']:
            return
        if timer_state['remaining'] > 0:
            timer_state['remaining'] -= 1
            draw_arc()
            timer_state['job'] = win.after(1000, tick)
        else:
            timer_state['running'] = False
            timer_state['sessions'] += 1
            sessions_lbl.config(text=f'Sessions today: {timer_state["sessions"]}')
            play_windows7_logon()
            show_system_notification('Focus Timer',
                f'{timer_state["label"]} complete! 🎉 {timer_state["sessions"]} sessions done.',
                kind='info')
            draw_arc()
            start_btn.config(text='▶  Start')

    def toggle():
        if timer_state['remaining'] == 0:
            return
        timer_state['running'] = not timer_state['running']
        if timer_state['running']:
            start_btn.config(text='⏸  Pause')
            tick()
        else:
            if timer_state['job']:
                win.after_cancel(timer_state['job'])
            start_btn.config(text='▶  Resume')

    def reset_timer():
        if timer_state['job']:
            win.after_cancel(timer_state['job'])
        timer_state['running'] = False
        timer_state['remaining'] = timer_state['total']
        draw_arc()
        start_btn.config(text='▶  Start')

    start_btn = tk.Button(ctrl_frame, text='▶  Start', bg='#1a3a7a', fg='#6ab4e8',
                          font=('Segoe UI', 12, 'bold'), relief='flat',
                          command=toggle, width=10)
    start_btn.pack(side='left', padx=4, ipady=6)
    tk.Button(ctrl_frame, text='↺  Reset', bg='#1a2a3a', fg='#4a7ab8',
              font=('Segoe UI', 10), relief='flat',
              command=reset_timer, width=8).pack(side='left', padx=4, ipady=6)

    # Custom time
    custom_frame = tk.Frame(win, bg='#0e1428')
    custom_frame.pack(pady=4)
    tk.Label(custom_frame, text='Custom minutes:', bg='#0e1428', fg='#2a4a7a',
             font=('Segoe UI', 9)).pack(side='left')
    custom_var = tk.StringVar(value='25')
    custom_e = tk.Entry(custom_frame, textvariable=custom_var, width=5,
                        bg='#0a1828', fg='#6ab4e8', font=('Consolas', 10),
                        insertbackground='#6ab4e8', relief='flat',
                        highlightthickness=1, highlightbackground='#1e4870',
                        justify='center')
    custom_e.pack(side='left', padx=4)
    tk.Button(custom_frame, text='Set', bg='#1a2a4a', fg='#6ab4e8',
              relief='flat', font=('Segoe UI', 9),
              command=lambda: set_preset('Custom',
                  int(custom_var.get()) if custom_var.get().isdigit() else 25,
                  '#a850e0')).pack(side='left')


# ============================================================
# BONUS FEATURE II: Habit Tracker
# — Daily habit checklist that persists across sessions
# ============================================================
def show_habit_tracker():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Habit Tracker')
    win.geometry('400x520')
    style_aero_window(win, '#0c1620')
    center_window(win, 400, 520)

    today_key = datetime.now().strftime('%Y-%m-%d')
    habits_data = state.setdefault('habits', {
        'items': ['💧 Drink 8 glasses of water', '🏃 30 min exercise',
                  '📚 Read for 20 minutes', '🧘 Meditate 10 min',
                  '💤 Sleep by 11 PM', '🥗 Eat healthy', '📵 No phone 1hr before bed'],
        'log': {}
    })
    today_log = habits_data['log'].setdefault(today_key, {})

    # Header
    tk.Label(win, text='✅  Habit Tracker', bg='#0c1620', fg='#c8deff',
             font=('Segoe UI', 15, 'bold')).pack(pady=(14, 2))
    tk.Label(win, text=datetime.now().strftime('%A, %B %d %Y'),
             bg='#0c1620', fg='#2a5a80', font=('Segoe UI', 10)).pack()

    # Streak
    def calc_streak():
        streak = 0
        check_date = datetime.now()
        for _ in range(365):
            dk = check_date.strftime('%Y-%m-%d')
            day_log = habits_data['log'].get(dk, {})
            items = habits_data['items']
            if items and all(day_log.get(h, False) for h in items):
                streak += 1
                check_date = check_date.replace(day=check_date.day - 1)
            else:
                break
        return streak

    streak_lbl = tk.Label(win, bg='#0c1620', fg='#e0a030', font=('Segoe UI', 10, 'bold'))
    streak_lbl.pack(pady=2)

    def update_streak():
        s = calc_streak()
        streak_lbl.config(text=f'🔥 Current streak: {s} day{"s" if s != 1 else ""}')

    update_streak()

    # Progress bar
    progress_cv = tk.Canvas(win, height=10, bg='#0c1620', highlightthickness=0)
    progress_cv.pack(fill='x', padx=20, pady=6)
    progress_bg = progress_cv.create_rectangle(0, 2, 380, 10, fill='#1a2a3a', outline='')
    progress_bar = progress_cv.create_rectangle(0, 2, 0, 10, fill='#30c060', outline='')

    def update_progress():
        items = habits_data['items']
        if not items:
            return
        done = sum(1 for h in items if today_log.get(h, False))
        pct = done / len(items)
        try:
            w = progress_cv.winfo_width() or 360
            progress_cv.coords(progress_bar, 0, 2, int(w * pct), 10)
        except Exception:
            pass

    # Habits list
    habit_frame = tk.Frame(win, bg='#0c1620')
    habit_frame.pack(fill='both', expand=True, padx=14, pady=6)

    vars_map = {}
    check_widgets = []

    def build_habits():
        for w in check_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        check_widgets.clear()
        vars_map.clear()
        for habit in habits_data['items']:
            var = tk.BooleanVar(value=today_log.get(habit, False))
            vars_map[habit] = var
            row = tk.Frame(habit_frame, bg='#0c1620')
            row.pack(fill='x', pady=3)
            cb = tk.Checkbutton(
                row, text=habit, variable=var,
                bg='#0c1620', fg='#c8deff' if not today_log.get(habit) else '#3ac870',
                selectcolor='#0a1828', activebackground='#0c1620',
                activeforeground='#c8deff', font=('Segoe UI', 10),
                command=lambda h=habit, v=var: on_toggle(h, v))
            cb.pack(side='left', anchor='w')
            check_widgets.append(row)

    def on_toggle(habit, var):
        today_log[habit] = var.get()
        save_state()
        update_progress()
        update_streak()
        if var.get():
            play_windows7_asterisk()
        # Recolor
        build_habits()

    build_habits()
    update_progress()

    # Add/remove habits
    add_frame = tk.Frame(win, bg='#0c1620')
    add_frame.pack(fill='x', padx=14, pady=4)
    new_habit_var = tk.StringVar()
    tk.Entry(add_frame, textvariable=new_habit_var, bg='#0a1828', fg='#c8deff',
             font=('Segoe UI', 9), insertbackground='#6ab4e8', relief='flat',
             highlightthickness=1, highlightbackground='#1e4870').pack(
             side='left', fill='x', expand=True, ipady=4)

    def add_habit():
        text = new_habit_var.get().strip()
        if text and text not in habits_data['items']:
            habits_data['items'].append(text)
            save_state()
            new_habit_var.set('')
            build_habits()
            update_progress()

    def remove_last():
        if habits_data['items']:
            removed = habits_data['items'].pop()
            today_log.pop(removed, None)
            save_state()
            build_habits()
            update_progress()

    tk.Button(add_frame, text='+ Add', bg='#1a4a2a', fg='#50c860', relief='flat',
              font=('Segoe UI', 9), command=add_habit).pack(side='left', padx=4, ipady=4)
    tk.Button(add_frame, text='− Remove', bg='#4a1a1a', fg='#e05050', relief='flat',
              font=('Segoe UI', 9), command=remove_last).pack(side='left', ipady=4)


# ============================================================
# BONUS FEATURE III: Live Markdown Editor with Preview
# — Write Markdown on the left, see rendered output on the right
# ============================================================
def show_markdown_editor():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Markdown Editor')
    win.geometry('820x580')
    style_aero_window(win, '#0e1828')
    center_window(win, 820, 580)

    tk.Label(win, text='📝  Markdown Editor  —  Live Preview',
             bg='#0e1828', fg='#c8deff', font=('Segoe UI', 12, 'bold')).pack(
             pady=(12, 4), anchor='w', padx=14)

    panes = tk.Frame(win, bg='#0e1828')
    panes.pack(fill='both', expand=True, padx=10, pady=(0, 8))

    # Left: editor
    left = tk.Frame(panes, bg='#060e18')
    left.pack(side='left', fill='both', expand=True, padx=(0, 4))
    tk.Label(left, text='Markdown Source', bg='#060e18', fg='#3a6898',
             font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=2)
    editor = tk.Text(left, bg='#060e18', fg='#c8e0ff', font=('Consolas', 10),
                     wrap='word', relief='flat', insertbackground='#60a8e0',
                     selectbackground='#1a3a6a', undo=True)
    editor.pack(fill='both', expand=True, padx=4, pady=(0, 4))
    editor_scroll = ttk.Scrollbar(left, command=editor.yview)
    editor.config(yscrollcommand=editor_scroll.set)

    # Right: preview
    right = tk.Frame(panes, bg='#f8faff')
    right.pack(side='left', fill='both', expand=True, padx=(4, 0))
    tk.Label(right, text='Preview', bg='#f8faff', fg='#3a6898',
             font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=2)
    preview = tk.Text(right, bg='#f8faff', fg='#1a2a3a', font=('Segoe UI', 10),
                      wrap='word', relief='flat', state='disabled',
                      selectbackground='#c8d8f0')
    preview.pack(fill='both', expand=True, padx=4, pady=(0, 4))
    preview_scroll = ttk.Scrollbar(right, command=preview.yview)
    preview.config(yscrollcommand=preview_scroll.set)

    # Configure preview text tags
    preview.tag_config('h1', font=('Segoe UI', 18, 'bold'), foreground='#1a3a7a',
                       spacing1=6, spacing3=4)
    preview.tag_config('h2', font=('Segoe UI', 14, 'bold'), foreground='#1a4a8a',
                       spacing1=4, spacing3=2)
    preview.tag_config('h3', font=('Segoe UI', 12, 'bold'), foreground='#2a5a9a',
                       spacing1=2, spacing3=2)
    preview.tag_config('bold', font=('Segoe UI', 10, 'bold'))
    preview.tag_config('italic', font=('Segoe UI', 10, 'italic'))
    preview.tag_config('code', font=('Consolas', 9), background='#e8eef8',
                       foreground='#c04040')
    preview.tag_config('hr', foreground='#aaaaaa')
    preview.tag_config('bullet', lmargin1=16, lmargin2=28)
    preview.tag_config('blockquote', lmargin1=20, foreground='#4a6888',
                       font=('Segoe UI', 10, 'italic'))

    def render_preview(event=None):
        src = editor.get('1.0', 'end')
        preview.config(state='normal')
        preview.delete('1.0', 'end')
        for line in src.splitlines():
            if line.startswith('### '):
                preview.insert('end', line[4:] + '\n', 'h3')
            elif line.startswith('## '):
                preview.insert('end', line[3:] + '\n', 'h2')
            elif line.startswith('# '):
                preview.insert('end', line[2:] + '\n', 'h1')
            elif line.startswith('---') or line.startswith('==='):
                preview.insert('end', '─' * 50 + '\n', 'hr')
            elif line.startswith('> '):
                preview.insert('end', line[2:] + '\n', 'blockquote')
            elif line.startswith('- ') or line.startswith('* '):
                preview.insert('end', '  • ' + line[2:] + '\n', 'bullet')
            elif re.match(r'^\d+\. ', line):
                preview.insert('end', '  ' + line + '\n', 'bullet')
            else:
                # Inline: **bold**, *italic*, `code`
                parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)', line)
                for part in parts:
                    if part.startswith('**') and part.endswith('**'):
                        preview.insert('end', part[2:-2], 'bold')
                    elif part.startswith('*') and part.endswith('*') and len(part) > 2:
                        preview.insert('end', part[1:-1], 'italic')
                    elif part.startswith('`') and part.endswith('`'):
                        preview.insert('end', part[1:-1], 'code')
                    else:
                        preview.insert('end', part)
                preview.insert('end', '\n')
        preview.config(state='disabled')

    editor.bind('<KeyRelease>', render_preview)

    # Starter template
    starter = '''# My Document

## Introduction
Write your **Markdown** here and see a *live preview* on the right.

### Features
- **Bold text** with `**bold**`
- *Italic text* with `*italic*`
- `inline code` with backticks
- Bullet lists with `- item`

---

> Blockquotes start with `>`

## Code Example
Use backticks for `inline code` snippets.
'''
    editor.insert('1.0', starter)
    render_preview()

    # Toolbar
    def save_md():
        path = filedialog.asksaveasfilename(
            defaultextension='.md', filetypes=[('Markdown', '*.md'), ('Text', '*.txt')],
            title='Save Markdown')
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(editor.get('1.0', 'end'))
            show_system_notification('Markdown Editor', f'Saved: {os.path.basename(path)}')

    def open_md():
        path = filedialog.askopenfilename(
            filetypes=[('Markdown', '*.md'), ('Text', '*.txt')], title='Open Markdown')
        if path:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            editor.delete('1.0', 'end')
            editor.insert('1.0', content)
            render_preview()

    bf = tk.Frame(win, bg='#0e1828')
    bf.pack(fill='x', padx=10, pady=(0, 6))
    for txt, cmd in [('Open', open_md), ('Save .md', save_md)]:
        tk.Button(bf, text=txt, bg='#1a3a6a', fg='#8ab4e8', relief='flat',
                  font=('Segoe UI', 9), command=cmd).pack(side='left', padx=4, ipady=4)
    tk.Label(bf, text='Ctrl+Z = undo  ·  Live preview updates on keystroke',
             bg='#0e1828', fg='#1a3a5a', font=('Segoe UI', 8)).pack(side='right', padx=8)
    editor.bind('<Control-z>', lambda e: editor.edit_undo())
    editor.bind('<Control-y>', lambda e: editor.edit_redo())


# ============================================================
# BONUS FEATURE IV: ASCII Art Studio
# — Draw with characters, choose from presets, export as text
# ============================================================
def show_ascii_art_studio():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('ASCII Art Studio')
    win.geometry('700x540')
    style_aero_window(win, '#060c10')
    center_window(win, 700, 540)

    tk.Label(win, text='█▓▒░  ASCII Art Studio  ░▒▓█', bg='#060c10', fg='#00ff88',
             font=('Consolas', 13, 'bold')).pack(pady=(14, 4))

    PRESETS = {
        'Windows 7 Logo': r"""
         __      ___           _
        \ \    / (_)         | |
         \ \  / / _ _ __   __| | _____      _____
          \ \/ / | | '_ \ / _` |/ _ \ \ /\ / / __|
           \  /  | | | | | (_| | (_) \ V  V /\__ \
            \/   |_|_| |_|\__,_|\___/ \_/\_/ |___/
        """,
        'Desktop PC': r"""
         ___________
        |           |
        |   RYAN'S  |
        |    W I N 7|
        |___________|
        |   ___     |
        |  |   |    |
        |__|___|____|
           |___|
        """,
        'Lock': r"""
         .------.
        /  .--. /
       |  (    |
       |   '--' |
       |________|
       |        |
       |  LOCK  |
       |________|
        """,
        'Coffee Break': r"""
            ) )
           (_(_)
          .-'-.
         /|6 6|\
        | | = | |
        |  '-'  |
         \     /
          '---'
        """,
        'Hello World': r"""
         _   _      _ _          __        __         _     _
        | | | | ___| | | ___    \ \      / /__  _ __| | __| |
        | |_| |/ _ \ | |/ _ \    \ \ /\ / / _ \| '__| |/ _` |
        |  _  |  __/ | | (_) |    \ V  V / (_) | |  | | (_| |
        |_| |_|\___|_|_|\___/      \_/\_/ \___/|_|  |_|\__,_|
        """,
    }

    # Toolbar
    tb = tk.Frame(win, bg='#060c10')
    tb.pack(fill='x', padx=10, pady=4)
    tk.Label(tb, text='Preset:', bg='#060c10', fg='#3a7a50',
             font=('Consolas', 9)).pack(side='left')
    preset_var = tk.StringVar(value='Windows 7 Logo')
    preset_cb = ttk.Combobox(tb, textvariable=preset_var,
                             values=list(PRESETS.keys()), state='readonly', width=18)
    preset_cb.pack(side='left', padx=6)

    # Chars palette
    tk.Label(tb, text='  Chars:', bg='#060c10', fg='#3a7a50',
             font=('Consolas', 9)).pack(side='left')
    char_var = tk.StringVar(value='█')
    for ch in ['█', '▓', '▒', '░', '#', '@', '*', '+', '.', ' ']:
        tk.Button(tb, text=ch, bg='#0a1820', fg='#00cc60', relief='flat',
                  font=('Consolas', 11), width=2,
                  command=lambda c=ch: char_var.set(c)).pack(side='left', padx=1)

    # Canvas area — grid of character cells
    COLS, ROWS = 60, 20
    cells = [[' '] * COLS for _ in range(ROWS)]
    canvas_frame = tk.Frame(win, bg='#000000')
    canvas_frame.pack(fill='both', expand=True, padx=10, pady=4)

    cell_size = 10
    cv = tk.Canvas(canvas_frame, bg='#000000', highlightthickness=0,
                   width=COLS * cell_size, height=ROWS * cell_size)
    cv.pack()

    def draw_grid():
        cv.delete('all')
        for r in range(ROWS):
            for c in range(COLS):
                ch = cells[r][c]
                x = c * cell_size + cell_size // 2
                y = r * cell_size + cell_size // 2
                color = '#00ff60' if ch != ' ' else '#0a1a0a'
                cv.create_text(x, y, text=ch, fill=color,
                               font=('Consolas', 8), anchor='center')

    draw_grid()

    def on_canvas_click(event):
        c = event.x // cell_size
        r = event.y // cell_size
        if 0 <= r < ROWS and 0 <= c < COLS:
            ch = char_var.get()
            cells[r][c] = ch[0] if ch else ' '
            x = c * cell_size + cell_size // 2
            y = r * cell_size + cell_size // 2
            cv.create_text(x, y, text=cells[r][c], fill='#00ff60',
                           font=('Consolas', 8), anchor='center')

    cv.bind('<Button-1>', on_canvas_click)
    cv.bind('<B1-Motion>', on_canvas_click)

    # Right-click to erase
    def on_canvas_erase(event):
        c = event.x // cell_size
        r = event.y // cell_size
        if 0 <= r < ROWS and 0 <= c < COLS:
            cells[r][c] = ' '
            draw_grid()

    cv.bind('<Button-3>', on_canvas_erase)
    cv.bind('<B3-Motion>', on_canvas_erase)

    def load_preset(event=None):
        name = preset_var.get()
        art = PRESETS.get(name, '')
        # Clear canvas
        for r in range(ROWS):
            for c in range(COLS):
                cells[r][c] = ' '
        for ri, line in enumerate(art.strip('\n').splitlines()):
            if ri >= ROWS:
                break
            for ci, ch in enumerate(line):
                if ci >= COLS:
                    break
                cells[ri][ci] = ch
        draw_grid()

    preset_cb.bind('<<ComboboxSelected>>', load_preset)
    load_preset()

    def export_art():
        text = '\n'.join(''.join(row) for row in cells)
        path = filedialog.asksaveasfilename(
            defaultextension='.txt', filetypes=[('Text', '*.txt')],
            title='Export ASCII Art')
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            show_system_notification('ASCII Art', f'Exported to {os.path.basename(path)}')

    def clear_canvas():
        for r in range(ROWS):
            for c in range(COLS):
                cells[r][c] = ' '
        draw_grid()

    bf = tk.Frame(win, bg='#060c10')
    bf.pack(pady=4)
    tk.Button(bf, text='Clear', bg='#1a0a0a', fg='#ff5050', relief='flat',
              font=('Consolas', 9), command=clear_canvas).pack(side='left', padx=4)
    tk.Button(bf, text='Export .txt', bg='#0a1a0a', fg='#00cc60', relief='flat',
              font=('Consolas', 9), command=export_art).pack(side='left', padx=4)
    tk.Label(bf, text='Left-click: draw  ·  Right-click: erase  ·  Pick char above',
             bg='#060c10', fg='#1a4a2a', font=('Consolas', 7)).pack(side='left', padx=10)


# ============================================================
# BONUS FEATURE V: Network Map Visualizer
# — Animated live-updating network topology diagram
# ============================================================
def show_network_map():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Network Map')
    win.geometry('700x520')
    style_aero_window(win, '#050e14')
    center_window(win, 700, 520)

    tk.Label(win, text='🌐  Network Map', bg='#050e14', fg='#00d0ff',
             font=('Segoe UI', 13, 'bold')).pack(pady=(12, 2))

    cv = tk.Canvas(win, bg='#030a10', highlightthickness=0)
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    status_bar = tk.Label(win, text='', bg='#050e14', fg='#1a5a70',
                          font=('Consolas', 8))
    status_bar.pack(pady=2)

    # Node definitions: (id, label, x_frac, y_frac, type)
    NODE_TYPES = {
        'router':  {'color': '#00d0ff', 'shape': 'diamond', 'size': 22},
        'switch':  {'color': '#40e0a0', 'shape': 'rect',    'size': 18},
        'pc':      {'color': '#8090ff', 'shape': 'circle',  'size': 14},
        'server':  {'color': '#ff9040', 'shape': 'rect',    'size': 16},
        'printer': {'color': '#e0a0ff', 'shape': 'circle',  'size': 12},
        'internet':{'color': '#ffcc30', 'shape': 'diamond', 'size': 26},
    }
    NODES = [
        ('internet', '🌐 Internet',  0.50, 0.06, 'internet'),
        ('router',   '🔀 Router',    0.50, 0.22, 'router'),
        ('switch1',  '⟨⟩ Switch 1',  0.25, 0.42, 'switch'),
        ('switch2',  '⟨⟩ Switch 2',  0.75, 0.42, 'switch'),
        ('pc1',      '💻 RYAN-PC',   0.12, 0.68, 'pc'),
        ('pc2',      '💻 GUEST-PC',  0.32, 0.68, 'pc'),
        ('server',   '🖥 SRV-01',    0.60, 0.68, 'server'),
        ('pc3',      '💻 WORK-PC',   0.80, 0.68, 'pc'),
        ('printer',  '🖨 HP-LaserJet',0.18, 0.88, 'printer'),
        ('nas',      '💾 NAS-01',    0.50, 0.88, 'server'),
    ]
    EDGES = [
        ('internet', 'router'), ('router', 'switch1'), ('router', 'switch2'),
        ('switch1', 'pc1'), ('switch1', 'pc2'), ('switch1', 'printer'),
        ('switch2', 'server'), ('switch2', 'pc3'), ('switch2', 'nas'),
    ]

    node_positions = {}
    packet_anim = []  # [(x1,y1,x2,y2,progress,color)]
    running = {'v': True}
    pulse = {'t': 0}

    def draw_map():
        if not win.winfo_exists():
            return
        cv.delete('all')
        W = cv.winfo_width() or 680
        H = cv.winfo_height() or 460

        # Background grid
        for gx in range(0, W, 40):
            cv.create_line(gx, 0, gx, H, fill='#091420', width=1)
        for gy in range(0, H, 40):
            cv.create_line(0, gy, W, gy, fill='#091420', width=1)

        # Compute positions
        for nid, label, xf, yf, ntype in NODES:
            node_positions[nid] = (int(W * xf), int(H * yf))

        # Draw edges with animated packets
        for (a, b) in EDGES:
            if a in node_positions and b in node_positions:
                x1, y1 = node_positions[a]
                x2, y2 = node_positions[b]
                cv.create_line(x1, y1, x2, y2, fill='#0a2a3a', width=2)

        # Animate packet flows
        for pkt in packet_anim:
            pkt['t'] += 0.04
            if pkt['t'] > 1.0:
                pkt['t'] = 0.0
            t = pkt['t']
            px = int(pkt['x1'] + (pkt['x2'] - pkt['x1']) * t)
            py = int(pkt['y1'] + (pkt['y2'] - pkt['y1']) * t)
            cv.create_oval(px-4, py-4, px+4, py+4, fill=pkt['color'], outline='')

        # Draw nodes
        pulse_r = math.sin(pulse['t'] * 0.1) * 3
        for nid, label, xf, yf, ntype in NODES:
            x, y = node_positions[nid]
            cfg = NODE_TYPES[ntype]
            color = cfg['color']
            sz = cfg['size']
            shape = cfg['shape']

            # Glow ring
            cv.create_oval(x - sz - 6, y - sz - 6, x + sz + 6, y + sz + 6,
                           outline=color, width=1,
                           fill='')

            if shape == 'circle':
                cv.create_oval(x-sz, y-sz, x+sz, y+sz, fill='#0a1820', outline=color, width=2)
            elif shape == 'rect':
                cv.create_rectangle(x-sz, y-int(sz*0.7), x+sz, y+int(sz*0.7),
                                    fill='#0a1820', outline=color, width=2)
            elif shape == 'diamond':
                pts = [x, y-sz-2, x+sz+2, y, x, y+sz+2, x-sz-2, y]
                cv.create_polygon(pts, fill='#0a1820', outline=color, width=2)

            # Label
            cv.create_text(x, y + sz + 10, text=label,
                          fill=color, font=('Consolas', 7), anchor='n')

        pulse['t'] += 1
        status_bar.config(
            text=f'{len(NODES)} nodes  ·  {len(EDGES)} connections  ·  '
                 f'Packets: {len(packet_anim)} active  ·  '
                 f'IP: 192.168.1.42  ·  Gateway: 192.168.1.1')
        if running['v'] and win.winfo_exists():
            win.after(60, draw_map)

    # Spawn packets periodically
    def spawn_packets():
        if not running['v'] or not win.winfo_exists():
            return
        if len(packet_anim) < 12 and random.random() < 0.6:
            a, b = random.choice(EDGES)
            if a in node_positions and b in node_positions:
                x1, y1 = node_positions[a]
                x2, y2 = node_positions[b]
                colors = ['#00d0ff', '#40e0a0', '#ff9040', '#8090ff', '#ffcc30']
                packet_anim.append({
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    't': random.random(), 'color': random.choice(colors)
                })
        # Remove old packets
        packet_anim[:] = packet_anim[-15:]
        if running['v'] and win.winfo_exists():
            win.after(400, spawn_packets)

    cv.bind('<Configure>', lambda e: draw_map())
    draw_map()
    spawn_packets()
    audit_log('NETWORK_MAP_OPENED', '', 'INFO')

    def on_close():
        running['v'] = False
        audit_log('NETWORK_MAP_CLOSED', '', 'INFO')
        win.destroy()
    win.protocol('WM_DELETE_WINDOW', on_close)

    # Click a node to see details
    def on_cv_click(event):
        W = cv.winfo_width() or 680
        H = cv.winfo_height() or 460
        for nid, label, xf, yf, ntype in NODES:
            x, y = int(W * xf), int(H * yf)
            sz = NODE_TYPES[ntype]['size']
            if abs(event.x - x) < sz + 6 and abs(event.y - y) < sz + 6:
                ips = {
                    'internet': '0.0.0.0/0',    'router': '192.168.1.1',
                    'switch1':  '192.168.1.2',   'switch2': '192.168.1.3',
                    'pc1':      '192.168.1.42',  'pc2':     '192.168.1.43',
                    'server':   '192.168.1.10',  'pc3':     '192.168.1.44',
                    'printer':  '192.168.1.50',  'nas':     '192.168.1.20',
                }
                ip = ips.get(nid, 'N/A')
                play_windows7_asterisk()
                show_system_notification('Network Map',
                    f'{label}  ·  IP: {ip}  ·  Status: Online')
                break

    cv.bind('<Button-1>', on_cv_click)


# ══════════════════════════════════════════════════════════════════════════════
#  10 FUTURISTIC / NEVER-SEEN-BEFORE FEATURES
# ══════════════════════════════════════════════════════════════════════════════

# ── I: AI Dream Canvas — generates surreal canvas art from keywords ──────────
def show_dream_canvas():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('AI Dream Canvas')
    win.geometry('780x560')
    style_aero_window(win, '#04080e')
    center_window(win, 780, 560)

    tk.Label(win, text='🌌  AI Dream Canvas',
             bg='#04080e', fg='#c0a0ff', font=('Segoe UI', 14, 'bold')).pack(pady=(12,2))
    tk.Label(win, text='Describe a scene — the canvas interprets it as abstract art.',
             bg='#04080e', fg='#4a3a6a', font=('Segoe UI', 9)).pack()

    cv = tk.Canvas(win, width=740, height=380, bg='#000000', highlightthickness=1,
                   highlightbackground='#2a1a4a')
    cv.pack(pady=8, padx=16)

    inp_frame = tk.Frame(win, bg='#04080e')
    inp_frame.pack(fill='x', padx=16, pady=4)
    tk.Label(inp_frame, text='Describe:', bg='#04080e', fg='#8060c0',
             font=('Segoe UI', 10)).pack(side='left')
    inp_var = tk.StringVar(value='cosmic storm over a neon city')
    inp_e = tk.Entry(inp_frame, textvariable=inp_var, bg='#0a0818', fg='#c0a0ff',
                     insertbackground='#c0a0ff', font=('Segoe UI', 10),
                     relief='flat', highlightthickness=2, highlightbackground='#3a1a6a')
    inp_e.pack(side='left', fill='x', expand=True, padx=8, ipady=4)

    dreaming = {'v': False}

    PALETTES = {
        'cosmic':  ['#0a0030','#1a0060','#4400cc','#8800ff','#cc44ff','#ff88ff'],
        'storm':   ['#001020','#002040','#0040a0','#0080ff','#40c0ff','#ffffff'],
        'neon':    ['#000010','#001830','#00ff88','#00ffcc','#ff0088','#ffcc00'],
        'forest':  ['#001008','#002010','#005020','#00a040','#40e060','#80ff80'],
        'fire':    ['#100000','#300000','#800000','#ff2000','#ff8000','#ffff00'],
        'ocean':   ['#000818','#001830','#003060','#0060c0','#0090ff','#60c8ff'],
        'sunset':  ['#100008','#300018','#800040','#c00060','#ff6040','#ffcc80'],
        'void':    ['#000000','#080008','#100020','#200040','#401080','#8040c0'],
    }

    def get_palette(text):
        text = text.lower()
        for key in PALETTES:
            if key in text:
                return PALETTES[key]
        return random.choice(list(PALETTES.values()))

    def dream(event=None):
        if dreaming['v']:
            return
        dreaming['v'] = True
        cv.delete('all')
        desc = inp_var.get() or 'abstract dream'
        palette = get_palette(desc)
        W, H = 740, 380
        random.seed(hash(desc) % 99999)

        # Background gradient
        for y in range(H):
            t = y / H
            i = int(t * (len(palette) - 1))
            c1 = palette[min(i, len(palette)-1)]
            c2 = palette[min(i+1, len(palette)-1)]
            def lerp_hex(h1, h2, t):
                r1,g1,b1 = int(h1[1:3],16),int(h1[3:5],16),int(h1[5:7],16)
                r2,g2,b2 = int(h2[1:3],16),int(h2[3:5],16),int(h2[5:7],16)
                return '#{:02x}{:02x}{:02x}'.format(
                    int(r1+(r2-r1)*t),int(g1+(g2-g1)*t),int(b1+(b2-b1)*t))
            t2 = (t * (len(palette)-1)) % 1
            col = lerp_hex(c1, c2, t2)
            cv.create_line(0, y, W, y, fill=col)

        # Layered abstract shapes
        for _ in range(120):
            shape = random.choice(['oval','rect','line','arc','polygon'])
            x = random.randint(0, W); y = random.randint(0, H)
            sz = random.randint(10, 160)
            col = random.choice(palette)
            alpha_col = col  # no real alpha in tkinter — use stipple
            stipple = random.choice(['', 'gray12', 'gray25', 'gray50', ''])
            if shape == 'oval':
                cv.create_oval(x-sz//2, y-sz//4, x+sz//2, y+sz//4,
                               fill=col, outline='', stipple=stipple)
            elif shape == 'rect':
                cv.create_rectangle(x-sz//2, y-sz//3, x+sz//2, y+sz//3,
                                    fill=col, outline='', stipple=stipple)
            elif shape == 'line':
                angle = random.uniform(0, math.pi*2)
                cv.create_line(x, y,
                               x+int(sz*math.cos(angle)),
                               y+int(sz*math.sin(angle)),
                               fill=col, width=random.randint(1,4),
                               smooth=True)
            elif shape == 'arc':
                cv.create_arc(x-sz, y-sz, x+sz, y+sz,
                              start=random.randint(0,360),
                              extent=random.randint(30,270),
                              fill=col, outline='', stipple=stipple)
            elif shape == 'polygon':
                pts = []
                n = random.randint(3, 7)
                for k in range(n):
                    a = k * 2*math.pi/n + random.uniform(-0.3,0.3)
                    r = sz//2 + random.randint(-sz//4, sz//4)
                    pts += [x+int(r*math.cos(a)), y+int(r*math.sin(a))]
                if len(pts) >= 6:
                    cv.create_polygon(pts, fill=col, outline='', stipple=stipple, smooth=True)

        # Word echoes
        words = desc.split()[:6]
        for i, word in enumerate(words):
            wx = random.randint(40, W-40)
            wy = random.randint(20, H-20)
            col = random.choice(palette[-2:])
            cv.create_text(wx, wy, text=word.upper(),
                           fill=col, font=('Segoe UI', random.randint(8,22), 'bold'),
                           stipple='gray50')

        dreaming['v'] = False

    inp_e.bind('<Return>', dream)
    tk.Button(inp_frame, text='✨ Dream', bg='#2a0860', fg='#c0a0ff',
              relief='flat', font=('Segoe UI', 10, 'bold'),
              command=dream).pack(side='left', padx=4)
    tk.Button(inp_frame, text='Save', bg='#1a0440', fg='#8060a0',
              relief='flat', font=('Segoe UI', 9),
              command=lambda: [
                  cv.postscript(file=os.path.join(DATA_DIR, 'dream.ps')),
                  show_system_notification('Dream Canvas', 'Saved as dream.ps')
              ]).pack(side='left', padx=2)
    dream()


# ── II: Mind Map Builder ─────────────────────────────────────────────────────
def show_mind_map():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Mind Map Builder')
    win.geometry('820x580')
    style_aero_window(win, '#060c14')
    center_window(win, 820, 580)

    tk.Label(win, text='🧠  Mind Map Builder', bg='#060c14', fg='#60d0ff',
             font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Double-click canvas to add node  ·  Click node to select  ·  Drag to move',
             bg='#060c14', fg='#1a4a6a', font=('Segoe UI', 8)).pack()

    cv = tk.Canvas(win, bg='#020810', highlightthickness=1,
                   highlightbackground='#1a3a5a')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    inp_frame = tk.Frame(win, bg='#060c14')
    inp_frame.pack(fill='x', padx=10, pady=4)
    node_var = tk.StringVar(value='New Idea')
    tk.Entry(inp_frame, textvariable=node_var, bg='#0a1828', fg='#60d0ff',
             insertbackground='#60d0ff', font=('Segoe UI', 10),
             relief='flat', highlightthickness=1,
             highlightbackground='#1a3a5a').pack(side='left', fill='x',
                                                  expand=True, padx=4, ipady=3)

    nodes = {}   # id → {'text','x','y','parent'}
    edges = {}   # id → canvas edge id
    sel = {'id': None}
    _id_counter = {'v': 0}

    def new_id():
        _id_counter['v'] += 1
        return f'n{_id_counter["v"]}'

    NODE_R = 38
    COLORS = ['#1e5898','#1e7840','#7a2a00','#5a1a7a','#006060','#7a3a00']

    def draw_node(nid):
        n = nodes[nid]
        x, y = n['x'], n['y']
        color = COLORS[hash(nid) % len(COLORS)]
        # Delete old
        for tag in cv.find_withtag(nid):
            cv.delete(tag)
        # Draw rounded rect via oval + rect
        cv.create_oval(x-NODE_R, y-NODE_R//2, x+NODE_R, y+NODE_R//2,
                       fill=color, outline='#60d0ff', width=2, tags=nid)
        cv.create_text(x, y, text=n['text'], fill='white',
                       font=('Segoe UI', 9, 'bold'), tags=nid, width=NODE_R*2-4)
        if n.get('parent'):
            p = nodes.get(n['parent'])
            if p:
                eid = edges.get(nid)
                if eid:
                    try: cv.delete(eid)
                    except: pass
                eid = cv.create_line(p['x'], p['y'], x, y,
                                     fill='#204060', width=2, smooth=True)
                edges[nid] = eid
                cv.tag_lower(eid)

    def add_node(x, y, parent_id=None):
        nid = new_id()
        nodes[nid] = {'text': node_var.get() or 'Idea',
                      'x': x, 'y': y, 'parent': parent_id}
        draw_node(nid)
        sel['id'] = nid
        play_windows7_asterisk()

    # Seed with center node
    W = win.winfo_screenwidth()//2; H = 240
    win.after(100, lambda: add_node(400, 240, None))

    def on_dbl(event):
        add_node(event.x, event.y, sel['id'])

    drag = {'id': None, 'ox': 0, 'oy': 0}

    def on_press(event):
        items = cv.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
        for item in reversed(items):
            tags = cv.gettags(item)
            for t in tags:
                if t in nodes:
                    sel['id'] = t
                    drag['id'] = t
                    drag['ox'] = event.x - nodes[t]['x']
                    drag['oy'] = event.y - nodes[t]['y']
                    return

    def on_motion(event):
        nid = drag['id']
        if nid and nid in nodes:
            nodes[nid]['x'] = event.x - drag['ox']
            nodes[nid]['y'] = event.y - drag['oy']
            draw_node(nid)
            # Redraw children
            for cid, n in nodes.items():
                if n.get('parent') == nid:
                    draw_node(cid)

    def on_release(event):
        drag['id'] = None

    cv.bind('<Double-1>', on_dbl)
    cv.bind('<ButtonPress-1>', on_press)
    cv.bind('<B1-Motion>', on_motion)
    cv.bind('<ButtonRelease-1>', on_release)

    def del_node():
        nid = sel['id']
        if not nid or nid not in nodes:
            return
        for tag in cv.find_withtag(nid):
            cv.delete(tag)
        eid = edges.pop(nid, None)
        if eid:
            try: cv.delete(eid)
            except: pass
        nodes.pop(nid, None)
        sel['id'] = None

    def export_map():
        lines = []
        for nid, n in nodes.items():
            p = nodes.get(n.get('parent', ''), {}).get('text', '(root)')
            lines.append(f'{p} → {n["text"]}')
        path = filedialog.asksaveasfilename(defaultextension='.txt',
            filetypes=[('Text','*.txt')], title='Export Mind Map')
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            show_system_notification('Mind Map', 'Exported!')

    tk.Button(inp_frame, text='Delete Node', bg='#3a0a0a', fg='#ff8888',
              relief='flat', font=('Segoe UI', 9), command=del_node).pack(side='left', padx=4)
    tk.Button(inp_frame, text='Export', bg='#0a2a1a', fg='#60d0a0',
              relief='flat', font=('Segoe UI', 9), command=export_map).pack(side='left', padx=4)


# ── III: Code Visualizer — paste code, see live call graph ──────────────────
def show_code_visualizer():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Code Visualizer')
    win.geometry('900x580')
    style_aero_window(win, '#040c10')
    center_window(win, 900, 580)

    tk.Label(win, text='⚡  Code Visualizer  —  Live Call Graph',
             bg='#040c10', fg='#40e0ff', font=('Segoe UI', 12, 'bold')).pack(pady=(10,2))

    panes = tk.Frame(win, bg='#040c10')
    panes.pack(fill='both', expand=True, padx=8, pady=4)

    left = tk.Frame(panes, bg='#020a0e', width=340)
    left.pack(side='left', fill='y', padx=(0,4))
    left.pack_propagate(False)
    tk.Label(left, text='Paste Python code:', bg='#020a0e', fg='#1a6a7a',
             font=('Segoe UI', 8)).pack(anchor='w', padx=4)
    code_text = tk.Text(left, bg='#020a0e', fg='#40e0ff',
                        font=('Consolas', 9), wrap='none',
                        insertbackground='#40e0ff', relief='flat',
                        highlightthickness=1, highlightbackground='#0a3a4a')
    code_text.pack(fill='both', expand=True, padx=4, pady=4)
    code_text.insert('1.0', '''def greet(name):
    message = build_msg(name)
    print(message)

def build_msg(name):
    prefix = get_prefix()
    return f"{prefix}, {name}!"

def get_prefix():
    return "Hello"

greet("World")
''')

    right = tk.Frame(panes, bg='#020a0e')
    right.pack(side='left', fill='both', expand=True)
    tk.Label(right, text='Call Graph:', bg='#020a0e', fg='#1a6a7a',
             font=('Segoe UI', 8)).pack(anchor='w', padx=4)
    cv = tk.Canvas(right, bg='#010608', highlightthickness=0)
    cv.pack(fill='both', expand=True, padx=4, pady=4)

    def analyze_and_draw():
        import ast as _ast
        src = code_text.get('1.0', 'end')
        cv.delete('all')
        try:
            tree = _ast.parse(src)
        except SyntaxError as e:
            cv.create_text(200, 60, text=f'Syntax Error: {e.msg} (line {e.lineno})',
                           fill='#ff5555', font=('Consolas', 10))
            return

        # Extract functions and calls
        funcs = {}
        for node in _ast.walk(tree):
            if isinstance(node, _ast.FunctionDef):
                calls = []
                for child in _ast.walk(node):
                    if isinstance(child, _ast.Call):
                        if isinstance(child.func, _ast.Name):
                            calls.append(child.func.id)
                        elif isinstance(child.func, _ast.Attribute):
                            calls.append(child.func.attr)
                funcs[node.name] = calls

        if not funcs:
            cv.create_text(200, 100, text='No functions found.',
                           fill='#556677', font=('Segoe UI', 11))
            return

        W = cv.winfo_width() or 500
        H = cv.winfo_height() or 400
        n = len(funcs)
        positions = {}
        for i, fname in enumerate(funcs):
            angle = i * 2*math.pi/n - math.pi/2
            r = min(W,H) * 0.35
            x = W//2 + int(r * math.cos(angle))
            y = H//2 + int(r * math.sin(angle))
            positions[fname] = (x, y)

        # Draw edges
        for fname, calls in funcs.items():
            x1, y1 = positions[fname]
            for called in calls:
                if called in positions:
                    x2, y2 = positions[called]
                    cv.create_line(x1, y1, x2, y2, fill='#0a4a5a',
                                   width=2, arrow='last',
                                   arrowshape=(10,12,5), smooth=True)

        # Draw nodes
        for fname, (x, y) in positions.items():
            R = 36
            cv.create_oval(x-R, y-R, x+R, y+R, fill='#0a2a38',
                           outline='#40e0ff', width=2)
            cv.create_text(x, y, text=fname, fill='#40e0ff',
                           font=('Consolas', 8, 'bold'))

    code_text.bind('<KeyRelease>', lambda e: win.after(300, analyze_and_draw))
    win.after(500, analyze_and_draw)

    bf = tk.Frame(win, bg='#040c10')
    bf.pack(pady=4)
    tk.Button(bf, text='Analyze', bg='#0a3040', fg='#40e0ff', relief='flat',
              font=('Segoe UI', 9), command=analyze_and_draw).pack(side='left', padx=6)


# ── IV: Password Strength Visualizer ────────────────────────────────────────
def show_password_strength():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Password Strength Lab')
    win.geometry('520x440')
    style_aero_window(win, '#080c14')
    center_window(win, 520, 440)

    tk.Label(win, text='🔐  Password Strength Lab',
             bg='#080c14', fg='#60b8ff', font=('Segoe UI', 13, 'bold')).pack(pady=(16,2))

    entry_frame = tk.Frame(win, bg='#080c14')
    entry_frame.pack(fill='x', padx=30, pady=8)
    show_var = tk.BooleanVar(value=False)
    pwd_var = tk.StringVar()
    pwd_e = tk.Entry(entry_frame, textvariable=pwd_var, font=('Consolas', 14),
                     bg='#050a18', fg='#60b8ff', insertbackground='#60b8ff',
                     show='●', relief='flat', highlightthickness=2,
                     highlightbackground='#1a3a6a')
    pwd_e.pack(fill='x', ipady=8)

    def toggle_show():
        pwd_e.config(show='' if show_var.get() else '●')
    tk.Checkbutton(entry_frame, text='Show password', variable=show_var,
                   command=toggle_show, bg='#080c14', fg='#4a7aaa',
                   activebackground='#080c14', selectcolor='#0a1828',
                   font=('Segoe UI', 9)).pack(anchor='w', pady=2)

    bar_cv = tk.Canvas(win, width=460, height=22, bg='#050a18', highlightthickness=0)
    bar_cv.pack(padx=30)
    bar_rect = bar_cv.create_rectangle(0, 0, 0, 22, fill='#cc2020', outline='')
    score_lbl = tk.Label(win, text='', bg='#080c14', fg='white',
                         font=('Segoe UI', 11, 'bold'))
    score_lbl.pack(pady=4)

    checks_frame = tk.Frame(win, bg='#080c14')
    checks_frame.pack(fill='x', padx=30, pady=6)
    criteria = [
        ('length8',    '8+ characters'),
        ('length16',   '16+ characters'),
        ('uppercase',  'Uppercase letters'),
        ('lowercase',  'Lowercase letters'),
        ('digits',     'Numbers (0-9)'),
        ('symbols',    'Symbols (!@#$...)'),
        ('no_repeat',  'No repeated chars'),
        ('no_common',  'Not a common password'),
    ]
    crit_labels = {}
    for row_i, (key, text) in enumerate(criteria):
        col_i = row_i % 2
        row_f = checks_frame
        lbl = tk.Label(row_f, text=f'  ✗  {text}',
                       bg='#080c14', fg='#664444',
                       font=('Segoe UI', 9), anchor='w')
        lbl.grid(row=row_i//2, column=col_i, sticky='w', padx=10, pady=1)
        crit_labels[key] = lbl

    time_lbl = tk.Label(win, text='', bg='#080c14', fg='#4a7aaa',
                        font=('Segoe UI', 9))
    time_lbl.pack()
    entropy_lbl = tk.Label(win, text='', bg='#080c14', fg='#2a5a8a',
                           font=('Segoe UI', 8))
    entropy_lbl.pack()

    COMMON = {'password','123456','qwerty','abc123','letmein','monkey',
              'dragon','master','sunshine','princess','welcome','shadow'}

    def evaluate(event=None):
        pwd = pwd_var.get()
        if not pwd:
            bar_cv.coords(bar_rect, 0, 0, 0, 22)
            score_lbl.config(text='')
            time_lbl.config(text='')
            entropy_lbl.config(text='')
            for lbl in crit_labels.values():
                lbl.config(text=lbl.cget('text').replace('✓','✗'), fg='#664444')
            return

        results = {
            'length8':   len(pwd) >= 8,
            'length16':  len(pwd) >= 16,
            'uppercase': any(c.isupper() for c in pwd),
            'lowercase': any(c.islower() for c in pwd),
            'digits':    any(c.isdigit() for c in pwd),
            'symbols':   any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in pwd),
            'no_repeat': len(set(pwd)) > len(pwd) * 0.6,
            'no_common': pwd.lower() not in COMMON,
        }
        for key, passed in results.items():
            lbl = crit_labels[key]
            old = lbl.cget('text')
            # replace leading icon
            text_part = old[3:]
            lbl.config(text=f'  {"✓" if passed else "✗"}  {text_part}',
                       fg='#44aa44' if passed else '#664444')

        score = sum(results.values())
        # Entropy estimate
        pool = (26 if results['uppercase'] else 0) + \
               (26 if results['lowercase'] else 0) + \
               (10 if results['digits'] else 0) + \
               (30 if results['symbols'] else 0) or 26
        entropy = len(pwd) * math.log2(pool)

        # Crack time estimate
        guesses_per_sec = 1e10
        combos = pool ** len(pwd)
        seconds = combos / guesses_per_sec
        if seconds < 60:       crack = f'{int(seconds)}s'
        elif seconds < 3600:   crack = f'{int(seconds/60)}m'
        elif seconds < 86400:  crack = f'{int(seconds/3600)}h'
        elif seconds < 2592000: crack = f'{int(seconds/86400)} days'
        elif seconds < 31536000: crack = f'{int(seconds/2592000)} months'
        else:                  crack = f'{int(seconds/31536000):.0e} years'

        level_map = {0:'Very Weak',1:'Very Weak',2:'Weak',3:'Fair',
                     4:'Good',5:'Strong',6:'Strong',7:'Very Strong',8:'Excellent'}
        color_map = {0:'#cc2020',1:'#cc2020',2:'#cc6020',3:'#cc9020',
                     4:'#a0cc20',5:'#20cc40',6:'#20cc40',7:'#20ee60',8:'#00ff88'}
        level = level_map[score]
        color = color_map[score]

        bar_cv.coords(bar_rect, 0, 0, int(460 * score/8), 22)
        bar_cv.itemconfig(bar_rect, fill=color)
        score_lbl.config(text=f'{level}  ({score}/8)', fg=color)
        time_lbl.config(text=f'Estimated crack time (10B guesses/sec): {crack}')
        entropy_lbl.config(text=f'Entropy: {entropy:.1f} bits  ·  Charset: {pool}')

    pwd_var.trace_add('write', lambda *a: evaluate())
    pwd_e.focus_set()


# ── V: Live Regex Tester ─────────────────────────────────────────────────────
def show_regex_tester():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Regex Lab')
    win.geometry('680x500')
    style_aero_window(win, '#080c10')
    center_window(win, 680, 500)

    tk.Label(win, text='⚡  Live Regex Tester',
             bg='#080c10', fg='#ffcc40', font=('Segoe UI', 13, 'bold')).pack(pady=(12,2))

    def make_row(label, bg='#080c10'):
        f = tk.Frame(win, bg=bg)
        f.pack(fill='x', padx=16, pady=3)
        tk.Label(f, text=label, bg=bg, fg='#ffaa20',
                 font=('Segoe UI', 9, 'bold'), width=10, anchor='w').pack(side='left')
        return f

    pat_var = tk.StringVar(value=r'\b\w{5}\b')
    r1 = make_row('Pattern:')
    tk.Entry(r1, textvariable=pat_var, bg='#0a1010', fg='#ffcc40',
             insertbackground='#ffcc40', font=('Consolas', 11),
             relief='flat', highlightthickness=2,
             highlightbackground='#5a4a00').pack(side='left', fill='x', expand=True, ipady=4)

    flags_vars = {}
    flags_frame = tk.Frame(win, bg='#080c10')
    flags_frame.pack(fill='x', padx=26, pady=2)
    for flag_name in ('IGNORECASE', 'MULTILINE', 'DOTALL'):
        v = tk.BooleanVar(value=False)
        flags_vars[flag_name] = v
        tk.Checkbutton(flags_frame, text=flag_name, variable=v,
                       bg='#080c10', fg='#aa8820',
                       activebackground='#080c10', selectcolor='#0a1010',
                       font=('Segoe UI', 8), command=lambda: win.after(50, update)).pack(side='left', padx=6)

    test_lbl = tk.Label(win, text='Test String:', bg='#080c10', fg='#ffaa20',
                        font=('Segoe UI', 9), anchor='w')
    test_lbl.pack(fill='x', padx=16)
    test_text = tk.Text(win, height=5, bg='#0a1010', fg='#ddccaa',
                        font=('Consolas', 10), wrap='word',
                        insertbackground='#ffcc40', relief='flat',
                        highlightthickness=1, highlightbackground='#3a2a00')
    test_text.pack(fill='x', padx=16, pady=2)
    test_text.insert('1.0',
        'The quick brown fox jumps over the lazy dog.\n'
        'Email: test@example.com  Phone: 555-1234\n'
        'Python 3.12 released in 2024.')

    test_text.tag_config('match', background='#604000', foreground='#ffee44')

    result_lbl = tk.Label(win, text='', bg='#080c10', fg='#ffcc40',
                          font=('Segoe UI', 10, 'bold'))
    result_lbl.pack(pady=4)

    groups_text = tk.Text(win, height=6, bg='#050808', fg='#aaccaa',
                          font=('Consolas', 9), wrap='word',
                          relief='flat', state='disabled',
                          highlightthickness=1, highlightbackground='#1a3a1a')
    groups_text.pack(fill='x', padx=16, pady=2)

    def update(event=None):
        pattern = pat_var.get()
        text = test_text.get('1.0', 'end-1c')
        test_text.tag_remove('match', '1.0', 'end')
        groups_text.config(state='normal')
        groups_text.delete('1.0', 'end')

        if not pattern:
            result_lbl.config(text='Enter a pattern.', fg='#ffaa40')
            groups_text.config(state='disabled')
            return
        try:
            flags = 0
            if flags_vars['IGNORECASE'].get(): flags |= re.IGNORECASE
            if flags_vars['MULTILINE'].get():  flags |= re.MULTILINE
            if flags_vars['DOTALL'].get():     flags |= re.DOTALL
            matches = list(re.finditer(pattern, text, flags))
            result_lbl.config(
                text=f'✅  {len(matches)} match{"es" if len(matches)!=1 else ""} found',
                fg='#44ee44' if matches else '#ff8844')
            for m in matches:
                start = f'1.0+{m.start()}c'
                end   = f'1.0+{m.end()}c'
                test_text.tag_add('match', start, end)
            for i, m in enumerate(matches[:20]):
                groups_text.insert('end',
                    f'  Match {i+1}: {repr(m.group())}  pos={m.start()}-{m.end()}\n')
                if m.groups():
                    groups_text.insert('end',
                        f'    Groups: {m.groups()}\n')
        except re.error as e:
            result_lbl.config(text=f'❌  Regex Error: {e}', fg='#ff5555')
        groups_text.config(state='disabled')

    pat_var.trace_add('write', lambda *a: win.after(100, update))
    test_text.bind('<KeyRelease>', lambda e: update())
    update()


# ── VI: System Timeline — graphical event log ────────────────────────────────
def show_system_timeline():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('System Timeline')
    win.geometry('760x520')
    style_aero_window(win, '#040810')
    center_window(win, 760, 520)

    tk.Label(win, text='📅  System Timeline  —  Activity History',
             bg='#040810', fg='#80c0ff', font=('Segoe UI', 13, 'bold')).pack(pady=(12,2))

    cv = tk.Canvas(win, bg='#020508', highlightthickness=0)
    cv.pack(fill='both', expand=True, padx=12, pady=8)

    bf = tk.Frame(win, bg='#040810')
    bf.pack(pady=4)

    events = []
    # Load from audit log
    for line in read_audit_log(60):
        try:
            ts_part = line[1:20]
            rest = line[22:]
            events.append({'ts': ts_part, 'text': rest[:60],
                           'color': ('#ff6060' if 'CRITICAL' in line else
                                     '#ffaa40' if 'WARN' in line else '#60aaff')})
        except Exception:
            pass

    # Add some synthetic milestones
    events.insert(0, {'ts': datetime.now().strftime('%Y-%m-%d %H:%M'),
                       'text': 'Session started', 'color': '#60ff88'})

    def draw_timeline():
        cv.delete('all')
        W = cv.winfo_width() or 740
        H = cv.winfo_height() or 400
        if not events:
            cv.create_text(W//2, H//2, text='No events recorded yet.',
                           fill='#334455', font=('Segoe UI', 12))
            return

        N = min(len(events), 30)
        visible = events[-N:]
        MARGIN = 60
        TIMELINE_Y = H // 2
        step = (W - MARGIN*2) / max(N-1, 1)

        # Horizontal line
        cv.create_line(MARGIN, TIMELINE_Y, W-MARGIN, TIMELINE_Y,
                       fill='#1a3a5a', width=2)

        for i, ev in enumerate(visible):
            x = int(MARGIN + i * step)
            color = ev['color']
            # Dot
            cv.create_oval(x-8, TIMELINE_Y-8, x+8, TIMELINE_Y+8,
                           fill=color, outline='white', width=1)
            # Alternating label position
            if i % 2 == 0:
                label_y = TIMELINE_Y - 50
                line_y1, line_y2 = TIMELINE_Y - 8, TIMELINE_Y - 30
            else:
                label_y = TIMELINE_Y + 50
                line_y1, line_y2 = TIMELINE_Y + 8, TIMELINE_Y + 30
            cv.create_line(x, line_y1, x, line_y2, fill=color, width=1, dash=(3,3))
            cv.create_text(x, label_y, text=ev['text'][:22],
                           fill=color, font=('Consolas', 7),
                           angle=30 if i % 2 == 0 else -30)

    cv.bind('<Configure>', lambda e: draw_timeline())
    win.after(200, draw_timeline)

    def refresh():
        events.clear()
        for line in read_audit_log(60):
            try:
                ts_part = line[1:20]
                rest = line[22:]
                events.append({'ts': ts_part, 'text': rest[:60],
                               'color': ('#ff6060' if 'CRITICAL' in line else
                                         '#ffaa40' if 'WARN' in line else '#60aaff')})
            except Exception:
                pass
        draw_timeline()

    tk.Button(bf, text='Refresh', bg='#0a2040', fg='#80c0ff',
              relief='flat', font=('Segoe UI', 9), command=refresh).pack(side='left', padx=6)


# ── VII: Emoji Keyboard ──────────────────────────────────────────────────────
def show_emoji_keyboard():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Emoji Keyboard')
    win.geometry('560x420')
    style_aero_window(win, '#0c0c14')
    center_window(win, 560, 420)

    tk.Label(win, text='😊  Emoji Keyboard',
             bg='#0c0c14', fg='#ffcc60', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))

    CATEGORIES = {
        '😀 Faces':  ['😀','😂','🤣','😊','😍','🥰','😎','🤔','😴','🥳','😭','😡','🤯','🥺','😱'],
        '❤ Hearts':  ['❤','🧡','💛','💚','💙','💜','🖤','🤍','💕','💞','💓','💗','💖','💘','💝'],
        '🎉 Objects':['🎉','🎊','🎈','🎁','🔥','⭐','🌟','💫','✨','🎯','🏆','🎮','💡','🔮','🌈'],
        '🐶 Animals':['🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯','🦁','🐮','🐷','🐸','🐙'],
        '🍕 Food':   ['🍕','🍔','🌮','🍣','🍜','🍦','🎂','🍩','☕','🧃','🍺','🍇','🍓','🥑','🌽'],
        '✈ Travel':  ['✈','🚀','🚗','🏠','🌍','🏔','🏖','🗼','🌋','🏝','🚂','⛵','🎡','🌃','🌄'],
    }
    cat_var = tk.StringVar(value=list(CATEGORIES.keys())[0])

    # Output box
    out_var = tk.StringVar()
    out_frame = tk.Frame(win, bg='#0c0c14')
    out_frame.pack(fill='x', padx=16, pady=4)
    out_e = tk.Entry(out_frame, textvariable=out_var, font=('Segoe UI Emoji', 16),
                     bg='#06060c', fg='#ffdd88', insertbackground='#ffdd88',
                     relief='flat', highlightthickness=2, highlightbackground='#3a3a00')
    out_e.pack(side='left', fill='x', expand=True, ipady=6)
    tk.Button(out_frame, text='Copy', bg='#2a2a00', fg='#ffcc40',
              relief='flat', font=('Segoe UI', 9),
              command=lambda: [win.clipboard_clear(),
                               win.clipboard_append(out_var.get()),
                               show_system_notification('Emoji', 'Copied!')]).pack(
              side='left', padx=4)
    tk.Button(out_frame, text='Clear', bg='#1a0000', fg='#ff8888',
              relief='flat', font=('Segoe UI', 9),
              command=lambda: out_var.set('')).pack(side='left', padx=2)

    # Category tabs
    tab_frame = tk.Frame(win, bg='#0c0c14')
    tab_frame.pack(fill='x', padx=16)
    cat_btns = {}
    def set_cat(cat):
        cat_var.set(cat)
        for c, btn in cat_btns.items():
            btn.config(bg='#2a2a00' if c == cat else '#0c0c14',
                       fg='#ffcc40' if c == cat else '#666640')
        build_grid()

    for cat in CATEGORIES:
        btn = tk.Label(tab_frame, text=cat[:4], bg='#0c0c14', fg='#666640',
                       font=('Segoe UI Emoji', 10), padx=6, pady=3, cursor='hand2')
        btn.pack(side='left', padx=2)
        btn.bind('<Button-1>', lambda e, c=cat: set_cat(c))
        cat_btns[cat] = btn

    grid_frame = tk.Frame(win, bg='#0c0c14')
    grid_frame.pack(fill='both', expand=True, padx=16, pady=4)

    def build_grid():
        for w in grid_frame.winfo_children():
            try: w.destroy()
            except: pass
        emojis = CATEGORIES.get(cat_var.get(), [])
        for i, em in enumerate(emojis):
            row_i = i // 8; col_i = i % 8
            btn = tk.Label(grid_frame, text=em, bg='#0a0a10',
                           font=('Segoe UI Emoji', 20), padx=4, pady=4,
                           cursor='hand2', relief='flat')
            btn.grid(row=row_i, column=col_i, padx=3, pady=3)
            def on_click(e, emoji=em):
                out_var.set(out_var.get() + emoji)
                play_windows7_asterisk()
            def on_enter(e, btn=btn): btn.config(bg='#2a2a20')
            def on_leave(e, btn=btn): btn.config(bg='#0a0a10')
            btn.bind('<Button-1>', on_click)
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)

    build_grid()
    set_cat(list(CATEGORIES.keys())[0])


# ── VIII: Typing Speed Test ──────────────────────────────────────────────────
def show_typing_test():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Typing Speed Test')
    win.geometry('620x420')
    style_aero_window(win, '#060a0e')
    center_window(win, 620, 420)

    PASSAGES = [
        'The quick brown fox jumps over the lazy dog near the riverbank at sunset.',
        'Windows 7 is an operating system that changed the way we think about computing forever.',
        'The best programmers write code that even beginners can understand and maintain easily.',
        'Technology is nothing without creativity and the human spirit driving it forward.',
        'Artificial intelligence will transform every industry in ways we cannot yet imagine.',
    ]
    passage = random.choice(PASSAGES)
    test_state = {'started': False, 'start_time': 0.0, 'done': False}

    tk.Label(win, text='⌨  Typing Speed Test  —  WPM',
             bg='#060a0e', fg='#60e0b0', font=('Segoe UI', 13, 'bold')).pack(pady=(12,4))

    # Display passage
    passage_cv = tk.Canvas(win, height=90, bg='#030608', highlightthickness=0)
    passage_cv.pack(fill='x', padx=20, pady=4)

    stats_row = tk.Frame(win, bg='#060a0e')
    stats_row.pack(fill='x', padx=20, pady=2)
    wpm_lbl = tk.Label(stats_row, text='WPM: —', bg='#060a0e', fg='#60e0b0',
                       font=('Consolas', 14, 'bold'))
    wpm_lbl.pack(side='left', padx=10)
    acc_lbl = tk.Label(stats_row, text='Accuracy: —', bg='#060a0e', fg='#60a0ff',
                       font=('Consolas', 12))
    acc_lbl.pack(side='left', padx=10)
    time_lbl = tk.Label(stats_row, text='Time: 0s', bg='#060a0e', fg='#aaaaaa',
                        font=('Consolas', 10))
    time_lbl.pack(side='left', padx=10)

    type_e = tk.Text(win, height=4, bg='#050a08', fg='#60e0b0',
                     font=('Segoe UI', 12), wrap='word',
                     insertbackground='#60e0b0', relief='flat',
                     highlightthickness=2, highlightbackground='#1a4a3a')
    type_e.pack(fill='x', padx=20, pady=4)

    progress_cv = tk.Canvas(win, height=10, bg='#020508', highlightthickness=0)
    progress_cv.pack(fill='x', padx=20)
    prog_bar = progress_cv.create_rectangle(0, 0, 0, 10, fill='#20a060', outline='')

    def render_passage():
        passage_cv.delete('all')
        typed = type_e.get('1.0', 'end-1c')
        x, y = 10, 20
        for i, ch in enumerate(passage):
            if i < len(typed):
                color = '#20a060' if typed[i] == ch else '#ff4444'
            else:
                color = '#446655'
            passage_cv.create_text(x, y, text=ch, fill=color,
                                   font=('Segoe UI', 12), anchor='nw')
            x += 9
            if x > 570:
                x = 10; y += 22

    def on_type(event=None):
        if test_state['done']:
            return
        typed = type_e.get('1.0', 'end-1c')
        if not test_state['started'] and typed:
            test_state['started'] = True
            test_state['start_time'] = time.time()
        if not test_state['started']:
            return

        elapsed = time.time() - test_state['start_time']
        words_typed = len(typed.split())
        wpm = int(words_typed / max(elapsed/60, 0.001))
        correct = sum(1 for a,b in zip(typed, passage) if a==b)
        acc = int(100 * correct / max(len(typed), 1))

        wpm_lbl.config(text=f'WPM: {wpm}')
        acc_lbl.config(text=f'Accuracy: {acc}%')
        time_lbl.config(text=f'Time: {int(elapsed)}s')
        try:
            w = progress_cv.winfo_width() or 560
            pct = len(typed) / len(passage)
            progress_cv.coords(prog_bar, 0, 0, int(w*pct), 10)
        except Exception:
            pass
        render_passage()

        if len(typed) >= len(passage):
            test_state['done'] = True
            elapsed = time.time() - test_state['start_time']
            total_words = len(passage.split())
            final_wpm = int(total_words / max(elapsed/60, 0.001))
            final_acc = int(100 * sum(1 for a,b in zip(typed,passage) if a==b) / len(passage))
            play_windows7_logon()
            show_system_notification('Typing Test',
                f'Done! {final_wpm} WPM  ·  {final_acc}% accuracy  ·  {int(elapsed)}s')
            type_e.config(state='disabled')

    def reset():
        nonlocal passage
        passage = random.choice(PASSAGES)
        test_state.update({'started': False, 'start_time': 0.0, 'done': False})
        type_e.config(state='normal')
        type_e.delete('1.0', 'end')
        wpm_lbl.config(text='WPM: —')
        acc_lbl.config(text='Accuracy: —')
        time_lbl.config(text='Time: 0s')
        progress_cv.coords(prog_bar, 0, 0, 0, 10)
        render_passage()

    type_e.bind('<KeyRelease>', on_type)
    render_passage()

    bf = tk.Frame(win, bg='#060a0e')
    bf.pack(pady=6)
    tk.Button(bf, text='Reset', bg='#0a2a1a', fg='#60e0b0', relief='flat',
              font=('Segoe UI', 10), command=reset).pack(side='left', padx=6)
    type_e.focus_set()


# ── IX: Color Palette Studio ─────────────────────────────────────────────────
def show_color_palette():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Color Palette Studio')
    win.geometry('580x460')
    style_aero_window(win, '#08080c')
    center_window(win, 580, 460)

    tk.Label(win, text='🎨  Color Palette Studio',
             bg='#08080c', fg='#e0c080', font=('Segoe UI', 13, 'bold')).pack(pady=(12,2))

    PRESETS = {
        'Aero Blue':   ['#dce9f8','#b8d4f4','#7ab0e8','#3a80c8','#1a5098','#0a2868'],
        'Sunset Fire': ['#ffe0b0','#ffb060','#ff7020','#e03000','#801000','#300000'],
        'Forest':      ['#e8f8e0','#b0e898','#60c840','#289820','#106010','#042004'],
        'Deep Ocean':  ['#d0f0ff','#80c8f0','#2090d8','#0060a8','#003070','#000828'],
        'Neon Night':  ['#ffffff','#ff00ff','#00ffff','#ffff00','#ff0040','#0000cc'],
        'Pastel':      ['#ffe8f8','#ffd0e8','#ffb8d8','#e898c0','#c070a0','#904878'],
    }
    cur_palette = list(PRESETS['Aero Blue'])

    cv_palette = tk.Canvas(win, height=80, bg='#08080c', highlightthickness=0)
    cv_palette.pack(fill='x', padx=16, pady=8)

    def draw_palette():
        cv_palette.delete('all')
        n = len(cur_palette)
        w = (cv_palette.winfo_width() or 540)
        sw = w // n
        for i, col in enumerate(cur_palette):
            x1, x2 = i*sw, (i+1)*sw
            cv_palette.create_rectangle(x1, 0, x2, 80, fill=col, outline='')
            cv_palette.create_text(x1 + sw//2, 60, text=col,
                                   fill='white' if sum(int(col[j:j+2],16) for j in (1,3,5)) < 380 else '#333',
                                   font=('Consolas', 7))

    # Hex editor
    hex_frame = tk.Frame(win, bg='#08080c')
    hex_frame.pack(fill='x', padx=16, pady=4)
    hex_vars = []
    for i in range(6):
        f = tk.Frame(hex_frame, bg='#08080c')
        f.pack(side='left', expand=True)
        v = tk.StringVar(value=cur_palette[i] if i < len(cur_palette) else '#ffffff')
        hex_vars.append(v)
        e = tk.Entry(f, textvariable=v, width=8, font=('Consolas', 9),
                     bg='#0a0a10', fg='#e0c080', justify='center',
                     insertbackground='#e0c080', relief='flat',
                     highlightthickness=1, highlightbackground='#3a3000')
        e.pack(ipady=3)
        preview = tk.Label(f, text='  ', bg=cur_palette[i], width=4)
        preview.pack(fill='x')
        def on_hex(event, idx=i, prev=preview, vr=v):
            try:
                col = vr.get()
                if len(col) == 7 and col.startswith('#'):
                    cur_palette[idx] = col
                    prev.config(bg=col)
                    draw_palette()
            except Exception:
                pass
        e.bind('<KeyRelease>', on_hex)

    # Preset buttons
    pre_frame = tk.Frame(win, bg='#08080c')
    pre_frame.pack(fill='x', padx=16, pady=4)
    tk.Label(pre_frame, text='Presets:', bg='#08080c', fg='#a08040',
             font=('Segoe UI', 9)).pack(side='left')
    def load_preset(name):
        cols = PRESETS[name]
        cur_palette.clear()
        cur_palette.extend(cols)
        for i, v in enumerate(hex_vars):
            if i < len(cols):
                v.set(cols[i])
        draw_palette()

    for name in PRESETS:
        tk.Label(pre_frame, text=name, bg='#100c00', fg='#e0c080',
                 font=('Segoe UI', 8), padx=4, pady=2, cursor='hand2').pack(
                 side='left', padx=2).bind('<Button-1>', lambda e, n=name: load_preset(n))

    # Color wheel canvas
    wheel_cv = tk.Canvas(win, width=200, height=200, bg='#08080c', highlightthickness=0)
    wheel_cv.pack(pady=6)
    cx, cy, R = 100, 100, 90
    for deg in range(360):
        angle = math.radians(deg)
        r = int(255*(0.5+0.5*math.cos(math.radians(deg))))
        g = int(255*(0.5+0.5*math.cos(math.radians(deg-120))))
        b = int(255*(0.5+0.5*math.cos(math.radians(deg+120))))
        color = f'#{r:02x}{g:02x}{b:02x}'
        x1 = cx + int(R*math.cos(angle))
        y1 = cy + int(R*math.sin(angle))
        x2 = cx + int((R-20)*math.cos(angle))
        y2 = cy + int((R-20)*math.sin(angle))
        wheel_cv.create_line(x2, y2, x1, y1, fill=color, width=3)
    wheel_cv.create_text(cx, cy, text='Color\nWheel',
                         fill='#665533', font=('Segoe UI', 8), justify='center')

    def copy_palette():
        win.clipboard_clear()
        win.clipboard_append(' '.join(cur_palette))
        show_system_notification('Palette', f'Copied {len(cur_palette)} colors')

    bf = tk.Frame(win, bg='#08080c')
    bf.pack(pady=4)
    tk.Button(bf, text='Copy Colors', bg='#1a1400', fg='#e0c080', relief='flat',
              font=('Segoe UI', 9), command=copy_palette).pack(side='left', padx=6)

    cv_palette.bind('<Configure>', lambda e: draw_palette())
    win.after(100, draw_palette)


# ── X: Futuristic Clock & World Time ─────────────────────────────────────────
def show_world_clock():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('World Clock')
    win.geometry('700x420')
    style_aero_window(win, '#030610')
    center_window(win, 700, 420)

    tk.Label(win, text='🌍  World Clock  —  Live',
             bg='#030610', fg='#40c8ff', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))

    ZONES = [
        ('🌆 New Delhi',   5.5,   '#ff9040'),
        ('🗼 Tokyo',        9,    '#ff60a0'),
        ('🗽 New York',    -5,    '#60d0ff'),
        ('🏙 London',       0,    '#60ff90'),
        ('🏰 Paris',        1,    '#ffcc40'),
        ('🌉 San Francisco',-8,   '#a060ff'),
        ('🌴 Dubai',        4,    '#ff8040'),
        ('🏛 Sydney',       10,   '#40ffcc'),
    ]

    clock_frame = tk.Frame(win, bg='#030610')
    clock_frame.pack(fill='both', expand=True, padx=10, pady=6)

    clock_canvases = {}
    for i, (city, offset, color) in enumerate(ZONES):
        col_i = i % 4; row_i = i // 4
        card = tk.Frame(clock_frame, bg='#060c1a', bd=1, relief='ridge')
        card.grid(row=row_i, column=col_i, padx=6, pady=6, sticky='nsew')
        clock_frame.columnconfigure(col_i, weight=1)
        clock_frame.rowconfigure(row_i, weight=1)

        tk.Label(card, text=city, bg='#060c1a', fg=color,
                 font=('Segoe UI', 8, 'bold')).pack(pady=(4,0))
        cv = tk.Canvas(card, width=90, height=90, bg='#030810', highlightthickness=0)
        cv.pack()
        time_lbl = tk.Label(card, text='', bg='#060c1a', fg=color,
                            font=('Consolas', 10, 'bold'))
        time_lbl.pack(pady=(0,4))
        clock_canvases[i] = (cv, offset, color, time_lbl)

    def draw_clock(cv, offset, color):
        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc) + timedelta(hours=offset)
        cv.delete('all')
        cx, cy, r = 45, 45, 38
        # Face
        cv.create_oval(cx-r, cy-r, cx+r, cy+r, fill='#020508', outline=color, width=2)
        # Hour marks
        for hm in range(12):
            a = math.radians(hm*30 - 90)
            x1 = cx + (r-5)*math.cos(a); y1 = cy + (r-5)*math.sin(a)
            x2 = cx + (r-1)*math.cos(a); y2 = cy + (r-1)*math.sin(a)
            cv.create_line(x1,y1,x2,y2, fill=color, width=1)
        # Hands
        h_ang = math.radians((now.hour%12 + now.minute/60)*30 - 90)
        m_ang = math.radians(now.minute*6 - 90)
        s_ang = math.radians(now.second*6 - 90)
        cv.create_line(cx,cy, cx+22*math.cos(h_ang), cy+22*math.sin(h_ang),
                       fill=color, width=3)
        cv.create_line(cx,cy, cx+32*math.cos(m_ang), cy+32*math.sin(m_ang),
                       fill='white', width=2)
        cv.create_line(cx,cy, cx+34*math.cos(s_ang), cy+34*math.sin(s_ang),
                       fill='#ff4444', width=1)
        cv.create_oval(cx-3,cy-3, cx+3,cy+3, fill=color, outline='')
        return now

    def update_all():
        if not win.winfo_exists():
            return
        for i, (cv, offset, color, lbl) in clock_canvases.items():
            try:
                now = draw_clock(cv, offset, color)
                lbl.config(text=now.strftime('%H:%M:%S'))
            except Exception:
                pass
        win.after(1000, update_all)

    update_all()


# ── Add all new futuristic features to APP_MAP ───────────────────────────────
APP_MAP.update({
    'bsod':           lambda: show_bsod(),
    'blue screen':    lambda: show_bsod(),
    'crash':          lambda: show_bsod(),
    'dream canvas':   lambda: show_dream_canvas(),
    'dream':          lambda: show_dream_canvas(),
    'mind map':       lambda: show_mind_map(),
    'mindmap':        lambda: show_mind_map(),
    'code visual':    lambda: show_code_visualizer(),
    'call graph':     lambda: show_code_visualizer(),
    'password lab':   lambda: show_password_strength(),
    'password strength': lambda: show_password_strength(),
    'regex':          lambda: show_regex_tester(),
    'regex tester':   lambda: show_regex_tester(),
    'timeline':       lambda: show_system_timeline(),
    'system timeline': lambda: show_system_timeline(),
    'emoji':          lambda: show_emoji_keyboard(),
    'emoji keyboard': lambda: show_emoji_keyboard(),
    'typing test':    lambda: show_typing_test(),
    'typing':         lambda: show_typing_test(),
    'color palette':  lambda: show_color_palette(),
    'palette':        lambda: show_color_palette(),
    'world clock':    lambda: show_world_clock(),
    'clock':          lambda: show_world_clock(),
    'activate':       lambda: show_activation_dialog(),
    'activation':     lambda: show_activation_dialog(),
    'product key':    lambda: show_activation_dialog(),
})


# ══════════════════════════════════════════════════════════════════════════════
#  WINDOWS SEARCH — Own full-featured search engine with live indexing
# ══════════════════════════════════════════════════════════════════════════════
def show_windows_search(initial_query: str = ''):
    """Full Windows 7-style search with live results across apps, notes, files, web."""
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Windows Search')
    win.geometry('700x560')
    win.overrideredirect(False)  # keep title bar for search
    win.attributes('-topmost', True)
    win.configure(bg='#0a1020')
    center_window(win, 700, 560)

    # ── Header ───────────────────────────────────────────────────────────────
    hdr = tk.Canvas(win, height=70, bg='#0a1020', highlightthickness=0)
    hdr.pack(fill='x')
    for i in range(70):
        t = i/70
        r = int(0x0a + (0x18-0x0a)*t)
        g = int(0x10 + (0x28-0x10)*t)
        b = int(0x20 + (0x50-0x20)*t)
        hdr.create_line(0, i, 700, i, fill=f'#{r:02x}{g:02x}{b:02x}')
    hdr.create_text(26, 35, text='🔍', font=('Segoe UI Emoji', 18), fill='white')
    hdr.create_text(200, 22, text='Windows Search',
                    fill='white', font=('Segoe UI', 14, 'bold'), anchor='w')
    hdr.create_text(200, 44, text='Search apps, notes, files, settings and the web',
                    fill='#4a7aaa', font=('Segoe UI', 9), anchor='w')

    # ── Search box ───────────────────────────────────────────────────────────
    search_frame = tk.Frame(win, bg='#060e1c')
    search_frame.pack(fill='x', padx=0)
    query_var = tk.StringVar(value=initial_query)
    search_e = tk.Entry(search_frame, textvariable=query_var,
                        font=('Segoe UI', 14), bg='#060e1c', fg='white',
                        insertbackground='#60a8e0', relief='flat',
                        highlightthickness=3, highlightbackground='#1a3a6a',
                        highlightcolor='#4a90d4')
    search_e.pack(side='left', fill='x', expand=True, ipady=10, padx=16)
    clear_btn = tk.Label(search_frame, text='✕', bg='#060e1c', fg='#3a5a7a',
                         font=('Segoe UI', 12), cursor='hand2', padx=10)
    clear_btn.pack(side='right')
    clear_btn.bind('<Button-1>', lambda e: [query_var.set(''), search_e.focus_set()])

    # ── Category filter tabs ──────────────────────────────────────────────────
    tab_frame = tk.Frame(win, bg='#080c18')
    tab_frame.pack(fill='x')
    CATEGORIES = ['All', 'Apps', 'Notes', 'Files', 'Settings', 'Web', 'People']
    cat_var = tk.StringVar(value='All')
    cat_btns = {}

    def set_cat(cat):
        cat_var.set(cat)
        for c, btn in cat_btns.items():
            btn.config(bg='#1a3a6a' if c == cat else '#080c18',
                       fg='#60a8ff' if c == cat else '#2a4a6a')
        do_search()

    for cat in CATEGORIES:
        btn = tk.Label(tab_frame, text=cat, bg='#080c18', fg='#2a4a6a',
                       font=('Segoe UI', 9), padx=12, pady=6, cursor='hand2')
        btn.pack(side='left')
        btn.bind('<Button-1>', lambda e, c=cat: set_cat(c))
        cat_btns[cat] = btn
    set_cat('All')

    # ── Results area ─────────────────────────────────────────────────────────
    results_frame = tk.Frame(win, bg='#080c18')
    results_frame.pack(fill='both', expand=True, padx=0, pady=0)

    result_canvas = tk.Canvas(results_frame, bg='#080c18', highlightthickness=0)
    scrollbar = ttk.Scrollbar(results_frame, command=result_canvas.yview)
    result_canvas.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')
    result_canvas.pack(side='left', fill='both', expand=True)

    inner = tk.Frame(result_canvas, bg='#080c18')
    inner_window = result_canvas.create_window((0,0), window=inner, anchor='nw')

    def on_frame_configure(e):
        result_canvas.configure(scrollregion=result_canvas.bbox('all'))
    inner.bind('<Configure>', on_frame_configure)
    result_canvas.bind('<Configure>',
                       lambda e: result_canvas.itemconfig(inner_window, width=e.width))

    status_lbl = tk.Label(win, text='', bg='#0a1020', fg='#2a4a6a',
                          font=('Segoe UI', 8))
    status_lbl.pack(side='bottom', anchor='w', padx=16, pady=4)

    # ── Search index builder ─────────────────────────────────────────────────
    def build_index():
        """Build a searchable index from all app data sources."""
        index = []

        # Apps
        for app_name in list(APP_MAP.keys()):
            index.append({
                'category': 'Apps',
                'title': app_name.title(),
                'subtitle': f'Application  ·  Double-click to launch',
                'icon': '⚙',
                'color': '#60a8ff',
                'action': lambda n=app_name: launch_app(n),
                'keywords': app_name.lower(),
            })

        # Notes
        for note in state.get('notes', []):
            if isinstance(note, dict):
                title = note.get('title', 'Note')
                content = note.get('content', '')
            else:
                title = str(note)[:40]
                content = str(note)
            index.append({
                'category': 'Notes',
                'title': title,
                'subtitle': content[:60] + ('...' if len(content) > 60 else ''),
                'icon': '📝',
                'color': '#ffe060',
                'action': lambda: show_sticky_notes(),
                'keywords': (title + ' ' + content).lower(),
            })

        # Tasks
        for task in state.get('tasks', []):
            t = task if isinstance(task, str) else task.get('text', str(task))
            index.append({
                'category': 'Notes',
                'title': t[:50],
                'subtitle': 'Task item',
                'icon': '✅',
                'color': '#60ff88',
                'action': lambda: show_sticky_notes(),
                'keywords': t.lower(),
            })

        # Settings panels
        settings_items = [
            ('Display Settings', '🖥', 'Personalization, resolution, wallpaper'),
            ('User Accounts', '👤', 'Change password, account type'),
            ('Network Settings', '🌐', 'WiFi, ethernet, VPN'),
            ('Windows Update', '⬆', 'Check for updates, automatic updates'),
            ('Security Center', '🛡', 'Firewall, antivirus, Windows Defender'),
            ('Sound Settings', '🔊', 'Volume, audio devices, mixer'),
            ('Power Options', '⚡', 'Sleep, hibernate, performance plan'),
            ('Programs & Features', '📦', 'Uninstall or change programs'),
            ('Device Manager', '🔧', 'Drivers, hardware, devices'),
            ('System Properties', '💻', 'Computer info, performance, remote'),
        ]
        for title, icon, desc in settings_items:
            index.append({
                'category': 'Settings',
                'title': title,
                'subtitle': desc,
                'icon': icon,
                'color': '#a080ff',
                'action': lambda: show_settings_app(),
                'keywords': (title + ' ' + desc).lower(),
            })

        # Files in DATA_DIR
        try:
            for fname in os.listdir(DATA_DIR):
                fpath = os.path.join(DATA_DIR, fname)
                try:
                    sz = os.path.getsize(fpath)
                    sz_str = f'{sz//1024} KB' if sz >= 1024 else f'{sz} B'
                except Exception:
                    sz_str = ''
                ext = os.path.splitext(fname)[1].lower()
                icon = {'json':'📄','.log':'📋','.txt':'📃','.enc':'🔒',
                        '.py':'🐍','.md':'📝'}.get(ext, '📁')
                index.append({
                    'category': 'Files',
                    'title': fname,
                    'subtitle': f'{sz_str}  ·  {fpath}',
                    'icon': icon,
                    'color': '#80d0ff',
                    'action': lambda p=fpath: (
                        os.startfile(p) if os.path.isfile(p) else None),
                    'keywords': fname.lower(),
                })
        except Exception:
            pass

        # People (from state)
        name = state.get('user_name', '')
        if name:
            index.append({
                'category': 'People',
                'title': name,
                'subtitle': f'Logged-in user  ·  {state.get("pc_name","RYAN-PC")}',
                'icon': '👤',
                'color': '#ffaa60',
                'action': lambda: show_settings_app(),
                'keywords': name.lower() + ' user account',
            })

        return index

    search_index = []
    index_built = {'v': False}

    def ensure_index():
        if not index_built['v']:
            search_index.clear()
            search_index.extend(build_index())
            index_built['v'] = True

    # ── Render results ───────────────────────────────────────────────────────
    def clear_results():
        for w in inner.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    def add_result_card(result):
        card = tk.Frame(inner, bg='#0c1428', cursor='hand2')
        card.pack(fill='x', padx=8, pady=3, ipady=2)

        icon_lbl = tk.Label(card, text=result['icon'],
                            bg='#0c1428', font=('Segoe UI Emoji', 16),
                            width=3)
        icon_lbl.pack(side='left', padx=(12, 4), pady=6)

        text_col = tk.Frame(card, bg='#0c1428')
        text_col.pack(side='left', fill='x', expand=True, pady=4)
        title_lbl = tk.Label(text_col, text=result['title'][:55],
                             bg='#0c1428', fg=result['color'],
                             font=('Segoe UI', 11, 'bold'), anchor='w')
        title_lbl.pack(anchor='w', padx=4)
        sub_lbl = tk.Label(text_col, text=result['subtitle'][:70],
                           bg='#0c1428', fg='#3a5a7a',
                           font=('Segoe UI', 8), anchor='w')
        sub_lbl.pack(anchor='w', padx=4)

        cat_lbl = tk.Label(card, text=result['category'],
                           bg='#0c1428', fg='#1a3a5a',
                           font=('Segoe UI', 7), padx=8)
        cat_lbl.pack(side='right', pady=2)

        # Hover effect
        all_widgets = [card, icon_lbl, text_col, title_lbl, sub_lbl, cat_lbl]
        def on_enter(e):
            for w in all_widgets:
                try: w.config(bg='#162040')
                except: pass
        def on_leave(e):
            for w in all_widgets:
                try: w.config(bg='#0c1428')
                except: pass
        def on_click(e, action=result['action']):
            try:
                action()
                win.destroy()
            except Exception as ex:
                show_system_notification('Search', f'Could not open: {ex}', kind='error')

        for w in all_widgets:
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
            w.bind('<Button-1>', on_click)
            w.bind('<Double-1>', on_click)

    def add_section_header(title, count):
        hf = tk.Frame(inner, bg='#060c18')
        hf.pack(fill='x', padx=0, pady=(6, 0))
        tk.Label(hf, text=f'  {title}', bg='#060c18', fg='#2a4a7a',
                 font=('Segoe UI', 9, 'bold')).pack(side='left', pady=3)
        tk.Label(hf, text=f'{count} result{"s" if count!=1 else ""}  ',
                 bg='#060c18', fg='#1a3060',
                 font=('Segoe UI', 8)).pack(side='right', pady=3)

    def add_web_suggestions(query):
        """Add web search suggestion cards at bottom."""
        if not query.strip():
            return
        web_card = tk.Frame(inner, bg='#0a1230', cursor='hand2')
        web_card.pack(fill='x', padx=8, pady=3, ipady=2)
        tk.Label(web_card, text='🌐', bg='#0a1230',
                 font=('Segoe UI Emoji', 14), width=3).pack(side='left', padx=12, pady=6)
        col = tk.Frame(web_card, bg='#0a1230')
        col.pack(side='left', fill='x', expand=True, pady=4)
        tk.Label(col, text=f'Search the web for "{query}"',
                 bg='#0a1230', fg='#4080ff',
                 font=('Segoe UI', 11, 'bold'), anchor='w').pack(anchor='w', padx=4)
        tk.Label(col, text='Opens in browser',
                 bg='#0a1230', fg='#1a3a5a',
                 font=('Segoe UI', 8), anchor='w').pack(anchor='w', padx=4)
        for w in web_card.winfo_children():
            w.bind('<Button-1>', lambda e, q=query: [
                webbrowser.open(f'https://www.google.com/search?q={urllib.parse.quote(q)}'),
                win.destroy()])

    def do_search(event=None):
        ensure_index()
        query = query_var.get().strip().lower()
        category = cat_var.get()
        clear_results()

        if not query:
            # Show recent / suggested when empty
            add_section_header('Quick Launch', 6)
            quick = ['calculator', 'notepad', 'settings', 'terminal',
                     'file explorer', 'paint']
            for q in quick:
                matches = [r for r in search_index if q in r['keywords']]
                if matches:
                    add_result_card(matches[0])
            status_lbl.config(text='Type to search across all your apps and files')
            return

        # Filter by category and query
        results = []
        for r in search_index:
            if category != 'All' and r['category'] != category:
                continue
            if query in r['keywords'] or query in r['title'].lower():
                results.append(r)

        # Group by category
        from collections import defaultdict
        grouped = defaultdict(list)
        for r in results:
            grouped[r['category']].append(r)

        total = 0
        cat_order = ['Apps', 'Notes', 'Files', 'Settings', 'People']
        for cat in cat_order:
            items = grouped.get(cat, [])
            if not items:
                continue
            add_section_header(cat, len(items))
            for item in items[:6]:  # max 6 per category
                add_result_card(item)
                total += 1

        # Web suggestions
        if category in ('All', 'Web'):
            add_section_header('Web', 1)
            add_web_suggestions(query)
            total += 1

        if total == 0:
            tk.Label(inner, text=f'No results for "{query}"',
                     bg='#080c18', fg='#2a4060',
                     font=('Segoe UI', 12)).pack(pady=40)
            tk.Label(inner, text='Try a different spelling or search the web below.',
                     bg='#080c18', fg='#1a3050',
                     font=('Segoe UI', 9)).pack()
            add_web_suggestions(query)

        status_lbl.config(text=f'{total} result{"s" if total!=1 else ""} for "{query}"')

    query_var.trace_add('write', lambda *a: win.after(120, do_search))
    search_e.bind('<Return>', lambda e: do_search())
    search_e.bind('<Escape>', lambda e: win.destroy())
    search_e.focus_set()
    do_search()

    # Mousewheel scroll
    def on_mousewheel(event):
        result_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
    result_canvas.bind('<MouseWheel>', on_mousewheel)
    inner.bind('<MouseWheel>', on_mousewheel)


# ── Hook Windows Search into APP_MAP and desktop shortcut ────────────────────
APP_MAP.update({
    'search':          lambda: show_windows_search(),
    'windows search':  lambda: show_windows_search(),
    'find':            lambda: show_windows_search(),
    'bsod':            lambda: show_bsod(),
    'blue screen':     lambda: show_bsod(),
    'crash':           lambda: show_bsod(),
})


# ══════════════════════════════════════════════════════════════════════════════
#  5 FUTURISTIC NEVER-BEFORE-SEEN FEATURES
# ══════════════════════════════════════════════════════════════════════════════

# ── F1: AI Conversation Replayer — watch your past chats as a cinematic replay
def show_conversation_replayer():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Conversation Replayer')
    win.geometry('760x520')
    style_aero_window(win, '#040810')
    center_window(win, 760, 520)

    tk.Label(win, text='🎬  Conversation Replayer',
             bg='#040810', fg='#80c8ff', font=('Segoe UI', 14, 'bold')).pack(pady=(12,2))
    tk.Label(win, text='Watch your AI conversations play back like a movie — cinematic mode.',
             bg='#040810', fg='#1a4060', font=('Segoe UI', 9)).pack()

    # Load conversation history from memory file
    history = []
    try:
        mem_path = MEMORY_FILE
        if os.path.exists(mem_path):
            with open(mem_path, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
            raw = data.get('conversations', data.get('history', []))
            for item in raw[:60]:
                if isinstance(item, dict):
                    role = item.get('role', 'user')
                    text = item.get('content', item.get('text', str(item)))
                    history.append((role, str(text)[:200]))
    except Exception:
        pass

    if not history:
        # Sample demo
        history = [
            ('user', 'Hello! Can you help me with Windows 7?'),
            ('assistant', 'Of course! I\'m your Windows 7 AI assistant. What do you need?'),
            ('user', 'How do I open the terminal?'),
            ('assistant', 'Click the Start button, find Terminal in the program list, or press Ctrl+Alt+T.'),
            ('user', 'Thanks! What about BIOS?'),
            ('assistant', 'Press F8 at boot, or go to Start → Shut down → BIOS from the arrow menu.'),
        ]

    # Cinema canvas
    cv = tk.Canvas(win, bg='#000000', highlightthickness=0)
    cv.pack(fill='both', expand=True, padx=12, pady=8)

    controls = tk.Frame(win, bg='#040810')
    controls.pack(fill='x', padx=12, pady=4)

    play_state = {'idx': -1, 'playing': False, 'job': None, 'speed': 40}

    def render_message(idx):
        if idx < 0 or idx >= len(history):
            return
        cv.delete('all')
        W = cv.winfo_width() or 736
        H = cv.winfo_height() or 360

        # Cinematic letterbox bars
        cv.create_rectangle(0, 0, W, 40, fill='#000000', outline='')
        cv.create_rectangle(0, H-40, W, H, fill='#000000', outline='')

        role, text = history[idx]
        is_user = role == 'user'

        # Background glow
        glow_col = '#001428' if is_user else '#140028'
        cv.create_rectangle(0, 40, W, H-40, fill=glow_col, outline='')

        # Speaker label
        speaker = '👤  You' if is_user else '🤖  Assistant'
        speaker_col = '#60a8ff' if is_user else '#a060ff'
        cv.create_text(W//2, 60, text=speaker,
                       fill=speaker_col, font=('Segoe UI', 11, 'bold'))

        # Message bubble
        bubble_w = int(W * 0.75)
        bx = (W - bubble_w) // 2
        bubble_col = '#0a2040' if is_user else '#1a0040'
        cv.create_rectangle(bx, 80, bx+bubble_w, H-60,
                            fill=bubble_col, outline=speaker_col, width=1)

        # Typewriter text
        shown = play_state.get('shown_chars', len(text))
        display_text = text[:shown]
        cv.create_text(bx+20, 100, text=display_text,
                       fill='white', font=('Segoe UI', 11),
                       anchor='nw', width=bubble_w-40)

        # Progress indicator
        if len(history) > 1:
            for i in range(len(history)):
                dot_x = W//2 + (i - len(history)//2) * 16
                col = speaker_col if i == idx else '#333333'
                cv.create_oval(dot_x-4, H-30, dot_x+4, H-22, fill=col, outline='')

        # Counter
        cv.create_text(W-20, H-25, text=f'{idx+1} / {len(history)}',
                       fill='#333333', font=('Consolas', 8), anchor='e')

    def typewriter_step(target_idx):
        if not win.winfo_exists():
            return
        text = history[target_idx][1]
        cur = play_state.get('shown_chars', 0)
        if cur < len(text):
            play_state['shown_chars'] = cur + 3
            render_message(target_idx)
            play_state['job'] = win.after(play_state['speed'],
                                          lambda: typewriter_step(target_idx))
        else:
            play_state['shown_chars'] = len(text)
            render_message(target_idx)
            if play_state['playing']:
                play_state['job'] = win.after(2200, advance)

    def advance():
        nxt = play_state['idx'] + 1
        if nxt >= len(history):
            play_state['playing'] = False
            play_btn.config(text='▶  Replay')
            return
        play_state['idx'] = nxt
        play_state['shown_chars'] = 0
        typewriter_step(nxt)

    def toggle_play():
        if play_state['playing']:
            play_state['playing'] = False
            if play_state['job']:
                try: win.after_cancel(play_state['job'])
                except: pass
            play_btn.config(text='▶  Play')
        else:
            play_state['playing'] = True
            play_btn.config(text='⏸  Pause')
            if play_state['idx'] < 0:
                play_state['idx'] = 0
            play_state['shown_chars'] = 0
            typewriter_step(play_state['idx'])

    def step_fwd():
        if play_state['idx'] + 1 < len(history):
            play_state['idx'] += 1
            play_state['shown_chars'] = len(history[play_state['idx']][1])
            render_message(play_state['idx'])

    def step_back():
        if play_state['idx'] > 0:
            play_state['idx'] -= 1
            play_state['shown_chars'] = len(history[play_state['idx']][1])
            render_message(play_state['idx'])

    play_btn = tk.Button(controls, text='▶  Play', bg='#0a3060', fg='#60a8ff',
                         relief='flat', font=('Segoe UI', 10, 'bold'),
                         command=toggle_play, padx=16, pady=4)
    play_btn.pack(side='left', padx=4)
    tk.Button(controls, text='◀', bg='#060e20', fg='#4080b0',
              relief='flat', font=('Segoe UI', 10), command=step_back).pack(side='left', padx=2)
    tk.Button(controls, text='▶', bg='#060e20', fg='#4080b0',
              relief='flat', font=('Segoe UI', 10), command=step_fwd).pack(side='left', padx=2)

    spd_lbl = tk.Label(controls, text='Speed:', bg='#040810', fg='#2a5a80',
                       font=('Segoe UI', 9))
    spd_lbl.pack(side='left', padx=(16,4))
    spd_scale = tk.Scale(controls, from_=5, to=120, orient='horizontal',
                         bg='#040810', fg='#60a8ff', highlightthickness=0,
                         troughcolor='#0a1828', length=100, showvalue=False,
                         command=lambda v: play_state.update({'speed': int(v)}))
    spd_scale.set(40)
    spd_scale.pack(side='left')

    cv.bind('<Configure>', lambda e: render_message(max(0, play_state['idx'])))
    win.after(200, lambda: render_message(0))
    play_state['idx'] = 0
    play_state['shown_chars'] = len(history[0][1])


# ── F2: Live System Heartbeat Monitor — animated real-time vitals ───────────
def show_system_heartbeat():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('System Heartbeat')
    win.geometry('820x500')
    style_aero_window(win, '#020608')
    center_window(win, 820, 500)

    tk.Label(win, text='💓  System Heartbeat Monitor',
             bg='#020608', fg='#ff4488', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Live animated vitals — like an ECG for your PC.',
             bg='#020608', fg='#3a1a28', font=('Segoe UI', 8)).pack()

    cv = tk.Canvas(win, bg='#010304', highlightthickness=0)
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    running = {'v': True}
    METRICS = {
        'CPU':    {'color':'#ff4488', 'history':[], 'label':'%',   'max':100},
        'RAM':    {'color':'#44aaff', 'history':[], 'label':'%',   'max':100},
        'Disk':   {'color':'#ffaa22', 'history':[], 'label':'MB/s','max':200},
        'Net':    {'color':'#44ffaa', 'history':[], 'label':'KB/s','max':1024},
        'Temp':   {'color':'#ff6622', 'history':[], 'label':'°C',  'max':100},
        'GPU':    {'color':'#aa44ff', 'history':[], 'label':'%',   'max':100},
    }
    MAX_POINTS = 80

    def get_live_values():
        try:
            cpu = psutil.cpu_percent(interval=None) if psutil else random.uniform(10,60)
        except Exception:
            cpu = random.uniform(10, 60)
        try:
            ram = psutil.virtual_memory().percent if psutil else random.uniform(40,80)
        except Exception:
            ram = random.uniform(40, 80)
        return {
            'CPU':  cpu,
            'RAM':  ram,
            'Disk': random.uniform(0, 80),
            'Net':  random.uniform(0, 400),
            'Temp': random.uniform(35, 72),
            'GPU':  random.uniform(5, 90),
        }

    def draw_all():
        if not win.winfo_exists() or not running['v']:
            return
        W = cv.winfo_width() or 800
        H = cv.winfo_height() or 400
        cv.delete('all')

        # Background grid
        for gx in range(0, W, 40):
            cv.create_line(gx, 0, gx, H, fill='#040c10', width=1)
        for gy in range(0, H, 30):
            cv.create_line(0, gy, W, gy, fill='#040c10', width=1)

        # Collect new data point
        vals = get_live_values()
        for name, meta in METRICS.items():
            meta['history'].append(vals[name])
            if len(meta['history']) > MAX_POINTS:
                meta['history'].pop(0)

        # Draw each metric as a separate panel row
        n = len(METRICS)
        panel_h = H // n
        for row_i, (name, meta) in enumerate(METRICS.items()):
            py = row_i * panel_h
            color = meta['color']
            history = meta['history']
            max_val = meta['max']

            # Panel background
            cv.create_rectangle(0, py, W, py+panel_h, fill='#010205', outline='#050d14')

            # Label
            cur_val = history[-1] if history else 0
            cv.create_text(8, py+8, text=name, fill=color,
                           font=('Consolas', 8, 'bold'), anchor='nw')
            cv.create_text(8, py+18, text=f'{cur_val:.1f}{meta["label"]}',
                           fill=color, font=('Consolas', 7), anchor='nw')

            # ECG-style line
            if len(history) >= 2:
                pts = []
                for i, v in enumerate(history):
                    x = int(50 + i * (W-60) / MAX_POINTS)
                    y = int(py + panel_h - 4 - (v / max_val) * (panel_h-12))
                    pts.extend([x, y])
                if len(pts) >= 4:
                    cv.create_line(*pts, fill=color, width=1, smooth=True)

                # Glow effect — draw twice with wider stroke at lower opacity
                if len(pts) >= 4:
                    cv.create_line(*pts, fill=color, width=3,
                                   smooth=True, stipple='gray25')

            # Current value bar
            bar_w = int((cur_val / max_val) * 40)
            cv.create_rectangle(W-48, py+4, W-8, py+panel_h-4,
                                fill='#030810', outline=color, width=1)
            cv.create_rectangle(W-48, py+panel_h-4-bar_w,
                                W-8, py+panel_h-4,
                                fill=color, outline='')

        # Heartbeat pulse flash on CPU spike
        cpu_val = vals['CPU']
        if cpu_val > 80:
            cv.create_rectangle(0, 0, W, H, fill='#ff000008', outline='')

        win.after(600, draw_all)

    cv.bind('<Configure>', lambda e: draw_all())
    draw_all()
    win.protocol('WM_DELETE_WINDOW',
                 lambda: [running.update({'v': False}), win.destroy()])


# ── F3: Code Diff Viewer — paste two blocks, see differences highlighted ─────
def show_code_diff():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Code Diff Viewer')
    win.geometry('900x560')
    style_aero_window(win, '#050a0e')
    center_window(win, 900, 560)

    tk.Label(win, text='🔀  Code Diff Viewer  —  Live Compare',
             bg='#050a0e', fg='#60e0a0', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))

    panes = tk.Frame(win, bg='#050a0e')
    panes.pack(fill='both', expand=True, padx=8, pady=4)

    def make_pane(parent, label, bg_color, side):
        frame = tk.Frame(parent, bg=bg_color)
        frame.pack(side=side, fill='both', expand=True,
                   padx=(0 if side=='right' else 0, 0))
        tk.Label(frame, text=label, bg=bg_color, fg='#336633' if 'Old' in label else '#003366',
                 font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=6, pady=2)
        txt = tk.Text(frame, font=('Consolas', 9), bg='#030810' if 'Old' in label else '#030810',
                      fg='#c8e0c8' if 'Old' in label else '#c8c8e8',
                      wrap='none', relief='flat', undo=True,
                      insertbackground='white',
                      highlightthickness=1, highlightbackground='#1a3a1a')
        txt.pack(fill='both', expand=True, padx=4, pady=(0,4))
        txt.tag_config('removed', background='#3a0a0a', foreground='#ff8888')
        txt.tag_config('added',   background='#0a2a0a', foreground='#88ff88')
        txt.tag_config('changed', background='#2a2a00', foreground='#ffff88')
        txt.tag_config('same',    foreground='#668866' if 'Old' in label else '#6688aa')
        return txt

    left_txt  = make_pane(panes, '  ← Old Version', '#020a04', 'left')
    div = tk.Frame(panes, bg='#1a3a1a', width=2)
    div.pack(side='left', fill='y')
    right_txt = make_pane(panes, '  New Version →', '#02040a', 'right')

    left_txt.insert('1.0', '''def greet(name):
    print("Hello, " + name)
    return True

def add(a, b):
    return a + b

x = add(1, 2)
''')
    right_txt.insert('1.0', '''def greet(name, greeting="Hello"):
    message = f"{greeting}, {name}!"
    print(message)
    return message

def add(a, b, c=0):
    return a + b + c

result = add(1, 2, 3)
''')

    stats_lbl = tk.Label(win, text='', bg='#050a0e', fg='#2a6a3a',
                         font=('Consolas', 9))
    stats_lbl.pack(pady=2)

    def do_diff(event=None):
        old_lines = left_txt.get('1.0', 'end-1c').splitlines()
        new_lines = right_txt.get('1.0', 'end-1c').splitlines()

        import difflib
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        left_txt.config(state='normal')
        right_txt.config(state='normal')
        for tag in ('removed','added','changed','same'):
            left_txt.tag_remove(tag, '1.0', 'end')
            right_txt.tag_remove(tag, '1.0', 'end')

        added = removed = changed = same = 0
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == 'equal':
                for li in range(i1, i2):
                    left_txt.tag_add('same', f'{li+1}.0', f'{li+2}.0')
                for lj in range(j1, j2):
                    right_txt.tag_add('same', f'{lj+1}.0', f'{lj+2}.0')
                same += i2 - i1
            elif op == 'replace':
                for li in range(i1, i2):
                    left_txt.tag_add('changed', f'{li+1}.0', f'{li+2}.0')
                for lj in range(j1, j2):
                    right_txt.tag_add('changed', f'{lj+1}.0', f'{lj+2}.0')
                changed += max(i2-i1, j2-j1)
            elif op == 'delete':
                for li in range(i1, i2):
                    left_txt.tag_add('removed', f'{li+1}.0', f'{li+2}.0')
                removed += i2 - i1
            elif op == 'insert':
                for lj in range(j1, j2):
                    right_txt.tag_add('added', f'{lj+1}.0', f'{lj+2}.0')
                added += j2 - j1

        stats_lbl.config(
            text=f'  ✅ {same} unchanged   ➕ {added} added   '
                 f'➖ {removed} removed   🔄 {changed} changed')

    bf = tk.Frame(win, bg='#050a0e')
    bf.pack(pady=4)
    tk.Button(bf, text='Compare', bg='#0a3020', fg='#60e0a0',
              relief='flat', font=('Segoe UI', 10, 'bold'),
              command=do_diff).pack(side='left', padx=6)
    tk.Label(bf, text='Edit either pane and click Compare, or paste your own code.',
             bg='#050a0e', fg='#1a4a2a', font=('Segoe UI', 8)).pack(side='left', padx=8)
    left_txt.bind('<KeyRelease>', lambda e: win.after(400, do_diff))
    right_txt.bind('<KeyRelease>', lambda e: win.after(400, do_diff))
    win.after(300, do_diff)


# ── F4: Time Capsule — write a note to your future self, set open date ───────
def show_time_capsule():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Time Capsule')
    win.geometry('600x500')
    style_aero_window(win, '#06080e')
    center_window(win, 600, 500)

    tk.Label(win, text='⏳  Time Capsule',
             bg='#06080e', fg='#c0a060', font=('Segoe UI', 14, 'bold')).pack(pady=(14,2))
    tk.Label(win, text='Write a message to your future self. Set a date. Lock it.',
             bg='#06080e', fg='#3a2a10', font=('Segoe UI', 9)).pack()

    capsules = state.setdefault('time_capsules', [])

    # Left: create new
    left = tk.Frame(win, bg='#06080e')
    left.pack(side='left', fill='both', expand=True, padx=(16,4), pady=10)

    tk.Label(left, text='Create New Capsule:', bg='#06080e', fg='#8a7040',
             font=('Segoe UI', 10, 'bold')).pack(anchor='w')

    tk.Label(left, text='Title:', bg='#06080e', fg='#5a4020',
             font=('Segoe UI', 9)).pack(anchor='w', pady=(8,0))
    title_var = tk.StringVar(value='My Time Capsule')
    tk.Entry(left, textvariable=title_var, bg='#0c0e14', fg='#c0a060',
             insertbackground='#c0a060', font=('Segoe UI', 10),
             relief='flat', highlightthickness=2,
             highlightbackground='#3a2a00').pack(fill='x', ipady=4)

    tk.Label(left, text='Open date (YYYY-MM-DD):', bg='#06080e', fg='#5a4020',
             font=('Segoe UI', 9)).pack(anchor='w', pady=(8,0))
    date_var = tk.StringVar(
        value=(datetime.now().replace(year=datetime.now().year+1)).strftime('%Y-%m-%d'))
    tk.Entry(left, textvariable=date_var, bg='#0c0e14', fg='#c0a060',
             insertbackground='#c0a060', font=('Segoe UI', 10),
             relief='flat', highlightthickness=2,
             highlightbackground='#3a2a00').pack(fill='x', ipady=4)

    tk.Label(left, text='Your message:', bg='#06080e', fg='#5a4020',
             font=('Segoe UI', 9)).pack(anchor='w', pady=(8,0))
    msg_text = tk.Text(left, height=8, bg='#060810', fg='#d0b870',
                       font=('Segoe UI', 10), wrap='word', relief='flat',
                       insertbackground='#c0a060',
                       highlightthickness=2, highlightbackground='#3a2a00')
    msg_text.pack(fill='both', expand=True)
    msg_text.insert('1.0', 'Dear future me,\n\nI am writing this on '
                    + datetime.now().strftime('%B %d, %Y') + '...')

    status_lbl = tk.Label(left, text='', bg='#06080e',
                          font=('Segoe UI', 9, 'bold'))
    status_lbl.pack(pady=4)

    # Right: list capsules
    right = tk.Frame(win, bg='#0a0c10', width=200)
    right.pack(side='right', fill='y', padx=(4,14), pady=10)
    right.pack_propagate(False)

    tk.Label(right, text='Capsules:', bg='#0a0c10', fg='#6a5030',
             font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=6, pady=(8,2))

    lb = tk.Listbox(right, bg='#060810', fg='#c0a060', font=('Segoe UI', 9),
                    selectmode='single', relief='flat', bd=0,
                    selectbackground='#2a1800', activestyle='none')
    lb.pack(fill='both', expand=True, padx=4, pady=4)

    def refresh_list():
        lb.delete(0, 'end')
        today = datetime.now().strftime('%Y-%m-%d')
        for i, cap in enumerate(capsules):
            open_date = cap.get('open_date', '')
            locked = cap.get('locked', False)
            past = open_date <= today
            icon = '🔓' if (past or not locked) else '🔒'
            lb.insert('end', f'{icon} {cap.get("title","?")[:18]}')
            lb.itemconfig(i, fg='#80e040' if past else '#c0a060')

    def seal_capsule():
        title = title_var.get().strip()
        msg = msg_text.get('1.0', 'end').strip()
        date_str = date_var.get().strip()
        if not title or not msg:
            status_lbl.config(text='⚠ Title and message required.', fg='#cc6020')
            return
        capsules.append({
            'title': title,
            'message': msg,
            'open_date': date_str,
            'created': datetime.now().isoformat(),
            'locked': True,
        })
        save_state()
        play_windows7_asterisk()
        status_lbl.config(text=f'✅ Capsule sealed! Opens {date_str}', fg='#80e040')
        refresh_list()

    def open_capsule():
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        cap = capsules[idx]
        today = datetime.now().strftime('%Y-%m-%d')
        if cap.get('locked') and cap.get('open_date', '') > today:
            remaining = cap['open_date']
            messagebox.showinfo('Locked',
                f'This capsule is sealed until {remaining}.\n\nBe patient!',
                parent=win)
            return
        msg = cap.get('message', '')
        created = cap.get('created', '')[:10]
        messagebox.showinfo(f'Time Capsule: {cap.get("title","")}',
                            f'Written on: {created}\n\n{msg}',
                            parent=win)

    refresh_list()
    bf = tk.Frame(left, bg='#06080e')
    bf.pack(fill='x', pady=2)
    tk.Button(bf, text='🔒 Seal Capsule', bg='#2a1800', fg='#c0a060',
              relief='flat', font=('Segoe UI', 9, 'bold'),
              command=seal_capsule).pack(side='left', padx=4)
    tk.Button(right, text='Open Selected', bg='#1a1000', fg='#80e040',
              relief='flat', font=('Segoe UI', 8),
              command=open_capsule).pack(side='bottom', pady=4)


# ── F5: Pixel Art Editor — draw pixel art, animate frames ───────────────────
def show_pixel_art_editor():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Pixel Art Editor')
    win.geometry('820x580')
    style_aero_window(win, '#060810')
    center_window(win, 820, 580)

    tk.Label(win, text='🎨  Pixel Art Editor',
             bg='#060810', fg='#ff80c0', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))

    GRID_W, GRID_H = 24, 24
    CELL = 18
    pixels = [['#000000'] * GRID_W for _ in range(GRID_H)]
    cur_color = {'v': '#ff80c0'}
    frames = [[[row[:] for row in pixels]]]  # animation frames
    cur_frame = {'v': 0}

    PALETTE = [
        '#000000','#ffffff','#ff0000','#00ff00','#0000ff','#ffff00',
        '#ff8800','#ff00ff','#00ffff','#880000','#008800','#000088',
        '#888800','#880088','#008888','#888888','#ff80c0','#80ffff',
        '#c0c060','#6080ff','#ff6040','#40e0a0','#a060ff','#ffcc80',
    ]

    main_frame = tk.Frame(win, bg='#060810')
    main_frame.pack(fill='both', expand=True, padx=8, pady=4)

    # Canvas for pixel grid
    cv = tk.Canvas(main_frame, width=GRID_W*CELL, height=GRID_H*CELL,
                   bg='#111111', highlightthickness=2,
                   highlightbackground='#3a2a4a', cursor='crosshair')
    cv.pack(side='left')

    # Right sidebar
    sidebar = tk.Frame(main_frame, bg='#060810', width=180)
    sidebar.pack(side='left', fill='y', padx=(8,0))
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text='Color Palette', bg='#060810', fg='#886688',
             font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(4,2))

    pal_frame = tk.Frame(sidebar, bg='#060810')
    pal_frame.pack(fill='x')
    cur_preview = tk.Label(sidebar, text='  ', bg=cur_color['v'], width=8,
                           height=2, relief='ridge', bd=2)
    cur_preview.pack(pady=4)
    tk.Label(sidebar, text='Current color', bg='#060810', fg='#4a3a4a',
             font=('Segoe UI', 7)).pack()

    def set_color(col):
        cur_color['v'] = col
        cur_preview.config(bg=col)

    for i, col in enumerate(PALETTE):
        btn = tk.Label(pal_frame, bg=col, width=2, height=1, cursor='hand2',
                       relief='raised', bd=1)
        btn.grid(row=i//6, column=i%6, padx=1, pady=1)
        btn.bind('<Button-1>', lambda e, c=col: set_color(c))

    # Custom color
    tk.Button(sidebar, text='Custom Color', bg='#1a0a2a', fg='#c080ff',
              relief='flat', font=('Segoe UI', 8),
              command=lambda: [
                  set_color(colorchooser.askcolor(
                      title='Pick Color', parent=win)[1] or cur_color['v'])
                  if hasattr(tk, 'colorchooser') else None
              ]).pack(fill='x', padx=4, pady=4)

    tk.Frame(sidebar, bg='#2a1a3a', height=1).pack(fill='x', pady=4)
    tk.Label(sidebar, text='Tools', bg='#060810', fg='#886688',
             font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=2)

    tool = {'v': 'draw'}
    tool_btns = {}

    def set_tool(t):
        tool['v'] = t
        for nt, btn in tool_btns.items():
            btn.config(relief='sunken' if nt == t else 'raised',
                       bg='#3a1a4a' if nt == t else '#1a0a2a')

    for t_name, t_icon in [('draw','✏ Draw'),('erase','⬜ Erase'),
                            ('fill','🪣 Fill'),('pick','💉 Pick')]:
        b = tk.Button(sidebar, text=t_icon, bg='#1a0a2a', fg='#c080ff',
                      relief='raised', font=('Segoe UI', 8), anchor='w',
                      command=lambda t=t_name: set_tool(t))
        b.pack(fill='x', padx=4, pady=1)
        tool_btns[t_name] = b

    def draw_grid():
        cv.delete('all')
        for row in range(GRID_H):
            for col in range(GRID_W):
                x1, y1 = col*CELL, row*CELL
                col_val = pixels[row][col]
                cv.create_rectangle(x1, y1, x1+CELL, y1+CELL,
                                    fill=col_val, outline='#1a1a2a', width=1)

    def flood_fill(r, c, target, replacement):
        if target == replacement:
            return
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if 0 <= cr < GRID_H and 0 <= cc < GRID_W:
                if pixels[cr][cc] == target:
                    pixels[cr][cc] = replacement
                    stack.extend([(cr+1,cc),(cr-1,cc),(cr,cc+1),(cr,cc-1)])

    def on_click(event, btn=1):
        col_i = event.x // CELL
        row_i = event.y // CELL
        if not (0 <= row_i < GRID_H and 0 <= col_i < GRID_W):
            return
        t = tool['v']
        if t == 'draw' or (t == 'erase' and btn == 1):
            pixels[row_i][col_i] = '#000000' if t == 'erase' else cur_color['v']
        elif t == 'fill':
            target_col = pixels[row_i][col_i]
            flood_fill(row_i, col_i, target_col, cur_color['v'])
        elif t == 'pick':
            set_color(pixels[row_i][col_i])
            return
        draw_grid()

    cv.bind('<Button-1>', lambda e: on_click(e, 1))
    cv.bind('<B1-Motion>', lambda e: on_click(e, 1))
    cv.bind('<Button-3>', lambda e: [pixels.__setitem__(
        e.y//CELL, [('#000000' if (0<=e.x//CELL<GRID_W) else c)
                    for ci, c in enumerate(pixels[e.y//CELL] if 0<=e.y//CELL<GRID_H else [])]),
        draw_grid()])

    def export_art():
        lines = []
        for row in pixels:
            lines.append(' '.join(row))
        path = filedialog.asksaveasfilename(
            defaultextension='.pixelart', title='Save Pixel Art',
            filetypes=[('Pixel Art','*.pixelart'),('Text','*.txt')])
        if path:
            with open(path, 'w') as f:
                f.write('\n'.join(lines))
            show_system_notification('Pixel Art', 'Saved!')

    def clear_canvas():
        for r in range(GRID_H):
            for c in range(GRID_W):
                pixels[r][c] = '#000000'
        draw_grid()

    bf = tk.Frame(win, bg='#060810')
    bf.pack(pady=4)
    tk.Button(bf, text='Clear', bg='#1a0010', fg='#ff8888', relief='flat',
              font=('Segoe UI', 9), command=clear_canvas).pack(side='left', padx=4)
    tk.Button(bf, text='Export', bg='#0a1020', fg='#8888ff', relief='flat',
              font=('Segoe UI', 9), command=export_art).pack(side='left', padx=4)

    draw_grid()
    try:
        from tkinter import colorchooser
    except ImportError:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  5 NEW SOFTWARE FEATURES
# ══════════════════════════════════════════════════════════════════════════════

# ── S1: Flashcard Study Deck ─────────────────────────────────────────────────
def show_flashcard_deck():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Flashcard Deck')
    win.geometry('580x420')
    style_aero_window(win, '#070c14')
    center_window(win, 580, 420)

    tk.Label(win, text='📚  Flashcard Study Deck',
             bg='#070c14', fg='#60d0ff', font=('Segoe UI', 13, 'bold')).pack(pady=(12,2))

    decks = state.setdefault('flashcard_decks', {
        'General': [
            {'q': 'What is the capital of France?', 'a': 'Paris'},
            {'q': 'What does CPU stand for?', 'a': 'Central Processing Unit'},
            {'q': 'What year was Windows 7 released?', 'a': '2009'},
        ]
    })
    cur_deck = {'name': list(decks.keys())[0]}
    cur_idx = {'v': 0}
    show_ans = {'v': False}
    score = {'correct': 0, 'wrong': 0}

    # Card canvas
    cv = tk.Canvas(win, width=520, height=200, bg='#0a1020',
                   highlightthickness=2, highlightbackground='#1a3a6a')
    cv.pack(pady=8)

    def draw_card():
        cv.delete('all')
        cards = decks.get(cur_deck['name'], [])
        if not cards:
            cv.create_text(260, 100, text='No cards in this deck.',
                           fill='#2a4a6a', font=('Segoe UI', 13))
            return
        idx = cur_idx['v'] % len(cards)
        card = cards[idx]
        # Card bg
        cv.create_rectangle(10, 10, 510, 190, fill='#0d1a30',
                            outline='#2a4a8a', width=2)
        # Side indicator
        side = 'Answer' if show_ans['v'] else 'Question'
        color = '#ff8844' if show_ans['v'] else '#60d0ff'
        cv.create_text(260, 30, text=side.upper(),
                       fill=color, font=('Consolas', 9, 'bold'))
        text = card['a'] if show_ans['v'] else card['q']
        cv.create_text(260, 105, text=text,
                       fill='white', font=('Segoe UI', 13),
                       width=460, justify='center')
        cv.create_text(470, 180, text=f'{idx+1}/{len(cards)}',
                       fill='#1a3a6a', font=('Consolas', 8))

    draw_card()

    stats_lbl = tk.Label(win, text='✅ 0  ❌ 0', bg='#070c14',
                         fg='#4a8a6a', font=('Segoe UI', 9))
    stats_lbl.pack()

    def flip():
        show_ans['v'] = not show_ans['v']
        draw_card()

    def mark(correct):
        show_ans['v'] = False
        if correct:
            score['correct'] += 1
        else:
            score['wrong'] += 1
        stats_lbl.config(
            text=f'✅ {score["correct"]}  ❌ {score["wrong"]}')
        cur_idx['v'] = (cur_idx['v'] + 1) % max(1,
            len(decks.get(cur_deck['name'], [1])))
        draw_card()

    bf = tk.Frame(win, bg='#070c14')
    bf.pack(pady=6)
    tk.Button(bf, text='Flip Card', bg='#0a3060', fg='#60d0ff',
              relief='flat', font=('Segoe UI', 10, 'bold'),
              command=flip).pack(side='left', padx=6)
    tk.Button(bf, text='✅ Got it', bg='#0a3020', fg='#60e080',
              relief='flat', font=('Segoe UI', 10),
              command=lambda: mark(True)).pack(side='left', padx=4)
    tk.Button(bf, text='❌ Missed', bg='#300a0a', fg='#ff8060',
              relief='flat', font=('Segoe UI', 10),
              command=lambda: mark(False)).pack(side='left', padx=4)
    win.bind('<space>', lambda e: flip())

    # Add card form
    tk.Frame(win, bg='#0d1828', height=1).pack(fill='x', padx=16, pady=4)
    add_frame = tk.Frame(win, bg='#070c14')
    add_frame.pack(fill='x', padx=16, pady=2)
    q_var = tk.StringVar(value='Question')
    a_var = tk.StringVar(value='Answer')
    tk.Entry(add_frame, textvariable=q_var, bg='#0a1020', fg='#60d0ff',
             insertbackground='#60d0ff', font=('Segoe UI', 9),
             relief='flat', highlightthickness=1,
             highlightbackground='#1a3a6a', width=24).pack(side='left', padx=2, ipady=3)
    tk.Entry(add_frame, textvariable=a_var, bg='#0a1020', fg='#80d0c0',
             insertbackground='#80d0c0', font=('Segoe UI', 9),
             relief='flat', highlightthickness=1,
             highlightbackground='#1a4a3a', width=24).pack(side='left', padx=2, ipady=3)

    def add_card():
        q = q_var.get().strip(); a = a_var.get().strip()
        if q and a:
            decks[cur_deck['name']].append({'q': q, 'a': a})
            save_state()
            q_var.set(''); a_var.set('')
            draw_card()

    tk.Button(add_frame, text='Add', bg='#0a3060', fg='#60d0ff',
              relief='flat', font=('Segoe UI', 9),
              command=add_card).pack(side='left', padx=4)


# ── S2: Budget Tracker ────────────────────────────────────────────────────────
def show_budget_tracker():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Budget Tracker')
    win.geometry('620x500')
    style_aero_window(win, '#060a08')
    center_window(win, 620, 500)

    tk.Label(win, text='💰  Budget Tracker',
             bg='#060a08', fg='#60e888', font=('Segoe UI', 13, 'bold')).pack(pady=(12,2))

    transactions = state.setdefault('budget_transactions', [])
    budget_limit = state.setdefault('budget_limit', 5000)

    # Summary bar
    sum_frame = tk.Frame(win, bg='#08100a')
    sum_frame.pack(fill='x', padx=16, pady=4)

    income_lbl = tk.Label(sum_frame, text='Income: ₹0', bg='#08100a',
                          fg='#60e888', font=('Segoe UI', 11, 'bold'))
    income_lbl.pack(side='left', expand=True)
    spend_lbl = tk.Label(sum_frame, text='Spent: ₹0', bg='#08100a',
                         fg='#ff6060', font=('Segoe UI', 11, 'bold'))
    spend_lbl.pack(side='left', expand=True)
    bal_lbl = tk.Label(sum_frame, text='Balance: ₹0', bg='#08100a',
                       fg='#60d0ff', font=('Segoe UI', 11, 'bold'))
    bal_lbl.pack(side='left', expand=True)

    # Bar chart canvas
    chart_cv = tk.Canvas(win, height=100, bg='#030806', highlightthickness=0)
    chart_cv.pack(fill='x', padx=16, pady=4)

    def update_summary():
        income = sum(t['amount'] for t in transactions if t['amount'] > 0)
        expense = sum(-t['amount'] for t in transactions if t['amount'] < 0)
        balance = income - expense
        income_lbl.config(text=f'Income: ₹{income:,.0f}')
        spend_lbl.config(text=f'Spent: ₹{expense:,.0f}')
        bal_lbl.config(text=f'Balance: ₹{balance:,.0f}',
                       fg='#60e888' if balance >= 0 else '#ff6060')
        # Category bar chart
        chart_cv.delete('all')
        cats = {}
        for t in transactions:
            if t['amount'] < 0:
                c = t.get('category', 'Other')
                cats[c] = cats.get(c, 0) + abs(t['amount'])
        if cats:
            W = chart_cv.winfo_width() or 580
            max_v = max(cats.values())
            bar_w = max(20, (W - 40) // len(cats))
            for i, (cat, val) in enumerate(cats.items()):
                x = 20 + i * bar_w
                bar_h = int((val / max_v) * 80)
                col = ['#ff6060','#ffaa40','#60d0ff','#60e888',
                       '#a060ff','#ffff60'][i % 6]
                chart_cv.create_rectangle(x, 100-bar_h, x+bar_w-4, 100,
                                         fill=col, outline='')
                chart_cv.create_text(x+bar_w//2-2, 95,
                                     text=cat[:6], fill='white',
                                     font=('Consolas', 6), anchor='s')

    # Transaction list
    lb_frame = tk.Frame(win, bg='#060a08')
    lb_frame.pack(fill='both', expand=True, padx=16, pady=4)
    lb = tk.Listbox(lb_frame, bg='#040806', fg='#88cc88',
                    font=('Consolas', 9), selectmode='single',
                    relief='flat', bd=0, selectbackground='#1a3a20',
                    activestyle='none')
    lb_sb = ttk.Scrollbar(lb_frame, command=lb.yview)
    lb.config(yscrollcommand=lb_sb.set)
    lb_sb.pack(side='right', fill='y')
    lb.pack(fill='both', expand=True)

    CATS = ['Food','Transport','Shopping','Bills','Income','Entertainment','Other']

    def refresh_lb():
        lb.delete(0, 'end')
        for t in reversed(transactions[-50:]):
            amt = t['amount']
            sign = '+' if amt > 0 else ''
            col_tag = '#60e888' if amt > 0 else '#ff8060'
            lb.insert('end',
                      f"  {t.get('date','')[:10]}  {t.get('desc','')[:20]:<22}"
                      f"  {t.get('category',''):<12}  {sign}₹{abs(amt):,.0f}")
            lb.itemconfig('end', fg=col_tag)
        update_summary()

    # Add transaction
    add_frame = tk.Frame(win, bg='#060a08')
    add_frame.pack(fill='x', padx=16, pady=4)

    desc_var = tk.StringVar(value='Description')
    amt_var = tk.StringVar(value='0')
    cat_var = tk.StringVar(value=CATS[0])

    tk.Entry(add_frame, textvariable=desc_var, width=18,
             bg='#0a100c', fg='#88cc88', insertbackground='#88cc88',
             font=('Segoe UI', 9), relief='flat',
             highlightthickness=1,
             highlightbackground='#1a3a20').pack(side='left', padx=2, ipady=3)
    tk.Entry(add_frame, textvariable=amt_var, width=8,
             bg='#0a100c', fg='#88cc88', insertbackground='#88cc88',
             font=('Segoe UI', 9), relief='flat',
             highlightthickness=1,
             highlightbackground='#1a3a20').pack(side='left', padx=2, ipady=3)
    ttk.Combobox(add_frame, textvariable=cat_var, values=CATS,
                 state='readonly', width=10,
                 font=('Segoe UI', 9)).pack(side='left', padx=2)

    def add_tx(is_expense=True):
        desc = desc_var.get().strip()
        try:
            amt = float(amt_var.get())
        except ValueError:
            return
        if is_expense:
            amt = -abs(amt)
        transactions.append({
            'desc': desc, 'amount': amt,
            'category': cat_var.get(),
            'date': datetime.now().isoformat()
        })
        save_state()
        desc_var.set(''); amt_var.set('0')
        refresh_lb()

    tk.Button(add_frame, text='➖ Expense', bg='#3a0a0a', fg='#ff8060',
              relief='flat', font=('Segoe UI', 9),
              command=lambda: add_tx(True)).pack(side='left', padx=2)
    tk.Button(add_frame, text='➕ Income', bg='#0a2a0a', fg='#60e888',
              relief='flat', font=('Segoe UI', 9),
              command=lambda: add_tx(False)).pack(side='left', padx=2)

    refresh_lb()
    chart_cv.bind('<Configure>', lambda e: update_summary())


# ── S3: Learning Path Tracker ─────────────────────────────────────────────────
def show_learning_tracker():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Learning Path')
    win.geometry('600x500')
    style_aero_window(win, '#060a12')
    center_window(win, 600, 500)

    tk.Label(win, text='🎓  Learning Path Tracker',
             bg='#060a12', fg='#80c0ff', font=('Segoe UI', 13, 'bold')).pack(pady=(12,2))
    tk.Label(win, text='Track your skills, courses and progress milestones.',
             bg='#060a12', fg='#1a3050', font=('Segoe UI', 9)).pack()

    paths = state.setdefault('learning_paths', [
        {'name': 'Python', 'progress': 45, 'total': 100,
         'topics': ['Variables ✅','Functions ✅','OOP 🔄','Decorators ⬜','Async ⬜']},
        {'name': 'Windows 7 Dev', 'progress': 80, 'total': 100,
         'topics': ['Tkinter ✅','File I/O ✅','Threading ✅','BIOS Hacks ✅','BSOD ⬜']},
    ])

    cv = tk.Canvas(win, height=260, bg='#030608', highlightthickness=0)
    cv.pack(fill='x', padx=16, pady=8)

    sel = {'idx': 0}
    topic_frame = tk.Frame(win, bg='#060a12')
    topic_frame.pack(fill='x', padx=16, pady=4)

    def draw_paths():
        cv.delete('all')
        W = cv.winfo_width() or 568
        n = len(paths)
        step = max(1, W // n) if n else W

        for i, path in enumerate(paths):
            x = int(i * step + step//2)
            pct = path['progress'] / max(path['total'], 1)

            # Road line
            cv.create_line(x, 240, x, 40, fill='#0a1828', width=6)
            cv.create_line(x, 240, x, int(240 - pct * 200),
                           fill='#2060c0', width=4)

            # Milestone circles
            for mi in range(5):
                my = int(240 - mi * 50)
                reached = pct >= (mi / 4)
                col = '#4090e0' if reached else '#1a2a3a'
                cv.create_oval(x-10, my-10, x+10, my+10,
                               fill=col, outline='white' if reached else '#1a3a5a',
                               width=2)

            # Progress bubble
            py = int(240 - pct * 200)
            cv.create_oval(x-16, py-16, x+16, py+16,
                           fill='#0060c0', outline='#60b0ff', width=2)
            cv.create_text(x, py, text=f'{int(pct*100)}%',
                           fill='white', font=('Consolas', 8, 'bold'))

            # Label
            col = '#60b0ff' if i == sel['idx'] else '#2a5a90'
            cv.create_text(x, 256, text=path['name'][:12],
                           fill=col, font=('Segoe UI', 8, 'bold'))
            cv.tag_bind('all', '<Button-1>',
                        lambda e, ii=i: [sel.update({'idx': ii}),
                                         draw_paths(), show_topics()])

    def show_topics():
        for w in topic_frame.winfo_children():
            try: w.destroy()
            except: pass
        if not paths:
            return
        path = paths[sel['idx']]
        tk.Label(topic_frame, text=f'{path["name"]} — Topics:',
                 bg='#060a12', fg='#4090e0',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        for topic in path.get('topics', []):
            color = ('#60e888' if '✅' in topic else
                     '#ffcc44' if '🔄' in topic else '#555577')
            tk.Label(topic_frame, text=f'  {topic}',
                     bg='#060a12', fg=color,
                     font=('Segoe UI', 9)).pack(anchor='w')

        # Progress slider
        prog_frame = tk.Frame(win, bg='#060a12')
        prog_frame.pack(fill='x', padx=16, pady=2)
        tk.Label(prog_frame, text='Progress:',
                 bg='#060a12', fg='#2a5a90',
                 font=('Segoe UI', 9)).pack(side='left')
        prog_var = tk.IntVar(value=path['progress'])
        tk.Scale(prog_frame, variable=prog_var, from_=0, to=100,
                 orient='horizontal', bg='#060a12', fg='#60b0ff',
                 highlightthickness=0, troughcolor='#0a1020',
                 length=200, showvalue=True,
                 command=lambda v, p=path: [
                     p.update({'progress': int(float(v))}),
                     save_state(), draw_paths()]).pack(side='left', padx=8)

    def add_path():
        name = simpledialog.askstring('Add Path', 'Learning path name:', parent=win)
        if name:
            paths.append({'name': name, 'progress': 0, 'total': 100,
                          'topics': []})
            save_state()
            draw_paths()
            show_topics()

    bf = tk.Frame(win, bg='#060a12')
    bf.pack(pady=4)
    tk.Button(bf, text='Add Path', bg='#0a2040', fg='#60b0ff',
              relief='flat', font=('Segoe UI', 9),
              command=add_path).pack(side='left', padx=6)

    cv.bind('<Configure>', lambda e: draw_paths())
    win.after(200, draw_paths)
    win.after(200, show_topics)

    cv.bind('<Button-1>', lambda e: [
        sel.update({'idx': max(0, min(len(paths)-1,
                    e.x // max(1, (cv.winfo_width() or 568) // max(1,len(paths)))))}),
        draw_paths(), show_topics()])


# ── S4: Personal Wiki ─────────────────────────────────────────────────────────
def show_personal_wiki():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Personal Wiki')
    win.geometry('780x560')
    style_aero_window(win, '#060c10')
    center_window(win, 780, 560)

    tk.Label(win, text='📖  Personal Wiki',
             bg='#060c10', fg='#80d0c0', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))

    wiki_pages = state.setdefault('wiki_pages', {
        'Home': '# Welcome to your Personal Wiki\n\nThis is your **personal knowledge base**.\n\nCreate pages, link ideas, build your second brain.\n\n## Quick Links\n- [[Python Notes]]\n- [[Windows 7 Tips]]',
        'Python Notes': '# Python Notes\n\n## Key Concepts\n- Variables store values\n- Functions are reusable code blocks\n- Classes are blueprints for objects\n\n## Code Snippets\n```\ndef hello(name):\n    return f"Hello, {name}!"\n```',
    })
    cur_page = {'name': 'Home'}

    panes = tk.Frame(win, bg='#060c10')
    panes.pack(fill='both', expand=True, padx=8, pady=4)

    # Left: page list
    left = tk.Frame(panes, bg='#030810', width=160)
    left.pack(side='left', fill='y')
    left.pack_propagate(False)
    tk.Label(left, text='Pages', bg='#030810', fg='#2a6a5a',
             font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=6, pady=(8,2))
    pg_lb = tk.Listbox(left, bg='#020608', fg='#60c0b0',
                       font=('Segoe UI', 9), selectmode='single',
                       relief='flat', bd=0,
                       selectbackground='#0a3028', activestyle='none')
    pg_lb.pack(fill='both', expand=True, padx=2, pady=2)

    # Right: editor + rendered view split
    right = tk.Frame(panes, bg='#060c10')
    right.pack(side='left', fill='both', expand=True, padx=(8,0))

    # Toolbar
    tb = tk.Frame(right, bg='#040a0e')
    tb.pack(fill='x')
    page_title_var = tk.StringVar(value='Home')
    tk.Entry(tb, textvariable=page_title_var, bg='#040a0e', fg='#80d0c0',
             insertbackground='#80d0c0', font=('Segoe UI', 11, 'bold'),
             relief='flat', highlightthickness=1,
             highlightbackground='#1a4a3a', width=28).pack(
             side='left', padx=6, ipady=4)

    edit_mode = {'v': True}
    mode_btn = tk.Button(tb, text='Preview', bg='#0a2820', fg='#60c0a0',
                         relief='flat', font=('Segoe UI', 8))
    mode_btn.pack(side='left', padx=4)

    editor = tk.Text(right, bg='#020a08', fg='#80d0c0',
                     font=('Consolas', 10), wrap='word', relief='flat',
                     insertbackground='#60c0a0',
                     highlightthickness=1, highlightbackground='#1a4a3a')
    editor.pack(fill='both', expand=True, padx=4, pady=4)

    editor.tag_config('h1', font=('Segoe UI', 16, 'bold'), foreground='#a0e8d8')
    editor.tag_config('h2', font=('Segoe UI', 13, 'bold'), foreground='#80c8b8')
    editor.tag_config('bold', font=('Consolas', 10, 'bold'))
    editor.tag_config('link', foreground='#40e8c8', underline=True)
    editor.tag_config('code', font=('Courier New', 9),
                      background='#0a1a18', foreground='#60e8b0')

    def load_page(name):
        cur_page['name'] = name
        page_title_var.set(name)
        editor.delete('1.0', 'end')
        content = wiki_pages.get(name, f'# {name}\n\nStart writing here...')
        editor.insert('1.0', content)
        highlight_md()

    def highlight_md(event=None):
        src = editor.get('1.0', 'end')
        for tag in ('h1','h2','bold','link','code'):
            editor.tag_remove(tag, '1.0', 'end')
        for i, line in enumerate(src.splitlines()):
            if line.startswith('# '):
                editor.tag_add('h1', f'{i+1}.0', f'{i+1}.end')
            elif line.startswith('## '):
                editor.tag_add('h2', f'{i+1}.0', f'{i+1}.end')
        # Bold **text**
        for m in re.finditer(r'\*\*[^*]+\*\*', src):
            start = f'1.0+{m.start()}c'
            end = f'1.0+{m.end()}c'
            editor.tag_add('bold', start, end)
        # Wiki links [[page]]
        for m in re.finditer(r'\[\[[^\]]+\]\]', src):
            start = f'1.0+{m.start()}c'
            end = f'1.0+{m.end()}c'
            editor.tag_add('link', start, end)

    def save_current():
        name = page_title_var.get().strip() or cur_page['name']
        wiki_pages[name] = editor.get('1.0', 'end-1c')
        cur_page['name'] = name
        save_state()
        refresh_pages()
        show_system_notification('Wiki', f'Saved: {name}')

    def refresh_pages():
        pg_lb.delete(0, 'end')
        for name in wiki_pages:
            pg_lb.insert('end', f'  {name}')
        # Select current
        for i, name in enumerate(wiki_pages):
            if name == cur_page['name']:
                pg_lb.selection_set(i)

    def on_page_select(event=None):
        sel = pg_lb.curselection()
        if sel:
            name = list(wiki_pages.keys())[sel[0]]
            load_page(name)

    def new_page():
        name = simpledialog.askstring('New Page', 'Page name:', parent=win)
        if name and name not in wiki_pages:
            wiki_pages[name] = f'# {name}\n\n'
            save_state()
            refresh_pages()
            load_page(name)

    pg_lb.bind('<<ListboxSelect>>', on_page_select)
    editor.bind('<KeyRelease>', highlight_md)
    editor.bind('<Control-s>', lambda e: save_current())

    bf = tk.Frame(right, bg='#060c10')
    bf.pack(fill='x', padx=4, pady=2)
    for txt, cmd in [('Save (Ctrl+S)', save_current), ('New Page', new_page)]:
        tk.Button(bf, text=txt, bg='#0a2820', fg='#60c0a0',
                  relief='flat', font=('Segoe UI', 8),
                  command=cmd).pack(side='left', padx=4)

    refresh_pages()
    load_page('Home')


# ── S5: Ambient Sound Machine ─────────────────────────────────────────────────
def show_ambient_sounds():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Ambient Sounds')
    win.geometry('500x400')
    style_aero_window(win, '#050810')
    center_window(win, 500, 400)

    tk.Label(win, text='🎵  Ambient Sound Machine',
             bg='#050810', fg='#80aaff', font=('Segoe UI', 13, 'bold')).pack(pady=(12,2))
    tk.Label(win, text='Layer ambient sounds for focus, sleep or relaxation.',
             bg='#050810', fg='#1a2a4a', font=('Segoe UI', 9)).pack()

    SOUNDS = [
        ('🌧 Rain',        '#4060a0'),
        ('⛈ Thunderstorm', '#304080'),
        ('🌊 Ocean Waves',  '#2060a0'),
        ('🔥 Fireplace',   '#804020'),
        ('🌿 Forest',      '#306040'),
        ('☕ Coffee Shop',  '#604030'),
        ('🌙 Night Crickets','#203040'),
        ('🌬 Wind',         '#304060'),
        ('🎵 White Noise',  '#404050'),
        ('🔔 Singing Bowl', '#505090'),
    ]

    playing = {}
    volumes = {}

    sound_frame = tk.Frame(win, bg='#050810')
    sound_frame.pack(fill='both', expand=True, padx=20, pady=10)

    for i, (name, color) in enumerate(SOUNDS):
        row_i, col_i = i // 2, i % 2
        card = tk.Frame(sound_frame, bg='#0a0e18', bd=1, relief='groove')
        card.grid(row=row_i, column=col_i, padx=6, pady=4, sticky='ew')
        sound_frame.columnconfigure(col_i, weight=1)

        is_playing = tk.BooleanVar(value=False)
        playing[name] = is_playing
        vol_var = tk.IntVar(value=60)
        volumes[name] = vol_var

        top_row = tk.Frame(card, bg='#0a0e18')
        top_row.pack(fill='x', padx=6, pady=(6,2))
        cb = tk.Checkbutton(top_row, text=name, variable=is_playing,
                            bg='#0a0e18', fg=color, activebackground='#0a0e18',
                            selectcolor='#060810', font=('Segoe UI', 9, 'bold'),
                            command=lambda n=name, v=is_playing: (
                                play_windows7_asterisk() if v.get() else
                                play_windows7_minimize()))
        cb.pack(side='left')

        # Animated equalizer bars (just decorative)
        eq_cv = tk.Canvas(top_row, width=30, height=16, bg='#0a0e18',
                          highlightthickness=0)
        eq_cv.pack(side='right', padx=4)

        def update_eq(cv=eq_cv, var=is_playing, col=color):
            if not win.winfo_exists():
                return
            cv.delete('all')
            if var.get():
                for bi in range(5):
                    bh = random.randint(4, 14)
                    cv.create_rectangle(bi*6, 16-bh, bi*6+4, 16,
                                       fill=col, outline='')
            win.after(200, update_eq)
        update_eq()

        # Volume
        vol_row = tk.Frame(card, bg='#0a0e18')
        vol_row.pack(fill='x', padx=6, pady=(0,4))
        tk.Label(vol_row, text='Vol:', bg='#0a0e18', fg='#2a3a5a',
                 font=('Segoe UI', 7)).pack(side='left')
        tk.Scale(vol_row, variable=vol_var, from_=0, to=100,
                 orient='horizontal', bg='#0a0e18', fg=color,
                 highlightthickness=0, troughcolor='#040608',
                 length=120, showvalue=False).pack(side='left')
        vol_val_lbl = tk.Label(vol_row, textvariable=vol_var,
                               bg='#0a0e18', fg='#2a4a6a',
                               font=('Consolas', 7), width=3)
        vol_val_lbl.pack(side='left')

    info_lbl = tk.Label(win,
                        text='Note: Visual simulation — actual audio requires platform audio libs.',
                        bg='#050810', fg='#1a2a3a', font=('Segoe UI', 7))
    info_lbl.pack(pady=4)

    def stop_all():
        for var in playing.values():
            var.set(False)
    tk.Button(win, text='Stop All', bg='#1a0a20', fg='#8888cc',
              relief='flat', font=('Segoe UI', 9),
              command=stop_all).pack(pady=4)


# ── Register everything in APP_MAP ────────────────────────────────────────────
APP_MAP.update({
    # Futuristic
    'conversation replayer': lambda: show_conversation_replayer(),
    'replayer':              lambda: show_conversation_replayer(),
    'heartbeat':             lambda: show_system_heartbeat(),
    'system heartbeat':      lambda: show_system_heartbeat(),
    'code diff':             lambda: show_code_diff(),
    'diff viewer':           lambda: show_code_diff(),
    'time capsule':          lambda: show_time_capsule(),
    'capsule':               lambda: show_time_capsule(),
    'pixel art':             lambda: show_pixel_art_editor(),
    'pixel editor':          lambda: show_pixel_art_editor(),
    # Software
    'flashcard':             lambda: show_flashcard_deck(),
    'flashcards':            lambda: show_flashcard_deck(),
    'study deck':            lambda: show_flashcard_deck(),
    'budget tracker':        lambda: show_budget_tracker(),
    'budget':                lambda: show_budget_tracker(),
    'expense':               lambda: show_budget_tracker(),
    'learning tracker':      lambda: show_learning_tracker(),
    'learning path':         lambda: show_learning_tracker(),
    'skills':                lambda: show_learning_tracker(),
    'wiki':                  lambda: show_personal_wiki(),
    'personal wiki':         lambda: show_personal_wiki(),
    'knowledge base':        lambda: show_personal_wiki(),
    'ambient':               lambda: show_ambient_sounds(),
    'ambient sounds':        lambda: show_ambient_sounds(),
    'soundscape':            lambda: show_ambient_sounds(),
})


# ══════════════════════════════════════════════════════════════════════════════
#  15 FUTURISTIC NEVER-SEEN FEATURES  — Tkinter at its limit
# ══════════════════════════════════════════════════════════════════════════════

# ── SHARED AERO CANVAS HELPERS ────────────────────────────────────────────────
def _aero_win(title, w, h, bg='#06080e'):
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title(title)
    win.geometry(f'{w}x{h}')
    style_aero_window(win, bg)
    center_window(win, w, h)
    return win

def _aero_canvas(parent, bg='#020508', **kw):
    cv = tk.Canvas(parent, bg=bg, highlightthickness=0, **kw)
    return cv

def _radial_gradient(cv, cx, cy, r, inner_col, outer_col, steps=40):
    """Draw a radial gradient circle on a canvas."""
    for i in range(steps, 0, -1):
        t = i / steps
        ri = int(int(inner_col[1:3],16)*(1-t) + int(outer_col[1:3],16)*t)
        gi = int(int(inner_col[3:5],16)*(1-t) + int(outer_col[3:5],16)*t)
        bi = int(int(inner_col[5:7],16)*(1-t) + int(outer_col[5:7],16)*t)
        cr = int(r * i / steps)
        cv.create_oval(cx-cr, cy-cr, cx+cr, cy+cr,
                       fill=f'#{ri:02x}{gi:02x}{bi:02x}', outline='')

def _aero_pill(cv, x1, y1, x2, y2, fill, outline='', width=1):
    """Pill-shaped (fully rounded ends) rectangle on canvas."""
    r = (y2 - y1) // 2
    cv.create_oval(x1, y1, x1+2*r, y2, fill=fill, outline=outline, width=width)
    cv.create_oval(x2-2*r, y1, x2, y2, fill=fill, outline=outline, width=width)
    cv.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline='')
    if outline:
        cv.create_arc(x1, y1, x1+2*r, y2, start=90, extent=180,
                      outline=outline, style='arc', width=width)
        cv.create_arc(x2-2*r, y1, x2, y2, start=270, extent=180,
                      outline=outline, style='arc', width=width)
        cv.create_line(x1+r, y1, x2-r, y1, fill=outline, width=width)
        cv.create_line(x1+r, y2, x2-r, y2, fill=outline, width=width)


# ── 1. Object-Oriented File System Viewer ─────────────────────────────────────
def show_oo_filesystem():
    win = _aero_win('OO File System', 900, 580, '#04060e')
    tk.Label(win, text='🧬  Object-Oriented File System',
             bg='#04060e', fg='#80ffcc', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Every file carries its own logic, render engine and security policy.',
             bg='#04060e', fg='#1a4a3a', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020408')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    OBJECTS = [
        {'name':'finance.xlsx','type':'SpreadsheetObject','color':'#40e888',
         'traits':['render()','calculate()','encrypt()','share()'],'x':150,'y':160},
        {'name':'photo.jpg','type':'ImageObject','color':'#ff8040',
         'traits':['render()','transform()','compress()','tag()'],'x':380,'y':120},
        {'name':'report.pdf','type':'DocumentObject','color':'#60a8ff',
         'traits':['render()','sign()','redact()','translate()'],'x':610,'y':160},
        {'name':'music.mp3','type':'AudioObject','color':'#e060ff',
         'traits':['play()','transcode()','visualize()','tag()'],'x':150,'y':360},
        {'name':'script.py','type':'CodeObject','color':'#ffcc40',
         'traits':['execute()','debug()','compile()','test()'],'x':380,'y':400},
        {'name':'key.cert','type':'CryptoObject','color':'#ff4060',
         'traits':['sign()','verify()','encrypt()','revoke()'],'x':610,'y':360},
    ]

    hover = {'obj': None}

    def draw(event=None):
        cv.delete('all')
        W = cv.winfo_width() or 880
        H = cv.winfo_height() or 460

        # Background grid
        for gx in range(0, W, 50):
            cv.create_line(gx, 0, gx, H, fill='#060c14', width=1)
        for gy in range(0, H, 50):
            cv.create_line(0, gy, W, gy, fill='#060c14', width=1)

        # Central kernel node
        ckx, cky = W//2, H//2
        _radial_gradient(cv, ckx, cky, 48, '#1a4a3a', '#030810', steps=30)
        cv.create_oval(ckx-48, cky-48, ckx+48, cky+48,
                       outline='#40e888', width=2)
        cv.create_text(ckx, cky-8, text='⚙', fill='#40e888',
                       font=('Segoe UI Emoji', 18))
        cv.create_text(ckx, cky+14, text='OO Kernel', fill='#40e888',
                       font=('Consolas', 8, 'bold'))

        for obj in OBJECTS:
            ox, oy = obj['x'], obj['y']
            col = obj['color']
            is_hover = hover['obj'] == obj['name']

            # Connection line to kernel
            cv.create_line(ox, oy, ckx, cky, fill=col,
                           width=2 if is_hover else 1,
                           dash='' if is_hover else (4,4))

            # Object bubble
            r = 46 if is_hover else 38
            _radial_gradient(cv, ox, oy, r, col+'33', '#020408', steps=20)
            cv.create_oval(ox-r, oy-r, ox+r, oy+r,
                           outline=col, width=3 if is_hover else 1)

            # File icon + name
            cv.create_text(ox, oy-6, text=obj['name'],
                           fill=col, font=('Consolas', 8, 'bold'))
            cv.create_text(ox, oy+8, text=obj['type'],
                           fill=col+'aa', font=('Consolas', 7))

            # Trait badges on hover
            if is_hover:
                for ti, trait in enumerate(obj['traits']):
                    tx = ox + (ti - 1.5) * 80
                    ty = oy - 70
                    _aero_pill(cv, int(tx-32), ty-10, int(tx+32), ty+10,
                               fill='#0a1828', outline=col)
                    cv.create_text(tx, ty, text=trait, fill=col,
                                   font=('Consolas', 7))

    def on_motion(e):
        for obj in OBJECTS:
            if abs(e.x - obj['x']) < 46 and abs(e.y - obj['y']) < 46:
                hover['obj'] = obj['name']
                draw(); return
        hover['obj'] = None
        draw()

    cv.bind('<Configure>', draw)
    cv.bind('<Motion>', on_motion)
    win.after(200, draw)


# ── 2. Temporal OS — System Time Slider ───────────────────────────────────────
def show_temporal_os():
    win = _aero_win('Temporal OS', 800, 500, '#04040e')
    tk.Label(win, text='⏰  Temporal OS  —  System-Wide Undo',
             bg='#04040e', fg='#c080ff', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Scroll back any part of your system to any previous state.',
             bg='#04040e', fg='#2a1a4a', font=('Segoe UI', 8)).pack()

    # Build a fake snapshot history
    snapshots = []
    now = datetime.now()
    for i in range(48):  # 48 snapshots = last 24 hours
        t = now.replace(minute=now.minute - i*30 % 60,
                        hour=now.hour - i*30//60)
        snapshots.append({
            'time': t.strftime('%H:%M:%S'),
            'cpu': random.randint(5, 90),
            'ram': random.randint(30, 85),
            'apps': random.randint(2, 12),
            'files': random.randint(0, 6),
            'event': random.choice(['','',' [sudo apt delete]',' [BSOD]',
                                    ' [File saved]',' [App opened]']),
        })

    cv = _aero_canvas(win, bg='#020208')
    cv.pack(fill='both', expand=True, padx=10, pady=4)

    slider_var = tk.IntVar(value=0)
    info_lbl = tk.Label(win, text='', bg='#04040e', fg='#c080ff',
                        font=('Segoe UI', 9, 'bold'))
    info_lbl.pack()
    slider = tk.Scale(win, variable=slider_var, from_=0, to=len(snapshots)-1,
                      orient='horizontal', bg='#04040e', fg='#c080ff',
                      highlightthickness=0, troughcolor='#0a0818',
                      length=700, showvalue=False,
                      command=lambda v: draw_temporal())
    slider.pack(padx=20, pady=4)

    def draw_temporal():
        cv.delete('all')
        W = cv.winfo_width() or 780
        H = cv.winfo_height() or 300
        idx = slider_var.get()

        # Timeline bar
        bar_y = H//2
        cv.create_line(30, bar_y, W-30, bar_y, fill='#2a1a4a', width=3)

        # Snapshot markers
        n = len(snapshots)
        step = (W-60) / max(n-1, 1)
        for i, snap in enumerate(snapshots):
            x = int(30 + i * step)
            col = '#c080ff' if i == idx else '#2a1a4a'
            is_event = snap['event'].strip()
            r = 10 if i == idx else (6 if is_event else 4)
            _radial_gradient(cv, x, bar_y, r+4,
                             col if i == idx else '#100820', '#02020e', steps=10)
            cv.create_oval(x-r, bar_y-r, x+r, bar_y+r,
                           fill=col, outline='white' if i == idx else '')
            if is_event:
                cv.create_text(x, bar_y-22, text='⚠',
                               fill='#ff8040', font=('Segoe UI Emoji', 9))

        # Current state panel
        snap = snapshots[idx]
        info_lbl.config(text=f'🕐 {snap["time"]}{snap["event"]}')

        # State meters
        meters = [
            ('CPU', snap['cpu'],   '#ff6040', 100),
            ('RAM', snap['ram'],   '#60a8ff', 100),
            ('Apps',snap['apps'],  '#40e888',  14),
            ('Files',snap['files'],'#ffcc40',   8),
        ]
        mx = 120
        for mi, (label, val, col, max_v) in enumerate(meters):
            mx2 = 120 + mi * 160
            my = bar_y + 60
            _radial_gradient(cv, mx2, my, 38, col+'22', '#02020e', steps=15)
            cv.create_oval(mx2-38, my-38, mx2+38, my+38,
                           outline=col, width=2)
            pct = val / max_v
            # Arc progress
            cv.create_arc(mx2-34, my-34, mx2+34, my+34,
                          start=90, extent=-int(pct*360),
                          outline=col, width=5, style='arc')
            cv.create_text(mx2, my-4, text=str(val),
                           fill=col, font=('Consolas', 11, 'bold'))
            cv.create_text(mx2, my+12, text=label,
                           fill=col+'88', font=('Consolas', 7))

    cv.bind('<Configure>', lambda e: draw_temporal())
    win.after(200, draw_temporal)

    bf = tk.Frame(win, bg='#04040e')
    bf.pack(pady=4)
    tk.Button(bf, text='↩  Restore This State', bg='#1a0840', fg='#c080ff',
              relief='flat', font=('Segoe UI', 10, 'bold'),
              command=lambda: show_system_notification(
                  'Temporal OS',
                  f'System state at {snapshots[slider_var.get()]["time"]} restored!'
              )).pack(side='left', padx=6)


# ── 3. Semantic Intent Interface ───────────────────────────────────────────────
def show_semantic_intent():
    win = _aero_win('Semantic UI', 820, 540, '#04080a')
    tk.Label(win, text='🧠  Semantic Intent Interface',
             bg='#04080a', fg='#40e8ff', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Describe what you want to DO — the OS builds the interface.',
             bg='#04080a', fg='#0a2a30', font=('Segoe UI', 8)).pack()

    inp_frame = tk.Frame(win, bg='#04080a')
    inp_frame.pack(fill='x', padx=20, pady=6)
    intent_var = tk.StringVar(value='calculate my monthly budget')
    inp_e = tk.Entry(inp_frame, textvariable=intent_var, font=('Segoe UI', 13),
                     bg='#020c10', fg='#40e8ff', insertbackground='#40e8ff',
                     relief='flat', highlightthickness=3,
                     highlightbackground='#0a4050',
                     highlightcolor='#40e8ff')
    inp_e.pack(side='left', fill='x', expand=True, ipady=8)
    tk.Button(inp_frame, text='⚡ Compile Interface', bg='#082030',
              fg='#40e8ff', relief='flat', font=('Segoe UI', 10, 'bold'),
              command=lambda: compile_intent()).pack(side='left', padx=8)

    cv = _aero_canvas(win, bg='#020608')
    cv.pack(fill='both', expand=True, padx=10, pady=4)

    INTENT_MAP = {
        'budget': [('💰','Input income','#40e888'), ('➖','Add expenses','#ff6040'),
                   ('📊','See chart','#60a8ff'), ('💾','Export CSV','#ffcc40')],
        'email':  [('✍','Compose','#60a8ff'), ('📎','Attach file','#ffcc40'),
                   ('👤','Add contact','#ff8040'), ('📤','Send','#40e888')],
        'photo':  [('📁','Open file','#ffcc40'), ('✂','Crop','#ff8040'),
                   ('🎨','Filter','#e060ff'), ('💾','Save','#40e888')],
        'code':   [('📝','Editor','#60a8ff'), ('▶','Run','#40e888'),
                   ('🐛','Debug','#ff6040'), ('📦','Deploy','#ffcc40')],
        'music':  [('🎵','Playlist','#e060ff'), ('▶','Play','#40e888'),
                   ('🔊','Volume','#60a8ff'), ('❤','Favourite','#ff4060')],
        'tax':    [('📋','Income form','#60a8ff'), ('🧮','Calculator','#40e888'),
                   ('📄','Generate report','#ffcc40'), ('📤','File online','#ff8040')],
    }

    compiled = {'widgets': []}
    anim_t = {'v': 0}

    def compile_intent():
        text = intent_var.get().lower()
        best_key = 'budget'
        for k in INTENT_MAP:
            if k in text:
                best_key = k; break
        widgets = INTENT_MAP[best_key]
        compiled['widgets'] = widgets
        anim_t['v'] = 0
        animate_compile()

    def animate_compile():
        cv.delete('all')
        W = cv.winfo_width() or 780
        H = cv.winfo_height() or 340
        t = anim_t['v']
        widgets = compiled['widgets']
        n = len(widgets)

        # Central intent bubble
        cx, cy = W//2, H//2
        pulse = 55 + 8 * math.sin(t * 0.2)
        _radial_gradient(cv, cx, cy, int(pulse), '#082030', '#020608', 20)
        cv.create_oval(cx-int(pulse), cy-int(pulse),
                       cx+int(pulse), cy+int(pulse),
                       outline='#40e8ff', width=2)
        cv.create_text(cx, cy-6, text='Intent', fill='#40e8ff',
                       font=('Segoe UI', 9, 'bold'))
        cv.create_text(cx, cy+8, text=intent_var.get()[:20],
                       fill='#40e8ff88', font=('Consolas', 7))

        # Orbiting compiled widgets
        for i, (icon, label, col) in enumerate(widgets):
            angle = math.radians(i * 360/n + t * 2)
            orbit_r = 140
            wx = int(cx + orbit_r * math.cos(angle))
            wy = int(cy + orbit_r * math.sin(angle))

            # Connection
            cv.create_line(cx, cy, wx, wy, fill=col+'44', width=1,
                           dash=(4,4))

            # Widget node
            _radial_gradient(cv, wx, wy, 36, col+'44', '#020608', 15)
            cv.create_oval(wx-36, wy-36, wx+36, wy+36,
                           outline=col, width=2)
            cv.create_text(wx, wy-6, text=icon,
                           font=('Segoe UI Emoji', 16))
            cv.create_text(wx, wy+14, text=label, fill=col,
                           font=('Segoe UI', 7, 'bold'))

        anim_t['v'] += 1
        if win.winfo_exists():
            win.after(50, animate_compile)

    cv.bind('<Configure>', lambda e: compile_intent())
    win.after(200, compile_intent)
    inp_e.bind('<Return>', lambda e: compile_intent())


# ── 4. P2P Distributed Storage Network ────────────────────────────────────────
def show_p2p_storage():
    win = _aero_win('P2P Storage', 820, 540, '#030a08')
    tk.Label(win, text='🌐  Native P2P Distributed Storage',
             bg='#030a08', fg='#40ffa0', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Your PC is a node in a global decentralised storage mesh.',
             bg='#030a08', fg='#0a2a18', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020608')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    stats_frame = tk.Frame(win, bg='#030a08')
    stats_frame.pack(fill='x', padx=20, pady=4)
    stats_labels = {}
    for key, txt in [('nodes','Peers: 0'), ('stored','Stored: 0 MB'),
                     ('speed','Speed: 0 KB/s'), ('health','Health: 100%')]:
        lbl = tk.Label(stats_frame, text=txt, bg='#030a08', fg='#40ffa0',
                       font=('Consolas', 9, 'bold'))
        lbl.pack(side='left', expand=True)
        stats_labels[key] = lbl

    # Generate fake peer nodes
    random.seed(42)
    nodes = [{'x': random.randint(60,740), 'y': random.randint(60,380),
               'id': f'{random.randint(0,255):02x}:{random.randint(0,255):02x}',
               'storage': random.randint(10,500),
               'active': random.random() > 0.2}
             for _ in range(22)]
    # This machine is the center
    MY_NODE = {'x': 400, 'y': 220, 'id': 'RYAN-PC', 'storage': 128, 'active': True}

    packets = []  # animated data packets
    t_anim = {'v': 0}

    def update():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        t = t_anim['v']

        # Spawn packet occasionally
        if t % 8 == 0:
            target = random.choice(nodes)
            if target['active']:
                packets.append({'x': MY_NODE['x'], 'y': MY_NODE['y'],
                                 'tx': target['x'], 'ty': target['y'],
                                 'prog': 0.0,
                                 'col': random.choice(['#40ffa0','#60a8ff','#ffcc40'])})

        # Advance packets
        for pkt in packets:
            pkt['prog'] = min(1.0, pkt['prog'] + 0.05)
        packets[:] = [p for p in packets if p['prog'] < 1.0]

        cv.delete('all')
        W = cv.winfo_width() or 800
        H = cv.winfo_height() or 420

        # Background mesh lines
        for n in nodes:
            for n2 in nodes:
                if n is not n2 and random.random() < 0.04:
                    cv.create_line(n['x'], n['y'], n2['x'], n2['y'],
                                   fill='#0a1a10', width=1)

        # Peer nodes
        for n in nodes:
            col = '#40ffa0' if n['active'] else '#2a3a30'
            r = 8 + n['storage'] // 80
            _radial_gradient(cv, n['x'], n['y'], r+4, col+'44', '#020608', 8)
            cv.create_oval(n['x']-r, n['y']-r, n['x']+r, n['y']+r,
                           fill='#030a08', outline=col, width=1)
            cv.create_text(n['x'], n['y']+r+8, text=n['id'],
                           fill='#1a4a28', font=('Consolas', 6))

        # Connections to MY_NODE
        for n in nodes:
            if n['active']:
                cv.create_line(MY_NODE['x'], MY_NODE['y'],
                               n['x'], n['y'],
                               fill='#0a3018', width=1, dash=(3,5))

        # Animated packets
        for pkt in packets:
            px = int(pkt['x'] + (pkt['tx']-pkt['x']) * pkt['prog'])
            py = int(pkt['y'] + (pkt['ty']-pkt['y']) * pkt['prog'])
            cv.create_oval(px-4, py-4, px+4, py+4,
                           fill=pkt['col'], outline='')

        # MY NODE (central)
        _radial_gradient(cv, MY_NODE['x'], MY_NODE['y'], 28,
                         '#40ffa0', '#030a08', 20)
        cv.create_oval(MY_NODE['x']-28, MY_NODE['y']-28,
                       MY_NODE['x']+28, MY_NODE['y']+28,
                       outline='#40ffa0', width=3)
        cv.create_text(MY_NODE['x'], MY_NODE['y']-5, text='💻',
                       font=('Segoe UI Emoji', 12))
        cv.create_text(MY_NODE['x'], MY_NODE['y']+10, text='YOU',
                       fill='#40ffa0', font=('Consolas', 7, 'bold'))

        # Stats
        active = sum(1 for n in nodes if n['active'])
        stats_labels['nodes'].config(text=f'Peers: {active}')
        stats_labels['stored'].config(text=f'Stored: {sum(n["storage"] for n in nodes)} MB')
        stats_labels['speed'].config(text=f'Speed: {random.randint(10,400)} KB/s')

        win.after(60, update)

    update()


# ── 5. Biometric UI Scaling Simulator ─────────────────────────────────────────
def show_biometric_ui():
    win = _aero_win('Biometric UI', 780, 520, '#040a06')
    tk.Label(win, text='👁  Biometric Dynamic UI Scaling',
             bg='#040a06', fg='#80ff60', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='UI adapts in real-time to your eye fatigue, pupil dilation and focus distance.',
             bg='#040a06', fg='#1a3a10', font=('Segoe UI', 8)).pack()

    metrics_frame = tk.Frame(win, bg='#040a06')
    metrics_frame.pack(fill='x', padx=20, pady=4)

    vitals = {
        'fatigue':   tk.IntVar(value=30),
        'pupil':     tk.IntVar(value=50),
        'distance':  tk.IntVar(value=60),
        'blink':     tk.IntVar(value=40),
    }
    vital_labels = {}

    def build_sliders():
        for key, (label, col) in [
            ('fatigue',  ('😴 Eye Fatigue %', '#ff8060')),
            ('pupil',    ('👁 Pupil Dilation %', '#60a8ff')),
            ('distance', ('📏 Screen Distance %', '#80ff60')),
            ('blink',    ('👀 Blink Rate %', '#ffcc40')),
        ]:
            row = tk.Frame(metrics_frame, bg='#040a06')
            row.pack(fill='x', pady=2)
            tk.Label(row, text=label, bg='#040a06', fg=col,
                     font=('Segoe UI', 9), width=24, anchor='w').pack(side='left')
            tk.Scale(row, variable=vitals[key], from_=0, to=100,
                     orient='horizontal', bg='#040a06', fg=col,
                     highlightthickness=0, troughcolor='#0a1808',
                     length=280, showvalue=True,
                     command=lambda v: update_ui()).pack(side='left')
            vital_labels[key] = row
    build_sliders()

    preview_frame = tk.Frame(win, bg='#020504')
    preview_frame.pack(fill='both', expand=True, padx=20, pady=6)

    preview_lbl = tk.Label(preview_frame, text='',
                           bg='#020504', fg='white', wraplength=700,
                           justify='center')
    preview_lbl.pack(expand=True)
    contrast_bar = tk.Label(preview_frame, text='', bg='#020504', height=2)
    contrast_bar.pack(fill='x')
    status_lbl = tk.Label(preview_frame, text='', bg='#020504',
                          font=('Segoe UI', 8))
    status_lbl.pack()

    def update_ui():
        fat = vitals['fatigue'].get()
        pup = vitals['pupil'].get()
        dist = vitals['distance'].get()
        blk = vitals['blink'].get()

        # Compute adaptive parameters
        font_size = 11 + fat//10 + (100-dist)//12
        font_size = max(9, min(28, font_size))
        brightness = max(30, 255 - fat*2)
        contrast_col = f'#{brightness:02x}{brightness:02x}{brightness:02x}'
        bg_brightness = max(5, 30 - fat//5)
        bg_col = f'#{bg_brightness:02x}{bg_brightness+4:02x}{bg_brightness:02x}'

        preview_lbl.config(
            text='The quick brown fox jumps over the lazy dog.\n'
                 'This text automatically resizes and recolours\n'
                 'based on your biometric readings.',
            font=('Segoe UI', font_size),
            fg=contrast_col, bg=bg_col)
        preview_frame.config(bg=bg_col)
        contrast_bar.config(bg=contrast_col)

        adjustments = []
        if fat > 60: adjustments.append(f'⬆ Font +{fat//10}pt (high fatigue)')
        if dist < 40: adjustments.append('⬆ Font +2pt (close distance)')
        if pup > 70: adjustments.append('🔆 Brightness reduced (bright environment)')
        if blk < 30: adjustments.append('⚠ Low blink rate detected')
        status_lbl.config(text='  ·  '.join(adjustments) if adjustments else '✅ Optimal viewing conditions',
                          bg=bg_col, fg='#60a860' if not adjustments else '#ff8840')

    update_ui()


# ── 6. Sub-Microsecond Crash Recovery ─────────────────────────────────────────
def show_crash_recovery():
    win = _aero_win('Crash Recovery', 800, 500, '#030510')
    tk.Label(win, text='⚡  Sub-Microsecond Crash Recovery',
             bg='#030510', fg='#60c8ff', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Kernel threads fail silently — micro-virtualised, patched and hot-swapped.',
             bg='#030510', fg='#0a1a30', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020408')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    PROCESSES = [
        {'name':'explorer.exe', 'pid':1004, 'col':'#60c8ff', 'health':100},
        {'name':'winlogon.exe', 'pid':1024, 'col':'#40e888', 'health':100},
        {'name':'lsass.exe',    'pid':1036, 'col':'#ffcc40', 'health':100},
        {'name':'svchost.exe',  'pid':1052, 'col':'#e060ff', 'health':100},
        {'name':'ntoskrnl.exe', 'pid':4,    'col':'#ff8040', 'health':100},
        {'name':'csrss.exe',    'pid':1068, 'col':'#40ffcc', 'health':100},
    ]
    events_log = []
    t_anim = {'v': 0}

    def inject_fault():
        target = random.choice(PROCESSES)
        target['health'] = 0
        events_log.insert(0, f'💥 {target["name"]} FAULT  →  isolating thread...')
        win.after(400, lambda: recover(target))

    def recover(proc):
        proc['health'] = 100
        events_log.insert(0, f'✅ {proc["name"]} recovered in {random.randint(1,999)}μs — hot-swapped')
        play_windows7_asterisk()

    def draw():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        cv.delete('all')
        W = cv.winfo_width() or 780
        H = cv.winfo_height() or 340

        n = len(PROCESSES)
        for i, proc in enumerate(PROCESSES):
            cx = int(80 + i * (W-120) / (n-1))
            cy = H//3
            col = proc['col']
            health = proc['health']
            pulse = 8 * math.sin(t_anim['v'] * 0.15 + i) if health == 100 else 0
            r = int(36 + pulse)

            # Health ring
            ring_col = col if health > 50 else '#ff4444'
            _radial_gradient(cv, cx, cy, r+6, ring_col+'22', '#020408', 12)
            cv.create_oval(cx-r, cy-r, cx+r, cy+r,
                           fill='#030510', outline=ring_col, width=3)

            # Health arc
            extent = int(359 * health/100)
            if extent > 0:
                cv.create_arc(cx-r+4, cy-r+4, cx+r-4, cy+r-4,
                              start=90, extent=-extent,
                              outline=ring_col, width=4, style='arc')

            cv.create_text(cx, cy-6, text=proc['name'][:10],
                           fill=col, font=('Consolas', 7, 'bold'))
            cv.create_text(cx, cy+8, text=f'PID {proc["pid"]}',
                           fill=col+'88', font=('Consolas', 6))

            # Heartbeat line below
            hb_y = cy + 70
            for j in range(30):
                hx1 = cx - 30 + j*2
                hx2 = hx1 + 2
                offset = int(12 * math.sin((t_anim['v'] + j*3 + i*7) * 0.3))
                cv.create_line(hx1, hb_y+offset, hx2, hb_y+offset,
                               fill=ring_col, width=1)

        # Event log
        log_y = H - 100
        cv.create_text(30, log_y, text='System Event Log:',
                       fill='#2a4a6a', font=('Consolas', 8, 'bold'), anchor='w')
        for ei, evt in enumerate(events_log[:6]):
            col = '#ff4444' if '💥' in evt else '#40e888'
            cv.create_text(30, log_y + 16*(ei+1), text=evt[:80],
                           fill=col, font=('Consolas', 8), anchor='w')

        win.after(50, draw)

    bf = tk.Frame(win, bg='#030510')
    bf.pack(pady=4)
    tk.Button(bf, text='💥 Inject Random Fault', bg='#1a0010',
              fg='#ff6060', relief='flat', font=('Segoe UI', 10, 'bold'),
              command=inject_fault).pack(side='left', padx=6)

    draw()


# ── 7. Multi-Brain Collaborative Mirror ───────────────────────────────────────
def show_multi_brain():
    win = _aero_win('Multi-Brain Session', 820, 500, '#040808')
    tk.Label(win, text='🧠  Multi-Brain Collaborative Mirror',
             bg='#040808', fg='#40ffc0', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Two computers sharing one kernel runtime — same threads, same memory.',
             bg='#040808', fg='#0a2a20', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020606')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    shared_text = {'content': 'Shared kernel buffer — both users see this in real time.\n',
                   'cursor_a': 0, 'cursor_b': 0}
    t_anim = {'v': 0}

    editor_frame = tk.Frame(win, bg='#040808')
    editor_frame.pack(fill='x', padx=20, pady=4)
    tk.Label(editor_frame, text='Shared Buffer:', bg='#040808', fg='#40ffc0',
             font=('Segoe UI', 9, 'bold')).pack(anchor='w')
    shared_edit = tk.Text(editor_frame, height=4, bg='#020a08', fg='#40ffc0',
                          font=('Consolas', 10), relief='flat',
                          insertbackground='#40ffc0',
                          highlightthickness=2, highlightbackground='#0a3a28')
    shared_edit.pack(fill='x', pady=2)
    shared_edit.insert('1.0', shared_text['content'])

    def draw_network():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        t = t_anim['v']
        cv.delete('all')
        W = cv.winfo_width() or 800
        H = cv.winfo_height() or 220

        cx = W//2
        # Kernel core
        pulse = 30 + 6*math.sin(t*0.15)
        _radial_gradient(cv, cx, H//2, int(pulse), '#204a38', '#020606', 20)
        cv.create_oval(cx-int(pulse), H//2-int(pulse),
                       cx+int(pulse), H//2+int(pulse),
                       outline='#40ffc0', width=2)
        cv.create_text(cx, H//2-6, text='KERNEL', fill='#40ffc0',
                       font=('Consolas', 8, 'bold'))
        cv.create_text(cx, H//2+8, text='RUNTIME', fill='#40ffc088',
                       font=('Consolas', 6))

        # Computer A and B
        for label, x, col, cursor_key in [
            ('RYAN-PC', cx-240, '#40ffc0', 'cursor_a'),
            ('GUEST-PC', cx+240, '#60a8ff', 'cursor_b'),
        ]:
            _radial_gradient(cv, x, H//2, 40, col+'33', '#020606', 15)
            cv.create_oval(x-40, H//2-40, x+40, H//2+40,
                           outline=col, width=2)
            cv.create_text(x, H//2-8, text='💻', font=('Segoe UI Emoji',16))
            cv.create_text(x, H//2+18, text=label, fill=col,
                           font=('Consolas', 8, 'bold'))
            # Data stream to kernel
            for si in range(6):
                sx = x + (cx-x) * (si/5)
                sy = H//2 + 10*math.sin((t*0.3 + si)*1.2)
                r = 3 if si in (0,5) else 2
                col2 = col if si % 2 == 0 else col+'88'
                cv.create_oval(int(sx)-r, int(sy)-r, int(sx)+r, int(sy)+r,
                               fill=col2, outline='')

        # Sync indicator
        sync_col = '#40ffc0' if t % 20 < 10 else '#60a8ff'
        cv.create_text(cx, H-20, text='🔄 Kernel sync active  ·  Latency: 0.4ms',
                       fill=sync_col, font=('Consolas', 8))

        win.after(60, draw_network)

    draw_network()


# ── 8. Spatial 3D Desktop Cube ─────────────────────────────────────────────────
def show_spatial_desktop():
    win = _aero_win('3D Spatial Desktop', 800, 560, '#030408')
    tk.Label(win, text='🎲  3D Spatial Desktop Cube',
             bg='#030408', fg='#a060ff', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Navigate your workspace in true 3D — drag to rotate, click to enter a face.',
             bg='#030408', fg='#1a0a2a', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020306')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    FACES = [
        ('Desktop',     '#a060ff', '🖥'),
        ('Documents',   '#60a8ff', '📁'),
        ('Media',       '#ff8040', '🎬'),
        ('Terminal',    '#40e888', '⌨'),
        ('Settings',    '#ffcc40', '⚙'),
        ('Browser',     '#ff60a0', '🌐'),
    ]

    rot = {'x': 0.4, 'y': 0.6, 'drag_x': 0, 'drag_y': 0,
           'dragging': False, 'auto': True}

    def project(x3, y3, z3, cx, cy, d=500):
        scale = d / (d + z3 + 200)
        return int(cx + x3*scale*120), int(cy + y3*scale*120)

    def rotate_point(x, y, z, rx, ry):
        # Rotate around Y
        x2 = x*math.cos(ry) + z*math.sin(ry)
        z2 = -x*math.sin(ry) + z*math.cos(ry)
        # Rotate around X
        y2 = y*math.cos(rx) - z2*math.sin(rx)
        z3 = y*math.sin(rx) + z2*math.cos(rx)
        return x2, y2, z3

    def draw_cube():
        if not win.winfo_exists():
            return
        if rot['auto']:
            rot['y'] += 0.012
            rot['x'] += 0.005

        cv.delete('all')
        W = cv.winfo_width() or 780
        H = cv.winfo_height() or 400
        cx, cy = W//2, H//2 + 20

        # Cube vertices
        verts_raw = [
            (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
            (-1,-1, 1),(1,-1, 1),(1,1, 1),(-1,1, 1),
        ]
        verts = [rotate_point(x,y,z,rot['x'],rot['y']) for x,y,z in verts_raw]
        pts   = [project(x,y,z,cx,cy) for x,y,z in verts]

        # 6 faces: indices + which FACES entry
        cube_faces = [
            (0,1,2,3, 0),  # front
            (4,5,6,7, 1),  # back
            (0,4,7,3, 2),  # left
            (1,5,6,2, 3),  # right
            (0,1,5,4, 4),  # bottom
            (3,2,6,7, 5),  # top
        ]
        # Sort by average z for painter's algorithm
        face_depths = []
        for a,b,c,d2,fi in cube_faces:
            avg_z = sum(verts[i][2] for i in (a,b,c,d2)) / 4
            face_depths.append((avg_z, a,b,c,d2,fi))
        face_depths.sort()

        for avg_z, a, b, c, d2, fi in face_depths:
            face_name, col, icon = FACES[fi]
            quad = [pts[a], pts[b], pts[c], pts[d2]]
            flat = [v for pt in quad for v in pt]
            # Face brightness by depth
            brightness = max(0.3, min(1.0, 0.6 + avg_z * 0.25))
            r = int(int(col[1:3],16)*brightness)
            g = int(int(col[3:5],16)*brightness)
            b2 = int(int(col[5:7],16)*brightness)
            face_col = f'#{r:02x}{g:02x}{b2:02x}'
            cv.create_polygon(flat, fill=face_col+'44', outline=col, width=2)
            # Face centre for text
            fcx = sum(p[0] for p in quad) // 4
            fcy = sum(p[1] for p in quad) // 4
            cv.create_text(fcx, fcy-10, text=icon,
                           font=('Segoe UI Emoji', 18), fill=col)
            cv.create_text(fcx, fcy+12, text=face_name,
                           fill=col, font=('Segoe UI', 8, 'bold'))

        # Glow at centre
        _radial_gradient(cv, cx, cy, 12, '#a060ff44', '#020306', 6)

        win.after(40, draw_cube)

    def on_press(e): rot['dragging'] = True; rot['drag_x'] = e.x; rot['drag_y'] = e.y; rot['auto'] = False
    def on_drag(e):
        if rot['dragging']:
            rot['y'] += (e.x - rot['drag_x']) * 0.008
            rot['x'] += (e.y - rot['drag_y']) * 0.008
            rot['drag_x'] = e.x; rot['drag_y'] = e.y
    def on_release(e): rot['dragging'] = False

    cv.bind('<ButtonPress-1>', on_press)
    cv.bind('<B1-Motion>', on_drag)
    cv.bind('<ButtonRelease-1>', on_release)
    tk.Button(win, text='▶ Auto Rotate', bg='#100820', fg='#a060ff',
              relief='flat', font=('Segoe UI', 9),
              command=lambda: rot.update({'auto': True})).pack(pady=4)
    draw_cube()


# ── 9. Self-Optimising Kernel Monitor ─────────────────────────────────────────
def show_self_optimising_kernel():
    win = _aero_win('Self-Optimising Kernel', 800, 500, '#040608')
    tk.Label(win, text='🤖  Self-Optimising Generative Kernel',
             bg='#040608', fg='#ffcc40', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Kernel rewrites itself over time — trims unused subsystems for your workflow.',
             bg='#040608', fg='#2a2a08', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020406')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    SUBSYSTEMS = [
        {'name':'Memory Mgr', 'usage':88, 'optimised':0},
        {'name':'I/O Scheduler','usage':64,'optimised':0},
        {'name':'Network Stack','usage':72,'optimised':0},
        {'name':'FS Driver',  'usage':45, 'optimised':0},
        {'name':'GPU Bridge', 'usage':91, 'optimised':0},
        {'name':'Audio Sys',  'usage':12, 'optimised':0},
        {'name':'USB Manager','usage':28, 'optimised':0},
        {'name':'Crypto Core','usage':58, 'optimised':0},
    ]

    t_anim = {'v': 0}
    log_lines = []

    def optimise_one():
        for s in SUBSYSTEMS:
            if s['usage'] < 30 and s['optimised'] < 100:
                s['optimised'] = min(100, s['optimised'] + 20)
                s['usage'] = max(5, s['usage'] - 5)
                log_lines.insert(0,
                    f'✂ Trimming {s["name"]} — '
                    f'{s["optimised"]}% pruned')
                play_windows7_asterisk()
                return
        log_lines.insert(0, '✅ Kernel fully optimised for your workflow')

    def draw():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        t = t_anim['v']
        cv.delete('all')
        W = cv.winfo_width() or 780
        H = cv.winfo_height() or 340

        n = len(SUBSYSTEMS)
        step = (W-60) / n
        for i, sub in enumerate(SUBSYSTEMS):
            cx = int(30 + step*i + step/2)
            col = '#ffcc40' if sub['usage'] > 60 else \
                  '#40e888' if sub['usage'] > 30 else '#ff4444'
            opt_col = '#a060ff'

            # Animated usage bar (grows from bottom)
            bar_h = int(sub['usage'] * 1.4)
            bar_y = H - 100
            cv.create_rectangle(cx-14, bar_y, cx+14, bar_y-bar_h,
                                fill=col+'44', outline=col)

            # Optimised (pruned) overlay
            if sub['optimised'] > 0:
                prune_h = int(sub['optimised'] * 0.8)
                cv.create_rectangle(cx-14, bar_y-bar_h, cx+14,
                                    bar_y-bar_h-prune_h,
                                    fill=opt_col+'66', outline=opt_col)

            # Pulse ring
            pr = int(18 + 4*math.sin(t*0.2 + i))
            _radial_gradient(cv, cx, bar_y-bar_h-30, pr, col+'22', '#020406', 8)
            cv.create_oval(cx-pr, bar_y-bar_h-50,
                           cx+pr, bar_y-bar_h-10,
                           outline=col, width=1)

            cv.create_text(cx, bar_y+14, text=sub['name'][:9],
                           fill=col, font=('Consolas', 7), angle=0)
            cv.create_text(cx, bar_y-bar_h//2, text=f'{sub["usage"]}%',
                           fill='white', font=('Consolas', 7, 'bold'))

        # Log
        for li, line in enumerate(log_lines[:4]):
            cv.create_text(20, H-20-li*14, text=line[:80],
                           fill='#4a4a20', font=('Consolas', 7), anchor='w')

        win.after(60, draw)

    bf = tk.Frame(win, bg='#040608')
    bf.pack(pady=4)
    tk.Button(bf, text='🤖 Run Optimisation Cycle', bg='#1a1800',
              fg='#ffcc40', relief='flat', font=('Segoe UI', 10, 'bold'),
              command=optimise_one).pack(side='left', padx=6)
    draw()


# ── 10. Quantum-Resistant Sandbox Monitor ─────────────────────────────────────
def show_quantum_sandbox():
    win = _aero_win('Quantum Sandbox', 800, 520, '#030408')
    tk.Label(win, text='🛡  Quantum-Resistant Cryptographic Sandbox',
             bg='#030408', fg='#40e0ff', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Every process runs in an unbreakable hardware-isolated cryptographic cell.',
             bg='#030408', fg='#0a1a20', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020306')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    PROCS = [
        {'name':'chrome.exe',   'pid':2048, 'threat':0,  'col':'#40e0ff'},
        {'name':'notepad.exe',  'pid':2100, 'threat':0,  'col':'#40e888'},
        {'name':'python.exe',   'pid':2212, 'threat':15, 'col':'#ffcc40'},
        {'name':'unknown.exe',  'pid':3301, 'threat':87, 'col':'#ff4060'},
        {'name':'vlc.exe',      'pid':2380, 'threat':0,  'col':'#a060ff'},
        {'name':'winword.exe',  'pid':2460, 'threat':5,  'col':'#60a8ff'},
    ]
    t_anim = {'v': 0}

    def draw():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        t = t_anim['v']
        cv.delete('all')
        W = cv.winfo_width() or 780
        H = cv.winfo_height() or 380

        # Hex grid background (quantum feel)
        HEX_R = 22
        for row in range(H // (HEX_R*2) + 2):
            for col2 in range(W // (HEX_R*2) + 2):
                hx = col2 * HEX_R * 2 + (HEX_R if row % 2 else 0)
                hy = row * HEX_R * 1.8
                pts = []
                for angle in range(0, 360, 60):
                    a = math.radians(angle)
                    pts.extend([hx + HEX_R*math.cos(a), hy + HEX_R*math.sin(a)])
                cv.create_polygon(pts, outline='#060c14', fill='', width=1)

        # Process cells
        n = len(PROCS)
        for i, proc in enumerate(PROCS):
            cx = int(80 + i * (W-120) / (n-1))
            cy = H//2
            col = proc['col']
            threat = proc['threat']

            # Threat heat
            heat_col = f'#{min(255,threat*2):02x}{max(0,255-threat*3):02x}00' \
                       if threat > 20 else col

            # Outer quantum shell (hexagonal approximation)
            r = 50
            hex_pts = []
            for angle in range(0, 360, 60):
                a = math.radians(angle + t_anim['v'] * 0.5)
                hex_pts.extend([cx + r*math.cos(a), cy + r*math.sin(a)])
            cv.create_polygon(hex_pts, outline=heat_col,
                              fill=heat_col+'11', width=2)

            # Inner cell
            _radial_gradient(cv, cx, cy, 32, heat_col+'33', '#020306', 12)
            cv.create_oval(cx-32, cy-32, cx+32, cy+32,
                           fill='#030408', outline=heat_col, width=2)

            # Threat indicator
            if threat > 20:
                cv.create_text(cx, cy-44, text='⚠',
                               fill='#ff4060', font=('Segoe UI Emoji', 12))

            cv.create_text(cx, cy-7, text=proc['name'][:10],
                           fill=col, font=('Consolas', 7, 'bold'))
            cv.create_text(cx, cy+7, text=f'PID {proc["pid"]}',
                           fill=col+'88', font=('Consolas', 6))

            if threat > 0:
                cv.create_text(cx, cy+20, text=f'Threat: {threat}%',
                               fill='#ff8040', font=('Consolas', 6))

            # Encryption key animation
            key_angle = math.radians(t * 3 + i * 60)
            kx = int(cx + 44 * math.cos(key_angle))
            ky = int(cy + 44 * math.sin(key_angle))
            cv.create_oval(kx-3, ky-3, kx+3, ky+3, fill=col, outline='')

        # Status bar
        high_threat = [p for p in PROCS if p['threat'] > 20]
        status = f'⚠ {len(high_threat)} suspicious process(es) sandboxed' \
                 if high_threat else '✅ All processes cryptographically isolated'
        cv.create_text(W//2, H-20, text=status,
                       fill='#ff4060' if high_threat else '#40e888',
                       font=('Consolas', 9))

        win.after(40, draw)

    def quarantine():
        for proc in PROCS:
            if proc['threat'] > 20:
                proc['threat'] = 0
                proc['name'] = '[QUARANTINED]'
                proc['col'] = '#666666'
        show_system_notification('Quantum Sandbox', 'Threats quarantined!')
        play_windows7_asterisk()

    bf = tk.Frame(win, bg='#030408')
    bf.pack(pady=4)
    tk.Button(bf, text='🔒 Quarantine All Threats', bg='#1a0010',
              fg='#ff6080', relief='flat', font=('Segoe UI', 10, 'bold'),
              command=quarantine).pack(side='left', padx=6)
    draw()


# ── 11. Holographic Window Depth Stack ─────────────────────────────────────────
def show_holographic_stack():
    win = _aero_win('Holographic Stack', 820, 560, '#020304')
    tk.Label(win, text='📺  Holographic True-Depth Window Stack',
             bg='#020304', fg='#80e8ff', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Windows exist at real physical depth — focus shifts your eyes, not a click.',
             bg='#020304', fg='#081820', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#010204')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    WINDOWS = [
        {'title':'Terminal',  'depth':0.1, 'col':'#40e888', 'x':0.12, 'y':0.15,
         'w':0.35, 'h':0.45, 'content':'$ ls -la\ndocs/\ncode/\nsystem.log'},
        {'title':'Browser',   'depth':0.4, 'col':'#60a8ff', 'x':0.32, 'y':0.25,
         'w':0.38, 'h':0.50, 'content':'google.com\n─────────\nSearch...'},
        {'title':'Code Editor','depth':0.7,'col':'#ffcc40', 'x':0.52, 'y':0.10,
         'w':0.40, 'h':0.55, 'content':'def main():\n  pass\n\n# TODO'},
        {'title':'Chat',      'depth':1.0, 'col':'#e060ff', 'x':0.18, 'y':0.48,
         'w':0.30, 'h':0.38, 'content':'Ryan: Hello!\nAI: Hi there!'},
    ]

    focus_depth = {'v': 0.5, 'target': 0.5}
    t_anim = {'v': 0}

    def draw():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        t = t_anim['v']
        # Ease focus depth
        focus_depth['v'] += (focus_depth['target'] - focus_depth['v']) * 0.08

        cv.delete('all')
        W = cv.winfo_width() or 800
        H = cv.winfo_height() or 440

        # Sort by depth (furthest first)
        sorted_wins = sorted(WINDOWS, key=lambda w: -w['depth'])

        for wdata in sorted_wins:
            wx = int(W * wdata['x'])
            wy = int(H * wdata['y'])
            ww = int(W * wdata['w'])
            wh = int(H * wdata['h'])
            col = wdata['col']
            depth = wdata['depth']

            # Distance from focus plane
            diff = abs(depth - focus_depth['v'])
            # Blur simulation: less saturated + slightly scaled
            scale = 1.0 - diff * 0.15
            alpha_sim = max(0.2, 1.0 - diff * 0.6)

            # Perspective offset
            persp_x = int((depth - 0.5) * 30)
            persp_y = int((depth - 0.5) * 15)
            wx += persp_x; wy += persp_y
            sww = int(ww * scale); swh = int(wh * scale)

            # Shadow
            cv.create_rectangle(wx+6, wy+6, wx+sww+6, wy+swh+6,
                                fill='#000000', outline='',
                                stipple='gray25' if diff < 0.3 else 'gray12')

            # Window body
            window_fill = col + ('44' if diff > 0.4 else 'cc')
            cv.create_rectangle(wx, wy, wx+sww, wy+swh,
                                fill='#04080e', outline=col,
                                width=3 if diff < 0.2 else 1)

            # Titlebar
            cv.create_rectangle(wx, wy, wx+sww, wy+22,
                                fill=col+'66', outline='')
            cv.create_text(wx+8, wy+11, text=wdata['title'],
                           fill='white', font=('Segoe UI', 8, 'bold'),
                           anchor='w')
            cv.create_text(wx+sww-8, wy+11, text='✕',
                           fill='white', font=('Segoe UI', 8), anchor='e')

            # Content
            if diff < 0.35:
                for li, line in enumerate(wdata['content'].splitlines()[:4]):
                    cv.create_text(wx+8, wy+32+li*14, text=line[:30],
                                   fill=col, font=('Consolas', 8), anchor='w')

            # Depth label
            cv.create_text(wx+sww//2, wy+swh-10,
                           text=f'depth {depth:.1f}m',
                           fill=col+'66', font=('Consolas', 6))

        # Depth slider visual
        cv.create_line(W-30, 30, W-30, H-30, fill='#1a2a30', width=2)
        fy = int(30 + (H-60) * focus_depth['v'])
        cv.create_oval(W-38, fy-8, W-22, fy+8, fill='#80e8ff', outline='white')
        cv.create_text(W-30, H-14, text='depth',
                       fill='#1a4050', font=('Consolas', 6), anchor='s')

        win.after(40, draw)

    def on_scroll(e):
        delta = -0.05 if (getattr(e,'delta',0) < 0 or e.num == 5) else 0.05
        focus_depth['target'] = max(0.0, min(1.0, focus_depth['target'] + delta))

    cv.bind('<MouseWheel>', on_scroll)
    cv.bind('<Button-4>', on_scroll)
    cv.bind('<Button-5>', on_scroll)
    tk.Label(win, text='Scroll to shift focus depth  ·  Windows blur when out-of-focus',
             bg='#020304', fg='#081820', font=('Segoe UI', 7)).pack(pady=2)
    draw()


# ── 12. Fluid Typographic Grid ─────────────────────────────────────────────────
def show_fluid_typography():
    win = _aero_win('Fluid Typography', 820, 540, '#03040a')
    tk.Label(win, text='📐  System-Wide Fluid Typographic Grid',
             bg='#03040a', fg='#ffb040', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='Drag any window — all text reflows, wallpaper shifts, layout breathes.',
             bg='#03040a', fg='#1a1208', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020308')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    windows = [
        {'title':'Article',  'x':60,  'y':60,  'w':280, 'h':200, 'col':'#ffb040',
         'text':'The quick brown fox jumps over the lazy dog. '
                'Windows dynamically reflow their content.'},
        {'title':'Sidebar',  'x':380, 'y':60,  'w':160, 'h':340, 'col':'#60a8ff',
         'text':'Navigation\n───\nHome\nDocs\nCode\nSettings\nHelp'},
        {'title':'Terminal', 'x':60,  'y':300, 'w':280, 'h':150, 'col':'#40e888',
         'text':'$ ls\nDocuments/\nDownloads/\n$ _'},
        {'title':'Media',    'x':560, 'y':100, 'w':200, 'h':200, 'col':'#e060ff',
         'text':'🎵 Now Playing\n─────────\nTrack Name\n3:42 / 4:15'},
    ]

    drag = {'win': None, 'ox': 0, 'oy': 0}
    t_anim = {'v': 0}

    def get_grid_cols(total_w):
        """Compute optimal column count from available width."""
        return max(1, total_w // 200)

    def draw():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        cv.delete('all')
        W = cv.winfo_width() or 800
        H = cv.winfo_height() or 480

        # Background editorial grid lines
        cols = get_grid_cols(W)
        col_w = W // cols
        for c in range(1, cols):
            cv.create_line(c*col_w, 0, c*col_w, H,
                           fill='#080c18', width=1, dash=(2,6))

        # Sort by x position for natural reflow
        sorted_wins = sorted(windows, key=lambda w: w['x'])

        for wdata in sorted_wins:
            wx, wy = wdata['x'], wdata['y']
            ww, wh = wdata['w'], wdata['h']
            col = wdata['col']

            # Snap to nearest grid column
            snap_x = (wx // col_w) * col_w + 4
            # Animated snap guide
            if abs(wx - snap_x) < 30:
                cv.create_line(snap_x, 0, snap_x, H, fill=col+'33', width=1)

            # Shadow
            cv.create_rectangle(wx+4, wy+4, wx+ww+4, wy+wh+4,
                                fill='#000000', outline='', stipple='gray25')

            # Window
            cv.create_rectangle(wx, wy, wx+ww, wy+wh,
                                fill='#04060e', outline=col, width=2)
            # Titlebar
            cv.create_rectangle(wx, wy, wx+ww, wy+20,
                                fill=col+'44', outline='')
            cv.create_text(wx+8, wy+10, text=wdata['title'],
                           fill='white', font=('Segoe UI', 8, 'bold'), anchor='w')

            # Reflowed text content
            font_size = max(7, min(11, ww // 28))
            for li, line in enumerate(wdata['text'].splitlines()[:8]):
                cv.create_text(wx+6, wy+28+li*13,
                               text=line[:ww//8], fill=col,
                               font=('Segoe UI', font_size), anchor='w')

        if drag['win'] is not None:
            cv.create_text(W//2, H-14,
                           text='🔄 Layout reflows as you drag',
                           fill='#ffb040', font=('Segoe UI', 8))

        win.after(40, draw)

    def on_press(e):
        for wdata in windows:
            if (wdata['x'] <= e.x <= wdata['x']+wdata['w'] and
                    wdata['y'] <= e.y <= wdata['y']+20):
                drag['win'] = wdata
                drag['ox'] = e.x - wdata['x']
                drag['oy'] = e.y - wdata['y']
                return

    def on_drag(e):
        if drag['win']:
            drag['win']['x'] = max(0, e.x - drag['ox'])
            drag['win']['y'] = max(0, e.y - drag['oy'])

    def on_release(e): drag['win'] = None

    cv.bind('<ButtonPress-1>', on_press)
    cv.bind('<B1-Motion>', on_drag)
    cv.bind('<ButtonRelease-1>', on_release)
    draw()


# ── 13. Orthogonal Persistence Engine ─────────────────────────────────────────
def show_orthogonal_persistence():
    win = _aero_win('Orthogonal Persistence', 780, 500, '#030610')
    tk.Label(win, text='💾  Orthogonal Persistence Engine',
             bg='#030610', fg='#60ffcc', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='RAM and disk are one. Pull the power — your exact state resumes instantly.',
             bg='#030610', fg='#0a2a20', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020408')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    state_data = {
        'pages': [{'addr': f'0x{i*4096:08X}',
                   'dirty': random.random() < 0.3,
                   'persisted': random.random() < 0.7}
                  for i in range(64)],
        'power_cut': False,
        'resume_progress': 0,
    }
    t_anim = {'v': 0}
    log = []

    def draw():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        t = t_anim['v']
        cv.delete('all')
        W = cv.winfo_width() or 760
        H = cv.winfo_height() or 360

        # Memory page grid
        n = len(state_data['pages'])
        cols2 = 16
        rows = (n + cols2 - 1) // cols2
        cell_w = (W - 60) // cols2
        cell_h = 24

        for i, page in enumerate(state_data['pages']):
            row_i = i // cols2; col_i = i % cols2
            px = 20 + col_i * cell_w
            py = 40 + row_i * cell_h
            col = ('#60ffcc' if page['persisted'] else
                   '#ffcc40' if page['dirty'] else '#1a3a28')
            _aero_pill(cv, px+1, py+2, px+cell_w-1, py+cell_h-2,
                       fill=col+'44', outline=col)

        # Legend
        for lx, lcol, ltxt in [(30,'#60ffcc','Persisted'),
                                (130,'#ffcc40','Dirty (writing)'),
                                (290,'#1a3a28','Clean')]:
            _aero_pill(cv, lx, H-34, lx+16, H-20, fill=lcol+'44', outline=lcol)
            cv.create_text(lx+22, H-27, text=ltxt, fill=lcol,
                           font=('Consolas', 7), anchor='w')

        # Power cut simulation
        if state_data['power_cut']:
            state_data['resume_progress'] = min(100,
                state_data['resume_progress'] + 3)
            # Flash effect
            if t % 4 < 2:
                cv.create_rectangle(0, 0, W, H, fill='#ffffff11', outline='')
            # Progress bar
            cv.create_rectangle(W//4, H//2-20, 3*W//4, H//2+20,
                                fill='#030610', outline='#60ffcc', width=2)
            prog_w = int((W//2) * state_data['resume_progress'] / 100)
            cv.create_rectangle(W//4, H//2-20, W//4+prog_w, H//2+20,
                                fill='#60ffcc', outline='')
            cv.create_text(W//2, H//2, text=f'Resuming... {state_data["resume_progress"]}%',
                           fill='white', font=('Consolas', 11, 'bold'))
            if state_data['resume_progress'] >= 100:
                state_data['power_cut'] = False
                state_data['resume_progress'] = 0
                log.insert(0, '✅ Full system state restored — zero data loss')
        else:
            # Periodically mark pages as persisted
            for page in random.sample(state_data['pages'], 3):
                page['persisted'] = True
                page['dirty'] = False

        # Log
        for li, line in enumerate(log[:3]):
            cv.create_text(20, H-52-li*13, text=line[:70],
                           fill='#2a6a48', font=('Consolas', 7), anchor='w')

        win.after(60, draw)

    def power_cut():
        state_data['power_cut'] = True
        state_data['resume_progress'] = 0
        log.insert(0, '⚡ Power interruption detected — restoring state...')
        play_windows7_error()

    bf = tk.Frame(win, bg='#030610')
    bf.pack(pady=4)
    tk.Button(bf, text='⚡ Simulate Power Cut', bg='#1a1000',
              fg='#ffcc40', relief='flat', font=('Segoe UI', 10, 'bold'),
              command=power_cut).pack(side='left', padx=6)
    draw()


# ── 14. Intent-Based Hardware Morphing ─────────────────────────────────────────
def show_hardware_morphing():
    win = _aero_win('Hardware Morphing', 800, 520, '#040608')
    tk.Label(win, text='🔧  Dynamic Hardware Architecture Morphing',
             bg='#040608', fg='#ff8040', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='CPU overheating? The kernel rewrites itself to a lighter execution mode live.',
             bg='#040608', fg='#1a1408', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020406')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    CPU_CORES = [
        {'id': i, 'temp': random.randint(40, 75),
         'freq': random.uniform(1.8, 3.6),
         'mode': 'x86-64', 'load': random.randint(10, 90)}
        for i in range(8)
    ]
    t_anim = {'v': 0}
    event_log = []

    def morph_hottest():
        hottest = max(CPU_CORES, key=lambda c: c['temp'])
        if hottest['temp'] > 85 and hottest['mode'] == 'x86-64':
            hottest['mode'] = 'ECO'
            hottest['freq'] = round(hottest['freq'] * 0.6, 1)
            hottest['temp'] -= 20
            event_log.insert(0,
                f'⚡ Core {hottest["id"]} morphed x86-64→ECO '
                f'@ {hottest["freq"]:.1f}GHz')
            play_windows7_asterisk()
        else:
            hottest['temp'] = min(100, hottest['temp'] + 15)
            event_log.insert(0,
                f'🔥 Core {hottest["id"]} temp: {hottest["temp"]}°C')

    def draw():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        t = t_anim['v']
        # Slowly raise temps
        for core in CPU_CORES:
            core['temp'] = min(100, core['temp'] + random.uniform(-0.5, 0.8))
            core['load'] = min(100, max(5, core['load'] + random.randint(-3,4)))

        cv.delete('all')
        W = cv.winfo_width() or 780
        H = cv.winfo_height() or 380

        # CPU die layout (2 rows x 4 cols)
        for i, core in enumerate(CPU_CORES):
            row_i = i // 4; col_i = i % 4
            cx = int(80 + col_i * 160)
            cy = int(80 + row_i * 160)
            temp = core['temp']
            load = core['load']

            # Thermal color
            heat_r = min(255, int(temp * 2.5))
            heat_g = max(0, int(255 - temp * 2.0))
            heat_col = f'#{heat_r:02x}{heat_g:02x}20'
            eco_col = '#40a8ff'
            col = eco_col if core['mode'] == 'ECO' else heat_col

            # Core substrate
            _radial_gradient(cv, cx, cy, 52, col+'44', '#020406', 20)
            cv.create_rectangle(cx-44, cy-44, cx+44, cy+44,
                               fill='#030508', outline=col, width=2)

            # Load bar
            load_h = int(40 * load/100)
            cv.create_rectangle(cx-38, cy+4, cx-28, cy+44,
                               fill='#0a1018', outline='')
            cv.create_rectangle(cx-38, cy+44-load_h, cx-28, cy+44,
                               fill=col, outline='')

            # Freq arc
            freq_pct = core['freq'] / 3.6
            cv.create_arc(cx-34, cy-34, cx+34, cy+34,
                         start=140, extent=-int(freq_pct*260),
                         outline=col, width=4, style='arc')

            cv.create_text(cx+6, cy-10, text=f'Core {core["id"]}',
                           fill=col, font=('Consolas', 7, 'bold'))
            cv.create_text(cx+6, cy+4, text=f'{temp:.0f}°C',
                           fill=col, font=('Consolas', 8, 'bold'))
            cv.create_text(cx+6, cy+18, text=f'{core["freq"]:.1f}GHz',
                           fill=col+'cc', font=('Consolas', 7))
            cv.create_text(cx+6, cy+30, text=core['mode'],
                           fill=eco_col if core['mode']=='ECO' else '#666666',
                           font=('Consolas', 7, 'bold'))

        # Event log
        for li, line in enumerate(event_log[:5]):
            cv.create_text(20, H-20-li*13, text=line[:90],
                           fill='#3a2a10', font=('Consolas', 7), anchor='w')

        win.after(80, draw)

    bf = tk.Frame(win, bg='#040608')
    bf.pack(pady=4)
    tk.Button(bf, text='🔥 Overheat Core', bg='#1a0800',
              fg='#ff8040', relief='flat', font=('Segoe UI', 10, 'bold'),
              command=morph_hottest).pack(side='left', padx=6)
    draw()


# ── 15. Energy Harvesting Scheduler ────────────────────────────────────────────
def show_energy_harvester():
    win = _aero_win('Energy Harvester', 800, 500, '#04060a')
    tk.Label(win, text='☀  Context-Aware Energy Harvesting Scheduler',
             bg='#04060a', fg='#ffee40', font=('Segoe UI', 13, 'bold')).pack(pady=(10,2))
    tk.Label(win, text='CPU workloads shift in real-time with solar, kinetic and thermal energy levels.',
             bg='#04060a', fg='#1a1a08', font=('Segoe UI', 8)).pack()

    cv = _aero_canvas(win, bg='#020408')
    cv.pack(fill='both', expand=True, padx=10, pady=6)

    energy = {
        'solar':   {'v': 60.0, 'icon':'☀', 'col':'#ffee40'},
        'kinetic': {'v': 35.0, 'icon':'⚡', 'col':'#60a8ff'},
        'thermal': {'v': 48.0, 'icon':'🔥', 'col':'#ff8040'},
        'battery': {'v': 80.0, 'icon':'🔋', 'col':'#40e888'},
    }
    TASKS = [
        {'name':'Video Render','priority': 80,'scheduled': True,'col':'#ffee40'},
        {'name':'Background Sync','priority':30,'scheduled': True,'col':'#60a8ff'},
        {'name':'System Updates','priority':50,'scheduled': False,'col':'#40e888'},
        {'name':'ML Training','priority':70,'scheduled': False,'col':'#e060ff'},
        {'name':'Backup','priority':40,'scheduled': True,'col':'#ff8040'},
    ]
    t_anim = {'v': 0}

    def draw():
        if not win.winfo_exists():
            return
        t_anim['v'] += 1
        t = t_anim['v']

        # Fluctuate energy sources
        for key, src in energy.items():
            src['v'] = max(5, min(100, src['v'] + random.uniform(-2, 2)))
            if key == 'solar':
                src['v'] = max(5, 60 + 35*math.sin(t * 0.02))

        # Schedule tasks based on energy
        total_e = sum(s['v'] for s in energy.values()) / 4
        for task in TASKS:
            task['scheduled'] = (task['priority'] / 100) < (total_e / 100)

        cv.delete('all')
        W = cv.winfo_width() or 780
        H = cv.winfo_height() or 380

        # Energy sources — top row
        SRCS = list(energy.items())
        for i, (key, src) in enumerate(SRCS):
            cx = int(70 + i * 170)
            cy = 70
            col = src['col']
            v = src['v']

            # Radial energy display
            _radial_gradient(cv, cx, cy, 46, col+'44', '#020408', 20)
            cv.create_oval(cx-46, cy-46, cx+46, cy+46,
                           outline=col, width=2, fill='#030610')

            # Fill arc
            cv.create_arc(cx-40, cy-40, cx+40, cy+40,
                          start=90, extent=-int(v*3.6),
                          outline=col, width=6, style='arc')

            cv.create_text(cx, cy-8, text=src['icon'],
                           font=('Segoe UI Emoji', 16))
            cv.create_text(cx, cy+10, text=f'{v:.0f}%',
                           fill=col, font=('Consolas', 10, 'bold'))
            cv.create_text(cx, cy+26, text=key.title(),
                           fill=col+'88', font=('Consolas', 7))

        # Total energy flow
        cv.create_text(W//2, 150, text=f'Total available energy: {total_e:.0f}%',
                       fill='#ffee40', font=('Segoe UI', 10, 'bold'))

        # Task scheduler
        task_y = 175
        for i, task in enumerate(TASKS):
            tx = 40; ty = task_y + i*42
            col = task['col']
            active = task['scheduled']

            _aero_pill(cv, tx, ty, tx+200, ty+28,
                       fill=col+'33' if active else '#1a1a1a',
                       outline=col if active else '#333333',
                       width=2 if active else 1)
            cv.create_text(tx+12, ty+14, text=task['name'],
                           fill=col if active else '#444444',
                           font=('Segoe UI', 9, 'bold'), anchor='w')

            # Priority bar
            cv.create_rectangle(tx+210, ty+6, tx+370, ty+22,
                               fill='#0a0a0a', outline='#1a1a1a')
            bar_w = int(task['priority'] * 1.6)
            cv.create_rectangle(tx+210, ty+6, tx+210+bar_w, ty+22,
                               fill=col if active else '#2a2a2a', outline='')

            status = '▶ RUNNING' if active else '⏸ QUEUED'
            cv.create_text(tx+380, ty+14, text=status,
                           fill=col if active else '#333333',
                           font=('Consolas', 8, 'bold'), anchor='w')

        win.after(80, draw)

    draw()



# ══════════════════════════════════════════════════════════════════════════════
#  10 NEW WINDOWS FEATURES  (30% System · 20% AI · 50% Apps)
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. SCREEN MAGNIFIER  (System) ────────────────────────────────────────────
def show_screen_magnifier():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Screen Magnifier')
    win.geometry('460x340')
    win.attributes('-topmost', True)
    style_aero_window(win, '#eef5ff')
    center_window(win, 460, 340)
    register_app_in_taskbar(win)

    tk.Label(win, text='🔍  Screen Magnifier', bg='#eef5ff', fg='#1c3f73',
             font=('Segoe UI', 14, 'bold')).pack(pady=(12,4))
    tk.Label(win, text='Hover over the magnifier lens to zoom in on any screen area.',
             bg='#eef5ff', fg='#4a6a90', font=('Segoe UI', 9)).pack()

    zoom_lv = tk.IntVar(value=2)
    ctrl = tk.Frame(win, bg='#eef5ff')
    ctrl.pack(fill='x', padx=16, pady=6)
    tk.Label(ctrl, text='Zoom Level:', bg='#eef5ff', fg='#1c3f73',
             font=('Segoe UI', 10)).pack(side='left')
    for z in [1, 2, 3, 4, 5]:
        tk.Radiobutton(ctrl, text=f'{z}×', variable=zoom_lv, value=z,
                       bg='#eef5ff', font=('Segoe UI', 9)).pack(side='left', padx=4)

    lens_cv = tk.Canvas(win, width=400, height=200, bg='#001020',
                        highlightthickness=2, highlightbackground='#4f80d4',
                        cursor='crosshair')
    lens_cv.pack(padx=20, pady=8)

    _lens_active = {'v': False}

    def update_lens(event=None):
        if not win.winfo_exists(): return
        try:
            z = zoom_lv.get()
            mx = win.winfo_pointerx(); my = win.winfo_pointery()
            lens_cv.delete('all')
            W, H = 400, 200
            # Draw simulated magnified grid
            cell = 10 * z
            for row in range(0, H, cell):
                for col in range(0, W, cell):
                    shade = random.randint(60, 200)
                    c = f'#{shade:02x}{shade:02x}{min(255,shade+40):02x}'
                    lens_cv.create_rectangle(col, row, col+cell, row+cell,
                                            fill=c, outline='#002040', width=1)
            # Cross-hair
            lens_cv.create_line(W//2, 0, W//2, H, fill='#4fa8ff', width=1, dash=(4,4))
            lens_cv.create_line(0, H//2, W, H//2, fill='#4fa8ff', width=1, dash=(4,4))
            lens_cv.create_text(W//2, H//2, text=f'{z}×',
                                fill='#4fa8ff', font=('Segoe UI', 20, 'bold'))
            lens_cv.create_text(4, H-14, text=f'Pointer: ({mx},{my})',
                                fill='#4fa8ff', font=('Consolas', 8), anchor='w')
        except Exception:
            pass
        if win.winfo_exists():
            win.after(200, update_lens)

    update_lens()
    tk.Button(win, text='Close Magnifier', bg='#4f80d4', fg='white',
              relief='flat', command=win.destroy).pack(pady=4)


# ── 2. TASKBAR MANAGER  (System) ─────────────────────────────────────────────
def show_taskbar_manager():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Taskbar Manager')
    win.geometry('480x380')
    style_aero_window(win, '#eef5ff')
    center_window(win, 480, 380)
    register_app_in_taskbar(win)

    tk.Label(win, text='📌  Taskbar Manager', bg='#eef5ff', fg='#1c3f73',
             font=('Segoe UI', 14, 'bold')).pack(pady=(14,6))
    tk.Label(win, text='Manage open windows in your taskbar.',
             bg='#eef5ff', fg='#4a6a90', font=('Segoe UI', 9)).pack()

    frame = tk.Frame(win, bg='#eef5ff')
    frame.pack(fill='both', expand=True, padx=16, pady=10)

    listbox = tk.Listbox(frame, bg='white', fg='#1c3f73', font=('Segoe UI', 10),
                         selectbackground='#4f80d4', selectforeground='white',
                         relief='flat', bd=1, highlightthickness=1,
                         highlightbackground='#7aa6d8')
    sb = tk.Scrollbar(frame, command=listbox.yview)
    listbox.config(yscrollcommand=sb.set)
    sb.pack(side='right', fill='y')
    listbox.pack(fill='both', expand=True)

    def refresh():
        listbox.delete(0, 'end')
        for w in list(ACTIVE_APPS.keys()):
            try:
                if w.winfo_exists():
                    state_str = 'Minimized' if w.state() == 'withdrawn' else 'Open'
                    listbox.insert('end', f'{w.title():<40} [{state_str}]')
            except Exception:
                pass

    def restore_selected():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        wins = [w for w in ACTIVE_APPS if w.winfo_exists()]
        if idx < len(wins):
            wins[idx].deiconify(); wins[idx].lift(); wins[idx].focus_force()

    def close_selected():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        wins = [w for w in ACTIVE_APPS if w.winfo_exists()]
        if idx < len(wins):
            wins[idx].destroy()
        refresh()

    bf = tk.Frame(win, bg='#eef5ff')
    bf.pack(fill='x', padx=16, pady=8)
    for txt, cmd in [('Restore', restore_selected), ('Close App', close_selected), ('Refresh', refresh)]:
        tk.Button(bf, text=txt, bg='#4f80d4', fg='white', relief='flat',
                  font=('Segoe UI', 9), padx=10, command=cmd).pack(side='left', padx=4)
    refresh()


# ── 3. VIRTUAL DESKTOPS  (System) ────────────────────────────────────────────
_vdesktops = {'current': 1, 'count': 4, 'names': {1:'Desktop 1', 2:'Desktop 2', 3:'Desktop 3', 4:'Desktop 4'}}

def show_virtual_desktops():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Virtual Desktops')
    win.geometry('540x300')
    style_aero_window(win, '#0f1e38')
    center_window(win, 540, 300)
    register_app_in_taskbar(win)

    tk.Label(win, text='⬜  Virtual Desktops', bg='#0f1e38', fg='#7ad4ff',
             font=('Segoe UI', 14, 'bold')).pack(pady=(14,6))
    tk.Label(win, text='Switch between multiple virtual desktop spaces.',
             bg='#0f1e38', fg='#3a6898', font=('Segoe UI', 9)).pack()

    desk_frame = tk.Frame(win, bg='#0f1e38')
    desk_frame.pack(fill='both', expand=True, padx=20, pady=12)

    cur_lbl = tk.Label(win, text=f'Current: {_vdesktops["names"][_vdesktops["current"]]}',
                       bg='#0f1e38', fg='#40c8ff', font=('Segoe UI', 11, 'bold'))
    cur_lbl.pack(pady=(0,8))

    def switch_to(n):
        _vdesktops['current'] = n
        cur_lbl.config(text=f'Current: {_vdesktops["names"][n]}')
        for k, btn in btn_map.items():
            btn.config(bg='#1a4fa8' if k == n else '#0a2040',
                       relief='sunken' if k == n else 'flat')
        show_system_notification('Virtual Desktops', f'Switched to {_vdesktops["names"][n]}')

    btn_map = {}
    for i in range(1, _vdesktops['count'] + 1):
        col = '#1a4fa8' if i == _vdesktops['current'] else '#0a2040'
        rel = 'sunken' if i == _vdesktops['current'] else 'flat'
        b = tk.Button(desk_frame, text=f'🖥\n{_vdesktops["names"][i]}',
                      bg=col, fg='#7ad4ff', relief=rel,
                      font=('Segoe UI', 10), padx=20, pady=18,
                      cursor='hand2', highlightthickness=1,
                      highlightbackground='#2a6ad8',
                      command=lambda n=i: switch_to(n))
        b.grid(row=0, column=i-1, padx=10, pady=6)
        btn_map[i] = b


# ── 4. CLIPBOARD RING  (System) ──────────────────────────────────────────────
_clip_ring = []

def show_clipboard_ring():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Clipboard Ring')
    win.geometry('480x380')
    win.attributes('-topmost', True)
    style_aero_window(win, '#f5f8ff')
    center_window(win, 480, 380)
    register_app_in_taskbar(win)

    tk.Label(win, text='📋  Clipboard Ring', bg='#f5f8ff', fg='#1c3f73',
             font=('Segoe UI', 14, 'bold')).pack(pady=(14,4))
    tk.Label(win, text='Your recent clipboard history. Click any entry to copy again.',
             bg='#f5f8ff', fg='#4a6a90', font=('Segoe UI', 9)).pack()

    # Try to get current clipboard
    try:
        cur = root.clipboard_get()
        if cur and (not _clip_ring or _clip_ring[0] != cur):
            _clip_ring.insert(0, cur)
            if len(_clip_ring) > 20: _clip_ring.pop()
    except Exception:
        pass

    frame = tk.Frame(win, bg='#f5f8ff')
    frame.pack(fill='both', expand=True, padx=16, pady=8)

    lb = tk.Listbox(frame, bg='white', fg='#1c3f73', font=('Consolas', 9),
                    selectbackground='#4f80d4', selectforeground='white',
                    relief='flat', bd=1, highlightthickness=1, highlightbackground='#7aa6d8')
    sb = tk.Scrollbar(frame, command=lb.yview)
    lb.config(yscrollcommand=sb.set)
    sb.pack(side='right', fill='y')
    lb.pack(fill='both', expand=True)

    for i, item in enumerate(_clip_ring):
        lb.insert('end', f'{i+1:2}. {item[:80]}')

    if not _clip_ring:
        lb.insert('end', '(Clipboard is empty — copy something first)')

    def paste_selected(event=None):
        sel = lb.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(_clip_ring):
            try:
                root.clipboard_clear()
                root.clipboard_append(_clip_ring[idx])
                show_system_notification('Clipboard Ring', 'Copied to clipboard!')
            except Exception:
                pass

    lb.bind('<Double-1>', paste_selected)

    def add_current():
        try:
            txt = simpledialog.askstring('Add to Ring', 'Text to add:', parent=win)
            if txt:
                _clip_ring.insert(0, txt)
                lb.insert(0, f'1. {txt[:80]}')
        except Exception:
            pass

    bf = tk.Frame(win, bg='#f5f8ff')
    bf.pack(fill='x', padx=16, pady=8)
    tk.Button(bf, text='Use Selected', command=paste_selected, bg='#4f80d4', fg='white',
              relief='flat', font=('Segoe UI', 9), padx=10).pack(side='left', padx=4)
    tk.Button(bf, text='Add Entry', command=add_current, bg='#2a7a3a', fg='white',
              relief='flat', font=('Segoe UI', 9), padx=10).pack(side='left', padx=4)
    tk.Button(bf, text='Clear All', command=lambda: [_clip_ring.clear(), lb.delete(0,'end')],
              bg='#c94d4d', fg='white', relief='flat', font=('Segoe UI', 9), padx=10).pack(side='left', padx=4)


# ── 5. AI SMART SEARCH  (AI) ─────────────────────────────────────────────────
def show_ai_smart_search():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('AI Smart Search')
    win.geometry('560x440')
    style_aero_window(win, '#0a1428')
    center_window(win, 560, 440)
    register_app_in_taskbar(win)

    tk.Label(win, text='🤖  AI Smart Search', bg='#0a1428', fg='#40c8ff',
             font=('Segoe UI', 14, 'bold')).pack(pady=(14,4))
    tk.Label(win, text='Search notes, tasks, files and get AI-powered suggestions.',
             bg='#0a1428', fg='#2a5a80', font=('Segoe UI', 9)).pack()

    search_var = tk.StringVar()
    search_frame = tk.Frame(win, bg='#0a1428')
    search_frame.pack(fill='x', padx=20, pady=10)
    tk.Entry(search_frame, textvariable=search_var, font=('Segoe UI', 12),
             bg='#0a2040', fg='#60d0ff', insertbackground='#60d0ff',
             relief='flat', highlightthickness=2, highlightbackground='#2a6ad8'
             ).pack(side='left', fill='x', expand=True, ipady=8, padx=(0,8))

    results_text = tk.Text(win, font=('Segoe UI', 10), bg='#060c1e', fg='#a0c8e8',
                           relief='flat', padx=12, pady=10,
                           highlightthickness=1, highlightbackground='#1a3a6a',
                           state='disabled', wrap='word')
    results_text.pack(fill='both', expand=True, padx=20, pady=4)

    SUGGESTIONS = {
        'note': 'notes', 'task': 'tasks', 'file': 'file',
        'alarm': 'alarm', 'journal': 'journal',
    }

    def do_search(event=None):
        q = search_var.get().strip().lower()
        if not q:
            return
        results_text.config(state='normal')
        results_text.delete('1.0', 'end')
        results_text.insert('end', f'🔍 Searching for: "{q}"\n\n', 'header')

        # Search notes
        found = 0
        for n in state.get('notes', []):
            if q in n.get('text','').lower():
                results_text.insert('end', f'📝 Note #{n["id"]}: {n["text"][:100]}\n')
                found += 1
        for t in state.get('tasks', []):
            if q in t.get('task','').lower():
                done = '✅' if t.get('completed') else '⏳'
                results_text.insert('end', f'{done} Task #{t["id"]}: {t["task"][:100]}\n')
                found += 1
        for j in state.get('journal', []):
            if q in j.get('text','').lower():
                results_text.insert('end', f'📓 Journal: {j["date"][:10]} — {j["text"][:80]}\n')
                found += 1

        if found == 0:
            results_text.insert('end', 'No local results found.\n\n')

        # AI suggestion
        results_text.insert('end', f'\n💡 AI Suggestion:\n')
        if any(k in q for k in SUGGESTIONS):
            key = next(k for k in SUGGESTIONS if k in q)
            results_text.insert('end', f'You searched for "{q}". Try launching: {SUGGESTIONS[key]}\n')
        else:
            results_text.insert('end', f'Try adding a note about "{q}" or search the web for more info.\n')
        results_text.config(state='disabled')

    tk.Button(search_frame, text='Search', command=do_search, bg='#4f80d4', fg='white',
              relief='flat', font=('Segoe UI', 10), padx=12, pady=6).pack(side='left')
    search_var.trace('w', lambda *a: win.after(400, do_search))


# ── 6. AI WRITING ASSISTANT  (AI) ────────────────────────────────────────────
def show_ai_writing_assistant():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('AI Writing Assistant')
    win.geometry('620x500')
    style_aero_window(win, '#0d1a30')
    center_window(win, 620, 500)
    register_app_in_taskbar(win)

    tk.Label(win, text='✍  AI Writing Assistant', bg='#0d1a30', fg='#60d0ff',
             font=('Segoe UI', 14, 'bold')).pack(pady=(14,4))
    tk.Label(win, text='Get AI-powered suggestions, rephrasing and grammar tips.',
             bg='#0d1a30', fg='#2a5a80', font=('Segoe UI', 9)).pack()

    input_frame = tk.Frame(win, bg='#0d1a30')
    input_frame.pack(fill='both', expand=True, padx=20, pady=8)

    tk.Label(input_frame, text='Your text:', bg='#0d1a30', fg='#4a9adc',
             font=('Segoe UI', 9, 'bold')).pack(anchor='w')
    input_text = tk.Text(input_frame, font=('Segoe UI', 10), bg='#060e20',
                         fg='#a0c8e8', relief='flat', height=7,
                         highlightthickness=1, highlightbackground='#1a3a6a',
                         insertbackground='#60d0ff', padx=8, pady=6, wrap='word')
    input_text.pack(fill='x', pady=(2,8))
    input_text.insert('1.0', 'Type your text here and click an action below...')

    tk.Label(input_frame, text='AI Output:', bg='#0d1a30', fg='#4a9adc',
             font=('Segoe UI', 9, 'bold')).pack(anchor='w')
    output_text = tk.Text(input_frame, font=('Segoe UI', 10), bg='#04080e',
                          fg='#80e8c0', relief='flat', height=7,
                          highlightthickness=1, highlightbackground='#0a3a2a',
                          padx=8, pady=6, wrap='word', state='disabled')
    output_text.pack(fill='x')

    def show_output(text):
        output_text.config(state='normal')
        output_text.delete('1.0', 'end')
        output_text.insert('1.0', text)
        output_text.config(state='disabled')

    TEMPLATES = {
        'Summarise': lambda t: f'Summary:\n{t[:200].split(".")[0]}. [AI summarised {len(t.split())} words]',
        'Make Formal': lambda t: t.replace('can\'t','cannot').replace('don\'t','do not').replace('I\'m','I am').replace('it\'s','it is') + '\n[Formalised]',
        'Make Casual': lambda t: t.lower().replace('therefore','so').replace('however','but').replace('furthermore','also') + '\n[Made casual]',
        'Fix Grammar': lambda t: t.strip().capitalize().rstrip('.') + '.\n[Grammar checked — basic fix applied]',
        'Expand': lambda t: t + '\n\nFurthermore, it is important to note that this topic encompasses many additional dimensions worthy of consideration. The implications are broad and merit deeper exploration.\n[AI Expanded]',
        'Word Count': lambda t: f'Words: {len(t.split())}\nSentences: {t.count(".")}\nChars: {len(t)}\nParagraphs: {t.count(chr(10))+1}',
    }

    btn_frame = tk.Frame(win, bg='#0d1a30')
    btn_frame.pack(fill='x', padx=20, pady=6)
    for name, fn in TEMPLATES.items():
        tk.Button(btn_frame, text=name, bg='#1a3a6a', fg='#60d0ff', relief='flat',
                  font=('Segoe UI', 8), padx=8, pady=4, cursor='hand2',
                  highlightthickness=1, highlightbackground='#2a5a9a',
                  command=lambda f=fn: show_output(f(input_text.get('1.0','end').strip()))
                  ).pack(side='left', padx=3, pady=2)


# ── 7. QUICK APP LAUNCHER  (Apps) ────────────────────────────────────────────
def show_quick_app_launcher():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Quick Launcher')
    win.geometry('400x500')
    win.attributes('-topmost', True)
    style_aero_window(win, '#f0f5ff')
    center_window(win, 400, 500)

    tk.Label(win, text='⚡  Quick App Launcher', bg='#f0f5ff', fg='#1c3f73',
             font=('Segoe UI', 14, 'bold')).pack(pady=(14,4))

    search_var = tk.StringVar()
    search_entry = tk.Entry(win, textvariable=search_var, font=('Segoe UI', 12),
                            bg='white', fg='#1c3f73', relief='flat',
                            highlightthickness=2, highlightbackground='#4f80d4')
    search_entry.pack(fill='x', padx=16, ipady=8, pady=8)
    search_entry.focus_set()

    frame = tk.Frame(win, bg='#f0f5ff')
    frame.pack(fill='both', expand=True, padx=12, pady=4)

    QUICK_APPS = [
        ('📝', 'Word Processor',  show_word_processor),
        ('🧮', 'Calculator',      show_calculator_app),
        ('📁', 'File Explorer',   show_file_explorer),
        ('🎨', 'Paint',           show_paint_app),
        ('📅', 'Calendar',        show_calendar_app),
        ('📊', 'Spreadsheet',     show_excel_app),
        ('🎵', 'Media Player',    show_media_player),
        ('📓', 'Journal',         show_journal),
        ('⏰', 'Alarm',           show_alarm_manager),
        ('🍅', 'Pomodoro',        show_pomodoro),
        ('✅', 'Habits',          show_habit_tracker),
        ('📌', 'Sticky Notes',    show_sticky_notes),
        ('💰', 'Finance',         show_finance_tracker),
        ('🌍', 'World Clock',     show_world_clock),
        ('🔐', 'Password Gen',    show_password_generator),
        ('🎮', 'Minesweeper',     show_minesweeper_game),
    ]

    buttons = []

    def make_btn(icon, name, cmd):
        row = tk.Frame(frame, bg='white', highlightthickness=1,
                       highlightbackground='#cce0ff', cursor='hand2')
        li = tk.Label(row, text=icon, bg='white', font=('Segoe UI Emoji', 14), width=3)
        li.pack(side='left', padx=8, pady=4)
        ln = tk.Label(row, text=name, bg='white', fg='#1c3f73',
                      font=('Segoe UI', 10), anchor='w')
        ln.pack(side='left', fill='x', expand=True)
        def click():
            win.destroy()
            cmd()
        for w in (row, li, ln):
            w.bind('<Button-1>', lambda e, c=click: c())
            w.bind('<Enter>', lambda e, r=row, l=ln, li=li: [r.config(bg='#dceeff'), l.config(bg='#dceeff'), li.config(bg='#dceeff')])
            w.bind('<Leave>', lambda e, r=row, l=ln, li=li: [r.config(bg='white'), l.config(bg='white'), li.config(bg='white')])
        return row

    all_buttons = []
    for icon, name, cmd in QUICK_APPS:
        b = make_btn(icon, name, cmd)
        b.pack(fill='x', pady=2)
        all_buttons.append((name.lower(), b))

    def filter_apps(*args):
        q = search_var.get().lower()
        for name, btn in all_buttons:
            if q in name or not q:
                btn.pack(fill='x', pady=2)
            else:
                btn.pack_forget()

    search_var.trace('w', filter_apps)


# ── 8. FOCUS MODE  (Apps/Productivity) ───────────────────────────────────────
def show_focus_mode():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Focus Mode')
    win.geometry('480x360')
    style_aero_window(win, '#060e18')
    center_window(win, 480, 360)
    register_app_in_taskbar(win)

    tk.Label(win, text='🎯  Focus Mode', bg='#060e18', fg='#40e8a0',
             font=('Segoe UI', 16, 'bold')).pack(pady=(20,4))
    tk.Label(win, text='Block distractions and focus on one task.',
             bg='#060e18', fg='#1a6040', font=('Segoe UI', 10)).pack()

    task_var = tk.StringVar(value='Write report')
    tk.Label(win, text='Current Focus Task:', bg='#060e18', fg='#30c880',
             font=('Segoe UI', 10)).pack(pady=(16,2))
    task_entry = tk.Entry(win, textvariable=task_var, font=('Segoe UI', 13),
                          bg='#0a1a10', fg='#40e8a0', insertbackground='#40e8a0',
                          relief='flat', highlightthickness=2, highlightbackground='#2ae080',
                          justify='center')
    task_entry.pack(fill='x', padx=40, ipady=10, pady=6)

    timer_lbl = tk.Label(win, text='25:00', bg='#060e18', fg='#40e8a0',
                         font=('Consolas', 48, 'bold'))
    timer_lbl.pack(pady=8)

    prog_cv = tk.Canvas(win, height=8, bg='#060e18', highlightthickness=0)
    prog_cv.pack(fill='x', padx=40, pady=4)
    prog_bar = prog_cv.create_rectangle(0, 0, 0, 8, fill='#40e8a0', outline='')

    _focus = {'running': False, 'seconds': 25*60, 'total': 25*60}

    def draw_prog():
        W = prog_cv.winfo_width() or 400
        frac = 1 - _focus['seconds'] / _focus['total']
        prog_cv.coords(prog_bar, 0, 0, int(W * frac), 8)

    def tick():
        if not _focus['running'] or not win.winfo_exists(): return
        _focus['seconds'] = max(0, _focus['seconds'] - 1)
        m, s = divmod(_focus['seconds'], 60)
        timer_lbl.config(text=f'{m:02d}:{s:02d}')
        draw_prog()
        if _focus['seconds'] == 0:
            _focus['running'] = False
            start_btn.config(text='Start')
            play_windows7_exclamation()
            messagebox.showinfo('Focus Mode', f'✅ Focus session complete!\nTask: {task_var.get()}')
        else:
            win.after(1000, tick)

    def toggle():
        _focus['running'] = not _focus['running']
        if _focus['running']:
            start_btn.config(text='Pause')
            tick()
        else:
            start_btn.config(text='Resume')

    def reset():
        _focus['running'] = False
        _focus['seconds'] = _focus['total']
        start_btn.config(text='Start')
        m, s = divmod(_focus['total'], 60)
        timer_lbl.config(text=f'{m:02d}:{s:02d}')
        prog_cv.coords(prog_bar, 0, 0, 0, 8)

    def set_duration(mins):
        _focus['running'] = False
        _focus['seconds'] = mins * 60
        _focus['total'] = mins * 60
        reset()

    bf = tk.Frame(win, bg='#060e18')
    bf.pack(pady=6)
    start_btn = tk.Button(bf, text='Start', command=toggle, bg='#1a6040', fg='#40e8a0',
                          relief='flat', font=('Segoe UI', 12, 'bold'), padx=20, pady=8,
                          cursor='hand2')
    start_btn.pack(side='left', padx=6)
    tk.Button(bf, text='Reset', command=reset, bg='#1a3a40', fg='#40c8a0',
              relief='flat', font=('Segoe UI', 10), padx=12, pady=8).pack(side='left', padx=4)

    dur_frame = tk.Frame(win, bg='#060e18')
    dur_frame.pack()
    tk.Label(dur_frame, text='Duration:', bg='#060e18', fg='#1a6040',
             font=('Segoe UI', 8)).pack(side='left')
    for mins in [5, 10, 25, 45, 60]:
        tk.Button(dur_frame, text=f'{mins}m', command=lambda m=mins: set_duration(m),
                  bg='#0a2018', fg='#40a880', relief='flat',
                  font=('Segoe UI', 8), padx=6).pack(side='left', padx=2)


# ── 9. DARK/LIGHT MODE TOGGLE  (System/Apps) ─────────────────────────────────
_theme_mode = {'dark': False}

def show_theme_toggle():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('Dark / Light Mode')
    win.geometry('400x300')
    style_aero_window(win, '#f4f7ff')
    center_window(win, 400, 300)
    register_app_in_taskbar(win)

    def apply_mode(dark):
        _theme_mode['dark'] = dark
        if dark:
            bg = '#1a1a2e'; fg = '#e0e0ff'; acc = '#4f80d4'
            win.config(bg=bg)
            for w in win.winfo_children():
                try: w.config(bg=bg, fg=fg)
                except: pass
            if desktop_win and desktop_win.winfo_exists():
                desktop_win.config(bg='#0a0a1a')
            preview_lbl.config(text='🌙 Dark Mode Active', bg='#1a1a2e', fg='#9090ff')
            show_system_notification('Theme', 'Dark Mode enabled')
        else:
            bg = '#f4f7ff'; fg = '#1c3f73'; acc = '#4f80d4'
            win.config(bg=bg)
            for w in win.winfo_children():
                try: w.config(bg=bg, fg=fg)
                except: pass
            if desktop_win and desktop_win.winfo_exists():
                desktop_win.config(bg='#0f1733')
            preview_lbl.config(text='☀ Light Mode Active', bg='#f4f7ff', fg='#1c3f73')
            show_system_notification('Theme', 'Light Mode enabled')

    current_bg = '#1a1a2e' if _theme_mode['dark'] else '#f4f7ff'
    win.config(bg=current_bg)

    preview_lbl = tk.Label(win,
        text='🌙 Dark Mode Active' if _theme_mode['dark'] else '☀ Light Mode Active',
        bg=current_bg, fg='#9090ff' if _theme_mode['dark'] else '#1c3f73',
        font=('Segoe UI', 18, 'bold'))
    preview_lbl.pack(pady=(40,20))

    btn_frame = tk.Frame(win, bg=current_bg)
    btn_frame.pack(pady=16)
    tk.Button(btn_frame, text='🌙  Dark Mode', command=lambda: apply_mode(True),
              bg='#1a1a3a', fg='white', relief='flat',
              font=('Segoe UI', 12, 'bold'), padx=20, pady=12,
              cursor='hand2').pack(side='left', padx=8)
    tk.Button(btn_frame, text='☀  Light Mode', command=lambda: apply_mode(False),
              bg='#ffd700', fg='#222', relief='flat',
              font=('Segoe UI', 12, 'bold'), padx=20, pady=12,
              cursor='hand2').pack(side='left', padx=8)

    tk.Label(win, text='Applies to the desktop and new windows.',
             bg=current_bg, fg='#6080a0', font=('Segoe UI', 9)).pack(pady=8)


# ── 10. APP PINBOARD  (Apps) ─────────────────────────────────────────────────
def show_app_pinboard():
    win = tk.Toplevel(desktop_win if desktop_win and desktop_win.winfo_exists() else root)
    win.title('App Pinboard')
    win.geometry('560x440')
    style_aero_window(win, '#f5f8ff')
    center_window(win, 560, 440)
    register_app_in_taskbar(win)

    tk.Label(win, text='📌  App Pinboard', bg='#f5f8ff', fg='#1c3f73',
             font=('Segoe UI', 14, 'bold')).pack(pady=(14,4))
    tk.Label(win, text='Pin your favourite apps for one-click access.',
             bg='#f5f8ff', fg='#4a6a90', font=('Segoe UI', 9)).pack()

    pinned = state.setdefault('pinboard', [
        {'icon': '📝', 'name': 'Word', 'key': 'text editor'},
        {'icon': '📊', 'name': 'Spreadsheet', 'key': 'spreadsheet'},
        {'icon': '🎨', 'name': 'Paint', 'key': 'paint'},
        {'icon': '📅', 'name': 'Calendar', 'key': 'calendar'},
        {'icon': '🧮', 'name': 'Calculator', 'key': 'calculator'},
        {'icon': '📓', 'name': 'Journal', 'key': 'journal'},
    ])

    grid_frame = tk.Frame(win, bg='#f5f8ff')
    grid_frame.pack(fill='both', expand=True, padx=20, pady=10)

    def render_pins():
        for w in grid_frame.winfo_children():
            w.destroy()
        for idx, pin in enumerate(pinned):
            col = idx % 4
            row = idx // 4
            card = tk.Frame(grid_frame, bg='white', relief='flat',
                            highlightthickness=1, highlightbackground='#c0d8f0',
                            cursor='hand2')
            card.grid(row=row, column=col, padx=8, pady=8, sticky='nsew')
            tk.Label(card, text=pin['icon'], bg='white',
                     font=('Segoe UI Emoji', 24)).pack(pady=(14,2))
            tk.Label(card, text=pin['name'], bg='white', fg='#1c3f73',
                     font=('Segoe UI', 9, 'bold')).pack(pady=(0,10))

            def click_pin(k=pin['key']):
                if k in APP_MAP:
                    APP_MAP[k]()
                else:
                    launch_app(k)

            for w in (card,) + tuple(card.winfo_children()):
                w.bind('<Button-1>', lambda e, f=click_pin: f())
                w.bind('<Enter>', lambda e, c=card: c.config(bg='#dceeff', highlightbackground='#4f80d4'))
                w.bind('<Leave>', lambda e, c=card: c.config(bg='white', highlightbackground='#c0d8f0'))

        for col in range(4):
            grid_frame.columnconfigure(col, weight=1)

    render_pins()

    def add_pin():
        icon = simpledialog.askstring('Add Pin', 'Emoji icon (e.g. 🎮):', parent=win) or '📦'
        name = simpledialog.askstring('Add Pin', 'Display name:', parent=win)
        key  = simpledialog.askstring('Add Pin', 'App key (e.g. "snake", "calculator"):', parent=win)
        if name and key:
            pinned.append({'icon': icon, 'name': name, 'key': key.lower()})
            state['pinboard'] = pinned
            save_state()
            render_pins()

    tk.Button(win, text='+ Add Pin', command=add_pin, bg='#4f80d4', fg='white',
              relief='flat', font=('Segoe UI', 10), padx=16).pack(pady=8)


# ── Register the 10 new features in APP_MAP ────────────────────────────────────
APP_MAP.update({
    'magnifier':          lambda: show_screen_magnifier(),
    'screen magnifier':   lambda: show_screen_magnifier(),
    'taskbar manager':    lambda: show_taskbar_manager(),
    'virtual desktops':   lambda: show_virtual_desktops(),
    'task view':          lambda: show_virtual_desktops(),
    'clipboard ring':     lambda: show_clipboard_ring(),
    'clip ring':          lambda: show_clipboard_ring(),
    'ai search':          lambda: show_ai_smart_search(),
    'smart search':       lambda: show_ai_smart_search(),
    'ai writing':         lambda: show_ai_writing_assistant(),
    'writing assistant':  lambda: show_ai_writing_assistant(),
    'quick launcher':     lambda: show_quick_app_launcher(),
    'launcher':           lambda: show_quick_app_launcher(),
    'focus mode':         lambda: show_focus_mode(),
    'focus':              lambda: show_focus_mode(),
    'dark mode':          lambda: show_theme_toggle(),
    'light mode':         lambda: show_theme_toggle(),
    'theme toggle':       lambda: show_theme_toggle(),
    'pinboard':           lambda: show_app_pinboard(),
    'app pinboard':       lambda: show_app_pinboard(),
    'word':               lambda: show_word_processor(),
    'word processor':     lambda: show_word_processor(),
    'microsoft word':     lambda: show_word_processor(),
})


# ── Register all 15 in APP_MAP ────────────────────────────────────────────────
APP_MAP.update({
    'oo filesystem':       lambda: show_oo_filesystem(),
    'object filesystem':   lambda: show_oo_filesystem(),
    'temporal os':         lambda: show_temporal_os(),
    'time slider':         lambda: show_temporal_os(),
    'semantic intent':     lambda: show_semantic_intent(),
    'intent ui':           lambda: show_semantic_intent(),
    'p2p storage':         lambda: show_p2p_storage(),
    'distributed storage': lambda: show_p2p_storage(),
    'biometric ui':        lambda: show_biometric_ui(),
    'eye scaling':         lambda: show_biometric_ui(),
    'crash recovery':      lambda: show_crash_recovery(),
    'kernel recovery':     lambda: show_crash_recovery(),
    'multi brain':         lambda: show_multi_brain(),
    'collaborative mirror':lambda: show_multi_brain(),
    '3d desktop':          lambda: show_spatial_desktop(),
    'spatial desktop':     lambda: show_spatial_desktop(),
    'desktop cube':        lambda: show_spatial_desktop(),
    'self optimising':     lambda: show_self_optimising_kernel(),
    'generative kernel':   lambda: show_self_optimising_kernel(),
    'quantum sandbox':     lambda: show_quantum_sandbox(),
    'crypto sandbox':      lambda: show_quantum_sandbox(),
    'holographic stack':   lambda: show_holographic_stack(),
    'holographic':         lambda: show_holographic_stack(),
    'fluid typography':    lambda: show_fluid_typography(),
    'typographic grid':    lambda: show_fluid_typography(),
    'persistence engine':  lambda: show_orthogonal_persistence(),
    'orthogonal':          lambda: show_orthogonal_persistence(),
    'hardware morphing':   lambda: show_hardware_morphing(),
    'cpu morphing':        lambda: show_hardware_morphing(),
    'energy harvester':    lambda: show_energy_harvester(),
    'energy scheduler':    lambda: show_energy_harvester(),
})


# --- Wire buttons ---
btn_search.config(command=on_search)
btn_handover.config(command=on_handover_web)
btn_refresh_files.config(command=refresh_files_list)
btn_quarantine.config(command=on_quarantine_selected)
btn_encrypt.config(command=lambda: handle_encrypt(False))
btn_decrypt.config(command=lambda: handle_encrypt(True))
btn_delete_perm.config(command=on_delete_perm)
btn_send.config(command=process_input)

# --- Startup checks ---
load_state()
if 'apps' not in state:
    state['apps'] = []
# ensure built-in Google app is available as default
if not state['apps']:
    register_app('Google', 'https://www.google.com', 'Web')
if os.path.exists(SHUTDOWN_FLAG):
    root.withdraw()
    if messagebox.askyesno('Restore', 'Assistant is quarantined. Do you want to restore it now?'):
        if restore_quarantine():
            messagebox.showinfo('Restored', 'Assistant restored successfully.')
        else:
            messagebox.showerror('Failed', 'Could not restore the assistant. Close and inspect quarantined files.')
            if os.path.exists(DATA_DIR) and any(os.scandir(DATA_DIR)):
                if messagebox.askyesno('Continue', 'Your assistant data folder exists. Clear the stale quarantine lock and continue?'):
                    try:
                        os.remove(SHUTDOWN_FLAG)
                    except Exception:
                        pass
                else:
                    root.destroy()
                    raise SystemExit
            else:
                try:
                    os.remove(SHUTDOWN_FLAG)
                except Exception:
                    pass
    else:
        root.destroy()
        raise SystemExit
else:
    if not security:
        ok = ensure_password_set()
        if not ok:
            messagebox.showwarning('No password', 'Assistant requires a password. Exiting.')
            root.destroy()
            raise SystemExit

refresh_files_list()
post_message('Hello Ryan — secure assistant ready. Use Deep Search or manage files in the right panel.', 'assistant')
show_login()

if __name__ == '__main__':
    root.mainloop()