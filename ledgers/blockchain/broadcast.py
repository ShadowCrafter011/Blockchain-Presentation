#!/bin/env python3

from parser import args as parse_args
from transaction import Transaction
import json
import zmq
import os

def main():
    args = parse_args()
    transaction = Transaction.new(args.name, args.to, args.amount, args.password)

    if not os.path.isfile("clients.json"):
        raise ValueError("No miners to send transaction to")
    
    with open("clients.json") as clients_file:
        clients = json.load(clients_file)

    if len(clients["miners"]) == 0:
        raise ValueError("No miners to send transaction to")
    
    socket = zmq.Context().socket(zmq.REQ)

    for miner, port in clients["miners"].items():
        socket.connect(f"tcp://127.0.0.1:{port}")

        socket.send(transaction.to_bytes())
        print(f"Response from {miner}: {socket.recv().decode()}")


if __name__ == "__main__":
    main()
