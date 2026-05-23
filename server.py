import socket, threading, os, ast

FILE_NAME = "banlist.txt"
enc='utf-8'
host = '192.168.1.4'
port = 55555

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind((host,port))
server.listen()

clients = []
nicknames = []
banlist=[]
running = True

def load():
    global banlist
    with open(FILE_NAME,"r") as f:
        banlist = ast.literal_eval(f.read())

def save(m):
    with open(FILE_NAME,"w") as ff:
        ff.write(f"{m}")

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def broadcast(mes):
    for client in clients:
        client.send(mes)

def handle(client):
    while True:
        try:
            message = client.recv(1024)
            broadcast(message)
        except:
            index = clients.index(client)
            nickname = nicknames[index]
            clients.remove(client)
            client.close()
            
            broadcast(f"{nickname} left the chat".encode(enc))
            nicknames.remove(nickname)
            break

def receive():
    while running:
        load()
        try:
            client, address = server.accept()
            print(f"connected with {str(address)}")

            client.send('NICK'.encode(enc))
            nickname = client.recv(1024).decode(enc)
            if nickname in nicknames:
                client.send("ND".encode(enc))
                client.close()
                continue
            if nickname in banlist:
                client.send("BAN".encode(enc))
                client.close()
                continue

            nicknames.append(nickname)
            clients.append(client)

            print(f"the client nickname is {nickname}")
            broadcast(f"{nickname} joined the chat".encode(enc))
            client.send("connected to the server".encode(enc))

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
        except:
            break

def kick(nickname,s):
    if nickname in nicknames:
        index = nicknames.index(nickname)
        client = clients[index]
        if s == "k":
            client.send("you were kicked".encode(enc))
            broadcast(f"{nickname} was kicked by the great admin".encode(enc))
        else:
            client.send("you were banned".encode(enc))
            broadcast(f"{nickname} was kicked and banned by the great admin".encode(enc))
        client.close()

        print(f"{nickname} kicked")
    else:
        print("user not found")

def server_commands():
    global running, banlist

    while running:
        load()
        cmd = input("")

        if cmd == "/shutdown" or cmd == "/s":
            running = False
            broadcast("server shutting down".encode(enc))

            for client in clients:
                client.send("SERVER_SHUTDOWN".encode(enc))
                client.close()
            server.close()

            print("server closed")
            os._exit(0)
            break
        elif "/kick" in cmd:
            cmd = cmd.replace(" ","")
            nickname = cmd[5:]
            kick(nickname,"k")
        elif cmd == "/cls":
            clear()
        elif cmd == "/clients":
            if nicknames:
                for i, name in enumerate(nicknames):
                    print(f"{i+1}. {name}")
            else:
                print("currently, there are no clients")
        elif "/ban" in cmd:
            cmd = cmd.replace(" ","")
            nickname = cmd[4:]
            kick(nickname,"b")
            banlist.append(nickname)
            save(banlist)
        elif "/unban" in cmd:
            cmd = cmd.replace(" ","")
            nickname = cmd[6:]
            if nickname in banlist:
                banlist.remove(nickname)
                save(banlist)
                broadcast(f"{nickname} -> unban".encode(enc))
            else:
                print("no user found")
        elif cmd == "/blist":
            if banlist:
                for i, ban in enumerate(banlist):
                    print(f"{i+1}. {ban}")
            else:
                print("no user was banned")
        elif "/ms" in cmd:
            mes=cmd[4:]
            broadcast(f"{mes}".encode(enc))
        elif cmd == "/help" or cmd == "/h":
            print("/clients -> client lists\n/blist -> ban list\n/ms (message) -> send message")
            print("/kick (name) -> kick client\n/ban (name) -> ban client\n/unban (name) -> unband client")
            print("/cls -> clear screen\n/shutdown or /s -> close server\n/help or /h -> help")
        else:
            print("command unknown")

thread_cmd = threading.Thread(target=server_commands)
thread_cmd.start()
receive()

