import json
import ast
import os
from pathlib import Path

def get_file_names():
    if os.path.isfile('./key_generation/staking_deposit_cli/validator_keys/.DS_Store'):
        os.remove('./key_generation/staking_deposit_cli/validator_keys/.DS_Store')
    paths = sorted(Path('./key_generation/staking_deposit_cli/validator_keys').iterdir(), key=os.path.getmtime)
    return paths[len(paths) - 1], paths[len(paths) - 2]

def get_file_content(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

"""
    @Notice: This function will a string dict to dict
    @Dev:   We use the ast.literal_eval() to convert a string dict to dict object
"""
def convert_string_dict_to_dict(str_dict: str):
    return ast.literal_eval(str_dict)