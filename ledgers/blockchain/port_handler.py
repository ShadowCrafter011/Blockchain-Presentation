import json
import os

def get_port(name, client_type):
    if not client_type in ["miners", "ledgers"]:
        raise ValueError("Can only give port to types client or miner")
    
    create_clients_file()
    
    with open("clients.json") as clients_file:
        clients = json.load(clients_file)

    if name in list(clients["miners"].keys()) + list(clients["ledgers"].keys()):
        raise ValueError(f"Client with name {name} is already active")

    max_port = 5554
    for port in list(clients["miners"].values()) + list(clients["ledgers"].values()):
        max_port = max(port, max_port)

    max_port += 1

    clients[client_type][name] = max_port

    with open("clients.json", "w") as clients_file:
        json.dump(clients, clients_file)

def free_port(name):
    create_clients_file()

    with open("clients.json") as clients_file:
        clients = json.load(clients_file)

    if name in clients["miners"]:
        del clients["miners"][name]
    if name in clients["ledgers"]:
        del clients["ledgers"][name]

    with open("clients.json", "w") as clients_file:
        json.dump(clients_file)

def create_clients_file():
    if not os.path.isfile("clients.json"):
        with open("clients.json", "w") as clients_file:
            json.dump({
                "miners": {},
                "ledgers": {}
            }, clients_file)
