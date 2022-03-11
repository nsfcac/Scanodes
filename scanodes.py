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
import json
import pandas as pd
import utils
import process
import multiprocessing


def scanodes():
    username, password = utils.get_idrac_auth()
    nodelist = utils.get_nodelist()

    utils.print_status('Getting', 'nodes' , 'metadata')
    nodes_metadata = get_nodes_metadata(nodelist, username, password)

    utils.print_status('Writing', 'metadata' , 'to nodes_metadata.csv')
    df = pd.json_normalize(nodes_metadata)
    df.to_csv('./nodes_metadata.csv', encoding='utf-8',)


def get_nodes_metadata(nodelist: list, username: str, password: str):
    """get_cluster_info Get Cluster Info

    Get all nodes metadata

    Args:
        nodelist (list): a list of ip addresses of idracs
        username (str): idrac username
        password (str): idrac password
    """
    nodes_metadata = []
    cores = multiprocessing.cpu_count()
    try:
        bmc_base_url = "/redfish/v1/Managers/iDRAC.Embedded.1"
        system_base_url = "/redfish/v1/Systems/System.Embedded.1"

        system_urls = ["https://" + node + system_base_url for node in nodelist]
        bmc_urls = ["https://" + node + bmc_base_url for node in nodelist]

        # Fetch system info
        system_info = process.parallel_fetch(system_urls, 
                                             nodelist, 
                                             cores, 
                                             username, 
                                             password)
        # Fetch bmc info
        bmc_info = process.parallel_fetch(bmc_urls, 
                                          nodelist, 
                                          cores, 
                                          username, 
                                          password)

        # Process system and bmc info
        nodes_metadata = process.parallel_extract(system_info, bmc_info)
    except Exception as err:
        print(f'Cannot Get Nodes Metadata: {err}')
    
    return nodes_metadata


if __name__ == '__main__':
    scanodes()
