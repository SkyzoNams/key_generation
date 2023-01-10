import pexpect
import secrets
import os
import logging
import traceback
from key_generation.src.pgp_manager import PGP_Manager
from key_generation.src.DatabaseUtils import DataBaseUtils
from key_generation.src.utils import get_file_names, get_file_content
from key_generation.src.Secrets import Encrypt
from key_generation.src.api_caller import API_Caller
import uuid
from key_generation.src.TwoFA import TwoFA
from key_generation.src.Config import Config
import datetime
from xmlrpc.client import Boolean
import time

class Generator():
    def __init__(self, parsed_args):
        if isinstance(parsed_args, dict):
            self.email = parsed_args['email']
            self.locked_period = parsed_args['locked_period']
            self.staking_id = parsed_args['staking_id']
        else:
            self.email = parsed_args.email
            self.locked_period = parsed_args.locked_period
            self.staking_id = parsed_args.staking_id

    """
     @Notice: This function will generate the validator data, step by step
     @Dev:    We first move the execution to the staking_deposit_cli folder, then we generate a random password,
              after that we get the mnemonic value from the execute_deposit_bash function, we store the two generated file data to the
              dedicated databases and remove teh files.
    """
    def generate_validator_data(self):
        try:
            if self.is_keys_for_staking_id() is False:
                pwd = secrets.token_urlsafe(24)
                mnemonic = self.generate_mnemonic(pwd)
                new_filename = str(uuid.uuid4())
                deposit_data_filename, validator_key_filename = get_file_names()
                self.store_validator_keys(get_file_content(validator_key_filename), new_filename, pwd, mnemonic)
                self.store_deposit_data(get_file_content(deposit_data_filename)[0])
                logging.info('new filename: ' + new_filename)
                self.send_to_api(str(validator_key_filename), pwd, new_filename)
                self.update_investment_status()
                self.remove_generated_files(validator_key_filename, deposit_data_filename)
            else:
                logging.warning('There are already deposit data and validator keys for the staking id #' + str(self.staking_id))
        except Exception as e:
            self.insert_error(error=str(traceback.format_exc()), staking_id=self.staking_id, raised_error=e)
            raise e
    
    def generate_mnemonic(self, pwd):
        tries = 5
        mnemonic = None
        while mnemonic is None and tries >= 0:
            mnemonic = self.execute_deposit_bash(pwd, tries)
            tries -= 1
            if mnemonic is None:
                time.sleep(2)
                logging.info('retry to execute deposit.sh to generate mnmemonic')
        return mnemonic

    def send_to_api(self, validator_key_filename, pwd, new_filename):
        try:
            tries = 5
            while API_Caller().send_req(api_endpoint="create_node", args_list=[
                    Encrypt().encrypt_message(get_file_content(validator_key_filename)),
                    Encrypt().encrypt_message(pwd),
                    Encrypt().encrypt_message(new_filename)
                ]) != "200":
                tries -= 1
                if tries <= 0:
                    return self.send_alert(validator_key_filename, new_filename)
        except Exception as e:
            self.send_alert(validator_key_filename, new_filename)
            raise e

    def is_keys_for_staking_id(self):
        data_record = DataBaseUtils().db.execute(execution_string="SELECT * FROM data_store WHERE staking_id = '" + str(self.staking_id) + "'", fetch_one=True)
        validator_record = DataBaseUtils().db.execute(execution_string="SELECT * FROM validator_store WHERE staking_id = '" + str(self.staking_id) + "'", fetch_one=True)
        if data_record is not None and validator_record is not None and len(data_record) > 0 and len(validator_record) > 0:
            return True
        return False

    """
     @Notice: This function will execute the deposit.sh file and return the generated mnmemonics
     @Dev:    We use the pexpect lib to create a subprocess and apply comment lines on the standard input.
              for each step we wait for the right standard ouput before executing a new command line, using expect().
              Finally, we return the generated and formatted mnmemonics. 
    """
    def execute_deposit_bash(self, pwd, tries):
        try:
            if os.path.basename(os.getcwd()) == "app" or os.path.basename(os.getcwd()) == "Python":
                os.chdir("key_generation/staking_deposit_cli")
            child = pexpect.spawn('python3 ./staking_deposit/deposit.py new-mnemonic --num_validators=1 --mnemonic_language=english --chain=mainnet --folder=.')
            child.expect('Please choose your language')
            child.sendline('English')
            child.expect('Create a password that secures your validator keystore')
            child.sendline(pwd)
            child.expect('Repeat your keystore password for confirmation')
            child.sendline(pwd)
            index = child.expect(['Repeat your keystore password for confirmation', 'Press any key when you have written down your mnemonic'])
            if index == 0:
                child.sendline(pwd)
                child.expect('Press any key when you have written down your mnemonic')
                mnemonic = self.extract_mnemonic_from_output(child.before.decode())
            else:        
                mnemonic = self.extract_mnemonic_from_output(child.before.decode())
            child.sendline(' ')
            child.expect('Please type your mnemonic')
            child.sendline(mnemonic)
            child.expect('Success!')
            child.sendline(' ')
            logging.info("validator keys generated")
            if os.path.basename(os.getcwd()) == "staking_deposit_cli":
                os.chdir("../..")
            return mnemonic
        except Exception as e:
            if tries == 0:
                self.insert_error(error=str(traceback.format_exc()), staking_id=self.staking_id, raised_error=e)
            return None

    """
     @Notice: This function will get the mnmemonics from the standard output and format it
     @Dev:    We parse the output and join the list to make it a string with spaces between each word
              Then we return it. 
    """
    def extract_mnemonic_from_output(self, output):
        mnemonic = output.split("This is your mnemonic (seed phrase). Write it down and store it safely. It is the ONLY way to retrieve your deposit.")[-1].replace("\r\n\r\n\r\n", "").split(" ")
        mnemonic = ' '.join(mnemonic)
        return mnemonic
        
    """
     @Notice: This function will store to the dedicated database the validator key file content.
     @Dev:    We create a database instance, generate a row hash and verify if the data has already been inserted
              to the database. If not, we insert the data using the database instance insert_validator_keys function.
              validator_keys, password and mnmemonics are pgp encrypted.
    """
    def store_validator_keys(self, validator_keys, validator_key_filename, pwd, mnemonic):
        row_hash = Encrypt().hash_list([
            validator_keys['pubkey'],
            validator_keys,
            pwd,
            mnemonic,
            self.staking_id])
        if len(DataBaseUtils().select_record_with_row_hash("validator_store", row_hash)) == 0:
            DataBaseUtils().insert_validator_keys(
                validator_keys['pubkey'],
                validator_key_filename,
                PGP_Manager().encrypt_string(str(validator_keys), self.email),
                PGP_Manager().encrypt_string(pwd, self.email),
                PGP_Manager().encrypt_string(mnemonic, self.email),
                row_hash,
                self.staking_id)
            logging.info('validator data inserted')
        else:
            logging.info("validator data already inserted")
        
    """
     @Notice: This function will store to the dedicated database the deposit data file content.
     @Dev:    We create a database instance, verify if the data has already been inserted and if not,
              we insert the data to the database using the database instance insert_deposit_data function.
    """
    def store_deposit_data(self, deposist_data):
        row_hash = Encrypt().hash_list([
            deposist_data['pubkey'],
            deposist_data['withdrawal_credentials'],
            deposist_data['signature'],
            deposist_data['deposit_data_root'],
            self.locked_period,
            self.staking_id])
        if len(DataBaseUtils().select_record_with_row_hash("data_store", row_hash)) == 0:
            DataBaseUtils().insert_deposit_data(
                deposist_data['pubkey'],
                deposist_data['withdrawal_credentials'],
                deposist_data['signature'],
                deposist_data['deposit_data_root'],
                self.locked_period,
                self.staking_id,
                row_hash)
            logging.info('deposit data inserted')
        else:
            logging.info('deposit data already inserted')

    """
     @Notice: This function will remove/delete the two files generated
     @Dev:     We use the os.remove function to remove the two files, using the two file path
              passed in parameters.
    """
    def remove_generated_files(self, validator_key_filename, deposit_data_filename):
        os.remove(validator_key_filename)
        os.remove(deposit_data_filename)
        logging.info("file " + str(validator_key_filename) + " is now removed")
        logging.info("file " + str(deposit_data_filename) + " is now removed")

    def insert_error(self, error, contract_address = None, staking_id = None, raised_error=None):
        if os.getcwd().split('/')[-1] == "staking_deposit_cli":
            os.chdir('../..')
        if staking_id is not None:
            contract_address = DataBaseUtils().get_investment_address_by(staking_id)
        DataBaseUtils().insert_error(error, str(contract_address), "key_generation", raised_error)
        
    def filename_cleaner(self, filepath):
        return filepath.split('/')[-1]
    
    def send_alert(self, validator_key_filename, new_filename):
        validator_record = DataBaseUtils().db.execute(execution_string="SELECT * FROM validator_store WHERE staking_id = '" + str(self.staking_id) + "'", fetch_one=True)
        for receiver in Config().return_config_email_alerts(email_alerts_receivers=True):
            TwoFa_ = TwoFA(email=receiver, user_name=receiver)
            TwoFa_.email(mail_body="""<p><br>After 5 retrieves in key_generator, the api call to create a new node for the validator key filename '""" + validator_key_filename + """', renamed  '"""+ new_filename + """'.<br><br> 
                          <span style="font-weight:bolder">A manual action is needed to add it.</span><br><br>
                         Here you can find the validator_store record information:<br><br>
                        <span style="font-weight:bolder">-id:</span> """ + str(validator_record[0]) + """ <br>
                        <span style="font-weight:bolder">-pubkey:</span> """ + validator_record[1] + """ <br>
                        <span style="font-weight:bolder">-filename:</span> """ + DataBaseUtils().encryptor.decrypt_message(validator_record[2].tobytes()) + """ <br>
                        <span style="font-weight:bolder">-validator_key:</span> """ + DataBaseUtils().encryptor.decrypt_message(validator_record[3].tobytes()) + """ <br>
                        <span style="font-weight:bolder">-validator_key_passsword:</span> """ + DataBaseUtils().encryptor.decrypt_message(validator_record[4].tobytes()) + """ <br>
                        <span style="font-weight:bolder">-validator_mnmemonic:</span> """ + DataBaseUtils().encryptor.decrypt_message(validator_record[5].tobytes()) + """ <br>
                        <span style="font-weight:bolder">-created:</span> """ + str(datetime.datetime.strptime( DataBaseUtils().encryptor.decrypt_message(validator_record[6].tobytes()), '%Y-%m-%d %H:%M:%S.%f')) + """ <br>
                        <span style="font-weight:bolder">-row_hash:</span> """ + validator_record[7] + """ <br>
                        <span style="font-weight:bolder">-is_checked:</span> """ + str(Boolean(validator_record[8])) + """<br>
                        <span style="font-weight:bolder">-staking_id:</span> """ + str(validator_record[9]) + """ <br>
                    </p>""", subject="Alert: validator keys not sent after 5 trials")
            
    def update_investment_status(self):
        DataBaseUtils().update_column(table_name="investment_store", column_name="status", id_name="staking_id", id_value=self.staking_id, col_value="Waiting for joining epoc")
