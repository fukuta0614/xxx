import os
import sys
import time
import requests
from collect_image import ImageCollecter
from bingsearch import Bing

def bing_image_search(query):
    bing_url = 'https://api.datamarket.azure.com/Bing/Search/Image'
    MS_ACCTKEY = 'RN7BbJmPFT01Qhi9dH2IFBp0sGKVk7wix5dzafBIWHo'

    payload = { '$format': 'json',
                'Query': "'"+query+"'",
              }

    r = requests.get(bing_url, params=payload, auth=('', MS_ACCTKEY))

    count = 1
    for item in r.json()['d']['results']:
        image_url = item['MediaUrl']
        root,ext = os.path.splitext(image_url)
        if ext.lower() == '.jpg':
            r = requests.get(image_url)
            fname = "%04d.jpg" % count
            f = open(fname, 'wb')
            f.write(r.content)
            f.close()
            count += 1

if __name__ == '__main__':
    import datetime

    folder_path ='./img/' + datetime.datetime.today().strftime("%Y%m%d") + '/'

    if os.path.exists(folder_path):
        try:
            img_file_num = int(
                max([x for x in os.listdir(folder_path) if x.split('.')[0].isdigit()]).split('.')[0])
        except:
            img_file_num = 0
    else:
        os.mkdir(folder_path)
        img_file_num = 0
        with open(folder_path + 'downloaded.txt', 'w') as f:
            f.write('')

    query = sys.argv[1]
    bing = Bing()
    results = bing.web_search(query,10)

    try:
        for result in results:
            url = result['Url']
            c = ImageCollecter(url, folder_path)
            c.main()
    except Exception as e:
        print (e)
