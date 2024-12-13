#!/bin/env python3

from cryptography.hazmat.primitives.hashes import Hash, SHA256
from parser import args as parse_args
from bitstring import BitArray
from signer import Signer
from time import time
import json
import zmq
import os

def main():
    args = parse_args()
    signer = Signer()

    if not os.path.isfile("clients.json"):
        print("There are no clients to broadcast to")
        return

    with open("clients.json") as clients_file:
        clients = json.load(clients_file)

    if args.id:
        unique_id = args.id
    else:
        digest = Hash(SHA256())
        digest.update(
            f"{time()}, {args.name}, {args.to}, {args.amount}".encode()
        )
        unique_id = BitArray(digest.finalize()).hex

    try:
        signature = signer.sign_message(f"{args.name}, {args.to}, {args.amount}, {unique_id}", args.name, args.password)
    except:
        print(f"Failed to sign message. Password might be invalid for {args.name}")
        return

    if args.change_signature:
        signature = "a" + signature

    for name, port in clients.items():
        if args.only and name != args.only:
            continue

        socket = zmq.Context().socket(zmq.REQ)
        socket.connect(f"tcp://127.0.0.1:{port}")
        socket.send(
            f"{args.name}, {args.to}, {args.amount}, {unique_id}, {signature}".encode()
        )

        print(f"Response from {name}: {socket.recv().decode()}")


if __name__ == "__main__":
    main()
