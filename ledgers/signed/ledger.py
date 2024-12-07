#!/bin/env python3


from parser import SimpleLedgerArgparse
from signer import Signer
import os


def main():
    parser = SimpleLedgerArgparse()
    signer = Signer()

    if not os.path.isfile("ledger.txt"):
        ledger = []
    else:
        with open("ledger.txt") as ledger_file:
            ledger_lines = ledger_file.read().split("\n")
            ledger = []
            for line in ledger_lines:
                if not (stripped_line := line.strip()):
                    continue
                name, amount, signature = stripped_line.split(", ")
                if verify_transaction(signer, name, amount, signature):
                    ledger.append({
                        "name": name,
                        "amount": float(amount),
                        "signature": signature
                    })
                else:
                    print(f"Invalid transaction was rejected: {name} payed {amount}")

    match parser.command():
        case "list":
            total = 0
            people_total = {}
            for transaction in ledger:
                person, amount = transaction["name"], transaction["amount"]
                total += amount
                if person in people_total:
                    people_total[person] += amount
                else:
                    people_total[person] = amount

            if len(people_total) == 0:
                print("Ledger is empty")
                return

            per_person = total / len(people_total)

            for person, payed in people_total.items():
                people_total[person] = payed - per_person

            people = sorted(people_total.items(), key=lambda x: x[1])

            for person in people:
                name, amount = person
                if amount < 0:
                    print(f"{name} owes {round(-amount, 2)}$")
                elif amount > 0:
                    print(f"{name} recieves {round(amount, 2)}$")
                else:
                    print(f"{name} owes and recieves nothing")


        case "pay":
            name, amount, password = parser.name(), parser.amount(), parser.password()
            if name is None or amount is None or password is None:
                print("Name, amount and password are required to sign a transaction")
                return

            try:
                signature = signer.sign_message(str(amount), name, password)
            except:
                print(f"Could not sign message: Invalid password for {name}")
                return
            
            ledger.append({
                "name": name,
                "amount": amount,
                "signature": signature
            })

            print(f"Transaction successfull: {parser.name()} payed {parser.amount()}$")
            
        case _:
            raise ValueError(f"Command {parser.command()} was not recognized")

    ledger_lines = []
    for line in ledger:
        name, amount, signature = line["name"], line["amount"], line["signature"]
        ledger_lines.append(f"{name}, {amount}, {signature}")

    with open("ledger.txt", "w") as ledger_file:
        ledger_file.write("\n".join(ledger_lines))

def verify_transaction(signer: Signer, name, amount, signature):
    return signer.verify_signature(
        str(amount),
        name,
        signature
    )


if __name__ == "__main__":
    main()
