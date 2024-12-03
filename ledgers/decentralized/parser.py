import argparse

def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", required=True)
    parser.add_argument("-t", "--to", required=True)
    parser.add_argument("-a", "--amount", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument("-o", "--only")
    parser.add_argument("--change-signature", action="store_true")
    parser.add_argument("--id")
    args = parser.parse_args()
    args = lower(args, "name", "to", "only")
    args.amount = float(args.amount)
    return args

def lower(args, *attributes):
    for attr in attributes:
        if attr in args:
            if val := getattr(args, attr):
                setattr(args, attr, val.lower())
    return args
