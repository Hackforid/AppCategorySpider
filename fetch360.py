# -*- coding:utf-8 -*-
import random
import re
import signal

import requests

import proxy

import gevent
from gevent import monkey
from gevent.pool import Pool

from utils import retry


monkey.patch_all()

proxies_list = []
pool = Pool(200)

def match_app_info(page):
    p = re.compile(r"'sname': '([\S ]+)',.+?'cid2': ([\S ]+),.+?'pname': '([\S ]+)',", re.DOTALL)
    m = p.findall(page)
    if not m:
        return None
    r = m[0]
    return {'type': r[0], 'app_name': r[1], 'package_name': r[2]}

def match_apps_in_page(page):
    p = re.compile(r'<a sid="(\d+)"')
    ids = p.findall(page)
    return ids[::3]

@retry
def fetch_app(app_id):
    url = get_app_url(app_id)
    r = requests.get(url, proxies=get_proxy(), timeout=5, headers={
            'Connection': 'Keep-Alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'
        })
    return r.text
@retry
def fetch_pages(page_id=1):
    url = get_app_page_url(page_id)
    r = requests.get(url, proxies=get_proxy(), timeout=5, headers={
            'Connection': 'Keep-Alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'
        })
    return r.text

def get_app_info(app_id):
    page = fetch_app(app_id)
    info = match_app_info(page)
    return info

def get_apps_in_page(page_id):
    page = fetch_pages(page_id)
    app_ids = match_apps_in_page(page)

    if not app_ids:
        return None
    else:
        jobs = [pool.spawn(get_app_info, app_id) for app_id in app_ids]
        result = []
        for job in jobs:
            r = job.get()
            print r
            result.append(r)
        return result 


def get_app_page_url(page_id=1):
    return "http://zhushou.360.cn/list/index/cid/1?page=%s" % page_id 

def get_app_url(app_id):
    return "http://zhushou.360.cn/detail/index/soft_id/%s" % app_id

def spider():
    gevent.signal(signal.SIGQUIT, gevent.kill)
    load_more = True
    start = 0
    while load_more:
        jobs =  []
        for i in range(start, start + 100):
            jobs.append(gevent.spawn(get_apps_in_page, i))

        for job in jobs:
            r = job.get()
            if not r:
                load_more = False

        start += 100



def get_proxies_list():
    global proxies_list
    proxy_list = proxy.fetch()
    proxies_list = [{'http': 'http://%s:%s' % (item.get('ip'), item.get('port')), 'https':'http://%s:%s' % (item.get('ip'), item.get('port'))} for item in proxy_list]

def get_proxy():
    return random.choice(proxies_list)

def main():
    get_proxies_list()
    spider()


if __name__ == '__main__':
    main()


