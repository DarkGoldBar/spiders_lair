# coding=UTF-8
import random
import requests
from requests import Timeout, RequestException
from bs4 import BeautifulSoup


proxies_pool = [
    {},
    {'http': '172.19.0.11:8118','https': '172.19.0.11:8118'}
]
headers_ = {'user_agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0",
'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
'accept-encoding':'gzip, deflate, br',
'accept-language':'en,en-US;q=0.9,zh-CN;q=0.8,zh;q=0.7'
}
user_agent_pool = ["Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0"]


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
            data = BeautifulSoup(response.content)
            break
        except Timeout:
            print(f"Request Timeout {i}, retrying...")
        except RequestException as e:
            print(f"Request error: {e}")
            break
    else:
        print("Failed to fetch the page after multiple retries.", url)
    return data



import pandas as pd

def render_html(xls_fp):
    df = pd.read_excel(xls_fp)
    df2 = df[['compound', 'CAS']]
    df2['link'] = [f'https://www.chemscene.com/{cas}.html' for cas in df['CAS']]
    df2.to_html('index.html', index=False, render_links=True)
