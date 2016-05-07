# -*- coding: utf-8 -*-

import sys
import requests
import threading
import datetime
import io
from io import BytesIO
from PIL import Image
import re
import time
import os
from selenium import webdriver
from bs4 import BeautifulSoup
import multiprocessing as mp
from pymongo import MongoClient
import pprint

pp = pprint.PrettyPrinter(indent=4)
FOLDER_PATH = '/Users/fukuta0614/Documents/Program/python/'


def init_mongo(database,collection):
    connect = MongoClient('localhost', 27017)#, max_pool_size=None)
    db = connect[database]
    global collect
    # collect = db.movie_list
    collect = db[collection]


def download_list(img_url_list,folder_name):

    file_number = 1
    file_name_list = []
    for img_url in img_url_list:
        try:
            r = requests.get(img_url)
            img = Image.open(BytesIO(r.content))
        except:
            continue
        file_name = folder_name + '{:03d}.jpg'.format(file_number)
        img.save(FOLDER_PATH + file_name)
        # print (file_name)
        file_name_list.append(file_name)
        file_number += 1
    return file_name_list


def download(img_url,folder_name,file_number):

    r = requests.get(img_url)

    img = Image.open(BytesIO(r.content))

    file_name = '{:03d}.jpg'.format(file_number)
    img.save(folder_name + file_name)
    # print (file_name)

    return file_number + 1


def check():
    actress_dicts = collect.find()
    for actress in actress_dicts:
        if len(actress['article']) == 0:

            url = 'http://sumomo-ch.com/?tag={}'.format(re.sub(r'\（.+?\）','',actress['name']))
            # print(name)
            soup = BeautifulSoup(requests.get(url).content)
            actress['article'] = [article.a['href'] for article in soup.find_all('div',class_='kizi-more')]
            img_urls = []
            for article in soup.find_all('div',class_='kizi-body'):
                for imgs in article.find_all('img'):
                    img_urls.append(imgs['src'])
            actress['thumbnail'] =img_urls
            try:
                collect.save(actress)
            except Exception as e:
                print(e)
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(actress)


def collect_and_save_image():
    actress_dicts = collect.find()
    for i,actress in enumerate(actress_dicts):
        folder_name = 'av_actress/{}/'.format(actress['name'])
        try:
            os.mkdir(FOLDER_PATH + folder_name)
        except:
            if len(os.listdir(FOLDER_PATH + folder_name)) > 0:
                continue
            else:
                pass
        print(i,actress['name'])
        image_list = download_list(actress['thumbnail'],folder_name)
        actress['image_path'] = image_list
        collect.save(actress)

if __name__ == '__main__':
    driver = None
    init_mongo('fc2_movie','movie_list')
    # check()
    # collect_and_save_image()
    # main()
