# -*- coding: utf-8 -*-
# @Author  : HulkWu
# @Time    : 2017/3/30 14:33
# @File    : proxy.py

import cookielib
import urllib
import urllib2
import random
import threading
import socket
import time
import Queue
import httplib
from bs4 import BeautifulSoup

value = {
        'username': 'justfortest',
        'password': 'xxx'
    }
headers = {  # 伪装为浏览器抓取
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
    }

agent_url = 'http://www.xicidaili.com/'
login_url = "https://pixabay.com/zh/accounts/login/"
test_ip_url = "http://ip.catr.cn/"

# 锁
mutex = threading.Lock()
# 维护一个代理ip池
proxy_pool = []
# 暂时先写入文件
proxy_file = "./proxy_ip.txt"


def get_proxy():
    '''
    获取 http://www.xicidaili.com/ 上的代理ip列表，大概6min更新一次
    :return: [ip:port]列表
    '''
    global proxy_pool
    # 试图获取西刺代理的 IP 列表
    request = urllib2.Request(agent_url, headers=headers)
    try:
        content = urllib2.urlopen(request).read()
    except:
        print "无法获取代理信息！"
        return
    else:
        soup = BeautifulSoup(content, 'html.parser', from_encoding='GB18030')
        ip_tags = soup.find_all('tr', class_='odd')
        for ip_info in ip_tags:
            if ip_info.contents[11].string == "HTTP":
                proxy = ip_info.contents[3].string + ':' + ip_info.contents[5].string
                if check_ip(proxy) and proxy not in proxy_pool:
                    mutex.acquire()
                    proxy_pool.append(proxy)
                    mutex.release()


def change_proxy(proxies=[]):
    '''
    更改当前使用的ip代理
    '''
    # cookie
    cookie_file = './cookie.txt'
    cookie = cookielib.MozillaCookieJar(cookie_file)
    cookie.save(ignore_discard=True, ignore_expires=True)

    proxy = random.choice(proxies)
    if proxy:
        proxy_handler = urllib2.ProxyHandler({'http': "http://" + proxy})
    else:
        proxy_handler = urllib2.ProxyHandler({})
    # 实例化一个opener
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), proxy_handler)
    # 将post数据进行编码
    post_info = urllib.urlencode(value)
    # 构造一个request对象
    request = urllib2.Request(login_url, post_info)
    # 添加header信息
    opener.addheaders = [('User-Agent', headers['User-Agent'])]
    # 利用opener打开请求
    opener.open(request)
    # 安装opener
    # urllib2.install_opener(opener)
    # urllib2.urlopen(request)
    return opener


def check_ip(proxy=''):
    '''
    检查代理ip是否可用
    :param proxy: 代理ip:端口
    :return: 可用则true，否则false
    '''
    socket.setdefaulttimeout(3)
    try:
        proxy_host = "http://" + proxy
        proxy_temp = {"http": proxy_host}
        content = urllib.urlopen(test_ip_url, proxies=proxy_temp).read()
        soup = BeautifulSoup(content, 'html.parser', from_encoding='GB18030')
        if soup.find('span'):
            ip = soup.find('span').a.string
            if ip == proxy.split(':')[0]:
                return True
        return True
    except Exception:
        return False


def check_proxy_pool():
    '''
    定期检查代理ip池，去除不再可用的代理ip
    :return:
    '''
    global proxy_pool
    while True:
        if len(proxy_pool) > 0:
            temp_proxy_pool = []
            for proxy in proxy_pool:
                if check_ip(proxy):
                    temp_proxy_pool.append(proxy)
            mutex.acquire()
            proxy_pool = temp_proxy_pool
            mutex.release()


def update_proxy_pool():
    '''
    定期更新代理ip池，添加新的代理ip
    :return:
    '''
    while True:
        get_proxy()
        write_proxy(proxy_file)
        time.sleep(360)


# test
def print_cur_ip():
    try:
        content = urllib2.urlopen('http://ip.catr.cn/').read()
        soup = BeautifulSoup(content, 'html.parser', from_encoding='GB18030')
        ip = soup.find('span').a.string
        print ip
        print "======>"
    except urllib2.URLError, e:
        print e.reason


# 暂时先放文件中，后续存数据库
def write_proxy(file_name):
    with open(file_name, 'w') as f:
        for proxy in proxy_pool:
            f.write(proxy)
            f.write('\n')


if __name__ == "__main__":
    threads = []
    threads.append(threading.Thread(target=update_proxy_pool))
    threads.append(threading.Thread(target=check_proxy_pool))
    for thread in threads:
        thread.start()
    # get_proxy()
    # print proxy_pool
