import gnupg

class PGP_Manager():
    def __init__(self):
        self.gpg = gnupg.GPG('/usr/local/bin/gpg')
        self.gpg.encoding = 'utf-8'

    """
     @Notice: This function will generate a private and public key  
     @Dev:     We use the gen_key_input method from the gpg lib to generate both keys
    """
    def generate_key(self, email, password):
        key_input_data = self.gpg.gen_key_input(name_email=email, passphrase=password, key_type='RSA', key_length=4096)
        key = self.gpg.gen_key(key_input_data)
        return key

    """
     @Notice: This function will export the private and public keys in a file
     @Dev:    We use the gpg lib export_keys to get the keys and then we write them into a file (mykeyfile.asc)
    """
    def export_keys(self, key):
        ascii_armored_public_keys = self.gpg.export_keys(key)
        ascii_armored_private_keys = self.gpg.export_keys(key, True)
        with open('mykeyfile.asc', 'w') as f:
            f.write(ascii_armored_public_keys)
            f.write(ascii_armored_private_keys)
    
    """
     @Notice: This function will import the private and public keys from a file
     @Dev:    We use the gpg lib import_keys to get the keys from a file and import them.
    """
    def import_keys(self):
        key_data = open('mykeyfile.asc').read()
        import_result = self.gpg.import_keys(key_data)
        print(import_result.results)

    """
     @Notice: This function will encrypt a file content
     @Dev:    We open the file a replace its content to the encrypted content using 
              the encrypt_file method from the gpg lib
    """
    def encrypte_file(self, filepath, email):
        with open(filepath, 'rb') as f:
            self.gpg.encrypt_file(f, [email], output=str(filepath))
        
    """
     @Notice: This function will decrypt a file content
     @Dev:    We open the file a replace its content to the decrypted content using 
              the decrypt_file method from the gpg lib
    """
    def decrypt_file(self, filepath, password):
        with open(filepath, 'rb') as f:
            self.gpg.decrypt_file(f, passphrase=password, output=filepath)
        
    """
     @Notice: This function encrypt a string passing in parameter
     @Dev:    We encrypt a string passing in parameter, using the email to retrieve the key
              and return the encrypt() method return from the gpg lib
    """
    def encrypt_string(self, unencrypted_string, email):
        return str(self.gpg.encrypt(unencrypted_string, email))
        
    """
     @Notice: This function decrypt a string passing in parameter
     @Dev:    We decrypt a string passing in parameter, using the password to retrieve to unlock the private key
              and return the decrypt() method return from the gpg lib
    """
    def decrypt_string(self, encrypted_string, password):
        return str(self.gpg.decrypt(encrypted_string, passphrase=password))