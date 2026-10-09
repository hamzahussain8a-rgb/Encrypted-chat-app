from customtkinter import *
import socket
import threading
import queue
from datetime import datetime

from pgp_crypto import encrypt_message, decrypt_message

HOST = "127.0.0.1"  # change to the server's LAN IP when running on another machine
PORT = 5050

# ---------- theme ----------
set_appearance_mode("dark")
BG_SIDE = "#111b21"
BG_CHAT = "#0b141a"
BG_BAR = "#202c33"
BG_INPUT = "#2a3942"
BG_SYSTEM = "#182229"
BUBBLE_ME = "#005c4b"
BUBBLE_THEM = "#202c33"
ACCENT = "#00a884"
ACCENT_HOVER = "#06cf9c"
TEXT = "#e9edef"
MUTED = "#8696a0"
ROW_HOVER = "#1a262d"
ROW_ACTIVE = "#2a3942"
AVATAR_COLORS = ["#e26a5d", "#d98b2b", "#4f9d69", "#3f8ed1", "#8a6fd1", "#cf5fa0", "#2aa3a3"]

inbox = queue.Queue()  # network thread -> GUI thread

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
reader = sock.makefile("r", encoding="utf-8", newline="\n")


def send(code, payload=""):
    """Every outgoing message is one line: CODE:payload"""
    try:
        sock.sendall(f"{code}:{payload}\n".encode("utf-8"))
    except OSError:
        inbox.put(("ERR", "Disconnected from server"))


def read_line():
    line = reader.readline()
    if not line:
        return None, None
    code, _, payload = line.rstrip("\n").partition(":")
    return code.upper(), payload


def recv_loop():
    while True:
        try:
            code, payload = read_line()
        except (OSError, UnicodeDecodeError):
            code = None
        if code is None:
            inbox.put(("ERR", "Disconnected from server"))
            break
        inbox.put((code, payload))


root = CTk()
root.geometry("1000x640")
root.minsize(720, 460)
root.configure(fg_color=BG_CHAT)

# ---------- login ----------
username = None
while username is None:
    name = CTkInputDialog(text="Enter your username:", title="Login").get_input()
    if name is None:
        sock.close()
        raise SystemExit
    send("NAME", name.strip())
    code, payload = read_line()
    if code == "OK":
        username = payload
    elif code is None:
        raise SystemExit("Server closed the connection")

root.title(f"Chat - {username}")

# ---------- state ----------
active = None
last_users = []

F_TITLE = CTkFont(size=22, weight="bold")
F_NAME = CTkFont(size=15, weight="bold")
F_BODY = CTkFont(size=14)
F_SMALL = CTkFont(size=11)


