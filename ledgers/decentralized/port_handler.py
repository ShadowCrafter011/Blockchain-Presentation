import json
import os

def get_port(name: str) -> int:
    if not os.path.isfile("clients.json"):
        with open("clients.json", "w") as clients_file:
            json.dump({}, clients_file)
    with open("clients.json") as clients_file:
        clients = json.load(clients_file)
    max_port = 5554
    for port in clients.values():
        max_port = max(port, max_port)
    if name in clients:
        return None
    max_port += 1
    clients[name] = max_port
    with open("clients.json", "w") as clients_file:
        json.dump(clients, clients_file)
    return max_port

def free_port(name: str) -> None:
    if not os.path.isfile("clients.json"):
        return
    with open("clients.json") as clients_file:
        clients = json.load(clients_file)
    if not name in clients:
        return
    del clients[name]
    with open("clients.json", "w") as clients_file:
        json.dump(clients, clients_file)
