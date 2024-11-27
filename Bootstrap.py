import socket
import random
import json

class BootstrapServer:
    def __init__(self, host='localhost', port=5000, num_peers = 5):
        self.host = host
        self.port = port
        self.nodes = []
        self.num_peers = num_peers

    def start(self):
        # AF_INET - IPv4
        # SOCK_STREAM - TCP
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((self.host, self.port))
            server.listen()
            print("Bootstrap server started at", self.host, ":", self.port)
            
            while True:
                client, addr = server.accept()
                # print("OS ne diye ", client, addr)
                msg = client.recv(1024).decode()

                if msg.startswith("JOIN"):
                    _, host, port = msg.split(":")
                    addr = (host, int(port))
                    if addr not in self.nodes:
                        self.nodes.append(addr)

                    print(f"Node {addr} connected.")
                    client.sendall("JOINED".encode())

                elif msg.startswith("REQUEST_PEERS"):
                    _, host, port = msg.split(":")
                    addr = (host, int(port))
                
                    nodes = self.nodes.copy()
                    nodes.remove(addr)
                    # print(self.nodes, nodes)


                    if nodes:
                        if len(nodes) < self.num_peers:
                        # chosen_node = random.choice(self.nodes)
                            client.sendall(json.dumps(nodes).encode())
                        else:
                            indices = random.sample(range(len(nodes)), self.num_peers)
                            nodes_send = [nodes[i] for i in indices]
                            client.sendall(json.dumps(nodes_send).encode())

                    else:
                        client.sendall(b"NO_NODES")

                    # print(self.nodes)
    
                client.close()

if __name__ == "__main__":
    bootstrap = BootstrapServer()
    bootstrap.start()