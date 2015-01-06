#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time
import urllib2
import sys
import threading

reload(sys)
sys.setdefaultencoding('utf-8')


DEBUG = False

result = []
faile_ip_list = []

# 线程同步锁
lock_ip = threading.Lock()
lock_fail_ip = threading._allocate_lock()
lock_result = threading._allocate_lock()
lock_count = threading._allocate_lock()
lock_proxy = threading._allocate_lock()
lock_proxy_dic = threading._allocate_lock()


def synchtonous_lock_proxy_dic(f):
    def call(*args, **kwargs):
        lock_proxy_dic.acquire()
        try:
            return f(*args, **kwargs)
        finally:
            lock_proxy_dic.release()

    return call


def synchtonous_ip(f):
    def call(*args, **kwargs):
        lock_ip.acquire()
        try:
            return f(*args, **kwargs)
        finally:
            lock_ip.release()

    return call


def synchtonous_fail_ip(f):
    def call(*args, **kwargs):
        lock_fail_ip.acquire()
        try:
            return f(*args, **kwargs)
        finally:
            lock_fail_ip.release()

    return call


def synchtonous_count(f):
    def call(*args, **kwargs):
        lock_count.acquire()
        try:
            return f(*args, **kwargs)
        finally:
            lock_count.release()

    return call


def synchtonous_proxy(f):
    def call(*args, **kwargs):
        lock_proxy.acquire()
        try:
            return f(*args, **kwargs)
        finally:
            lock_proxy.release()

    return call


def synchtonous_result(f):
    def call(*args, **kwargs):
        lock_result.acquire()
        try:
            return f(*args, **kwargs)
        finally:
            lock_result.release()

    return call


proxy_error_dic = {}


def proxy_error_count(key):
    if key in proxy_error_dic:
        proxy_error_dic[key] = proxy_error_dic.get(key) + 1
        if proxy_error_dic[key] > 50:
            remove_proxy(key)
    else:
        proxy_error_dic[key] = 1


ip_list = []


# 放置一个ip
@synchtonous_ip
def put_ips(ips):
    global ip_list
    for ip in ips:
        ip_list.append(ip)


# 获取一个ip
@synchtonous_ip
def get_ip():
    global ip_list
    if len(ip_list) > 0:
        return ip_list.pop()
    else:
        return None


result_file = None
faile_file = None


# 保存结果
@synchtonous_result
def save_result(data):
    global result
    result.append(data)
    if len(result) >= 256:
        write_to_file('ip_location.txt', result)
        result = []


@synchtonous_fail_ip
def save_faile_ip(ip):
    global faile_ip_list
    faile_ip_list.append(ip)
    if len(faile_ip_list) >= 256:
        write_to_file('fail_ip_list.txt', faile_ip_list)
        faile_ip_list = []


def init_proxy(proxy_address):
    proxy_handler = urllib2.ProxyHandler({'http': proxy_address})
    opener = urllib2.build_opener(proxy_handler)
    return opener


def process_data(jsondata):
    if jsondata['data']['country']:
        country = jsondata['data']['country']
    else:
        country = "NULL"

    if jsondata['data']['area']:
        area = jsondata['data']['area']
    else:
        area = "NULL"

    if jsondata['data']['region']:
        region = jsondata['data']['region']
    else:
        region = "NULL"

    if jsondata['data']['city']:
        city = jsondata['data']['city']
    else:
        city = "NULL"

    '''
    if jsondata['data']['county']:
        county = jsondata['data']['county']
    else:
        county = "NULL"
    '''

    if jsondata['data']['isp']:
        isp = jsondata['data']['isp']
    else:
        isp = "NULL"
    return country, area, region, city, isp


def output_data(data):
    # ret = "%-4s\t%-4s\t%-4s\t%-4s\t%-4s\t%-4s\n" % ("country", "area", "region", "city", "isp")
    ret = "%-4s|%-4s|%-4s|%-4s|%-4s\n" % data
    return ret


