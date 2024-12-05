#!/bin/env python3

from transaction import Transaction, MintTransaction
from anytree.exporter import UniqueDotExporter
from port_handler import get_port, free_port
from threading import Thread
from anytree import Node
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
        self.blocks[block.b64_hash()] = block
        Thread(target=self.saldo, daemon=True).start()

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
            return []

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
        all_nodes = []
        node_blocks = {}
        
        # Index nodes by their previous hash
        while len(node_process_stack) > 0:
            block = node_process_stack.pop(0)
            node_name = f"Block {block.id}" if readable else block.b64_hash()
            node = Node(node_name)
            identifier = block.previous_hash or "start"
            if identifier in nodes:
                already_added = False
                for node_dict in nodes[identifier]:
                    if node_dict["block"].hash() == block.hash():
                        already_added = True

                if not already_added:
                    nodes[identifier].append({
                        "node": node,
                        "block": block
                    })
                    all_nodes.append(node)
            else:
                nodes[identifier] = [{
                    "node": node,
                    "block": block
                }]
                all_nodes.append(node)
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

        most_parented_node = None
        most_parents = 0
        for node in all_nodes:
            parents = 0
            n = node
            while n.parent is not None:
                parents += 1
                n = n.parent
            if parents > most_parents:
                most_parented_node = node
                most_parents = parents
            
        longest_chain = []
        while most_parented_node.parent is not None:
            longest_chain.insert(0, most_parented_node)
            most_parented_node = most_parented_node.parent

        # Insert genesis block
        longest_chain.insert(0, most_parented_node)
        return [node_blocks[node] for node in longest_chain]

def main():
    blockchain = BlockChain.load()
    
    port = get_port("blockchain", "ledgers")

    socket = zmq.Context().socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")

    try:
        while True:
            message = socket.recv().decode()
            if message.startswith("BLOCK:"):
                message = message.removeprefix("BLOCK:")
                block = pickle.loads(base64.b64decode(message))
                print(f"Recieved Block {block.id} with {block.num_transactions()} transactions")
                blockchain.add_block(block)
                with open("blockchain.pickle", "wb") as blockchain_file:
                    pickle.dump(blockchain, blockchain_file)
            socket.send(b"OK")
    except KeyboardInterrupt:
        free_port("blockchain")

if __name__ == "__main__":
    main()
