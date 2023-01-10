# /usr/bin/python3
import argparse
from key_generation.src.generator import Generator
import logging
import os
import datetime
logging.basicConfig(format="%(asctime)s: %(levelname)s - %(message)s", level=logging.INFO)

parser = argparse.ArgumentParser(description='Generate the staking deposit information and keys')
parser.add_argument('-mail', dest='email', help='the pgp key email address', required=True)
parser.add_argument('-days', dest='locked_period', help='the locked period in days', required=True)
parser.add_argument('-stake', dest='staking_id', help='the staking instance ID', required=True)

def run(email, locked_period, staking_id):
    try:
        generator = Generator({"email": email, "locked_period": locked_period, "staking_id": staking_id})
        generator.generate_validator_data()
    except Exception as e:
        raise e

def main():
    try:
        run(parser.parse_args())
    except Exception as e:
        #write_error_on_file(str(e))
        raise e

def write_error_on_file(error):
    try:
        if os.path.exists("/mnt/backend"):
            if os.path.exists("/mnt/backend/errors") is False:
                os.mkdir("/mnt/backend/errors")
            if os.path.exists("/mnt/backend/errors/key_generator") is False:
                os.mkdir("/mnt/backend/errors/key_generator")
            with open("/mnt/backend/errors/key_generator/key_generator-" + str(datetime.datetime.now()) + ".txt" , 'w') as file:
                file.write(error)
        else:
            logging.warning("\x1b[33;20m'/mnt/backend' not mounted here\x1b[0m")
    except Exception as e:
        raise e



if __name__ == "__main__":
    main()
