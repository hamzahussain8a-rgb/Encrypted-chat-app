# Encrypted Chat App

A Python-based real-time chat application with a graphical user interface, client-server communication, and an experimental message-obfuscation mechanism.

Originally developed as a chat application, this project was later improved to explore how message transformation affects the visibility of chat content during network packet analysis.

## Overview

The application allows users to connect to a central server, view available users, establish a chat connection, and exchange messages through a graphical interface.

The project also explores a basic security concept: transforming readable messages before transmitting them over a network, so that the original message is not immediately visible in a packet capture.

## Features

* **Real-time messaging:** Exchange messages between connected users.
* **Graphical interface:** Dark-themed chat interface built with CustomTkinter.
* **Client-server architecture:** TCP sockets handle communication between clients and the server.
* **Message transformation:** Messages are converted into a different representation before transmission.
* **Packet analysis experiment:** Observe how transformed messages appear in captured network traffic.
* **Modular structure:** Separate files for the chat interface, communication server, and message transformation logic.

## Technology Stack

* Python
* CustomTkinter
* TCP sockets
* Multithreading
* Network traffic analysis concepts

## Project Structure

```text
Encrypted-chat-app/
├── chat_app.py       # Chat client and graphical interface
├── comm.py           # TCP communication server
├── pgp_crypto.py     # Message transformation logic
└── screenshots/      # Project screenshots
```

## Getting Started

### Prerequisites

* Python 3
* pip
* Git

### 1. Clone the repository

```bash
git clone https://github.com/hamzahussain8a-rgb/Encrypted-chat-app.git
cd Encrypted-chat-app
```

### 2. Install dependencies

```bash
python -m pip install customtkinter
```

### 3. Start the server

Open a terminal in the project directory and run:

```bash
python comm.py
```

The server listens on port `5050`.

### 4. Start the chat client

Open a second terminal in the same directory and run:

```bash
python chat_app.py
```

Launch another client instance to test communication between users. The current client configuration uses `127.0.0.1`, so both clients should run on the same machine unless the connection address is configured for a local network.

## Security Experiment

The project explores how message content can be transformed before being sent across a network.

A packet capture can be used to compare the original message with the representation transmitted by the application.

**Important security note:** The current implementation uses a basic word-to-number substitution mechanism, not production-grade cryptographic encryption. It is intended for educational experimentation and does not provide reliable message confidentiality. The transformation can be reversed or inferred, and the shared mapping is available in the source code.

This project should not be used to transmit sensitive information.

## Learning Objectives

* Understand TCP client-server communication.
* Explore message handling in a multithreaded application.
* Observe application-layer data in network packet captures.
* Understand the difference between message obfuscation and cryptographic encryption.
* Identify limitations in a basic security implementation.

## Future Improvements

* Replace the substitution mechanism with a vetted cryptographic library.
* Implement secure key exchange and proper key management.
* Add authenticated encryption and message-integrity protection.
* Support encrypted connections between clients and the server.
* Improve error handling and connection management.
* Document and test the security design.

## Disclaimer

This is an educational project intended for learning about networking, message transformation, and cybersecurity concepts. It has not been audited for security and is not intended for production use.
