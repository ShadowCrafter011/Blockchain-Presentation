#!/bin/env python3

from listener import Listener

def main():
    listener = Listener()
    try:
        listener.start()
    except KeyboardInterrupt:
        listener.stop()

if __name__ == "__main__":
    main()
