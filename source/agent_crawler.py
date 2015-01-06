#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Queue
import threading
import urllib
import urllib2
import time
from bs4 import BeautifulSoup

DEBUG = True

queue = Queue.Queue()
out_queue = Queue.Queue()


class ThreadProxy(threading.Thread):

    def __init__(self, ip_queue, ip_out_queue):
        threading.Thread.__init__(self)
        self.queue = ip_queue
        self.out_queue = ip_out_queue
        self.test_url = "http://ip.taobao.com/"

    @staticmethod
    def init_proxy(proto, proxy_address):
        proxy_handler = urllib2.ProxyHandler({proto: r"%s://%s" % (proto, proxy_address)})
        opener = urllib2.build_opener(proxy_handler)
        return opener

    def verify_proxy(self, proto, proxy_address):
        opener = self.init_proxy(proto, proxy_address)
        try:
            start = time.clock()
            opener.open(self.test_url, timeout=2).read()
            cost = (time.clock() - start) * 1000
            print u"%s 验证成功.  耗时: %s ms" % (proxy_address, cost)
            return True, cost
        except Exception, e:
            if DEBUG:
                print e
            print u"%s 验证失败." % proxy_address
            return False, 0

    def run(self):
        while True:
            proxy_item = self.queue.get()
            time.sleep(0.1)
            is_work, cost = self.verify_proxy(proxy_item['proto'], proxy_item['proxy_address'])
            if is_work:
                item = dict()
                item['proxy_address'] = proxy_item['proxy_address']
                item['time'] = cost
                self.out_queue.put(item)
            self.queue.task_done()


def get_download_links(url):
    try:
        url_list = []
        page = urllib2.urlopen(url, timeout=10).read()
        soup = BeautifulSoup(page)
        links = soup.findAll(attrs={"class": "NavBoxContent"})[1]
        proto, rest = urllib.splittype(url)
        host, rest = urllib.splithost(rest)
        for li in links.find_all('li'):
            url_list.append("http://" + host+li.a['href'])
        return url_list
    except urllib2.HTTPError as e:  # 还可能会有403/500错误
        print u'服务器错误'
        print u'错误内容',e
        print u'话说网络链接正常不？'
        print u'转为使用旧有Header'
        return None
    except urllib2.URLError as e:
        print u'网络错误'
        print u'错误内容',e
        print u'话说网络链接正常不？'
        print u'转为使用旧有PostHeader'
        return None


def get_proxy_ip(url):
    try:
        proxy_list = []
        page = urllib2.urlopen(url, timeout=20).read()
        soup = BeautifulSoup(page)
        links = soup.findAll(attrs={"cellpadding": "0", "cellspacing": "1",
                                    "style": "width:100%; background-color:#ccc;"})
        proto, rest = urllib.splittype(url)
        host, rest = urllib.splithost(rest)
        host += "http://"

        for tr in links[0].find_all('tr'):
            td_list = tr.find_all(attrs={"style": None, "class": None, 'colspan': None})
            if len(td_list) == 5:
                ip = td_list[0].text.strip()
                port = td_list[1].text.strip()
                proxy_address = ip + ':' + port
                item = dict()
                item['proto'] = 'http'
                item['proxy_address'] = proxy_address
                proxy_list.append(item)
        return proxy_list
    except urllib2.HTTPError as e:  # 还可能会有403/500错误
        print u'服务器错误'
        print u'错误内容',e
        print u'话说网络链接正常不？'
        print u'转为使用旧有Header'
        return None
    except urllib2.URLError as e:
        print u'网络错误'
        print u'错误内容',e
        print u'话说网络链接正常不？'
        print u'转为使用旧有PostHeader'
        return None


def main():

    hosts = ["http://www.cz88.net/proxy/index.aspx"]
    proxy_list = []
    url_list = get_download_links(hosts[0])
    for url in url_list:
        proxy_list.extend(get_proxy_ip(url))
    with open('proxy.txt', 'w') as fw:
        for ip_address in proxy_list:
            fw.write(ip_address['proxy_address']+'\n')

    proxy_list = []
    with open('proxy.txt') as fr:
        for line in fr:
            proxy_address = line.strip()
            item = dict()
            item['proto'] = 'http'
            item['proxy_address'] = proxy_address
            proxy_list.append(item)

    for i in xrange(20):
        t = ThreadProxy(queue, out_queue)
        t.setDaemon(True)
        t.start()

    for item in proxy_list:
        queue.put(item)
    queue.join()
    out_list = []
    while not out_queue.empty():
        out_list.append(out_queue.get())

    print len(out_list)
    out_list.sort(lambda x, y: cmp(x['time'], y['time']))

    fw = open('verify_proxy.txt', 'w')
    for proxy_item in out_list:
        fw.write(proxy_item['proxy_address'] + '\t' + str(proxy_item['time']) + '\n')


if __name__ == '__main__':
    main()
