#!/bin/env python3


from parser import SimpleLedgerArgparse
from signer import Signer
import os


def main():
    parser = SimpleLedgerArgparse()
    signer = Signer()
    max_id = -1

    if not os.path.isfile("ledger.txt") and parser.command() != "setup":
        print("Ledger is not setup yet. Please use the setup command")
        return
    elif parser.command() != "setup":
        with open("ledger.txt") as ledger_file:
            first_split = ledger_file.read().split("\n", maxsplit=1)
            prepay_amount = first_split[0]
            if len(first_split) == 2:
                ledger_lines = first_split[1].split("\n")
            else:
                ledger_lines = []
            prepay_amount = float(prepay_amount)
            ledger = []
            currency_amount = {}
            ids = []
            for line in ledger_lines:
                if not (stripped_line := line.strip()):
                    continue
                id, name, to, amount, signature = stripped_line.split(", ")
                id = int(id)
                amount = float(amount)
                if verify_transaction(signer, name, to, id, amount, signature):
                    if id in ids:
                        print(f"Transaction with duplicate id was rejected: {name} payed {amount}")
                        continue
                    ids.append(id)
                    if id > max_id:
                        max_id = id
                    if not name in currency_amount:
                        currency_amount[name] = prepay_amount
                    if not to in currency_amount:
                        currency_amount[to] = prepay_amount
                    if currency_amount[name] >= amount:
                        currency_amount[name] -= amount
                        currency_amount[to] += amount
                    else:
                        print(f"Overpaid transaction was rejected: {name} to {to} overpaied by {amount - currency_amount[name]} DD")
                        continue
                    ledger.append({
                        "id": id,
                        "name": name,
                        "to": to,
                        "amount": float(amount),
                        "signature": signature
                    })
                else:
                    print(f"Invalid transaction was rejected: {name} payed {amount}")

    match parser.command():
        case "setup":
            if os.path.isfile("ledger.txt"):
                print("Ledger already exists")
                return
            with open("ledger.txt", "w") as ledger_file:
                ledger_file.write(f"{parser.amount()}\n")
            print(f"Ledger was setup with prepay amount of {parser.amount()} DD")
            return

        case "list":
            if len(currency_amount) == 0:
                print("Ledger is empty")
            for name, currency_left in currency_amount.items():
                print(f"{name} has {currency_left} DD")

        case "pay":
            name, to, amount, password = parser.name(), parser.to(), parser.amount(), parser.password()
            if name is None or to is None or amount is None or password is None:
                print("Name, to, amount and password are required to sign a transaction")
                return
            
            if name not in currency_amount:
                currency_amount[name] = prepay_amount
            
            if amount > currency_amount[name]:
                print(f"Transaction invalid: {name} does not have enough budget")
                return

            try:
                max_id += 1
                signature = signer.sign_message(f"{max_id}, {to}, {amount}", name, password)
            except:
                print(f"Could not sign message: Invalid password for {name}")
                return
            
            ledger.append({
                "id": max_id,
                "name": name,
                "to": to,
                "amount": amount,
                "signature": signature
            })

            print(f"Transaction successfull: {parser.name()} payed {parser.amount()} DD to {parser.to()}")
            
        case _:
            raise ValueError(f"Command {parser.command()} was not recognized")

    ledger_lines = [str(prepay_amount)]
    for line in ledger:
        id, name, to, amount, signature = line["id"], line["name"], line["to"], line["amount"], line["signature"]
        ledger_lines.append(f"{id}, {name}, {to}, {amount}, {signature}")

    with open("ledger.txt", "w") as ledger_file:
        ledger_file.write("\n".join(ledger_lines))

def verify_transaction(signer: Signer, name, to, id, amount, signature):
    return signer.verify_signature(
        f"{id}, {to}, {amount}",
        name,
        signature
    )


if __name__ == "__main__":
    main()
