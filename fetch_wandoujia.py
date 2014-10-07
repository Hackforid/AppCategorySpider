# -*- coding:utf-8 -*-
import random

import requests
from pyquery import PyQuery as pq

import proxy

import gevent
from gevent import monkey
from gevent.pool import Pool


monkey.patch_socket()

proxies_list = []
pool = Pool(1024)

def retry(fn, time=5):
    def _(*args, **kwargs):
        for i in range(time):
            try:
                return fn(*args, **kwargs)
            except:
                print 'retry', i
                pass
    return _

@retry
def fetch_pkg(url):
    r = requests.get(url, proxies=get_proxy(), timeout=5)
    if r.status_code == 404:
        print url, '404'
        return 404
    elif r.status_code != 200:
        print 'status_code = ', r.status_code
        raise Exception()
    else:
        print 'r=', r.json()
        return r.json()


def get_cate_url(cate_name, start = 0, count = 60):
    return 'http://apps.wandoujia.com/api/v1/apps?tag=%s&max=%s&start=%s&opt_fields=apps.packageName' % (cate_name, count, start)


def get_packname_by_cate(cate_name):
    per_max = 60
    start_pos = 0
    load_more = True
    
    while load_more:
        jobs = []
        for i in range(start_pos, start_pos+10):
            start = i * per_max
            url = get_cate_url(cate_name, start, per_max)
            jobs.append(gevent.spawn(fetch_pkg, url))

        for job in jobs:
            r = job.get()
            if r == 404:
                load_more = False

        start_pos += 10

    print 'done'


def get_cate():
    r = pq(url='http://www.wandoujia.com/tag/app')
    cate_spans = r('span.cate-name')
    return [span.text() for span in cate_spans.items() if span.text()]


def get_proxy():
    return random.choice(proxies_list)


def get_proxies_list():
    global proxies_list
    proxy_list = proxy.fetch()
    proxies_list = [{'http': 'http://%s:%s' % (item.get('ip'), item.get('port')), 'https':'http://%s:%s' % (item.get('ip'), item.get('port'))} for item in proxy_list]


def main():
    get_proxies_list()
    cate_list = get_cate()
    print cate_list

    threads = [gevent.spawn(get_packname_by_cate, cate_name) for cate_name in cate_list]
    gevent.joinall(threads)
    #get_packname_by_cate(cate_list[1])

    print 'end'


if __name__ == '__main__':
    main()


