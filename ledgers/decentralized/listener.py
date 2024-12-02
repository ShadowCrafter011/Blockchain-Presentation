from port_handler import get_port, free_port
from signer import Signer
import argparse
import json
import zmq
import os


class Listener:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("name")
        args = parser.parse_args()
        self.name = args.name.lower()

        self.signer = Signer()

        self.ledger = {}

        if os.path.isfile(f"ledgers/ledger-{self.name}.txt"):
            with open(f"ledgers/ledger-{self.name}.txt") as ledger_file:
                ledger_lines = ledger_file.read().split("\n")
            for line in ledger_lines:
                if not line.strip():
                    continue

                name, to, amount, *_ = line.split(", ")
                amount = float(amount)
                if not name in self.ledger:
                    self.ledger[name] = 100.0
                if not to in self.ledger:
                    self.ledger[to] = 100.0
                
                self.ledger[name] -= amount
                self.ledger[to] += amount
            
            self.__print_ledger()

        
        if (port := get_port(self.name)) is None:
            raise ValueError(f"Client with name {self.name} is already active")

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"tcp://127.0.0.1:{port}")

    def start(self):
        while True:
            new_line = self.socket.recv().decode()
            name, to, amount, unique_id, signature = new_line.split(", ")
            amount = float(amount)

            if not self.signer.verify_signature(
                f"{name}, {to}, {amount}, {unique_id}",
                name,
                signature
            ):
                err = f"ERR Invalid signature for {name} sending {amount} DD to {to}"
                print(err)
                self.socket.send(err.encode())
                continue

            if not name in self.ledger:
                self.ledger[name] = 100.0
            if not to in self.ledger:
                self.ledger[to] = 100.0

            if amount > self.ledger[name]:
                err = f"ERR {name} does not have enough budget to send {amount} to {to} ({self.ledger[name]} DD)"
                print(err)
                self.socket.send(err.encode())
                continue

            self.ledger[name] -= amount
            self.ledger[to] += amount

            with open(f"ledgers/ledger-{self.name}.txt", "a") as ledger_file:
                ledger_file.write(new_line + "\n")

            print(f"{name}, {to}, {amount}, {unique_id[:5]}-{unique_id[-5:]}, {signature[:5]}-{signature[-5:]}")
            self.__print_ledger()
            self.socket.send(b"OK")
    
    def stop(self):
        free_port(self.name)

    def __print_ledger(self):
        for name, amount in self.ledger.items():
            print(f"{name.capitalize()} has {amount} DD")