def avatar(parent, name, size):
    return CTkLabel(parent, text=name[:1].upper(), width=size, height=size,
                    corner_radius=size // 2, fg_color=AVATAR_COLORS[sum(map(ord, name)) % len(AVATAR_COLORS)],
                    text_color="white", font=CTkFont(size=size // 2, weight="bold"))


# ---------- sidebar ----------
sidebar = CTkFrame(root, width=290, fg_color=BG_SIDE, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

CTkLabel(sidebar, text="Chats", font=F_TITLE, text_color=TEXT, anchor="w").pack(fill="x", padx=20, pady=(20, 4))
CTkLabel(sidebar, text="Online now", font=F_SMALL, text_color=MUTED, anchor="w").pack(fill="x", padx=20, pady=(0, 8))

me_bar = CTkFrame(sidebar, fg_color=BG_BAR, corner_radius=0, height=64)
me_bar.pack(side="bottom", fill="x")
me_bar.pack_propagate(False)
avatar(me_bar, username, 38).pack(side="left", padx=(14, 10))
me_text = CTkFrame(me_bar, fg_color="transparent")
me_text.pack(side="left")
CTkLabel(me_text, text=username, font=F_NAME, text_color=TEXT, anchor="w").pack(anchor="w")
CTkLabel(me_text, text="● online", font=F_SMALL, text_color=ACCENT, anchor="w").pack(anchor="w")

user_con = CTkScrollableFrame(sidebar, fg_color="transparent", corner_radius=0)
user_con.pack(fill="both", expand=True, padx=(6, 0))

# ---------- chat pane ----------
chat_con = CTkFrame(root, fg_color=BG_CHAT, corner_radius=0)
chat_con.pack(side="left", fill="both", expand=True)

header = CTkFrame(chat_con, fg_color=BG_BAR, corner_radius=0, height=64)
header.pack(fill="x")
header.pack_propagate(False)
header_inner = CTkFrame(header, fg_color="transparent")
header_inner.pack(side="left", padx=16, fill="y")
header_av = avatar(header_inner, "?", 40)
header_title = CTkLabel(header_inner, text="Select a chat", font=F_NAME, text_color=TEXT, anchor="w")
header_sub = CTkLabel(header_inner, text="Pick someone from the sidebar", font=F_SMALL, text_color=MUTED, anchor="w")
header_title.grid(row=0, column=1, sticky="sw", padx=(12, 0))
header_sub.grid(row=1, column=1, sticky="nw", padx=(12, 0))
header_inner.grid_rowconfigure((0, 1), weight=1)

message_con = CTkScrollableFrame(chat_con, fg_color=BG_CHAT, corner_radius=0)
message_con.pack(fill="both", expand=True, padx=(0, 0))

input_bar = CTkFrame(chat_con, fg_color=BG_BAR, corner_radius=0, height=70)
input_bar.pack(fill="x", side="bottom")
input_bar.pack_propagate(False)

message_box = CTkEntry(input_bar, placeholder_text="Type a message", height=42, corner_radius=21,
                       fg_color=BG_INPUT, border_width=0, text_color=TEXT, font=F_BODY)
message_box.pack(side="left", fill="x", expand=True, padx=(16, 10), pady=14)

sendbtn = CTkButton(input_bar, text="➤", width=42, height=42, corner_radius=21, font=CTkFont(size=18),
                    fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white")
sendbtn.pack(side="left", padx=(0, 16), pady=14)


# ---------- helpers ----------
def scroll_bottom():
    root.update_idletasks()
    message_con._parent_canvas.yview_moveto(1.0)


def clear_messages():
    for w in message_con.winfo_children():
        w.destroy()


def set_input_enabled(enabled):
    state = "normal" if enabled else "disabled"
    message_box.configure(state=state)
    sendbtn.configure(state=state, fg_color=ACCENT if enabled else BG_INPUT)


def show_system(text):
    row = CTkFrame(message_con, fg_color="transparent")
    row.pack(fill="x", pady=8)
    CTkLabel(row, text=text, font=F_SMALL, text_color=MUTED, fg_color=BG_SYSTEM,
             corner_radius=10).pack(ipadx=10, ipady=3)
    scroll_bottom()


def show_empty_state(text):
    clear_messages()
    CTkLabel(message_con, text=text, font=F_BODY, text_color=MUTED).pack(pady=120)


def show_message(text, mine):
    row = CTkFrame(message_con, fg_color="transparent")
    row.pack(fill="x", padx=10, pady=3)
    bubble = CTkFrame(row, fg_color=BUBBLE_ME if mine else BUBBLE_THEM, corner_radius=14)
    bubble.pack(side="right" if mine else "left", padx=6)
    CTkLabel(bubble, text=text, font=F_BODY, text_color=TEXT, wraplength=380,
             justify="left").pack(padx=14, pady=(8, 0), anchor="w")
    CTkLabel(bubble, text=datetime.now().strftime("%H:%M"), font=F_SMALL,
             text_color=MUTED).pack(padx=12, pady=(0, 6), anchor="e")
    scroll_bottom()


def set_header(name):
    if name:
        header_av.configure(text=name[:1].upper(),
                            fg_color=AVATAR_COLORS[sum(map(ord, name)) % len(AVATAR_COLORS)])
        header_av.grid(row=0, column=0, rowspan=2)
        header_title.configure(text=name)
        header_sub.configure(text="● connected", text_color=ACCENT)
    else:
        header_av.grid_remove()
        header_title.configure(text="Select a chat")
        header_sub.configure(text="Pick someone from the sidebar", text_color=MUTED)


def update_users(users):
    global last_users
    last_users = users
    for w in user_con.winfo_children():
        w.destroy()
    if not users:
        CTkLabel(user_con, text="Nobody else is online yet", font=F_BODY,
                 text_color=MUTED).pack(padx=10, pady=30)
        return
    for u in users:
        make_user_row(u)


def make_user_row(name):
    selected = name == active
    base = ROW_ACTIVE if selected else "transparent"
    row = CTkFrame(user_con, fg_color=base, corner_radius=10, height=58, cursor="hand2")
    row.pack(fill="x", padx=6, pady=2)
    row.pack_propagate(False)
    av = avatar(row, name, 38)
    av.pack(side="left", padx=(10, 12))
    lbl = CTkLabel(row, text=name, font=F_NAME, text_color=TEXT, anchor="w")
    lbl.pack(side="left", fill="x", expand=True)
    dot = CTkLabel(row, text="●", font=F_SMALL, text_color=ACCENT)
    dot.pack(side="right", padx=14)

    def enter(_):
        if name != active:
            row.configure(fg_color=ROW_HOVER)

    def leave(_):
        x, y = row.winfo_pointerxy()
        under = row.winfo_containing(x, y)
        if under is None or not str(under).startswith(str(row)):
            row.configure(fg_color=ROW_ACTIVE if name == active else "transparent")

    for w in (row, av, lbl, dot):
        w.bind("<Button-1>", lambda e, n=name: send("CONN", n))
        w.bind("<Enter>", enter)
        w.bind("<Leave>", leave)


# ---------- network events ----------
def process_inbox():
    global active
    while not inbox.empty():
        code, payload = inbox.get()
        if code == "USERS":
            update_users([u for u in payload.split(",") if u])
        elif code == "CONN":
            active = payload
            clear_messages()
            set_header(payload)
            set_input_enabled(True)
            update_users(last_users)
            show_system(f"Connection established with {payload}")
            message_box.focus()
        elif code == "MSG":
            _, _, encrypted_text = payload.partition(":")
            try:
                text = decrypt_message(encrypted_text)
            except Exception:
                text = "[could not decrypt message]"
            show_message(text, mine=False)
        elif code == "LEFT":
            active = None
            set_header(None)
            set_input_enabled(False)
            update_users(last_users)
            show_system(f"{payload} left the chat")
        elif code == "ERR":
            show_system(payload)
            if payload.startswith("Disconnected"):
                set_input_enabled(False)
    root.after(100, process_inbox)


def on_send(event=None):
    text = message_box.get().strip()
    if not text or active is None:
        return
    send("SEND", encrypt_message(text))  # the code is attached automatically; payload is encrypted
    message_box.delete(0, END)
    show_message(text, mine=True)  # show our own plaintext locally, we already know what we typed


message_box.bind("<Return>", on_send)
sendbtn.configure(command=on_send)


def on_close():
    send("EXIT")
    try:
        sock.close()
    except OSError:
        pass
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)

# ---------- start ----------
set_header(None)
set_input_enabled(False)
update_users([])
show_empty_state("Select someone from the sidebar to start chatting")
threading.Thread(target=recv_loop, daemon=True).start()
send("LIST")
process_inbox()
root.mainloop()