current_count = 0


# 线程函数,获取ip归属地
def get_ip_location(url, max_length):
    global current_count
    while True:
        if current_count >= max_length:
            return

        ip = get_ip()
        print u"目前进度是:%d" % current_count
        currrent_count_add()
        if ip is None:
            time.sleep(1)
            continue

        try:
            proxy_address = get_proxy()
            opener = init_proxy(proxy_address)
            data = opener.open(url + ip).read()
            datadict = json.loads(data)
            if datadict['code'] == 0:
                data = output_data(process_data(datadict))
                save_result(ip + '|' + data)
        except urllib2.HTTPError:  # 还可能会有403/500错误
            proxy_error_count(proxy_address)
            print u'服务器错误:{}\t{}\t{}\n'.format(str(ip), str(proxy_address), proxy_error_dic.get(proxy_address))
            # print   u'错误内容',e
            save_faile_ip(ip + '\n')
        except urllib2.URLError:
            proxy_error_count(proxy_address)
            print u'网络错误:{}\t{}\t{}\n'.format(str(ip), str(proxy_address), proxy_error_dic.get(proxy_address))
            # print   u'错误内容',e
            save_faile_ip(ip + '\n')
        except Exception:
            proxy_error_count(proxy_address)
            print u'失败ip:{}\t{}\t{}\n'.format(str(ip), str(proxy_address), proxy_error_dic.get(proxy_error_count))
            save_faile_ip(ip + '\n')


proxy_list = []
proxy_count = 0


def init_proxy_list(filename):
    global proxy_list
    proxy_list = []
    with open(filename, 'r') as fr:
        for line in fr:
            words = line.split('\t')
            proxy_list.append(words[0])
    return proxy_list


@synchtonous_proxy
def get_proxy():
    global proxy_list
    global proxy_count
    proxy_address = proxy_list[proxy_count].split(' ')[0]
    proxy_count = (proxy_count + 1) % len(proxy_list)
    return proxy_address


@synchtonous_proxy
def remove_proxy(proxy_address):
    global proxy_list
    try:
        n = proxy_list.index(proxy_address)
        del proxy_list[n]
    except Exception:
        pass


@synchtonous_count
def currrent_count_add():
    global current_count
    current_count += 1

'''
def write_to_file(result_buffer):
    global result_file
    with open('ip_location.txt', 'a') as result_file:
        for item in result_buffer:
            result_file.write(item)
'''


def write_to_file(filename, data_set):
    with open(filename, 'a') as fw:
        for item in data_set:
            fw.write(item)


def get_file_lines_num():
    with open('../data/ip.txt', 'rb') as fr:
        count = 0
        while True:
            read_buffer = fr.read(8192 * 1024)
            if not read_buffer:
                break
            count += read_buffer.count('\n')
        return count


def read_ip_from_file():
    global ip_list
    with open('../data/ip.txt', 'rb') as fr:
        ips = []
        for line in fr:
            ips.append(line.strip())
            if len(ips) >= 4000:
                put_ips(ips)
                ips = []
            while len(ip_list) > 4000:
                time.sleep(10)
        if len(ips) > 0:
            put_ips(ips)


def main():
    max_length = 313860414
    print max_length
    global proxy_list
    proxy_list = init_proxy_list('verify_proxy.txt')
    thread_pool = []
    # 淘宝ip库接口
    url = "http://ip.taobao.com/service/getIpInfo.php?ip="
    thread_pool.append(threading.Thread(target=read_ip_from_file, args=()))
    for i in range(40):
        th = threading.Thread(target=get_ip_location, args=(url, max_length))
        thread_pool.append(th)

    # start threads one by one
    for thread in thread_pool:
        thread.start()

    for thread in thread_pool:
        threading.Thread.join(thread)


if __name__ == '__main__':
    main()
