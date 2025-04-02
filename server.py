import socket
import threading
import datetime

HOST = "127.0.0.1"
PORT = 10624

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

# Lists of clients and their nicknames
clients = []
nicknames = []


def broadcast(message, sender_socket=None):
    """
    Send a message to all connected clients except the sender (if provided).
    """
    for client in clients:
        if client != sender_socket:
            client.send(message)


def handle_client(client):
    """
    Handle communication for a single connected client in a separate thread.
    """
    while True:
        try:
            message = client.recv(1024)
            if not message:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                nicknames.remove(nickname)
                broadcast(f"{nickname} has left the chat.\n".encode("utf-8"))
                break

            decoded_msg = message.decode("utf-8").strip()
            index = clients.index(client)
            nickname = nicknames[index]

            # Check if the message starts with a slash => possible command
            if decoded_msg.startswith("/"):
                if decoded_msg == "/quit":
                    broadcast(
                        f"{nickname} has left the chat.\n".encode("utf-8"), client
                    )
                    client.send("You left the chat.\n".encode("utf-8"))
                    client.close()
                    clients.remove(client)
                    nicknames.remove(nickname)
                    break
                else:
                    client.send("Unknown command.\n".encode("utf-8"))
            else:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                full_message = f"[{timestamp}] {nickname}: {decoded_msg}\n"
                print(full_message, end="")
                broadcast(full_message.encode("utf-8"), client)

        except Exception as e:
            # Handle unexpected errors
            print(f"Error handling client {nickname}: {e}")
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                nicknames.remove(nickname)
                broadcast(f"{nickname} has left the chat.\n".encode("utf-8"))
            break


def receive_connections():
    """
    Continuously accept new client connections.
    """
    print(f"Server is listening on {HOST}:{PORT}...")
    while True:
        client, address = server.accept()
        print(f"New connection from {address}")
        client.send("NICK".encode("utf-8"))
        nickname = client.recv(1024).decode("utf-8")

        # Store the nickname and client socket
        nicknames.append(nickname)
        clients.append(client)

        print(f"Client nickname: {nickname}")
        broadcast(f"{nickname} has joined the chat!\n".encode("utf-8"))
        client.send(
            "You are now connected to the server!\nType '/quit' to exit.\n".encode(
                "utf-8"
            )
        )
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()


if __name__ == "__main__":
    receive_connections()
