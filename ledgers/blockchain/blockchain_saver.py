#!/bin/env python3

from anytree.exporter import UniqueDotExporter
from port_handler import get_port, free_port
from anytree import Node, RenderTree
from block import Block
import base64
import pickle
import zmq
import os

class BlockChain:
    def __init__(self):
        self.blocks: dict[str, Block] = {}
        self.node_block_dict = {}

    @classmethod
    def load(cls) -> BlockChain:
        if os.path.isfile("blockchain.pickle"):
            with open("blockchain.pickle", "rb") as blockchain_file:
                return pickle.load(blockchain_file)
        return BlockChain()
    
    def add_block(self, block: Block):
        hash = base64.b64encode(block.hash()).decode()
        self.blocks[hash] = block

    def construct_tree(self, readable=False):
        previous_hahes = []
        for block in self.blocks.values():
            previous_hahes.append(block.previous_hash)
        
        node_process_stack = []
        for hash, block in self.blocks.items():
            if hash in previous_hahes:
                continue

            node_process_stack.append(block)

        nodes = {}
        
        while len(node_process_stack) > 0:
            block = node_process_stack.pop(0)
            hash = base64.b64encode(block.hash()).decode()
            node_name = f"Block {block.id}" if readable else hash
            node = Node(node_name)
            identifier = block.previous_hash or "start"
            if identifier in nodes:
                nodes[identifier].append({
                    "node": node,
                    "block": block
                })
            else:
                nodes[identifier] = [{
                    "node": node,
                    "block": block
                }]
            if block.previous_hash:
                node_process_stack.append(
                    self.blocks[block.previous_hash]
                )

        node_process_stack: list[dict] = [n for n in nodes["start"]]
        while len(node_process_stack) > 0:
            to_process = node_process_stack.pop(0)
            if to_process["block"].b64_hash() in nodes:
                for next_node in nodes[to_process["block"].b64_hash()]:
                    next_node["node"].parent = to_process["node"]
                    node_process_stack.append(next_node)

        self.node_block_dict = nodes.copy()
        
        for index, node_dict in enumerate(nodes["start"]):
            UniqueDotExporter(node_dict["node"]).to_picture(f"blockchain-{index}.png")


def main():
    blockchain = BlockChain.load()
    
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
