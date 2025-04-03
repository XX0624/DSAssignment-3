import socket
import threading
import datetime
from collections import defaultdict

HOST = "127.0.0.1"
PORT = 10624

# Create and bind the server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

# Data structures to manage clients, nicknames, and channels
nickname_to_client = {}
client_to_nickname = {}
nickname_to_channel = {}
channel_to_nicknames = defaultdict(set)


def broadcast(message, channel, sender_nickname=None):
    """
    Send 'message' to all nicknames in 'channel' except 'sender_nickname' (if provided).
    """
    for nick in channel_to_nicknames[channel]:
        if nick != sender_nickname:
            nickname_to_client[nick].send(message)


def handle_client(client):
    """
    Handle messages/commands from a single client in a separate thread.
    """
    while True:
        try:
            message = client.recv(1024)
            if not message:
                disconnect_client(client)
                break

            decoded_msg = message.decode("utf-8").strip()
            sender_nickname = client_to_nickname[client]
            channel = nickname_to_channel[sender_nickname]

            if decoded_msg.startswith("/"):
                parts = decoded_msg.split(" ", 2)
                command = parts[0]

                if command == "/quit":
                    disconnect_client(client, notify=True)
                    break

                elif command == "/join":
                    if len(parts) < 2:
                        client.send("Usage: /join <channel_name>\n".encode("utf-8"))
                    else:
                        join_channel(sender_nickname, parts[1])

                elif command == "/pm":
                    # /pm <nickname> <message>
                    if len(parts) < 3:
                        client.send("Usage: /pm <nickname> <message>\n".encode("utf-8"))
                    else:
                        target_nick = parts[1]
                        pm_message = parts[2]
                        private_message(sender_nickname, target_nick, pm_message)

                else:
                    client.send("Unknown command.\n".encode("utf-8"))

            else:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                full_message = f"[{timestamp}] {sender_nickname}: {decoded_msg}\n"
                print(full_message, end="")
                broadcast(full_message.encode("utf-8"), channel, sender_nickname)

        except:
            # In case of unexpected error
            disconnect_client(client)
            break


def disconnect_client(client, notify=False):
    """
    Remove a client from all data structures and close its connection.
    If 'notify' is True, broadcast a "left the chat" message.
    """
    if client not in client_to_nickname:
        return

    nickname = client_to_nickname[client]
    channel = nickname_to_channel[nickname]
    del client_to_nickname[client]
    del nickname_to_client[nickname]
    del nickname_to_channel[nickname]
    channel_to_nicknames[channel].remove(nickname)

    client.close()

    if notify:
        broadcast(f"{nickname} has left the chat.\n".encode("utf-8"), channel)


def join_channel(nickname, new_channel):
    """
    Move a nickname from its current channel to 'new_channel'.
    """
    old_channel = nickname_to_channel[nickname]
    if old_channel == new_channel:
        nickname_to_client[nickname].send(
            "You are already in that channel.\n".encode("utf-8")
        )
        return

    # Leave old channel
    channel_to_nicknames[old_channel].remove(nickname)
    broadcast(
        f"{nickname} has left channel {old_channel}.\n".encode("utf-8"),
        old_channel,
        nickname,
    )

    # Join new channel
    nickname_to_channel[nickname] = new_channel
    channel_to_nicknames[new_channel].add(nickname)

    broadcast(
        f"{nickname} has joined channel {new_channel}.\n".encode("utf-8"),
        new_channel,
        nickname,
    )
    nickname_to_client[nickname].send(
        f"You have joined channel {new_channel}.\n".encode("utf-8")
    )


def private_message(sender, target, message):
    """
    Send a private message from 'sender' to 'target'.
    """
    if target not in nickname_to_client:
        nickname_to_client[sender].send("User not found.\n".encode("utf-8"))
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pm_to_target = f"[{timestamp}] Private from {sender}: {message}\n"
    pm_to_sender = f"[{timestamp}] Private to {target}: {message}\n"

    target_client = nickname_to_client[target]
    target_client.send(pm_to_target.encode("utf-8"))
    nickname_to_client[sender].send(pm_to_sender.encode("utf-8"))


def receive_connections():
    """
    Main loop to accept new client connections and assign nicknames/channels.
    """
    print(f"Server is listening on {HOST}:{PORT}...")
    while True:
        client, address = server.accept()
        print(f"New connection from {address}")

        # Prompt for nickname
        client.send("NICK".encode("utf-8"))
        nickname = client.recv(1024).decode("utf-8").strip()

        # If nickname already in use, disconnect
        if nickname in nickname_to_client:
            client.send("Nickname already in use. Disconnecting.\n".encode("utf-8"))
            client.close()
            continue

        nickname_to_client[nickname] = client
        client_to_nickname[client] = nickname
        nickname_to_channel[nickname] = "general"  # default channel
        channel_to_nicknames["general"].add(nickname)

        print(f"Client nickname: {nickname}")
        broadcast(
            f"{nickname} has joined the chat (channel: general)!\n".encode("utf-8"),
            "general",
            nickname,
        )

        # Instructions to the new user
        client.send("You are now connected to the server!\n".encode("utf-8"))
        client.send("Type '/quit' to exit.\n".encode("utf-8"))
        client.send("Use '/join <channel>' to switch channels.\n".encode("utf-8"))
        client.send(
            "Use '/pm <nickname> <message>' to send a private message.\n".encode(
                "utf-8"
            )
        )

        # Start a thread to handle this client
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()


if __name__ == "__main__":
    receive_connections()
