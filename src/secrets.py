from cryptography.fernet import Fernet
import http.client
import json
import hashlib
import math
from key_generation.src.Config import Config as Gc

class Encrypt(object):
    def __init__(self):
        self.conn = http.client.HTTPSConnection(Gc().return_config_secrets(secrets_http_client_URL=True))
        self.jwt_secret = Gc().return_config_secrets(secrets_jwt_secret=True)
        self.salt_key = Gc().return_config_secrets(secrets_hash_salt_key=True)
        self.secret_key = Gc().return_config_secrets(secrets_fernet_key=True)

    """
     @Notice: This function will generate an encryption secret key
     @Dev:    We user the Fernet generate_key method to generate a key and store in a secret.key file
    """

    def generate_key(self, key_location: str = None):
        with open("./src/%s" % key_location, "wb") as key_file:
            key_file.write(Fernet.generate_key())

    """
     @Notice: This function will load an existing encryption key from a file
     @Dev:    We open a file and return its content
    """
    def load_key(self, key_path=None):
        """if key_path is None:
            return open("%ssecret.key" % self.key_location, "rb").read()
        return open(key_path, "rb").read()"""
        return b"o3yaVEZLx2k_2hh8DSgIWGYeQIr4xmfT5ZyOTBXIYc4="

    """
     @Notice: This function will encrypt a string using the loaded encryption key
     @Dev:    We use the Fernet encrypt method and the loaded encryption key to encrypt a string
    """
    def encrypt_message(self, message):
        return Fernet(self.secret_key).encrypt(str(message).encode()).decode()

    """
     @Notice: This function will decrypt a string using the loaded encryption key
     @Dev:    We use the Fernet decrypt method and the loaded encryption key to decrypt a string
    """

    def decrypt_message(self, encrypted_message):
        return Fernet(self.secret_key).decrypt(encrypted_message).decode()

    """
     @Notice: This function will generate the jwt authentification token
     @Dev:    We return the jwt token generated by the API using the righ header 
    """

    def get_jwt(self):
        payload = "{\"client_id\":\"A0vOnWjqj1J4K92uVEK6PpMPzWzU0QrF\"," \
                  "\"client_secret\":\"%s\", " \
                  "\"audience\":\"carbonyte.io/api/\",\"grant_type\":\"client_credentials\"} " % self.jwt_secret
        headers = {'content-type': "application/json"}
        self.conn.request("POST", "/oauth/token", payload, headers)
        res = self.conn.getresponse()
        data = res.read().decode("utf-8")
        data = json.loads(data)
        return "Bearer %s" % data['access_token']

    """
     @Notice: This function will generate a sha3 row hash
     @Dev:    We concatenate the arguments string list to a string, hash it and 32 bits salt it, then we salt it again using the salt.key
    """

    def hash_list(self, args_list: list):
        concatenated_row = "".join(str(e) for e in args_list)
        obj_sha3_256 = hashlib.sha3_256(concatenated_row.encode())
        hash_salt = "".join(str(letter) for index, letter in enumerate(concatenated_row) if index % 2 == 0)
        if len(hash_salt) > 32:
            hash_salt = hash_salt[:32]
        elif len(hash_salt) < 32:
            hash_salt = hash_salt * math.floor(32 / len(hash_salt))
            hash_salt = hash_salt + hash_salt[:(32 % len(hash_salt))]
        obj_sha3_256.update(hash_salt.encode())
        obj_sha3_256.update(self.decrypt_message(self.salt_key.encode()).encode())
        return obj_sha3_256.hexdigest()


if __name__ == "__main__":
    pass
