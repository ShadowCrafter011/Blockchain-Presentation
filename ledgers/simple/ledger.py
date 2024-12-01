#!/bin/env python3


from parser import SimpleLedgerArgparse
import os


def main():
    if not os.path.isfile("ledger.txt"):
        ledger = []
    else:
        with open("ledger.txt") as ledger_file:
            ledger_lines = ledger_file.read().split("\n")
            ledger = []
            for line in ledger_lines:
                if not (stripped_line := line.strip()):
                    continue
                ledger.append({
                    stripped_line.split(", ")[0]: float(stripped_line.split(", ")[1])
                })

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
            ledger.append({
                parser.person(): parser.amount()
            })

            print(f"Transaction successfull: {parser.person()} payed {parser.amount()}")
            
        case _:
            raise ValueError(f"Command {parser.command()} was not recognized")

    ledger_lines = []
    for line in ledger:
        name, amount = list(line.items())[0]
        ledger_lines.append(f"{name}, {amount}")

    with open("ledger.txt", "w") as ledger_file:
        ledger_file.write("\n".join(ledger_lines))


if __name__ == "__main__":
    main()
