import socket
import os
import threading

# Constants
BUFFER_SIZE = 1024
QUERY_MESSAGE = "FILE_REQUEST:"

def handle_client(client_socket, client_address, shared_directory):
    """
    Handles incoming client queries for files.
    """
    print(f"[Server] Connection from {client_address}")
    try:
        data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        if data.startswith(QUERY_MESSAGE):
            filename = data[len(QUERY_MESSAGE):]
            file_path = os.path.join(shared_directory, filename)

            if os.path.exists(file_path):
                print(f"[Server] File '{filename}' found, sending to {client_address}")
                client_socket.send(b"FOUND")

                # Send file in chunks
                with open(file_path, "rb") as file:
                    while chunk := file.read(BUFFER_SIZE):
                        client_socket.send(chunk)
                        print("sent", chunk)

                client_socket.send(b"END")  # Signal end of file transfer
            else:
                print(f"[Server] File '{filename}' not found")
                client_socket.send(b"NOT_FOUND")
        else:
            print("[Server] Invalid request received")
    except Exception as e:
        print(f"[Server] Error: {e}")
    finally:
        client_socket.close()

def server_mode(host, port, shared_directory):
    """
    Server mode: Listens for incoming queries.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[Server] Listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address, shared_directory))
        thread.start()

def client_mode(target_host, target_port, shared_directory):
    """
    Client mode: Sends queries to the other client and handles responses.
    """
    while True:
        filename = input("[Client] Enter the filename to query: ")

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((target_host, target_port))

            # Send file request
            client_socket.send(f"{QUERY_MESSAGE}{filename}".encode('utf-8'))

            # Handle response
            response = client_socket.recv(BUFFER_SIZE)
            if response == b"FOUND":
                print("[Client] File found. Receiving it...")
                save_path = os.path.join(shared_directory, f"received_{filename}")
                with open(save_path, "wb") as file:
                    while True:
                        chunk = client_socket.recv(BUFFER_SIZE)
                        print("received", chunk)
                        if not chunk:
                            break
                        file.write(chunk)
                        file.flush()
                print(f"[Client] File '{filename}' received and saved as '{save_path}'")
            elif response == b"NOT_FOUND":
                print("[Client] File not found on the remote server.")
            else:
                print("[Client] Unexpected response from server.")
        except Exception as e:
            print(f"[Client] Error: {e}")
        finally:
            client_socket.close()

def main():
    # Configuration
    shared_directory = "./shared_files"
    os.makedirs(shared_directory, exist_ok=True)

    role = input("Enter your role (server/client): ").strip().lower()
    host = input("Enter your host (e.g., 127.0.0.1): ").strip()
    port = int(input("Enter your port: "))

    if role == "server":
        print("[Info] Running in server mode.")
        server_mode(host, port, shared_directory)
    elif role == "client":
        target_host = input("Enter the target host: ").strip()
        target_port = int(input("Enter the target port: "))
        print("[Info] Running in client mode.")
        client_mode(target_host, target_port, shared_directory)
    else:
        print("[Error] Invalid role. Choose 'server' or 'client'.")

if __name__ == "__main__":
    main()
