#!/bin/env python3

from transaction import  MintTransaction
from blockchain_saver import BlockChain
from fraudulent_id import FraudulentId
from secrets import token_bytes
from bitstring import BitArray
from miner import miner_args
from signer import Signer
from block import Block
from time import sleep
import pickle
import base64
import json
import zmq

class FraudulentMiner:
    def __init__(self, name, hashes, difficulty):
        self.name = name
        self.hashes = hashes
        self.difficulty = difficulty

        blockchain = BlockChain.load()

        if blockchain.last_block:
            self.block = Block(FraudulentId(blockchain.last_block.id + 1), previous_hash=blockchain.last_block.b64_hash())
        else:
            self.block = Block(FraudulentId(0))

        self.block.add_transaction(MintTransaction(name, 50))

    def mine(self):
        self.block.nonce = int.from_bytes(token_bytes(4))

        bits = BitArray(self.block.hash()).bin
            
        if bits.startswith("0" * self.difficulty):
            print(f"{self.name}: Found valid nonce {self.block.nonce} for block {self.block.id}")
            
            pickled_block = pickle.dumps(self.block)

            with open("clients.json") as clients_file:
                clients = json.load(clients_file)

            for port in clients["ledgers"].values():
                socket = zmq.Context().socket(zmq.REQ)
                socket.connect(f"tcp://127.0.0.1:{port}")
                socket.send(pickled_block)
                socket.recv()

            self.block = Block(FraudulentId(self.block.id + 1), previous_hash=self.block.b64_hash())
            self.block.add_transaction(MintTransaction(self.name, 50))
        else:
            sleep(1 / self.hashes)

def main():
    args = miner_args()

    fraudulent_miner = FraudulentMiner(args.name, args.hashes, args.difficulty)

    try:
        while True:
            fraudulent_miner.mine()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
