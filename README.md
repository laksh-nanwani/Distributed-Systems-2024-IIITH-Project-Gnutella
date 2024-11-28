# Gnutella-like P2P Network

## Team 13
Laksh Nanwani (2021701002)

Harshita Harshita (2023201002)

## Overview
This project implements a Gnutella-inspired peer-to-peer (P2P) network. The network consists of nodes communicating and sharing files efficiently using messages such as `PING`, `PONG`, `QUERY`, and `QUERYHIT`.

## How It Works

### 1. Start the Bootstrap Server
- First, run the **bootstrap server**. This server helps new nodes join the network by providing them with the IP and port of an existing node.

### 2. Run Nodes
- Each node is started by running `nodes.py`.
- When started, a node connects to the bootstrap server and receives the IP and port of a random node in the network.
- The node then connects to this random peer to establish its first link in the network.

### 3. Flooding with PING
- After connecting to a peer, the node floods the network with a `PING` message, which has a Time-to-Live (TTL) value.
- Nodes that receive the `PING` respond with a `PONG` message, which traces back the same path as the `PING` message.
- This ensures strong connectivity and helps nodes discover others in the network.

### 4. File Querying
- If a node needs a file, it sends a `QUERY` message, which is also flooded through the network like `PING`.
- Nodes with the requested file respond with a `QUERYHIT` message, which traces back to the querying node.

### 5. File Transfer
- After receiving all `QUERYHIT` responses, the node selects the peer with the **highest bandwidth** to download the file.
- The file is then transferred directly between the nodes.

## Getting Started

### Requirements
- Python 3.8 or later

### Running the Project
1. Start the bootstrap server:
   ```bash
   python bootstrap_server.py
   ```
2. Start a node:
   ```bash
   python nodes.py /directory_to_store_files
   ```
3. Repeat step 2 to add more nodes to the network.
4. Use the terminal interface provided by the nodes to send `QUERY` messages or observe network connectivity.

## Message Types
- **PING**: Initiates discovery of other nodes in the network.
- **PONG**: Response to a `PING` includes details like IP, port, and available resources.
- **QUERY**: Used to search for files in the network.
- **QUERYHIT**: Response to a `QUERY` includes the file's location and the peer's bandwidth.

## Features
- Decentralized P2P network with dynamic node discovery.
- File searching and efficient file transfer.
- Flooding mechanism for robust connectivity.
