from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature
import base64
import os


class Signer:
    def __init__(self):
        self.private_keys = {}

        for pem_file in os.listdir("keys"):
            if pem_file == ".keep":
                continue

            pem_path = os.path.join("keys", pem_file)

            with open(pem_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                )
                self.private_keys[pem_file.removesuffix(".pem")] = private_key

    def sign_message(self, message: str, name: str) -> str:
        name = name.lower()

        signature = self.__get_private_key(name).sign(
            message.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode("utf-8")

    def verify_signature(self, message: str, name: str, signature: str):
        name = name.lower()

        public_key = self.__get_private_key(name).public_key()
        try:
            public_key.verify(
                base64.b64decode(signature),
                message.encode("utf-8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except:
            return False
        else:
            return True

    def __get_private_key(self, name: str):
        if not name in self.private_keys:
            private_key = self.__generate_private_key()
            self.private_keys[name] = private_key
            self.__save_private_key(private_key, name)
            return private_key
        return self.private_keys[name]

    def __generate_private_key(self):
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

    def __save_private_key(self, private_key, name):
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(f"keys/{name}.pem", "wb") as pem_file:
            pem_file.write(pem)
