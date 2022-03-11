"""
MIT License

Copyright (c) 2022 Texas Tech University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""
This file is part of MonSter.

Author:
    Jie Li, jie.li@ttu.edu
"""

import yaml
import hostlist
from pathlib import Path


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_status(action: str, target: str, obj: str):
    """print_status Print Status

    Print status in a nice way

    Args:
        status (str): status
    """
    print(f'{action} {bcolors.OKBLUE}{target}{bcolors.ENDC} {obj}.')


def parse_config():
    """parse_config Parse Config

    Parse configuration files

    Returns:
        dict: Configuration in json format
    """
    cfg = []
    scanodes_path = Path(__file__).resolve().parent
    try:
        with open(f'{scanodes_path}/config.yml', 'r') as ymlfile:
            cfg = yaml.safe_load(ymlfile)
            return cfg
    except Exception as err:
        print(f"Parsing Configuration Error: {err}")


def get_idrac_auth():
    """get_idrac_auth Get iDRAC Authentication

    Get username and password for accessing idrac reports
    """
    idrac_config = parse_config()['idrac']
    username = idrac_config['username']
    password = idrac_config['password']
    return(username, password)


def get_config(target: str):
    """get_config Get Config

    Get Configuration for the specified target 

    Args:
        target (str): configuration target

    Raises:
        ValueError: Invalid configuration target

    Returns:
        dict: configurations of specified target
    """
    
    targets = ['timescaledb', 'idrac', 'slurm_rest_api']
    if target not in targets:
        raise ValueError(f"Invalid configuration target. Expected one of: {targets}")

    config = parse_config()[target]
    return config


def get_nodelist():
    """get_nodelist Get Nodelist

    Generate the nodelist according to the configuration
    """
    idrac_config = parse_config()['idrac']['nodelist']
    nodelist = []

    # print(idrac_config)
    try:
        for i in idrac_config:
            nodes = hostlist.expand_hostlist(i)
            nodelist.extend(nodes)
        
        return nodelist
    except Exception as err:
        print(f"Cannot generate nodelist: {err}")



