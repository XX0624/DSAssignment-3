import socket
import threading

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 10624

nickname = input("Choose your nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_HOST, SERVER_PORT))


def receive_messages():
    """
    Continuously listen to incoming messages from the server and print them.
    """
    while True:
        try:
            message = client.recv(1024).decode("utf-8")
            if message == "NICK":
                client.send(nickname.encode("utf-8"))
            else:
                print(message, end="")
        except:
            print("An error occurred. Closing connection.")
            client.close()
            break


def write_messages():
    """
    Continuously read user input and send to the server.
    """
    while True:
        message = input("")
        client.send(message.encode("utf-8"))


# Start two threads: one for receiving and one for sending
receive_thread = threading.Thread(target=receive_messages, daemon=True)
receive_thread.start()

write_thread = threading.Thread(target=write_messages, daemon=True)
write_thread.start()
receive_thread.join()
write_thread.join()
