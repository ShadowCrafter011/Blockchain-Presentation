#!/bin/env python3

from blockchain_saver import BlockChain
from threading import Thread
from miner import Miner
from time import sleep
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("number")
    parser.add_argument("-m", "--max-transactions", default="1")
    parser.add_argument("--hashes", default="1")
    parser.add_argument("--difficulty", default="3")
    args = parser.parse_args()
    args.max_transactions = int(args.max_transactions)
    args.hashes = int(args.hashes)
    args.difficulty = int(args.difficulty)
    args.number = int(args.number)

    miners: list[Miner] = [Miner(f"miner{x}", args.max_transactions, args.hashes, args.difficulty) for x in range(args.number)]
    [Thread(target=m.start, daemon=True).start() for m in miners]

    try:
        while True:
            sleep(.05)
    except KeyboardInterrupt:
        for miner in miners:
            miner.stop()

if __name__ == "__main__":
    main()
