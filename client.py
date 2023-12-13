import socket
import base64
import pickle
import threading
import random
import math

def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num ** 0.5) + 1):
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
    d = pow(e, -1, phi)

    return (e, n), (d, n)

def encrypt_message(message, public_key):
    e, n = public_key
    encrypted_message = [pow(ord(char), e, n) for char in message]
    return encrypted_message

def decrypt_message(encrypted_message, private_key):
    d, n = private_key
    decrypted_message = [chr(pow(char, d, n) % n) for char in encrypted_message]
    return ''.join(decrypted_message)

def receive_messages(client_socket, private_key):
    try:
        while True:
            # receive the encrypted reply from the server
            encoded_reply_str = client_socket.recv(1024).decode('utf-8')
            if not encoded_reply_str:
                break
            print(f"\nEncrypted server encoded in base 64: {encoded_reply_str} ")
            encoded_reply = pickle.loads(base64.b64decode(encoded_reply_str))

            # convert each element of the list
            encrypted_reply = [int(char) for char in encoded_reply]
            decrypted_reply = decrypt_message(encrypted_reply, private_key)

            print(f"Decrypted server: {decrypted_reply}")
            print("\nEnter a message to send to the server: ", end='')

    except KeyboardInterrupt:
        print("Client shutting down...")
    finally:
        client_socket.close()


def start_client():
    # client setup
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("192.168.213.1", 7777))

    # generate RSA key pair for the client
    client_public_key, client_private_key = generate_key_pair()

    # receive the server's public key
    encoded_server_public_key_str = client_socket.recv(1024).decode('utf-8')
    encoded_server_public_key = base64.b64decode(encoded_server_public_key_str)
    server_public_key = pickle.loads(encoded_server_public_key)

    # send the client's public key to the server (encoded in base64)
    encoded_client_public_key = base64.b64encode(pickle.dumps(client_public_key)).decode('utf-8')
    client_socket.send(encoded_client_public_key.encode('utf-8'))

    # start a thread to receive messages from the server
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket, client_private_key))
    receive_thread.start()

    try:
        while True:
            # send an encrypted message to the server
            message_to_send = input("\nEnter a message to send to the server: ")
            encrypted_message = encrypt_message(message_to_send, server_public_key)
            encoded_message = base64.b64encode(pickle.dumps(encrypted_message)).decode('utf-8')
            client_socket.send(encoded_message.encode('utf-8'))

    except KeyboardInterrupt:
        print("Client shutting down...")

    finally:
        # close the connection
        client_socket.close()


# start the client
start_client()
