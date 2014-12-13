#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time
import urllib
import urllib2
import sys
import linecache
reload(sys)
sys.setdefaultencoding('utf-8')

def init_proxy():
    proxy_handler = urllib2.ProxyHandler({'http': "111.161.126.101:80"})
    opener = urllib2.build_opener(proxy_handler)
    return  opener

def ip_location(url,ip):
        try:
            opener = init_proxy()
            data = opener.open(url + ip).read()
            datadict=json.loads(data)
        except  urllib2.HTTPError   as e    :#还可能会有403/500错误
            print   u'服务器错误'
            print   u'错误内容',e
            print   u'话说网络链接正常不？'
            print   u'转为使用旧有Header'
            return  null
        except  urllib2.URLError    as e    :
            print   u'网络错误'
            print   u'错误内容',e
            print   u'话说网络链接正常不？'
            print   u'转为使用旧有PostHeader'
            return  null
        if datadict['code'] == 0:
            return  datadict

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

    if jsondata['data']['county']:
        county = jsondata['data']['county']
    else:
        county = "NULL"

    if jsondata['data']['isp']:
        isp= jsondata['data']['isp']
    else:
        isp = "NULL"
    return (country, area, region, city, county, isp)

def output_data(data):
    #ret = "%-4s\t%-4s\t%-4s\t%-4s\t%-4s\t%-4s\n" % ("country", "area", "region", "city", "county", "isp")
    ret = "%-4s\t%-4s\t%-4s\t%-4s\t%-4s\t%-4s\n" % data
    return ret

def get_file_lines_num():
     with open('../data/ip.txt','rb') as fr:
        count = 0
        while True:
            buffer = fr.read(8192*1024)
            if not buffer:
                break
            count += buffer.count('\n')
        return count

def get_file_lines_num_method2():
    count = linecache.getline('../data/ip.txt')
    return  count

def main():

    #淘宝ip库接口
    url = "http://ip.taobao.com/service/getIpInfo.php?ip="
    with open('../data/ip.txt','rb') as fr:
        with open('iplocation.txt','w') as fw:
            for line in fr:
                #print line
                datadict = ip_location(url,line)
                if datadict == None:
                    continue
                data = output_data(process_data(datadict))
                fw.write(data)
                time.sleep(0.1)

if __name__ == '__main__':
    total_num = get_file_lines_num_method2()
    print total_num
    main()







