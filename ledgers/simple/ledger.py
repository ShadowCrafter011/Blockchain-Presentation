#!/bin/env python3


from parser import SimpleLedgerArgparse
import json
import os


def main():
    if not os.path.isfile("ledger.json"):
        with open("ledger.json", "w") as ledger_file:
            json.dump({}, ledger_file, indent=4)

    with open("ledger.json") as ledger_file:
        ledger: object = json.load(ledger_file)

    parser = SimpleLedgerArgparse()

    match parser.command():
        case "list":
            for name, owes in ledger.items():
                if len(owes) == 0:
                    continue

                print(name, "owes")
                for owes_to, amount in owes.items():
                    print(f"\t{amount}$ to {owes_to}")
                print()

        case "pay":
            person, to, amount = parser.person(), parser.to(), parser.amount()

            if person is None or to is None or amount is None:
                raise ValueError("Payment needs --amount, --person and --to to be set")
            
            # Add people in transaction to the root of the ledger if they are not there yet
            if not person in ledger:
                ledger[person] = {}
            if not to in ledger:
                ledger[to] = {}

            # Check if person owed to target
            if to in ledger[person]:
                # Debt is overreturned
                if amount > ledger[person][to]:
                    overpay_amount = amount - ledger[person][to]
                    del ledger[person][to]
                    add_debt(ledger, person, to, overpay_amount)
                # Debt is partially returned
                elif amount < ledger[person][to]:
                    ledger[person][to] -= amount
                # Debt is paied up precisely
                else:
                    del ledger[person][to]
            else:
                add_debt(ledger, person, to, amount)

            print(f"Transaction successfull")
            
        case _:
            raise ValueError(f"Command {parser.command()} was not recognized")

    with open("ledger.json", "w") as ledger_file:
        json.dump(ledger, ledger_file, indent=4)

def add_debt(ledger, pays, to, amount):
    if pays in ledger[to]:
        ledger[to][pays] += amount
    else:
        ledger[to][pays] = amount


if __name__ == "__main__":
    main()
