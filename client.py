import socket, os, string
import threading, random

#set
HOST       = '192.168.1.4'
PORT       = 55555
ENC        = 'utf-8'
SKIP_FILES = {'server.py', 'client.py', 'README.md', 'banlist.txt', 'LICENSE'}

#nama client
nickname = input("nickname : ").strip()

#client
client  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
running = True

# pembeda
dig = []
for f in os.listdir():
    if f not in SKIP_FILES and os.path.isfile(f):
        name, _ = os.path.splitext(f)
        dig.append(name[-3:])

def pembeda():
    chars = string.ascii_lowercase
    while True:
        s = "".join(random.choices(chars, k=3))
        if s not in dig:
            dig.append(s)
            return s

#
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def stop(reason = ""):
    global running
    running = False
    if reason:
        print(reason)
    try:
        client.close()
    except Exception:
        pass

#receive from server
def receive():
    global running

    #Buffer
    buf = b''

    while running:
        try:
            chunk = client.recv(4096)
            if not chunk:
                stop("disconnected")
                break
            buf += chunk
           
            while buf:
                #file
                if buf.startswith(b'FILE:'):
                    newline = buf.find(b'\n')
                    if newline == -1:
                        break

                    header = buf[:newline].decode(ENC)
                    _, ext, size_str = header.split(':')
                    filesize = int(size_str)
                    buf = buf[newline + 1:]

                    #data file
                    while len(buf) < filesize:
                        data = client.recv(4096)
                        if not data:
                            raise ConnectionResetError("connection lost during file transfer")
                        buf += data

                    file_data = buf[:filesize]
                    buf = buf[filesize:]

                    fname = f"file_{pembeda()}{ext}"
                    with open(fname, 'wb') as f:
                        f.write(file_data)
                    print(f"file received → {fname}")

                #text
                else:
                    newline = buf.find(b'\n')
                    if newline == -1:
                        message = buf.decode(ENC, errors='replace').strip()
                        buf = b''
                    else:
                        message = buf[:newline].decode(ENC, errors='replace').strip()
                        buf = buf[newline + 1:]

                    if not message:
                        break

                    #nama awal
                    if message == 'NICK':
                        client.send(nickname.encode(ENC))
                        resp = client.recv(1024).decode(ENC).strip()
                        if resp == 'BAN':
                            stop("you are banned from this server")
                        elif resp == 'ND':
                            stop("a user with this nickname already exists")
                        else:
                            print(resp)

                    elif message == 'you were kicked':
                        stop("you were kicked from the server")

                    elif message == 'you were banned':
                        stop("you were banned from the server")

                    elif message == 'SERVER_SHUTDOWN':
                        stop("server has shut down")

                    else:
                        print(message)

        except Exception as e:
            if running:
                stop(f"disconnected ({e})")
            break

def write():
    global running
    while running:
        try:
            m = input("")
            if not running:
                break

            if m == '/exit':
                stop("left the chat")
                break
            elif m == '/cls':
                clear()
            elif m.startswith('/'):
                print("unknown command — available: /exit, /cls")
            else:
                client.send(f"{nickname}: {m}".encode(ENC))
        except (EOFError, KeyboardInterrupt):
            stop()
            break
        except Exception:
            running = False
            break

threading.Thread(target=receive, daemon=True).start()
write()

