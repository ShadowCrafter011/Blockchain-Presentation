from argparse import ArgumentParser


class SimpleLedgerArgparse:
    def __init__(self):
        self.parser = ArgumentParser()

        self.parser.add_argument("command")
        self.parser.add_argument("-a", "--amount")
        self.parser.add_argument("-p", "--person")
        self.parser.add_argument("-t", "--to")

        self.args = self.parser.parse_args()

    def command(self):
        return self.args.command
    
    def amount(self):
        try:
            return int(self.args.amount)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid argument passed for transaction amount: {self.args.amount}")
    
    def person(self):
        return self.args.person
    
    def to(self):
        return self.args.to