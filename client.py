import socket, threading, os

nickname=input("nickname : ")
enc='utf-8'
client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(('192.168.1.4',55555))
running = True
shut=False

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def receive():
    global running
    while running:
        try:
            message = client.recv(1024).decode(enc)
            if not message:
                break
            if message == "NICK":
                client.send(nickname.encode(enc))
                next_mes = client.recv(1024).decode(enc)
                if next_mes == "BAN":
                    print("this user is banned")
                    client.close()
                elif next_mes == "ND":
                    print("a user with this name already exist")
                    client.close()
            elif message == "you were kicked":
                print(message)
                client.close()
                break
            elif message == "SERVER_SHUTDOWN":
                print("server closed")
                shut=True
                client.close()
                break
            else:
                print(message)
        except:
            running=False
            print("disconnect")
            client.close()
            break

def write():
    global running
    while running:
        try:
            m = input("")
            
            if not running:
                break

            if m == "/exit":
                client.close()
                print("keluar dari chat")
                break

            elif m == "/cls":
                clear()
                continue
            message = f"{nickname}: {m}"
            client.send(message.encode(enc))
        except:
            running = False
            break
        
if not shut:
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()