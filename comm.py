import socket
import threading

from pgp_crypto import decrypt_message  # only used if DEBUG_DECRYPT is on below

# Protocol (one line per message, "CODE:payload\n")
# Client -> Server: NAME:<username>  LIST:  CONN:<username>  SEND:<text>  EXIT:
# Server -> Client: OK:<username>  USERS:<a,b,c>  CONN:<username>
#                   MSG:<sender>:<text>  LEFT:<username>  ERR:<reason>

HOST = "0.0.0.0"
PORT = 5050
DEBUG_DECRYPT = False  # set True to have the server print decrypted content (it has the key — see pgp_crypto.py docstring)

clients = {}   # username -> socket
partners = {}  # username -> username they're chatting with
lock = threading.RLock()


def send(conn, code, payload=""):
    try:
        conn.sendall(f"{code}:{payload}\n".encode("utf-8"))
    except OSError:
        pass


def send_users(name):
    others = [u for u in clients if u != name]
    send(clients[name], "USERS", ",".join(others))


def broadcast_users():
    for name in list(clients):
        send_users(name)


def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")
    reader = conn.makefile("r", encoding="utf-8", newline="\n")
    name = None
    try:
        for line in reader:
            code, _, payload = line.rstrip("\n").partition(":")
            code = code.upper()

            if name is None:
                if code != "NAME":
                    send(conn, "ERR", "Register first")
                    continue
                payload = payload.strip()
                with lock:
                    if not payload or ":" in payload or "," in payload:
                        send(conn, "ERR", "Invalid username")
                    elif payload in clients:
                        send(conn, "ERR", "Username taken")
                    else:
                        name = payload
                        clients[name] = conn
                        send(conn, "OK", name)
                        broadcast_users()
                        print(f"[JOINED] {name}")
                continue

            with lock:
                if code == "LIST":
                    send_users(name)

                elif code == "CONN":
                    target = payload.strip()
                    if target == name or target not in clients:
                        send(conn, "ERR", "User not available")
                    elif target in partners and partners[target] != name:
                        send(conn, "ERR", "User is busy")
                    else:
                        partners[name] = target
                        partners[target] = name
                        send(clients[name], "CONN", target)
                        send(clients[target], "CONN", name)
                        print(f"[PAIRED] {name} <-> {target}")

                elif code == "SEND":
                    # payload is already an encrypted blob from pgp_crypto.encrypt_message().
                    # The server relays it as-is without needing to touch the contents.
                    target = partners.get(name)
                    if target is None:
                        send(conn, "ERR", "Not connected to anyone")
                    else:
                        send(clients[target], "MSG", f"{name}:{payload}")
                        if DEBUG_DECRYPT:
                            # proves the server CAN read it since it holds the same
                            # hardcoded private key — this is not true end-to-end secrecy
                            try:
                                print(f"[{name}] ==> [{target}] {decrypt_message(payload)}")
                            except Exception:
                                print(f"[{name}] ==> [{target}] <could not decrypt>")
                        else:
                            print(f"[{name}] ==> [{target}] <encrypted, {len(payload)} chars>")

                elif code == "EXIT":
                    break

                else:
                    send(conn, "ERR", "Unknown code")
    except (OSError, UnicodeDecodeError):
        pass
    finally:
        cleanup(conn, name)


def cleanup(conn, name):
    with lock:
        if name is not None:
            clients.pop(name, None)
            target = partners.pop(name, None)
            if target is not None:
                partners.pop(target, None)
                if target in clients:
                    send(clients[target], "LEFT", name)
            broadcast_users()
            print(f"[LEFT] {name}")
    try:
        conn.close()
    except OSError:
        pass


def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    start()
