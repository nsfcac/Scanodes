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

import time
import multiprocessing


def partition(arr:list, cores: int):
    """partition Partition a list

    Partition urls/nodes into several groups based on # of cores

    Args:
        arr (list): A list to be partitioned
        cores (int): Number of cores of the compute running MonSter

    Returns:
        list: partitioned list
    """
    
    groups = []
    try:
        arr_len = len(arr)
        arr_per_core = arr_len // cores
        arr_surplus = arr_len % cores

        increment = 1
        for i in range(cores):
            if(arr_surplus != 0 and i == (cores-1)):
                groups.append(arr[i * arr_per_core:])
            else:
                groups.append(arr[i * arr_per_core : increment * arr_per_core])
                increment += 1
    except Exception as err:
        print(f"Cannot Partition the list: {err}")
    return groups


def fetch(urls: list, nodes: list, username: str, password:str):
    """fetch Fetch Data From Urls

    Fetch Data From Urls of the specified nodes

    Args:
        urls (list): idrac urls
        nodes (list): a list of ip addresses of idracs
        username (str): idrac username
        password (str): idrac password

    Returns:
        [type]: [description]
    """
    idrac_metrics = []
    try:
        if urls:
            asyn_requests = AsyncioRequests(auth = (username, password),
                                            timeout = (15, 45),
                                            max_retries = 3)
            idrac_metrics = asyn_requests.bulk_fetch(urls, nodes)
    except Exception as err:
        print(f"Cannot fetch data from idrac urls: {err}")
    return idrac_metrics


def parallel_fetch(urllist: list, 
                   nodelist: list, 
                   cores: int,
                   username: str, 
                   password:str):
    """parallel_fetch Parallel Fetch Data from Urls

    Parallel fetch data from rrls of the specified nodes

    Args:
        urllist (list): idrac urls
        nodelist (list): a list of ip addresses of idracs
        cores (int): Number of cores of the compute running MonSter
        username (str): idrac username
        password (str): idrac password

    Returns:
        list: idrac metrics in a list
    """
    
    flatten_metrics = []
    try:
        # Partition
        urls_group = partition(urllist, cores)
        nodes_group = partition(nodelist, cores)

        fetch_args = []
        for i in range(cores):
            urls = urls_group[i]
            nodes = nodes_group[i]
            fetch_args.append((urls, nodes, username, password))

        with multiprocessing.Pool() as pool:
            metrics = pool.starmap(fetch, fetch_args)

        flatten_metrics = [item for sublist in metrics for item in sublist]
    except Exception as err:
        print(f"Cannot parallel fetch data from idrac urls: {err}")

    return flatten_metrics


def extract(system_info: dict, bmc_info: dict):
    """extract Extract Info

    Extract system and bmc info

    Args:
        system_info (dict): System info
        bmc_info (dict): BMC info

    Returns:
        dict: extracted info
    """
    
    bmc_ip_addr = system_info["node"]
    system_metrics = system_info["metrics"]
    bmc_metrics = bmc_info["metrics"]
    
    general = ["UUID", "SerialNumber", "HostName", "Model", "Manufacturer"]
    processor = ["ProcessorModel", "ProcessorCount", "LogicalProcessorCount"]
    memory = ["TotalSystemMemoryGiB"]
    bmc = ["BmcModel", "BmcFirmwareVersion"]
    metrics = {}
    try:
        # Update service tag
        if system_metrics:
            service_tag = system_metrics.get("SKU", None)
        else:
            service_tag = None

        metrics.update({
            "ServiceTag": service_tag
        })

        # Update System metrics
        if system_metrics:
            for metric in general:
                metrics.update({
                    metric: system_metrics.get(metric, None)
                })
            for metric in processor:
                if metric.startswith("Processor"):
                    metrics.update({
                        metric: system_metrics.get("ProcessorSummary", {}).get(metric[9:], None)
                    })
                else:
                    metrics.update({
                        metric: system_metrics.get("ProcessorSummary", {}).get(metric, None)
                    })
            for metric in memory:
                metrics.update({
                    metric: system_metrics.get("MemorySummary", {}).get("TotalSystemMemoryGiB", None)
                })
        else:
            for metric in general + processor + memory:
                metrics.update({
                    metric: None
                })

        metrics.update({
            "Bmc_Ip_Addr": bmc_ip_addr
        })

        # Update BMC metrics
        if bmc_metrics:
            for metric in bmc:
                metrics.update({
                    metric: bmc_metrics.get(metric[3:], None)
                })
        else:
            for metric in bmc:
                metrics.update({
                    metric: None
                })
        
        # Update Status
        if  (not system_metrics and 
             not bmc_metrics):
            metrics.update({
                "Status": "BMC unreachable in this query"
            })
        else:
            metrics.update({
                "Status": system_metrics.get("Status", {}).get("Health", None)
            })
            
        return metrics
    except Exception as err:
        print(f"Cannot extract info from system and bmc: {err}")


def parallel_extract(system_info_list: list, 
                     bmc_info_list: list):
    """parallel_extract Parallel Extract Info

    Parallel extract system and bmc info

    Args:
        system_info_list (list): a list of system info
        bmc_info_list (list): a list of bmc info

    Returns:
        list: a list of extracted info
    """
    
    info = []
    try:
        process_args = zip(system_info_list, 
                           bmc_info_list)
        with multiprocessing.Pool() as pool:
            info = pool.starmap(extract, process_args)
    except Exception as err:
        print(f"Cannot parallel extract info from system and bmc: {err}")
    return info


class AsyncioRequests:
    import aiohttp
    import asyncio
    from aiohttp import ClientSession


    def __init__(self, verify_ssl: bool = False, auth: tuple = (), 
                 timeout: tuple = (15, 45), max_retries: int = 3):
        self.metrics = {}
        self.retry = 0
        self.connector=self.aiohttp.TCPConnector(verify_ssl=verify_ssl)
        if auth:
            self.auth = self.aiohttp.BasicAuth(*auth)
        else:
            self.auth = None
        self.timeout = self.aiohttp.ClientTimeout(*timeout)
        self.max_retries = max_retries
        self.loop = self.asyncio.get_event_loop()
        
    
    async def __fetch_json(self, 
                           url: str, 
                           node: str, 
                           session: ClientSession):
        """__fetch_json Fetch Url

        Get request wrapper to fetch json data from API

        Args:
            url (str): url of idrac
            node (str): ip address of the idrac
            session (ClientSession): Client Session

        Returns:
            dict: The return of url in json format
        """
        
        try:
            resp = await session.request(method='GET', url=url)
            resp.raise_for_status()
            json = await resp.json()
            return {"node": node, 
                    "metrics": json}
        except (TimeoutError):
            self.retry += 1
            if self.retry >= self.max_retries:
                print(f"Cannot fetch data from {node} : {url}")
                return {"node": node, 
                        "metrics": {}}
            return await self.__fetch_json(url, node, session)
        except Exception as err:
            print(f"Cannot fetch data from {url} : {err}")
            return {"node": node, 
                    "metrics": {}}


    async def __requests(self, urls: list, nodes: list):
        async with self.ClientSession(connector=self.connector, 
                                      auth = self.auth, 
                                      timeout = self.timeout) as session:
            tasks = []
            for i, url in enumerate(urls):
                tasks.append(self.__fetch_json(url=url, 
                                               node=nodes[i], 
                                               session=session))
            return await self.asyncio.gather(*tasks)


    def bulk_fetch(self, urls: list, nodes: list):
        self.metrics =  self.loop.run_until_complete(self.__requests(urls, nodes))
        self.loop.close()
        return self.metrics
    