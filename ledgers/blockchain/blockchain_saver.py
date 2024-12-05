#!/bin/env python3

from transaction import Transaction, MintTransaction
from anytree.exporter import UniqueDotExporter
from port_handler import get_port, free_port
from anytree import Node, PreOrderIter
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

    def saldo(self):
        chain: list[Block] = self.construct_tree()
        saldo = {}
        for block in chain:
            for transaction in block.transactions:
                if isinstance(transaction, Transaction):
                    if not transaction.name in saldo:
                        saldo[transaction.name] = 0
                    if not transaction.to in saldo:
                        saldo[transaction.to] = 0
                    saldo[transaction.name] -= transaction.amount
                    saldo[transaction.to] += transaction.amount
                elif isinstance(transaction, MintTransaction):
                    if not transaction.minter in saldo:
                        saldo[transaction.minter] = transaction.amount
                    else:
                        saldo[transaction.minter] += transaction.amount
        return saldo

    def construct_tree(self, readable=True):
        if len(self.blocks) == 0:
            raise ValueError("BlockChain is empty")

        previous_hahes = []
        for block in self.blocks.values():
            previous_hahes.append(block.previous_hash)
        
        # Find nodes without previous hash
        node_process_stack = []
        for hash, block in self.blocks.items():
            if hash in previous_hahes:
                continue

            node_process_stack.append(block)

        nodes = {}
        node_blocks = {}
        
        # Index nodes by their previous hash
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

            # To be able to identify blocks by node
            node_blocks[node] = block

        # Construct blockchain tree with previous hashes index
        node_process_stack: list[dict] = [n for n in nodes["start"]]
        while len(node_process_stack) > 0:
            to_process = node_process_stack.pop(0)
            if to_process["block"].b64_hash() in nodes:
                for next_node in nodes[to_process["block"].b64_hash()]:
                    next_node["node"].parent = to_process["node"]
                    node_process_stack.append(next_node)

        self.node_block_dict = nodes.copy()
        
        # Generate image of blockchain
        for index, node_dict in enumerate(nodes["start"]):
            UniqueDotExporter(node_dict["node"]).to_picture(f"blockchain-{index}.png")

        # Find longest path in blockchain tree
        pathes = []
        current_path = []
        last_node = None
        for node in PreOrderIter(nodes["start"][0]["node"]):
            if last_node is None:
                last_node = node
                current_path.append(node)
            else:
                last_node_block = node_blocks[last_node]
                current_node_block = node_blocks[node]
                if current_node_block.previous_hash == last_node_block.b64_hash():
                    last_node = node
                    current_path.append(node)
                else:
                    pathes.append(current_path)
                    current_path = [node]
                    last_node = node

        if len(current_path) > 0:
            pathes.append(current_path)
        
        longest_path = []
        for path in pathes:
            if len(path) > len(longest_path):
                longest_path = path
        
        return [node_blocks[node] for node in longest_path]

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
