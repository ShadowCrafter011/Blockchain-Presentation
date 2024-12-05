from cryptography.hazmat.primitives.hashes import Hash, SHA256
from transaction import Transaction
from bitstring import BitArray
import base64

class Block:
    def __init__(self, id, previous_hash=""):
        self.id = id
        self.nonce = 0
        self.transactions: list[Transaction]  = []
        self.previous_hash = previous_hash

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def num_transactions(self):
        return len(self.transactions)

    def hash(self):
        digest = Hash(SHA256())
        digest.update(str(self.id).encode())
        digest.update(self.previous_hash.encode())
        digest.update(str(self.nonce).encode())
        for transaction in self.transactions:
            digest.update(transaction.to_bytes())
        return digest.finalize()
    
    def b64_hash(self) -> str:
        return base64.b64encode(self.hash()).decode()
    
    def __str__(self):
        transaction_lines = []
        for transaction in self.transactions:
            name, to, amount, unique_id, signature = transaction.to_list()
            transaction_lines.append(
                f"{name} -> {to}, {amount}, {unique_id[:5]}-{unique_id[-5:]}, {signature[:5]}-{signature[-5:]}"
            )
        hash = f"Block hash {BitArray(self.hash()).bin[:20]}"
        previous_hash = f"Previous hash {BitArray(base64.b64decode(self.previous_hash)).bin[:20]}"
        block_id = f"Block {self.id}"
        nonce = f"Nonce {self.nonce}"
        no_transactions = "No transactions"

        max_len = max(len(hash), len(previous_hash), len(block_id), len(nonce), len(no_transactions))
        for transaction_line in transaction_lines:
            max_len = max(max_len, len(transaction_line))
        
        separator = "-" * (max_len + 2)

        output = separator + "\n"
        for line in [block_id, previous_hash, hash, nonce]:
            output += f"|{line}{" " * (max_len - len(line))}|\n"
            output += separator + "\n"

        for transaction_line in transaction_lines:
            output += f"|{transaction_line}{" " * (max_len - len(transaction_line))}|\n"

        if len(transaction_lines) == 0:
            output += f"|{no_transactions}{" " * (max_len - len(no_transactions))}|\n"
        
        output += separator
        return output
        