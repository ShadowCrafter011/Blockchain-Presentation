#!/bin/env python3

from port_handler import get_port, free_port
from block import Block
import base64
import pickle
import zmq
import os

class BlockChain:
    def __init__(self):
        self.blocks: dict[str, Block] = {}
    
    def add_block(self, block: Block):
        hash = base64.b64encode(block.hash()).decode()
        self.blocks[hash] = block

def main():
    if not os.path.isfile("blockchain.pickle"):
        blockchain = BlockChain()
    else:
        with open("blockchain.pickle", "rb") as blockchain_file:
            blockchain = pickle.load(blockchain_file)
    
    port = get_port("blockchain", "ledgers")

    socket = zmq.Context().socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")

    try:
        while True:
            message = socket.recv().decode()
            if message.startswith("BLOCK:"):
                print(f"Recieved new block {message}")
                message = message.removeprefix("BLOCK:")
                block = pickle.loads(base64.b64decode(message))
                blockchain.add_block(block)
                with open("blockchain.pickle", "wb") as blockchain_file:
                    pickle.dump(blockchain, blockchain_file)
            socket.send(b"OK")
    except KeyboardInterrupt:
        free_port("blockchain")

if __name__ == "__main__":
    main()
