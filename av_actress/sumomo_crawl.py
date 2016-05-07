import time
import requests
#from pyquery import PyQuery as pq
from bs4 import BeautifulSoup
import csv
import gevent
from gevent import monkey,pool
monkey.patch_socket()
from pymongo import MongoClient
import pprint

def init_mongo():
    connect = MongoClient('localhost', 27017, max_pool_size=None)
    db = connect.fc2_movie
    global collect
    collect = db.actress

def insert(name):
    url = 'http://sumomo-ch.com/?tag={}'.format(name)
    # print(name)
    entry = {'name':name}
    soup = BeautifulSoup(requests.get(url).content)
    entry['article'] = [article.a['href'] for article in soup.find_all('div',class_='kizi-more')]
    img_urls = []
    for article in soup.find_all('div',class_='kizi-body'):
        for imgs in article.find_all('img'):
            img_urls.append(imgs['src'])
    entry['thumbnail'] =img_urls
    try:
        collect.save(entry)

    except:
        pass
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(entry)

def crawl():

    with open('actress.txt') as f:
        actresses = f.read().split('\n')

    p = pool.Pool(4)
    threads = []
    for actress in actresses:
        threads.append(p.spawn(insert,actress))

    gevent.joinall(threads,timeout=8, raise_error=True)

if __name__ == '__main__':
    init_mongo()
    crawl()