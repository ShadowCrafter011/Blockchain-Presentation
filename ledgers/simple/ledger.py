#!/bin/env python3


from parser import SimpleLedgerArgparse
import json
import os


def main():
    if not os.path.isfile("ledger.json"):
        with open("ledger.json", "w") as ledger_file:
            json.dump([], ledger_file, indent=4)

    with open("ledger.json") as ledger_file:
        ledger: list = json.load(ledger_file)

    parser = SimpleLedgerArgparse()

    match parser.command():
        case "list":
            total = 0
            people_total = {}
            for transaction in ledger:
                amount = list(transaction.values())[0]
                person = list(transaction.keys())[0]
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

            people = sorted(people_total, key=lambda x: x[1])

            for person in people:
                if people_total[person] < 0:
                    print(f"{person} owes {round(-people_total[person], 2)}$")
                elif people_total[person] > 0:
                    print(f"{person} recieves {round(people_total[person], 2)}$")


        case "pay":
            ledger.append({
                f"{parser.person()}": parser.amount()
            })

            print(f"Transaction successfull: {parser.person()} payed {parser.amount()}")
            
        case _:
            raise ValueError(f"Command {parser.command()} was not recognized")

    with open("ledger.json", "w") as ledger_file:
        json.dump(ledger, ledger_file, indent=4)


if __name__ == "__main__":
    main()
