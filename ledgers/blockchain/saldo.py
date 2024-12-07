#!/bin/env python3

from blockchain_saver import BlockChain

def main():
    saldo = BlockChain.load().saldo
    for name, amount in saldo.items():
        print(f"{name} has {amount} DD")

if __name__ == "__main__":
    main()
