import socket
import threading
import os
import argparse
import time
import select


class Node:
    def __init__(self, dir_path, host="localhost", port=0, bootstrap_host="localhost", bootstrap_port=5000):
        self.host = host
        self.port = port
        self.ttl = 2
        self.bootstrap_host = bootstrap_host
        self.bootstrap_port = bootstrap_port
        self.peers = []
        self.pongs = []
        self.dir = dir_path
        self.requests = {}

    def connect_to_bootstrap(self):
        print("connect_to_bootstrap", end="\n\n")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.bootstrap_host, self.bootstrap_port))

            # Listening Port info
            node_info = f"{self.host}:{self.port}"
            sock.sendall(node_info.encode())
            print("Sent info")

            response = sock.recv(1024).decode()

            if response == "NO_NODES":
                print("No nodes available, starting a new network.")
            else:
                peer_host, peer_port = response.split(":")

                peer_port = int(peer_port)
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_host, peer_port))
                peer_socket.sendall(node_info.encode())

                self.peers.append((peer_host, int(peer_port)))
                print(f"Connected to peer: {peer_host}:{peer_port}")

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((self.host, self.port))
            self.host, self.port = server.getsockname()
            print(self.host, self.port)
            print(f"Node started at {self.host}:{self.port}")

            # Register with bootstrap server and get initial peer if available
            self.connect_to_bootstrap()

            # Threads for listening to connections and user commands
            threading.Thread(target=self.listen_for_connections, args=(server,), daemon=True).start()
            threading.Thread(target=self.handle_commands, daemon=True).start()
            threading.Thread(target=self.file_transfer, daemon=True).start()

            # Flood PING to discover additional peers
            self.flood_ping()

            while True:
                pass

    def listen_for_connections(self, server):
        server.listen()
        while True:
            client, addr = server.accept()

            data = client.recv(1024).decode()
            # print("Received Data", data)

            if data.startswith("PING"):
                print("PINGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG")
                self.forward_ping(data)

            elif data.startswith("PONG"):
                print("PONGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG")
                self.handle_pong(data)

            elif data.startswith("QUERYHIT"):
                print("QUERY_HITTTTTTTTTYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
                self.handle_queryhit(data)

            elif data.startswith("QUERY"):
                print("QUERYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
                self.handle_query(data)

            elif data.startswith("GET"):
                print("FILE TRANSFERRRRRRRRRRRRRRRRRRRRRRRRR")
                self.send_file(data)
            elif ":" in data:
                print(f"Peer {data} connected.")
                host, port = data.split(":")
                self.peers.append((host, int(port)))

            client.close()

    def flood_ping(self):
        print("flood_ping", end="\n\n")
        for peer in self.peers[:]:  # Use a copy of the list to avoid modifying it during iteration
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.connect(peer)
                    print("Sending PING to", peer)
                    # message = f"PING:{self.host}:{self.port}"
                    # message = f"PING:{self.host}:{self.port}:{self.host}:{self.host}:{self.ttl}"
                    message = f"PING:{self.host}:{self.port}:{self.ttl}:{[(self.host, self.port)]}"
                    sock.sendall(message.encode())

                    response = sock.recv(1024).decode()
                    if response.startswith("PONG"):
                        _, host, port = response.split(":")
                        new_peer = (host, int(port))
                        if new_peer not in self.peers:
                            self.peers.append(new_peer)
                            print(f"Discovered new peer: {host}:{port}")

                except ConnectionRefusedError:
                    print(f"Failed to connect to {peer}")

    def send_pong(self, message):
        print("send_pong", end="\n\n")
        msg_parts = message.split(":")
        # print(msg_parts, end = "\n\n\n")
        ttl = int(msg_parts[3])
        path = eval(msg_parts[4])
        last_peer = path[-1]
        path.pop()
        print("SEEEEEEEEEEEEEEEEEEEEee")
        print(msg_parts)
        print(path)

        if len(path) == 0:
            # -------------------------------------
            self.pongs.append((msg_parts[1], msg_parts[2]))
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(last_peer)
                pong_message = f"PONG:{self.host}:{self.port}:{path}"
                print("SENDING PONGGG to", last_peer, pong_message)
                sock.sendall(pong_message.encode())

    def forward_ping(self, message):
        print("forward_ping", end="\n\n")
        msg_parts = message.split(":")
        print(msg_parts, end="\n\n\n")
        ttl = int(msg_parts[3])
        path = eval(msg_parts[4])  # Convert string back to list of tuples
        # print(msg_parts, ttl, path)

        # Append this node's address to the path and decrease TTL
        path.append((self.host, self.port))
        ttl -= 1

        if ttl > 0:
            # Forward the PING to each peer except the previous sender
            for peer in self.peers:
                if peer != path[-2]:  # Do not send back to the previous node
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        forward_message = f"PING:{msg_parts[1]}:{msg_parts[2]}:{ttl}:{path}"
                        print(forward_message)
                        sock.connect(peer)
                        sock.sendall(forward_message.encode())
        else:
            # If TTL is 0, respond with a PONG along the reverse path
            self.send_pong(message)

    def handle_pong(self, message):
        print("handle_pong", end="\n\n")
        print("AYAAAAAAAAAAAAAAAA")
        print(message.split(":"))
        m1, sender_host, sender_port, path_str = message.split(":")

        path = eval(path_str)
        print("PATH", path)

        # print("YEH DEKH   ", (self.host, self.port), path[0])
        if len(path) == 0:
            self.pongs.append((sender_host, int(sender_port)))
            print(f"Received PONG from {sender_host}:{sender_port}")
            return

        if (self.host, self.port) == path[0]:
            self.pongs.append((sender_host, int(sender_port)))
            print(f"Received PONG from {sender_host}:{sender_port}")
        else:
            if path:
                next_hop = path.pop()
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    # forward_message = f"PONG:{sender_host}:{sender_port}:{path}"
                    forward_message = f"{m1}:{sender_host}:{sender_port}:{path}"
                    sock.connect(next_hop)
                    sock.sendall(forward_message.encode())
            else:
                self.pongs.append((sender_host, int(sender_port)))

    def get_pongs(self):
        if self.pongs:
            print("PONGs received from nodes:")
            for peer in self.pongs:
                print(f"- {peer[0]}:{peer[1]}")
        else:
            print("Did not receive any replies yet.")

    def get_connected_nodes(self):
        if self.peers:
            print("Connected nodes:")
            for peer in self.peers:
                print(f"- {peer[0]}:{peer[1]}")
        else:
            print("No connected nodes.")

    def get_request_details(self):
        for file_name, peers in self.requests.items():
            print(f"File {file_name} with", end=" ")
            if len(peers) == 0:
                print("Not with peers:(")
            else:
                print()
                for peer in peers:
                    print(peer)
        else:
            print("No Requests!!!")

    def file_exists(self, directory, file_name):
        file_path = os.path.join(directory, file_name)
        return os.path.isfile(file_path)

    def handle_query(self, message):
        print("handle_query", end="\n\n")
        print(message)
        _, sender_host, sender_port, ttl, path, file_name = message.split(":")
        path = eval(path)

        if len(path) == 0:
            self.requests[file_name].append((sender_host, sender_port))
            return

        if self.file_exists(self.dir, file_name):
            query_reply = f"QUERYHIT:{self.host}:{self.port}:{path}:{file_name}"
            self.query_response(query_reply)

    def handle_queryhit(self, message):
        print("handle_query", end="\n\n")
        print(message)
        _, sender_host, sender_port, path, file_name = message.split(":")
        path = eval(path)

        if len(path) == 0:
            self.requests[file_name].append((sender_host, sender_port))
            return

        if self.file_exists(self.dir, file_name):
            query_reply = f"QUERYHIT:{self.host}:{self.port}:{path}:{file_name}"

    def query_response(self, message):
        print("query_response", end="\n\n")

        _, sender_host, sender_port, path, file_name = message.split(":")
        path = eval(path)

        if (self.host, self.port) == path[0]:
            self.requests[file_name].append(((sender_host, int(sender_port))))
            print(f"File with {sender_host}:{sender_port}")
            return

        if self.file_exists(self.dir, file_name):
            print("242", path)
            last_peer = path.pop()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(last_peer)
                query_reply = f"QUERYHIT:{self.host}:{self.port}:{path}:{file_name}"
                print("SENDING QUERY REPLY to", last_peer, query_reply)
                sock.sendall(query_reply.encode())

    def send_query(self, file_name):
        print("send_query", end="\n\n")

        for peer in self.peers[:]:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.connect(peer)
                    print("Sending QUERY to", peer)
                    message = f"QUERY:{self.host}:{self.port}:{self.ttl}:{[(self.host, self.port)]}:{file_name}"
                    print(message)
                    sock.sendall(message.encode())
                except ConnectionRefusedError:
                    print(f"Failed to connect to {peer}")

    def handle_commands(self):
        print("handle_commands", end="\n\n")
        while True:
            # print("1. Print Connected Nodes")
            # print("2. Print Pong Replies")
            # print("3. Exit")
            command = input("Enter command: ").strip().upper()
            if command == "1":
                self.get_connected_nodes()
            elif command == "2":
                self.get_pongs()
            elif command == "3":
                self.get_request_details()
            elif command == "4":
                file_name = input("Enter the file name :")
                self.requests[file_name] = []
                self.send_query(file_name)
            elif command == "5":
                exit(1)

    def file_transfer(self):
        while True:
            if self.requests:
                file_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                file_socket.bind((self.host, 9999))
                for file_name, list_peers in list(self.requests.items()):
                    for peer in list_peers:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                            # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            try:
                                peer_host, peer_port = peer
                                peer_port = int(peer_port)
                                sock.connect((peer_host, peer_port))
                                message = f"GET:{self.host}:{self.port}:{file_name}"
                                sock.sendall(message.encode())

                                file_path = os.path.join(self.dir, file_name)
                                print(file_path)
                                with open(file_path, "wb") as file:
                                    print("334")
                                    while 1:
                                        chunk, addr = file_socket.recvfrom(1024)
                                        print("CHUNKYY", chunk, addr)
                                        if not chunk:
                                            break
                                        print("CHUNK DATA", chunk)
                                        file.write(chunk)

                                print(f"Received data from socket {peer} : {file_name}")

                            except Exception as e:
                                print("337Error Occurred:", str(e))
                        # Will take file from the first peer
                        # print(f"Received data from socket {peer} : {file_name}")
                        break
                    del self.requests[file_name]
                file_socket.close()
            time.sleep(5)

    def send_file(self, message):
        _, peer_host, peer_port, file_name = message.split(":")
        print(peer_host, peer_port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                peer_port = int(peer_port)
                # sock.connect((peer_host, 9999))
                if self.file_exists(self.dir, file_name):
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock1:
                        # sock1.bind((self.host, 9999))
                        file_path = os.path.join(self.dir, file_name)
                        print(f"Sending file to {peer_host}:{9999}")
                        print(file_path)
                        with open(file_path, "rb") as file:
                            chunk = file.read(1024)
                            while chunk:
                                print(chunk)
                                if sock1.sendto(chunk, (peer_host, 9999)):
                                    chunk = file.read(1024)
                            # while chunk := file.read(1024):
                            #     print(chunk)
                            #     sock.sendto()
                else:
                    message = "File Not Available"
                    sock.sendall(message.encode())
            except Exception as e:
                print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory_path")
    args = parser.parse_args()
    if os.path.isdir(args.directory_path):
        print(f"Starting node with directory: {args.directory_path}")
    else:
        print("Enter a valid directory")
    node = Node(args.directory_path)
    node.start()
