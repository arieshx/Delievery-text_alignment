#coding=utf-8
import codecs
import json
import glob


jsonList = glob.glob('./dataset/kd_page_*.json')
url_list = []
for jsonName in jsonList[:100]:
    items = json.load(codecs.open(jsonName, 'r', 'utf-8'))
    for item in items[:]:
        try:
            if item['url'][-7:] == '164.jpg' and item['depponOcrResult'] and item['depponOcrResult']['codAmount'] != 'NULL':
                splited_url = item['url'].split('/')
                url_list.append('http://192.168.1.115/{}/{}'.format(splited_url[-2], splited_url[-1]))
        except:
            print item
print url_list[:10]