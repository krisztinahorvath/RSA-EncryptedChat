import socket
import base64
import pickle
import threading
import random
import math

def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def generate_large_prime():
    while True:
        num = random.randint(2 ** 10, 2 ** 16) | 1
        if is_prime(num):
            return num

def choose_random_public_exponent_e(phi):
    e = random.randint(2, phi - 1)
    while math.gcd(e, phi) != 1:
        e = random.randint(2, phi - 1)

    return e

def generate_key_pair():
    # generate random large prime numbers p and q
    p = generate_large_prime()
    q = generate_large_prime()

    # calculate n and φ(n)
    n = p * q
    phi = (p - 1) * (q - 1)

    # choose a random public exponent e
    e = choose_random_public_exponent_e(phi)

    # calculate private exponent d
    d = pow(e, -1,  phi)

    return (e, n), (d, n)

def encrypt_message(message, public_key):
    e, n = public_key

    # c = m^e % n
    encrypted_message = [pow(ord(char), e, n) for char in message]
    return encrypted_message

def decrypt_message(encrypted_message, private_key):
    d, n = private_key

    # m = c^d % n
    decrypted_message = [chr(pow(char, d, n) % n) for char in encrypted_message]
    return ''.join(decrypted_message)

def handle_client_messages(client_socket, server_private_key):
    try:
        while True:
            # receive encoded encrypted message from the client
            encoded_message_str = client_socket.recv(1024).decode('utf-8')
            encoded_message = base64.b64decode(encoded_message_str)
            encrypted_message = pickle.loads(encoded_message)

            # decrypt the message
            decrypted_message = decrypt_message(encrypted_message, server_private_key)
            print(f"\nEncrypted client encoded in base 64: {encoded_message_str}")
            print(f"Decrypted client: {decrypted_message}")

            print("\nEnter a message to send to the client: ", end='')

    except KeyboardInterrupt:
        print("Client shutting down...")
    finally:
        client_socket.close()

def handle_server_messages(server_socket, client_public_key):
    try:
        while True:
            # send an encrypted reply to the client
            message_to_send = input("\nEnter a message to send to the client: ")
            encrypted_reply = encrypt_message(message_to_send, client_public_key)
            encoded_reply = base64.b64encode(pickle.dumps(encrypted_reply)).decode('utf-8')
            server_socket.send(encoded_reply.encode('utf-8'))

    except KeyboardInterrupt:
        print("Server shutting down...")

    finally:
        server_socket.close()

# server setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", 7777))
server_socket.listen(1)

print("Server is listening for connections...")

# accept connection from client
client_socket, addr = server_socket.accept()
print(f"Connection from {addr}")

# generate RSA key pair for the server
server_public_key, server_private_key = generate_key_pair()

# send the server's public key to the client (encoded in base64)
encoded_server_public_key = base64.b64encode(pickle.dumps(server_public_key)).decode('utf-8')
client_socket.send(encoded_server_public_key.encode('utf-8'))

# receive the client's public key
encoded_client_public_key_str = client_socket.recv(1024).decode('utf-8')
encoded_client_public_key = base64.b64decode(encoded_client_public_key_str)
client_public_key = pickle.loads(encoded_client_public_key)

# start threads for handling messages
client_thread = threading.Thread(target=handle_client_messages, args=(client_socket, server_private_key))
server_thread = threading.Thread(target=handle_server_messages, args=(client_socket, client_public_key))

client_thread.start()
server_thread.start()
