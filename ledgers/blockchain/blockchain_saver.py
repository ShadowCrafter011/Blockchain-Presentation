#!/bin/env python3

from transaction import Transaction, MintTransaction
from anytree.exporter import UniqueDotExporter
from port_handler import get_port, free_port
from fraudulent_id import FraudulentId
from multiprocessing import Process
from bitstring import BitArray
from anytree import Node
from block import Block
from time import sleep
import argparse
import anytree
import sqlite3
import base64
import pickle
import zmq
import os

class BlockChain:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.genesis_nodes: list[Node] = []
        self.most_parented_node: Node = None
        self.end_nodes: list[Node] = []
        self.last_block: Block = None
        self.longest_chain: list[Block] = []
        self.saldo: dict[str, float] = {}
        self.processed_transactions: list[str] = []
        self.used_ids: list[str] = []

    @classmethod
    def load(cls) -> BlockChain:
        if os.path.isfile("/workspaces/Blockchain-Presentation/ledgers/blockchain/blockchain.pickle"):
            with open("/workspaces/Blockchain-Presentation/ledgers/blockchain/blockchain.pickle", "rb") as blockchain_file:
                return pickle.load(blockchain_file)
        return BlockChain()
    
    def add_block(self, block: Block):
        node = Node(f"Block {block.id}")
        setattr(node, "block", block)

        if block.previous_hash in self.nodes:
            node.parent = self.nodes[block.previous_hash]
        else:
            self.genesis_nodes.append(node)
        
        self.nodes[block.b64_hash()] = node

        self.post_add_routine()

    def compute_end_nodes(self):
        self.end_nodes = []
        for node in self.genesis_nodes:
            self.end_nodes += list(anytree.findall(node, lambda n: len(n.children) == 0))

    def compute_most_parented_node(self):
        max_parents = -1
        self.most_parented_node = None
        for node in self.end_nodes:
            parents = 0
            n = node
            while n.parent:
                parents += 1
                n = n.parent
            if parents > max_parents:
                max_parents = parents
                self.most_parented_node = node
    
    def compute_longest_chain(self):
        node = self.most_parented_node
        self.longest_chain = []
        while node.parent:
            self.longest_chain.insert(0, node.block)
            node = node.parent
        self.longest_chain.insert(0, node.block)
    
    def compute_last_block(self):
        chain = self.longest_chain
        self.last_block = chain[len(chain) - 1]

    def compute_saldo(self):
        self.saldo = {}
        self.processed_transactions = []
        self.used_ids = []
        for block in self.longest_chain:
            for transaction in block.transactions:
                self.processed_transactions.append(transaction.signature)
                self.used_ids.append(transaction.unique_id)

                if isinstance(transaction, Transaction):
                    if not transaction.name in self.saldo:
                        self.saldo[transaction.name] = 0
                    if not transaction.to in self.saldo:
                        self.saldo[transaction.to] = 0

                    self.saldo[transaction.name] -= transaction.amount
                    self.saldo[transaction.to] += transaction.amount

                if isinstance(transaction, MintTransaction):
                    if not transaction.minter in self.saldo:
                        self.saldo[transaction.minter] = transaction.amount
                    else:
                        self.saldo[transaction.minter] += transaction.amount

    def post_add_routine(self):
        self.compute_end_nodes()
        self.compute_most_parented_node()
        self.compute_longest_chain()
        self.compute_last_block()
        self.compute_saldo()

    def visualize(self):
        for index, genesis_node in enumerate(self.genesis_nodes):
            UniqueDotExporter(genesis_node).to_picture(f"blockchain-{index}.png")

    def prune(self):
        tombstoned = []
        for hash, node in self.nodes.items():
            if not node.block in self.longest_chain:
                node.parent = None
                tombstoned.append(hash)
        for hash in tombstoned:
            if self.nodes[hash] in self.genesis_nodes:
                self.genesis_nodes.remove(self.nodes[hash])
            del self.nodes[hash]
        self.compute_end_nodes()

    def send_longest_chain_to_db(self):
        con = sqlite3.connect("/workspaces/Blockchain-Presentation/viewer/db.sqlite3")
        cur = con.cursor()
        for block in self.longest_chain:
            save_block_to_db(con, cur, block)
        cur.close()
        con.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prune", action="store_true", default=False)
    args = parser.parse_args()

    blockchain = BlockChain.load()
    
    port = get_port("blockchain", "ledgers")

    socket = zmq.Context().socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")

    Process(target=visualize_process, args=(1,), daemon=True).start()

    con = sqlite3.connect("/workspaces/Blockchain-Presentation/viewer/db.sqlite3")
    cur = con.cursor()
    # cur.execute("INSERT INTO blockchain_block ('int_id', 'name', 'to', 'amount', 'unique_id', 'signature') VALUES ('0', 'lukas', 'nithus', 50, 'id', 'sig')")

    try:
        while True:
            message = socket.recv().decode()
            block: Block = pickle.loads(base64.b64decode(message))
            blockchain.add_block(block)
            if args.prune:
                blockchain.prune()
            with open("/workspaces/Blockchain-Presentation/ledgers/blockchain/blockchain.pickle", "wb") as blockchain_file:
                pickle.dump(blockchain, blockchain_file)
            print(f"Recieved Block {block.id} with {block.num_transactions()} transaction{"s" if block.num_transactions() != 1 else ""}")

            save_block_to_db(con, cur, block)

            socket.send(b"OK")
    except KeyboardInterrupt:
        free_port("blockchain")
        cur.close()
        con.close()


def save_block_to_db(con, cur, block: Block):
    transactions = []
    for transaction in block.transactions:
        fields = [type(transaction).__name__]
        fields += transaction.to_list()
        fields = map(lambda f: str(f), fields)
        transactions.append(",".join(fields))
    col_names = "('int_id', 'nonce', 'hash', 'previous_hash', 'transactions')"
    hash = BitArray(block.hash()).bin
    previous_hash = BitArray(base64.b64decode(block.previous_hash.encode())).bin
    values = f"('{block.id}', {block.nonce}, '{hash}', '{previous_hash}', '{";".join(transactions)}')"
    cur.execute(f"INSERT INTO blockchain_block {col_names} VALUES {values}")
    con.commit()

def visualize_process(interval):
    try:
        while True:
            BlockChain.load().visualize()
            sleep(interval)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
