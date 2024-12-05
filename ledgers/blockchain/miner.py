#!/bin/env python3

from transaction import Transaction, MintTransaction
from port_handler import get_port, free_port
from blockchain_saver import BlockChain
from multiprocessing import Queue
from secrets import token_bytes
from bitstring import BitArray
from threading import Thread
from signer import Signer
from block import Block
from time import sleep
import argparse
import pickle
import base64
import json
import zmq

class Miner:
    def __init__(self, name, max_transactions, hashes, difficulty):
        self.name = name
        self.max_transactions = max_transactions
        self.hashes = hashes
        self.difficulty = difficulty
        self.port = get_port(name, "miners")

        if self.port is None:
            raise ValueError("Miner could not be started: Found no port")

        blockchain = BlockChain.load()
        longest_chain = blockchain.construct_tree()
        if len(longest_chain) > 0:
            last_block: Block = longest_chain[len(longest_chain) - 1]
            self.block = Block(last_block.id + 1, previous_hash=last_block.b64_hash())
        else:
            self.block = Block(0)

        self.signer = Signer()

        self.block_queue = Queue()
        self.block_queue.put(self.block)

        self.mine_thread = Thread(target=self.mine, args=(name, self.block_queue, hashes, difficulty), daemon=True)

        self.transaction_queue = []

    def mine(self, name: str, block_queue: Queue, hashes: int, difficulty: int):
        block: Block = block_queue.get()

        while True:
            if not block_queue.empty():
                block = block_queue.get()            

            block.nonce = int.from_bytes(token_bytes(4))

            bits = BitArray(block.hash()).bin
            
            if bits.startswith("0" * difficulty):
                print(f"{name}: Found valid nonce {block.nonce} for block {block.id}")

                block.transactions.insert(0, MintTransaction(name, 50))
                
                pickled_block = pickle.dumps(block)
                block_string = f"BLOCK:{base64.b64encode(pickled_block).decode()}".encode()

                with open("clients.json") as clients_file:
                    clients = json.load(clients_file)

                for port in list(clients["miners"].values()) + list(clients["ledgers"].values()):
                    socket = zmq.Context().socket(zmq.REQ)
                    socket.connect(f"tcp://127.0.0.1:{port}")
                    socket.send(block_string)
                    socket.recv()

                block = block_queue.get()
            else:
                sleep(1 / hashes)

    def start(self):
        self.mine_thread.start()

        self.socket = zmq.Context().socket(zmq.REP)
        self.socket.bind(f"tcp://127.0.0.1:{self.port}")

        while True:
            message = self.socket.recv().decode()
            if message.startswith("TRANSACTION:"):
                message = message.removeprefix("TRANSACTION:")
                # print(message)
                try:
                    transaction = Transaction.parse(message)
                    
                    saldo = BlockChain.load().saldo()

                    if transaction.name in saldo and saldo[transaction.name] >= transaction.amount:
                        if self.block.num_transactions() < self.max_transactions:
                            self.block.add_transaction(transaction)
                            self.block_queue.put(self.block)
                        else:
                            self.transaction_queue.append(transaction)

                        self.socket.send(b"OK")
                    else:
                        budget = 0
                        if transaction.name in saldo:
                            budget = saldo[transaction.name]
                        self.socket.send(f"Not enough budget {transaction.amount} > {budget}".encode())
                except:
                    self.socket.send(f"Invalid transaction rejected".encode())
            elif message.startswith("BLOCK:"):
                message = message.removeprefix("BLOCK:")
                block: Block = pickle.loads(base64.b64decode(message))

                if not BitArray(block.hash()).bin.startswith("0" * self.difficulty):
                    continue

                self.block = Block(block.id + 1, previous_hash=block.b64_hash())

                while len(self.transaction_queue) > 0:
                    self.block.add_transaction(self.transaction_queue.pop(0))
                    if self.block.num_transactions() >= self.max_transactions:
                        break

                self.block_queue.put(self.block)

                self.socket.send(b"OK")
    
    def stop(self):
        free_port(self.name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("-m", "--max-transactions", default="1")
    parser.add_argument("--hashes", default="1")
    parser.add_argument("--difficulty", default="3")
    args = parser.parse_args()
    args.name = args.name.lower()
    args.max_transactions = int(args.max_transactions)
    args.hashes = float(args.hashes)
    args.difficulty = int(args.difficulty)

    miner = Miner(args.name, args.max_transactions, args.hashes, args.difficulty)

    try:
        miner.start()
    except KeyboardInterrupt:
        miner.stop()

if __name__ == "__main__":
    main()
