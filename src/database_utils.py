import datetime
from key_generation.src.Secrets import Encrypt
from key_generation.src.DatabaseDriver import DatabaseDriver
import logging
import os

class DataBaseUtils():
    def __init__(self):
        self.encryptor = Encrypt()
        self.db = DatabaseDriver()

    """
     @Notice: This function with select all the item stored in the database
     @Dev:    We first connect to the database, then we execute the SELECT query.
              Finally we use the fetchall method to get the items, we disconnect to the database and return the items
    """
    def select_all(self, table_name):
        self.connect()
        query = "SELECT * FROM " + table_name
        return self.db.execute(execution_string=query, fetch_all=True)

    """
     @Notice: This function will insert a new validator key record to the postgre sql database
     @Dev:   We first build our insert query with the given parameters and then we insert using the psycopg2 lib
    """
    def insert_validator_keys(self, pubkey, validator_key_filename, encrypted_validator_keys, encrypted_password, encrypted_mnemonic, row_hash, staking_id):
        insert_query = """INSERT INTO validator_store (public_key, file_name, validator_key, validator_key_password, validator_mnemonic, created, row_hash, is_checked, staking_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        item_tuple = (
            pubkey,
            self.encryptor.encrypt_message(validator_key_filename),
            self.encryptor.encrypt_message(encrypted_validator_keys),
            self.encryptor.encrypt_message(encrypted_password),
            self.encryptor.encrypt_message(encrypted_mnemonic),
            self.encryptor.encrypt_message(
                str(datetime.datetime.now())),
            row_hash,
            False,
            int(staking_id))
        self.db.execute(execution_string=insert_query, item_tuple=item_tuple, commit=True)

    """
     @Notice: This function will insert a new deposit data record to the postgre sql database
     @Dev:   We first build our insert query with the given parameters and then we insert using the psycopg2 lib
    """
    def insert_deposit_data(self, pubkey, withdrawal_credentials, signature, deposit_data_root, locked_period, staking_id, row_hash):
        insert_query = """INSERT INTO data_store (public_key, withdrawal_credentials, signature, deposit_data_root, is_checked, event_type, locked_period, created, row_hash, staking_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        item_tuple = (
            pubkey,
            self.encryptor.encrypt_message(withdrawal_credentials),
            self.encryptor.encrypt_message(signature),
            self.encryptor.encrypt_message(deposit_data_root),
            False,
            self.encryptor.encrypt_message("key_generation"),
            self.encryptor.encrypt_message(str(locked_period)),
            self.encryptor.encrypt_message(
                    str(datetime.datetime.now())),
            row_hash,
            int(staking_id))
        self.db.execute(execution_string=insert_query, item_tuple=item_tuple, commit=True)


    """
     @Notice: This function will select a record regarding its row_hash column
     @Dev:    If the args is a list (not a row_hash) we build a row_hash from it, if not we directly use args as a row_hash parameter.
              Then we build our query passing the row_hash and return the fetchall() return.
    """
    def select_record_with_row_hash(self, table_name, args):
        try:
            row_hash = args
            if isinstance(args, list):
                row_hash = self.encryptor.hash_list(args)
            query = """SELECT * FROM """ + table_name + \
                """ WHERE row_hash = '{row_hash}'""".format(row_hash=row_hash)
            return self.db.execute(execution_string=query, fetch_all=True)
        except Exception as e:
            raise e

    def create_validator_table(self):
        try:
            self.db.execute(execution_string="""CREATE TABLE validator_store (
                id SERIAL PRIMARY KEY,
                public_key TEXT NOT NULL,
                file_name BYTEA NOT NULL,
                validator_key BYTEA NOT NULL,
                validator_key_password BYTEA NOT NULL,
                validator_mnemonic BYTEA NOT NULL,
                created BYTEA NOT NULL,
                row_hash TEXT NOT NULL,
                is_checked BOOLEAN NOT NULL,
                staking_id INTEGER NOT NULL
            )""", commit=True)
            self.db.execute(execution_string="GRANT ALL PRIVILEGES ON TABLE validator_store TO xlr8", commit=True)
        except Exception as e:
            raise e

    def create_data_store_table(self):
        try:
            self.db.execute(execution_string="""
            CREATE TABLE data_store (
                id SERIAL PRIMARY KEY,
                public_key TEXT NOT NULL,
                staking_id INTEGER NOT NULL,
                withdrawal_credentials BYTEA NOT NULL,
                signature BYTEA NOT NULL,
                deposit_data_root BYTEA NOT NULL,
                is_checked BOOLEAN NOT NULL,
                event_type BYTEA NOT NULL,
                locked_period BYTEA NOT NULL,
                created BYTEA NOT NULL,
                row_hash TEXT NOT NULL
            )""", commit=True)
            self.db.execute(execution_string="GRANT ALL PRIVILEGES ON TABLE data_store TO xlr8", commit=True)
        except Exception as e:
            raise e

    """
     @Notice: This function will select from the database an item with the given parameters
     @Dev:    We first build our query using the row hash generate by the hash_list() function and then execute it with the tupple arguments
    """
    def select_by_row_hash(self, table_name: str, args_list: list):
        try:
            row_hash = self.encryptor.hash_list(args_list)
            query = """SELECT * FROM """ + table_name + \
                """ WHERE row_hash = '{row_hash}'""".format(row_hash=row_hash)
            return self.db.execute(execution_string=query, fetch_all=True)
        except Exception as e:
            raise e
        
    def insert_error(self, error, contract_address, name, raised_error):
        env = "test"
        if os.path.exists("/app") is True:
            env = "prod"
        item = self.select_by_row_hash("scripts_errors", [raised_error, contract_address, name, env])
        if len(item) == 0 or item[0][3] is True:
            insert_query = """INSERT INTO scripts_errors (error, contract_address, created, row_hash, name, env) VALUES (%s, %s, %s, %s, %s, %s)"""
            item_tuple = (self.encryptor.encrypt_message(error),
                        contract_address,
                        self.encryptor.encrypt_message(
                            str(datetime.datetime.now())),
                        self.encryptor.hash_list([raised_error, contract_address, name, env]),
                        self.encryptor.encrypt_message(name),
                        self.encryptor.encrypt_message(env)
                    )
            self.db.execute(execution_string=insert_query, item_tuple=item_tuple, commit=True)
            logging.info('error inserted to database')
            
    def get_investment_address_by(self, staking_id):
        query = """SELECT contract_address FROM investment_store WHERE staking_id = '""" + str(staking_id) + """'"""
        item = self.db.execute(execution_string=query, fetch_one=True)
        if item is None or len(item) == 0:
            logging.warning("there isn't investment records in the database for this staking_id: " + str(staking_id))
            return None
        return item[0]

    def update_column(self, table_name, column_name, id_name, id_value, col_value, encrypt=True, log_update=True):
        try:
            update_val = self.encryptor.encrypt_message(col_value)
            if encrypt is False:
                update_val = col_value
            query = "UPDATE " + table_name + " SET " + column_name + " = '" + str(update_val) + "' WHERE " + id_name + " = '" + str(id_value) + "'"
            self.db.execute(execution_string=query, commit=True)
            if log_update is True:
                logging.info('column ' + column_name + ' updated with value ' + str(col_value) + ' for record ' + str(id_name) + " " + str(id_value) + ' on table ' + table_name)
        except Exception as e:
            raise e