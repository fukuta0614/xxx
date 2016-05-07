#!/usr/bin/env python
# -*- coding:utf-8 -*-
from urllib.request import urlopen, urlretrieve, Request
from urllib.parse import urljoin
import sys
import os
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
from debugger import set_debugger
# from cv2 import cv


class ImageCollecter(object):

    def __init__(self, base_url, folder_path, ):

        if os.path.exists(folder_path):
            try:
                self.img_file_num = int(max([x for x in os.listdir(folder_path) if x.split('.')[0].isdigit()]).split('.')[0])
            except:
                self.img_file_num = 0
            if os.path.exists(folder_path + 'gif'):
                try:
                    self.gif_file_num = int(max([x for x in os.listdir(folder_path+'gif') if x.split('.')[0].isdigit()]).split('.')[0])
                except:
                    self.gif_file_num = 0
        else:
            os.mkdir(folder_path)
            self.img_file_num = 0
            self.gif_file_num = 0
            with open(folder_path + 'downloaded.txt', 'w') as f:
                f.write('')

        self.url = base_url
        self.folder_path = folder_path

        self.user_agent_chrome = 'Mozilla/5.0  \
                                (Macintosh; Intel Mac OS X 10_9_3) \
                                AppleWebKit/537.36 (KHTML, like Gecko) \
                                Chrome/35.0.1916.47 Safari/537.36'

        with open(self.folder_path + 'downloaded.txt') as f:
            self.downloaded = f.read()

    def main(self):

        print("start : {}".format(self.url))
        try:
            response = urlopen(Request(url, headers={'User-Agent': self.user_agent_chrome}), timeout=3)
            soup = BeautifulSoup(response.read(), "lxml")
            imgs = soup.findAll("img")
        except Exception as e:
            print(e)
            return

        for i in range(len(imgs)):
            imgurl = imgs[i].get("src")

            if imgurl in self.downloaded:
                continue

            self.download(imgurl)

            parsentage = round(100 * i / len(imgs), 2)
            p = "%.2f%%" % (parsentage)
            sys.stdout.write("\rdownload : " + p)
            sys.stdout.flush()

        print('\rdownload : 100%       ')
        # print("collect %d item" %(file_number-fnumber))
        # print ("")
        # elapsed_time = time.time() - start
        # print("elapsed_time:{0}".format(elapsed_time))

    def download(self, imgurl):
        try:
            if not imgurl.startswith('http'):
                imgurl = urljoin(url, imgurl)
            img_data = urlopen(Request(imgurl, headers={'User-Agent': self.user_agent_chrome}), timeout=3)

            ext = os.path.splitext(imgurl)[-1]
            if ext == ".gif":
                if self.gif_file_num == 0:
                    try:
                        os.mkdir(self.folder_path + 'gif/')
                    except:
                        pass
                self.gif_file_num += 1
                file_name = "{:03d}.gif".format(self.gif_file_num)
                with open(folder_name+'gif/'+file_name,'wb') as f:
                    f.write(img_data.read())

                return True

            else:
                img = Image.open(BytesIO(img_data.read()))
                width, height = img.size

                if height > 200 and width > 200:
                    self.img_file_num += 1
                    file_name = "{:03d}{}".format(self.img_file_num, ext)
                    img.save(folder_name+file_name)
                    return True
                else:
                    # print('too small')
                    return False

        except Exception as e:
            print(e, imgurl)
            return False


if __name__ == '__main__':
    import datetime
    folder_name = './img/' + datetime.datetime.today().strftime("%Y%m%d") + '/'
    url = sys.argv[1]
    c = ImageCollecter(url, folder_name)
    c.main()