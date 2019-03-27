# -*-coding:utf-8-*-

import os, json, cv2, requests, codecs
import numpy as np

from PIL import Image, ImageDraw, ImageFont

def get_data_from_api():
    # 获取kd数据文件存为json
    URL = 'http://manhattanic.hexin.im/image/getList?'
    for page_num in range(545,1000):
        print page_num
        params = {
            '_limit': 1000,
            '_page': page_num
        }
        res = requests.get(URL, params=params).json()['data']
        json.dump(res, codecs.open('./dataset/kd_page_{}.json'.format(page_num), 'w', 'utf-8'), ensure_ascii=False)

        for item in res:
            try:
                get_img(item['url'])
            except:
                print item['url']


def get_img(url):
    ''' get image from api url, save and return image '''
    splited_url = url.split('/')
    fpath = os.path.join('./dataset/kd_images', splited_url[-2])
    fname = splited_url[-1]
    if not os.path.exists(fpath): os.makedirs(fpath)
    # if image already exists, return
    if os.path.exists(os.path.join(fpath, fname)):
        return cv2.imread(os.path.join(fpath, fname))

    # get image from url and save in local
    img_url = 'http://192.168.1.115/{}/{}'.format(splited_url[-2], splited_url[-1])
    res = requests.get(img_url).content
    image = np.asarray(bytearray(res), dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    cv2.imwrite(os.path.join(fpath, fname), image)
    return image


def draw_image(img, x1, y1, x2, y2, text):
    ''' draw text(Chinese or English) '''
    
    # 1. write English text
    # cv2.rectangle(img, (x1,y1), (x2,y2), (0,0,255), 3)
    # get text_width and text_height
    # text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
    # text_width, text_height = text_size
    # cv2.rectangle(img, (x1,y2),(x1+text_width+1,y2+text_height+10), (255,255,255), cv2.FILLED)
    # cv2.rectangle(img, (x1,y2-5),(x1+int(abs(x2-x1)*0.5),y2+int(abs(y2-y1)*0.3)), (255,255,255), cv2.FILLED)
    # cv2.putText(img, str(x1), (x1, y2+15), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,0,0), thickness=1, lineType=cv2.LINE_AA)

    # 2. write Chinese on image
    cv2.rectangle(img, (x1,y2-5),(x1+int(abs(x2-x1)*0.5),y2+int(abs(y2-y1)*0.3)), (255,255,255), cv2.FILLED)
    img_PIL = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    font = ImageFont.truetype('NotoSansCJK-Black.ttc', 20)#NotoSansCJK-Black.ttc
    position = (x1,y2-10)
    if not isinstance(text, unicode):
        text = text.decode('utf8')
    # print(text)
    draw = ImageDraw.Draw(img_PIL)
    draw.text(position, text, font=font, fill=(0,0,255))
    img = cv2.cvtColor(np.asarray(img_PIL),cv2.COLOR_RGB2BGR)
    return img


def visualize_image():
    '''
    draw text on the image
    firstly draw all rectangles and then draw text
    '''
    LIST_kd = json.load(codecs.open('./dataset/kd_page_1.json', 'r', 'utf-8'))
    for item in LIST_kd[0:]:
        fname = os.path.basename(item['url'])
        img = get_img(item['url'])
        cv2.imwrite('./dataset/kd_vis/{}'.format(fname), img)
        # cv2.rectangle(img, (20,30), (100,100), (0,0,255), 3)
        for key in item['detectResult'].keys():
            # select content that has text list
            if not isinstance(item['detectResult'][key],dict) or 'text_list' not in item['detectResult'][key]: continue
            for rect in item['detectResult'][key]['text_list']:
                x1, y1, x2, y2 = rect['text_area']
                ocr_text = rect['text']
                print(rect['text_area'], ocr_text, type(ocr_text))
                cv2.rectangle(img, (x1,y1), (x2,y2), (0,0,255), 3)

        # make text is above bounding boxes
        for key in item['detectResult'].keys():
            # select content that has text list
            if not isinstance(item['detectResult'][key],dict) or 'text_list' not in item['detectResult'][key]: continue
            for rect in item['detectResult'][key]['text_list']:
                x1, y1, x2, y2 = rect['text_area']
                ocr_text = rect['text']
                img = draw_image(img, x1, y1, x2, y2, ocr_text)

        cv2.imwrite('./dataset/kd_vis/{}.vis.jpg'.format(fname), img)
        # cv2.imshow('1.jpg', img)
        # cv2.waitKey(0)
    
                    

if __name__ == '__main__':
    get_data_from_api()
    # visualize_image()
    