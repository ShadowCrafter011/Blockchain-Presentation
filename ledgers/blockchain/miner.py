#!/bin/env python3

from port_handler import get_port, free_port
from transaction import Transaction
from multiprocessing import Value
from threading import Thread
from signer import Signer
from block import Block
import argparse
import pickle
import base64
import mmap
import zmq

class Miner:
    def __init__(self, name, max_transactions):
        self.name = name
        self.max_transactions = max_transactions
        self.port = get_port(name, "miners")

        self.block = Block(0)
        self.signer = Signer()

        self.block_value = mmap.mmap(-1, -1)
        self.block_value.write()
        self.stop_mining = Value("i", 0)

        self.mine_thread = Thread(target=self.mine, args=(self.block_value, self.stop_mining))

    def mine(self, block_value, stop_mining):
        block = pickle.load(bytes(block_value.value))
        print(block)

    def start(self):
        self.mine_thread.start()

        self.socket = zmq.Context().socket(zmq.REP)
        self.socket.bind(f"tcp://127.0.0.1:{self.port}")

        while True:
            message = self.socket.recv()
            try:
                transaction = Transaction.parse(message.decode())
                # TODO: Validate that user has enough budget
            except:
                self.socket.send(f"Invalid transaction rejected by {self.name}".encode())

            self.block.add_transaction(transaction)
    
    def stop(self):
        free_port(self.name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("-m", "--max-transactions", default="1")
    args = parser.parse_args()
    args.name = args.name.lower()
    args.max_transactions = int(args.max_transactions)

    miner = Miner(args.name, args.max_transactions)

    try:
        miner.start()
    except KeyboardInterrupt:
        miner.stop()

if __name__ == "__main__":
    main()
