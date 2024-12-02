from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature
import base64
import os


class Signer:
    def sign_message(self, message: str, name: str, password: str) -> str:
        name = name.lower()

        signature = self.__get_private_key(name, password).sign(
            message.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode("utf-8")

    def verify_signature(self, message: str, name: str, signature: str) -> bool:
        name = name.lower()

        try:
            with open(f"keys/{name}.pub.pem", "rb") as pem_data:
                public_key = load_pem_public_key(pem_data.read())
            
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

    def __get_private_key(self, name: str, password: str) -> rsa.RSAPrivateKey:
        pem_path = f"keys/{name}.pem"
        if not os.path.isfile(pem_path):
            private_key = self.__generate_private_key()
            self.__save_private_key(private_key, name, password)
            return private_key
        with open(pem_path, "rb") as pem_file:
            return serialization.load_pem_private_key(
                pem_file.read(),
                password=password.encode("utf-8")
            )

    def __generate_private_key(self) -> rsa.RSAPrivateKey:
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

    def __save_private_key(self, private_key: rsa.RSAPrivateKey, name: str, password: str):
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8"))
        )
        with open(f"keys/{name}.pem", "wb") as pem_file:
            pem_file.write(pem)
        
        pub = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open(f"keys/{name}.pub.pem", "wb") as pub_file:
            pub_file.write(pub)
