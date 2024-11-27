import socket
import threading
import os
import argparse
import time
import select
import json
import random

class Node:
    def __init__(self, dir_path, host="localhost", port=0, bootstrap_host="localhost", bootstrap_port=5000, bandwith = 1000):
        self.host = host
        self.port = port
        self.ttl = 2
        self.bootstrap_host = bootstrap_host
        self.bootstrap_port = bootstrap_port
        self.peers = []
        self.pongs = []
        self.dir = dir_path
        self.requests = []
        self.bandwidth = bandwith
        self.ping_interval = 60
        self.pong_timeout = 5
        self.max_num_peers = 5

    def connect_to_bootstrap(self):
        print("connect_to_bootstrap", end="\n\n")

        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.bootstrap_host, self.bootstrap_port))

                # Listening Port info
                msg = f"JOIN:{self.host}:{self.port}"
                sock.sendall(msg.encode())
                print("Sent info")

                response = sock.recv(1024).decode()
                if response == "JOINED":
                    print("Connected to Bootstrap Server")
                    break

        time.sleep(10) # for more processors to join

        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.bootstrap_host, self.bootstrap_port))

                # Listening Port info
                msg = f"REQUEST_PEERS:{self.host}:{self.port}"
                sock.sendall(msg.encode())
                print("Requested Peers")

                response = sock.recv(1024).decode()
                nodes_string = ""
                while len(response) > 0:
                    nodes_string += response
                    response = sock.recv(1024).decode()

                if not (len(nodes_string) == 0 or nodes_string == "NO_NODES"):
                    peers = json.loads(nodes_string)
                    self.peers = [(peer[0], int(peer[1])) for peer in peers]
                    # peer_host, peer_port = response.split(":")

                    # peer_port = int(peer_port)
                    # peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # peer_socket.connect((peer_host, peer_port))
                    # peer_socket.sendall(node_info.encode())

                    # self.peers.append((peer_host, int(peer_port)))
                    # print(f"Connected to peer: {peer_host}:{peer_port}")
                    print("Received peers:", self.peers)
                    break

            print("No nodes available, retrying again in 15 secs")
            time.sleep(15)
            


    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.host, self.port = self.socket.getsockname()
        print(self.host, self.port)
        print(f"Node started at {self.host}:{self.port}")

        # Register with bootstrap server and get initial peer if available
        self.connect_to_bootstrap()

        # Threads for listening to connections and user commands
        threading.Thread(target=self.listen_for_connections, args=(self.socket,), daemon=True).start()
        threading.Thread(target=self.handle_commands, daemon=True).start()
        threading.Thread(target=self.file_transfer, daemon=True).start()
        threading.Thread(target=self.flood_ping, daemon=True).start()

        while True:
            pass

    def listen_for_connections(self, server):
        server.listen()
        while True:
            client_socket, client_addr = server.accept()

            data = client_socket.recv(1024).decode()
            # print("Received Data", data)

            if data.startswith("PING"):
                print("PINGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG")
                self.handle_ping(data)

            elif data.startswith("PONG"):
                print("PONGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG")
                self.handle_pong(data)

            # elif data.startswith("QUERYHIT"):
            #     print("QUERY_HITTTTTTTTTYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
            #     self.handle_queryhit(data)

            elif data.startswith("QUERY"):
                print("QUERYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
                self.handle_query(data, client_socket, client_addr)

            elif data.startswith("GET"):
                print("FILE TRANSFERRRRRRRRRRRRRRRRRRRRRRRRR")
                _, _, _, file_name = data.split(":")
                self.send_file(file_name, client_socket, client_addr)

            # elif ":" in data:
            #     print(f"Peer {data} connected.")
            #     host, port = data.split(":")
            #     self.peers.append((host, int(port)))

            client_socket.close()

    def send_ping(self, peers):
        failed_pings = []
        for peer in peers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.connect(peer)
                    print("Sending PING to", peer)
                    message = f"PING:{self.host}:{self.port}:{self.ttl}"
                    sock.sendall(message.encode())
                except ConnectionRefusedError:
                    print(f"Failed to connect to {peer}")
                    failed_pings.append(peer)
        return failed_pings

    def flood_ping(self):
        while True:
            print("flood_ping", end="\n\n")
            self.new_peers = set()
            self.update_neighbours = True
            timestamp = time.time()

            failed_pings = self.send_ping(self.peers)

            while time.time() - timestamp <= self.pong_timeout:
                failed_pings = self.send_ping(failed_pings)
                time.sleep(0.5)

            self.update_neighbours = False
            if len(self.new_peers) == 0:
                "No pongs received"
                self.connect_to_bootstrap()
            elif len(self.new_peers) <= self.max_num_peers:
                self.peers = list(self.new_peers)
            else:
                indices = random.sample(range(len(self.new_peers)), self.max_num_peers)
                new_peers = [self.new_peers[i] for i in indices]
                self.peers = new_peers
            
            print("New peers:", self.peers)
                
            time.sleep(self.ping_interval)

        # if len(self.peers) > self.max_peers:


    def send_pong(self, origin_host, origin_port):
        print("sending_pong", end="\n\n")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((origin_host,origin_port))
            pong_message = f"PONG:{self.host}:{self.port}"
            # print("SENDING PONG to", last_peer, pong_message)
            sock.sendall(pong_message.encode())

    def handle_ping(self, message):
        print("forward_ping", end="\n\n")
        msg_parts = message.split(":")
        print(msg_parts, end="\n\n\n")
        ttl = int(msg_parts[3])
        origin_host, origin_port = msg_parts[1], int(msg_parts[2])  # Convert string back to list of tuples
        # print(msg_parts, ttl, path)

        self.send_pong(origin_host, origin_port)

        # Append this node's address to the path and decrease TTL
        # path.append((self.host, self.port))
        ttl -= 1
        
        if ttl > 0:
            # Forward the PING to each peer except the previous sender
            for peer in self.peers:
                if peer[0] != origin_host and peer[1] != origin_port:  # Do not send back to the previous node
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        # print(f"Forwarding ping to {origin_host}:{origin_port}")
                        forward_message = f"PING:{msg_parts[1]}:{msg_parts[2]}:{ttl}"
                        print(forward_message)
                        sock.connect(peer)
                        sock.sendall(forward_message.encode())

        if self.update_neighbours:
            print(origin_host, origin_port)
            self.new_peers.add((origin_host, origin_port))

    def handle_pong(self, message):
        print("handle_pong", end="\n\n")
        # print("AYAAAAAAAAAAAAAAAA")
        print(message.split(":"))
        _, sender_host, sender_port = message.split(":")

        if self.update_neighbours:
            print(sender_host, sender_port)
            self.new_peers.add((sender_host, int(sender_port)))
            
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

    def handle_query(self, message, client_socket, client_addr):
        print("handle_query", end="\n\n")
        print(message)
        _, sender_host, sender_port, ttl, path, file_name = message.split(":")
        path = eval(path)

        # if len(path) == 0:
        #     self.requests[file_name].append((sender_host, sender_port))
        #     return

        if self.file_exists(self.dir, file_name):
            query_reply = f"QUERYHIT:{self.host}:{self.port}:{path}:{file_name}:{self.bandwidth}"
            # self.query_response(query_reply)
            client_socket.sendall(query_reply.encode())
        else:
            client_socket.sendall("QUERYFAIL".encode())

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

    # def query_response(self, message):
    #     print("query_response", end="\n\n")

    #     _, sender_host, sender_port, path, file_name = message.split(":")
    #     path = eval(path)

    #     if (self.host, self.port) == path[0]:
    #         self.requests[file_name].append(((sender_host, int(sender_port))))
    #         print(f"File with {sender_host}:{sender_port}")
    #         return

    #     if self.file_exists(self.dir, file_name):
    #         print("242", path)
    #         last_peer = path.pop()
    #         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    #             sock.connect(last_peer)
    #             query_reply = f"QUERYHIT:{self.host}:{self.port}:{path}:{file_name}"
    #             print("SENDING QUERY REPLY to", last_peer, query_reply)
    #             sock.sendall(query_reply.encode())

    def send_query(self, file_name):
        print("send_query", end="\n\n")

        peers_with_file = []
        for peer in self.peers[:]:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    peer_host, peer_port = peer
                    peer_port = int(peer_port)
                    sock.connect((peer_host, peer_port))
                    print("Sending QUERY to", peer)
                    message = f"QUERY:{self.host}:{self.port}:{self.ttl}:{[(self.host, self.port)]}:{file_name}"
                    print(message)
                    sock.sendall(message.encode())

                    reply = sock.recv(1024).decode()

                    if reply == "QUERYFAIL":
                        continue

                    peer_bandwidth = int(reply.split(":")[-1])

                    peers_with_file.append([peer_host, peer_port, peer_bandwidth])

                except ConnectionRefusedError:
                    print(f"Failed to connect to {peer}")

        best_peer = sorted(peers_with_file, key=lambda x: x[2], reverse = True)[0]
        print(f"Best peer selected for {file_name} : {best_peer}")

        self.requests.append([file_name, best_peer[0:2]])

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
                self.send_query(file_name)
            elif command == "5":
                exit(1)

    def file_transfer(self):
        while True:
            if len(self.requests) > 0:

                file_name, best_peer = self.requests[0]

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    try:
                        sock.connect((best_peer[0], best_peer[1]))
                        message = f"GET:{self.host}:{self.port}:{file_name}"
                        sock.sendall(message.encode())

                        file_path = os.path.join(self.dir, file_name)
                        print(file_path)
                        with open(file_path, "wb") as file:
                            print("334")
                            while 1:
                                chunk, addr = sock.recvfrom(1024)
                                print("CHUNKYY", chunk, addr)
                                if not chunk:
                                    break
                                print("CHUNK DATA", chunk)
                                file.write(chunk)
                                file.flush()

                        print(f"Received file from {best_peer[0:2]} : {file_name}")

                        self.requests.pop(0)

                    except Exception as e:
                        print(f"Exception while receiving file {file_name} from {best_peer}")
                        

    def send_file(self, file_name, client_socket, client_addr):
        try:
            # peer_port = int(peer_port)
            # sock.connect((peer_host, 9999))
            # if self.file_exists(self.dir, file_name):
                # sock1.bind((self.host, 9999))
            file_path = os.path.join(self.dir, file_name)
            print(f"Sending file to {client_addr}")
            print(file_path)
            with open(file_path, "rb") as file:
                chunk = file.read(1024)
                while chunk:
                    print(chunk)
                    if client_socket.send(chunk):
                        chunk = file.read(1024)
                    # while chunk := file.read(1024):
                    #     print(chunk)
                    #     sock.sendto()
            # else:
            #     message = "File Not Available Anymore"
            #     client_socket.sendall(message.encode())
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
