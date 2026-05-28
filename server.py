import socket, os, ast
import threading, time

#set
HOST = '192.168.1.4'
PORT = 55555
ENC = 'utf-8'
BANLIST = 'banlist.txt'
SKIP_FILES = {'server.py', 'client.py', 'README.md', 'banlist.txt', 'LICENSE'}

#server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

clients   = []
nicknames = []
banlist   = []
running   = True

def get_shareable_files():
    return [f for f in os.listdir() if f not in SKIP_FILES and os.path.isfile(f)]

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

#banlist func
def load_banlist():
    global banlist
    try:
        with open(BANLIST, 'r') as f:
            banlist = ast.literal_eval(f.read())
    except (FileNotFoundError, ValueError):
        banlist = []

def save_banlist():
    with open(BANLIST, 'w') as f:
        f.write(str(banlist))

#broadcast func
def broadcast(data, exclude = None):
    for c in list(clients):
        if c is not exclude:
            try:
                c.send(data)
            except Exception:
                pass

def handle(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                raise ConnectionResetError
            broadcast(message)
        except Exception:
            if client in clients:
                index    = clients.index(client)
                nickname = nicknames[index]
                clients.remove(client)
                nicknames.remove(nickname)
                client.close()
                broadcast(f"{nickname} left the chat".encode(ENC))
            break

#kick or ban func
def kick(nickname, reason = 'k'):
    if nickname not in nicknames:
        print("user not found")
        return
    index  = nicknames.index(nickname)
    client = clients[index]

    if reason == 'k':
        client.send("you were kicked".encode(ENC))
        broadcast(f"{nickname} was kicked by the great admin".encode(ENC))
    elif reason == 'b':
        client.send("you were banned".encode(ENC))
        broadcast(f"{nickname} was kicked and banned by the great admin".encode(ENC))
    
    client.close()
    print(f"{nickname} kicked")


def receive():
    while running:
        load_banlist()
        try:
            client, address = server.accept()
        except Exception:
            break

        print(f"connected with {address}")
        client.send(b'NICK')

        try:
            nickname = client.recv(1024).decode(ENC).strip()
        except Exception:
            client.close()
            continue

        if nickname in nicknames:
            client.send(b'ND')
            client.close()
            continue
        if nickname in banlist:
            client.send(b'BAN')
            client.close()
            continue

        nicknames.append(nickname)
        clients.append(client)

        print(f"client nickname: {nickname}")
        broadcast(f"{nickname} joined the chat".encode(ENC))
        client.send("connected to the server".encode(ENC))

        threading.Thread(target=handle, args=(client,), daemon=True).start()

def send_file_to(nickname, filename):
    if nickname not in nicknames:
        print("user not found")
        return False

    if not os.path.isfile(filename) or filename in SKIP_FILES:
        print("file not found")
        return False

    with open(filename, 'rb') as f:
        data = f.read()

    _, ext = os.path.splitext(filename)
    header = f"FILE:{ext}:{len(data)}\n".encode(ENC)
    client = clients[nicknames.index(nickname)]

    try:
        client.send(header)
        client.sendall(data)
        return True
    except Exception as e:
        print(f"send failed: {e}")
        return False

#admin command loop
def server_commands():
    global running

    while running:
        load_banlist()
        try:
            cmd = input("").strip()
        except (EOFError, KeyboardInterrupt):
            cmd = "/shutdown"

        if cmd in ('/shutdown', '/s'):
            running = False
            broadcast("server shutting down".encode(ENC))
            for c in list(clients):
                try:
                    c.send(b'SERVER_SHUTDOWN')
                    c.close()
                except Exception:
                    pass
            clients.clear()
            nicknames.clear()
            time.sleep(0.3)
            server.close()

            print("server closed")
            #os._exit(0)
            break

        elif cmd.startswith('/kick '):
            kick(cmd[6:].strip(), 'k')

        elif cmd.startswith('/ban '):
            name = cmd[5:].strip()
            kick(name, 'b')
            if name not in banlist:
                banlist.append(name)
                save_banlist()

        elif cmd.startswith('/unban '):
            name = cmd[7:].strip()
            if name in banlist:
                banlist.remove(name)
                save_banlist()
                broadcast(f"{name} was unbanned".encode(ENC))
                print(f"{name} unbanned")
            else:
                print("user not in ban list")

        elif cmd.startswith('/ms '):
            msg = cmd[4:]
            print(f"admin: {msg}")
            broadcast(f"admin: {msg}".encode(ENC))

        elif cmd == '/clients':
            if nicknames:
                for i, n in enumerate(nicknames, 1):
                    print(f"  {i}. {n}")
            else:
                print("no clients connected")

        elif cmd == '/blist':
            if banlist:
                for i, n in enumerate(banlist, 1):
                    print(f"  {i}. {n}")
            else:
                print("ban list is empty")

        elif cmd == '/brcl':
            if nicknames:
                msg = "  (admin)\nclient list\n- " + "\n- ".join(nicknames)
                print(msg)
                broadcast(msg.encode(ENC))
            else:
                print("no clients connected")

        elif cmd == '/brbl':
            if banlist:
                msg = "  (admin)\nban list\n- " + "\n- ".join(banlist)
                print(msg)
                broadcast(msg.encode(ENC))
            else:
                print("ban list is empty")

        elif cmd == '/sendf':
            files = get_shareable_files()
            if not files:
                print("no shareable files available")
                continue
            uname = input("username : ").strip()
            print("available files:", files)
            fname = input("file name : ").strip()
            if send_file_to(uname, fname):
                print("file sent successfully")
            else:
                print("failed — user or file not found")
        elif cmd == '/cls':
            clear()
        elif cmd in ('/help', '/h'):
            print("""  /clients          — list connected clients
  /blist            — list banned users
  /ms <msg>         — broadcast message as admin
  /kick <name>      — kick a client
  /ban <name>       — kick and ban a client
  /unban <name>     — unban a user
  /brcl             — broadcast client list
  /brbl             — broadcast ban list
  /sendf            — send a file to a client
  /cls              — clear screen
  /shutdown | /s    — shut down the server
  /help     | /h    — show this help""")



        elif cmd == '':
            continue

        else:
            print(f"unknown command: '{cmd}' — type /help or /h for a list")


load_banlist()
print(f"server listening on {HOST}:{PORT}")
threading.Thread(target=server_commands, daemon=True).start()
receive()
