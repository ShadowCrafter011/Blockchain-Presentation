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
        # Be able to have at least one transaction along with mint transaction
        self.max_transactions = max(max_transactions + 1, 2)
        self.hashes = hashes
        self.difficulty = difficulty
        self.port = get_port(name, "miners")

        if self.port is None:
            raise ValueError("Miner could not be started: Found no port")

        self.signer = Signer()

        self.transactions_queue = Queue()

        self.mine_thread = Thread(target=self.mine, daemon=True)

    def mine(self):
        transactions: list[Transaction | MintTransaction] = []
        for _ in range(self.transactions_queue.qsize()):
            transactions.append(self.transactions_queue.get())

        while True:
            try:
                blockchain = BlockChain.load()
            except:
                sleep(.01)
                continue
            
            if blockchain.last_block:
                block = Block(blockchain.last_block.id + 1, previous_hash=blockchain.last_block.b64_hash())
            else:
                block = Block(0)

            block.add_transaction(MintTransaction(self.name, 50))
            
            # Add newly recieved transactions to local queue
            for _ in range(self.transactions_queue.qsize()):
                transactions.append(self.transactions_queue.get())

            # Populate the block with transactions
            for transaction in transactions:
                if block.num_transactions() >= self.max_transactions:
                    break

                if transaction.unique_id in blockchain.used_ids:
                    continue

                block.add_transaction(transaction)

            print(f"Trying nonce for Block {block.id} with {block.num_transactions()} transaction{"s" if block.num_transactions() != 1 else ""}")

            # Add random nonce to the block to try and achieve n leading 0 bits on the hash
            block.nonce = int.from_bytes(token_bytes(4))

            bits = BitArray(block.hash()).bin
            
            if bits.startswith("0" * self.difficulty):
                print(f"{self.name}: Found valid nonce {block.nonce} for block {block.id}")
                
                pickled_block = pickle.dumps(block)

                with open("clients.json") as clients_file:
                    clients = json.load(clients_file)

                for port in clients["ledgers"].values():
                    socket = zmq.Context().socket(zmq.REQ)
                    socket.connect(f"tcp://127.0.0.1:{port}")
                    socket.send(pickled_block)
                    socket.recv()
            else:
                sleep(1 / self.hashes)

    def start(self):
        self.mine_thread.start()

        self.socket = zmq.Context().socket(zmq.REP)
        self.socket.bind(f"tcp://127.0.0.1:{self.port}")

        while True:
            message = self.socket.recv().decode()
            # print(message)
            try:
                transaction = Transaction.parse(message)
                
                while True:
                    try:
                        blockchain = BlockChain.load()
                        saldo = blockchain.saldo
                        used_ids = blockchain.used_ids
                        break
                    except:
                        sleep(.01)
                        continue

                if transaction.name in saldo and saldo[transaction.name] >= transaction.amount:
                    if not transaction.unique_id in used_ids:
                        self.transactions_queue.put(transaction)
                        self.socket.send(b"OK")
                    else:
                        self.socket.send(b"Unique ID of transaction must be unique but is not")
                else:
                    budget = 0
                    if transaction.name in saldo:
                        budget = saldo[transaction.name]
                    self.socket.send(f"Not enough budget {transaction.amount} > {budget}".encode())
            except:
                self.socket.send(f"Invalid transaction rejected".encode())
    
    def stop(self):
        free_port(self.name)

def main():
    args = miner_args()

    miner = Miner(args.name, args.max_transactions, args.hashes, args.difficulty)

    try:
        miner.start()
    except KeyboardInterrupt:
        miner.stop()

def miner_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("-m", "--max-transactions", default="1")
    parser.add_argument("--hashes", default="16")
    parser.add_argument("--difficulty", default="8")
    args = parser.parse_args()
    args.name = args.name.lower()
    args.max_transactions = int(args.max_transactions)
    args.hashes = float(args.hashes)
    args.difficulty = int(args.difficulty)
    return args

if __name__ == "__main__":
    main()
