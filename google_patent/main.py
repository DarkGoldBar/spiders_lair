import sqlite3
import json
import os
import re
import random
import requests
import pandas as pd
import threading
import queue
import sqlite3
import time
from pathlib import Path
from bs4 import BeautifulSoup
from IPython.display import ProgressBar
from requests.exceptions import Timeout, RequestException

QUERY = './patent/csv2'
DUMPTO = './patent/pdf2'

NTHREADS = 5
BATCH = 1000

dfs = []
for csv in sorted(Path(QUERY).glob('*.csv')):
    df = pd.read_csv(csv, skiprows=[0])
    dfs.append(df)
df = pd.concat(dfs, ignore_index=True)


proxies_pool = [
    {},
    {'http': '172.19.0.11:8118','https': '172.19.0.11:8118'}
]
headers_ = {'user_agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
'authority':'patents.google.com',
'method':'GET',
'scheme':'https',
'accept':'*/*',
'accept-encoding':'gzip, deflate, br',
'accept-language':'en,en-US;q=0.9,zh-CN;q=0.8,zh;q=0.7',
'cookie':'_ga=GA1.3.650546010.1557842690; 1P_JAR=2019-06-13-03; NID=185=HFLQWsc9gyTy7jWJiX-sZ242_kqMdEVUKf89m0r0R8jrCT1n2jN8cuSFmh6abb50bDB8u6qYhcF7KXWHgZy4TPj-zkheFl9g6kiLCqFrNEf6G_2hLhWzCfjwkz7EjLB8jrROilpayn5NIIKf0WLZsZCBemnNt88RdO4Tik_zYwg; _gid=GA1.3.814134454.1560407883; _gat=1'
}
user_agent_pool = ["Mozilla/5.0 (Macintosh; U; Mac OS X Mach-O; en-US; rv:2.0a) Gecko/20040614 Firefox/3.0.0 ",
"Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.0.3) Gecko/2008092414 Firefox/3.0.3",
"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1) Gecko/20090624 Firefox/3.5",
"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.14) Gecko/20110218 AlexaToolbar/alxf-2.0 Firefox/3.6.14",
"Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"]


def get_once(url, timeout=30, retry_count=2):
    proxies = random.choice(proxies_pool)
    user_agent = random.choice(user_agent_pool)
    headers = headers_.copy()
    headers['User_agent'] = user_agent
    data = None

    for i in range(retry_count):
        try:
            response = requests.get(url, proxies=proxies, headers=headers, timeout=timeout)
            if not response:
                print(f"Status code = {response.status_code},  retrying...")
                continue
            soup = BeautifulSoup(response.content)
            href = soup.select_one('a[itemprop]')['href']
            req2 = requests.get(href, proxies=proxies, headers=headers, timeout=timeout)
            data = req2.content
            break
        except Timeout:
            print(f"Request Timeout {i}, retrying...")
        except RequestException as e:
            print(f"Request error: {e}")
            break
    else:
        print("Failed to fetch the page after multiple retries.", url)
    return data


from multiprocessing import Pool
from IPython.display import ProgressBar

def func(x):
    u = x
    p = re.sub(r'.*patent/([A-Za-z0-9]+)/.*', r'patent/pdf2/\1.pdf', u)
    if not os.path.exists(p):
        r = get_once(u)
        if r:
            return (r, p)
        

def master(n):
    pool = Pool(NTHREADS)
    args = df['result link'].tolist()
    args = args[n*BATCH: (n+1)*BATCH]

    pb = ProgressBar(len(args))
    pb.display()
    ii = max(1, len(args) // 100)
    
    for i, res in enumerate(pool.imap(func, args)):
        if i % ii == 0:
            pb.progress = i
        if res:
            r, p = res
            with open(p, 'wb') as f:
                f.write(r)
    pb.progress = len(args)


for i in range(len(df) // BATCH + 1):
    print(f'processing {i} * {BATCH}')
    master(i)
