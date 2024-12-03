from cryptography.hazmat.primitives.hashes import Hash, SHA256
from cryptography.exceptions import InvalidSignature
from signer import Signer
from time import time

class Transaction:
    @classmethod
    def new(cls, name: str, to: str, amount: str, password: str) -> Transaction:
        signer = Signer()
        
        digest = Hash(SHA256())
        digest.update(f"{time()}, {name}, {to}, {amount}")
        unique_id = digest.finalize()

        signature = signer.sign_message(
            f"{name}, {to}, {amount}, {unique_id}",
            name,
            password
        )

        return Transaction(name, to, amount, unique_id, signature)
    
    @classmethod
    def parse(cls, transaction_string: str) -> Transaction:
        name, to, amount, unique_id, signature = transaction_string.split(", ")
        amount = float(amount)

        signer = Signer()

        if not signer.verify_signature(
            f"{name}, {to}, {amount}, {unique_id}",
            name,
            signature
        ):
            raise InvalidSignature(f"Invalid signature for {name} sending {amount} DD to {to}")
        
        return Transaction(name, to, amount, unique_id, signature)

    def __init__(self, name, to, amount, unique_id, signature):
        self.name = name
        self.to = to
        self.amount = amount
        self.unique_id = unique_id
        self.signature = signature

    def to_bytes(self) -> bytes:
        return f"{self.name}, {self.to}, {self.amount}, {self.unique_id}, {self.signature}".encode()
    
    def to_list(self) -> list:
        return [
            self.name,
            self.to,
            self.amount,
            self.unique_id,
            self.signature
        ]
