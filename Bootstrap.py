import socket
import random

class BootstrapServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.nodes = []

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
                
                if self.nodes:
                    chosen_node = random.choice(self.nodes)
                    client.sendall(f"{chosen_node[0]}:{chosen_node[1]}".encode())
                else:
                    client.sendall(b"NO_NODES")

                node_info = client.recv(1024).decode()
                if node_info:
                    print(f"Node {node_info} connected.")
                    host, port = node_info.split(":")
                    self.nodes.append((host, int(port)))
                    # print(self.nodes)
    
                client.close()

if __name__ == "__main__":
    bootstrap = BootstrapServer()
    bootstrap.start()