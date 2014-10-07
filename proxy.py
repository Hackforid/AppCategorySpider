# -*- coding:utf-8 -*-
import time

import requests

from pyquery import PyQuery as pq

import gevent
from gevent import monkey
from gevent.pool import Pool

monkey.patch_socket()

local_ip = ""
proxy_list = []


def ignore_exception(fn):
    def _(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except:
            return None
    return _


@ignore_exception
def get_ip_by_baidu(proxies=None):
    baidu = requests.get(
        'http://m.baidu.com/s?word=ip&pu=sz%401321_480&wpo=fast',
        proxies=proxies, timeout=5, headers={'user-agent': 'chrome', })
    r = pq(baidu.text)
    ip = r('span').eq(2).text()

    return ip


def get_local_ip():
    ip = get_ip_by_baidu()
    print 'local ip = ', ip
    return ip


def valid_proxy(ip, port):

    proxies = {'http': 'http://%s:%s' %
               (ip, port), 'https': 'https://%s:%s' % (ip, port)}
    time_start = time.time()
    ip = get_ip_by_baidu(proxies)
    time_cost = time.time() - time_start
    if (ip != None and ip != local_ip):
        return ip, port, time_cost
    else:
        return ip, port, None


def valid_proxies(ip_list):
    print 'validing ip_list ...'

    global proxy_list
    threads = []
    valid_proxy_list = []
    p = Pool(1024)

    for ip in ip_list:
        if not ip:
            continue
        url = '%s:%s' % (ip.get('ip'), ip.get('port'))
        if url in proxy_list:
            continue
        else:
            proxy_list.append(url)
            threads.append(p.spawn(valid_proxy, ip.get('ip'), ip.get('port')))

    for thread in threads:
        ip, port, time_cost = thread.get()
        if time_cost:
            valid_proxy_list.append(
                {'ip': ip, 'port': port, 'time': time_cost})

    print 'valided ip_list', len(valid_proxy_list)
    return valid_proxy_list


@ignore_exception
def fetch_kuaidaili():
    ip_list = []
    for i in range(1, 11):
        r = pq(url="http://www.kuaidaili.com/proxylist/%s" % i)
        trs = r('tbody').find('tr')
        ip_list.extend([{'ip': tds.eq(0).text(), 'port': tds.eq(1).text()}
                       for tds in [tr('td') for tr in trs.items()]])
    return ip_list


@ignore_exception
def fetch_cn_proxy_com():
    h = requests.get("http://cn-proxy.com/", timeout=10)
    r = pq(h.text)
    trs = r('tbody').find('tr')
    return [{'ip': tds.eq(0).text(), 'port': tds.eq(1).text()} for tds in [tr('td') for tr in trs.items()]]


def fetch():
    global local_ip
    local_ip = get_local_ip()

    fetch_methods = [fetch_cn_proxy_com, fetch_kuaidaili]

    ip_list = []

    print 'fetching proxy ips...'
    threads = [gevent.spawn(method) for method in fetch_methods]
    for thread in threads:
        ip_list.extend(thread.get())
    print 'fetched proxy', len(ip_list)

    return valid_proxies(ip_list)


def main():
    fetch()


if __name__ == "__main__":
    main()
