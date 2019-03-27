# -*-coding:utf-8-*-
import os, json, cv2, re, time, signal, codecs
import base64, glob, itertools, traceback
import numpy as np

import ancillary
from multiprocessing import Pool
from Bio.pairwise2 import format_alignment
from Bio import pairwise2
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

PUNCT = [',', '.', '?', ':', '!', ';']

def is_phoneNum(s):
    s = s.strip()
    p1 = re.compile(r'(13[0-9]|14[579]|15[0-3,5-9]|16[6]|17[0135678]|18[0-9]|19[89])\d{8}$')
    p2 = re.compile(r'(0\d{2,3}-?|)\d{7,8}(-\d{1,4}|)$')
    p3 = re.compile(r'^400(-?\d){7}$')
    deppon_month_code = '4008305555'

    if s.strip() == deppon_month_code:
        return False
    elif p1.match(s) or p2.match(s) or p3.match(s):
        return True
    else:
        return False

def shuchu(str):
    print repr(str).decode('unicode-escape')
def main(truth, pred, line_data):
    
    # truth = "湖南省娄底市新化县南正街金属藏衣"
    # pred = "湖南底新化南正街金面放"
    print(truth)
    print(pred)
    # print line_data['pic_path']
    try:
        print('RUNNING!')
        alignments = pairwise2.align.globalms(list(truth), list(pred), 2, -1, -1, -1, gap_char = ['_'])
        #print('----------')
        print alignments
        for alignment in alignments[:1]:
            align1, align2, score, begin, end = alignment
            #print align1, align2
            line_data['score'] = score
            correct_str = format_alignment_index(align1, align2, score, begin, end, line_data)
        # print('+++++++++')
        return correct_str
    except:
        print('ERROR!')
        print(traceback.format_exc())
        return ''
        
        


def format_alignment_index(align1, align2, score, begin, end, line_data):
    """ use Bio.pairwise2.format_alignment as reference
        http://biopython.org/DIST/docs/api/Bio.pairwise2-pysrc.html#format_alignment
    """

    # 文本长度以预测文本即align2的长度为准
    # end = len(align2.strip('-'))
    # end += 1 if (len(align1)>end and align1[end] in PUNCT) else 0
    align1 = ''.join(align1)
    align2 = ''.join(align2)
    print(begin, end)

    # 生成如下格式的字符串显示
    #   st-udy. Most of students study English by class. We don't have
    #   |  |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
    #   s-iudy. Most of students study English by class. We don't have
    s = []
    s.append("%s\n" % align1)
    for a, b, str_idx in zip(align1, align2, range(begin, end)):
        if a == b: 
            s.append("|")  # match 
        elif a == "_" or b == "_": 
            s.append(" ")  # gap 
        else: 
            s.append(".")  # mismatch

    s.append("\n") 
    s.append("%s\n" % align2)
    print(''.join(s))
    
    # 开始配对
    correct_str = correction(align1, align2, line_data)
    return correct_str

def isChinese(str):
    for ch in str:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False
    
def correction(align1, align2, line_data):
    # weights = line_data['prob']
    text_ocr_prob = line_data['text_ocr_prob']
    index = 0
    correct_str = []
    # if line_data['isNumber']:
    if (line_data['isNumber'] and line_data['score'] / len(align1) >= 1) \
    or (not line_data['isNumber'] and line_data['score'] >= 0):
        print '-------------------'
        if (align1[-2:] == '先生' or align1[-2:] == '小姐'):
            # print align1
            # print align2
            # print(line_data['score'])
            # time.sleep(2)
            return ''
        for t, p in zip(list(align1), list(align2)):
            if t == p:
                index += 1
                correct_str.append(t)
            elif t == '_':
                if text_ocr_prob[index] > 0.8:
                    correct_str.append(p)
                index += 1
            elif p == '_':
                correct_str.append(t)
            else:
                if text_ocr_prob[index] > 0.95:
                    correct_str.append(p)
                else:
                    correct_str.append(t)
                index += 1
        return ''.join(correct_str)
    else:
        return ''
    # else:
        # if line_data['score'] >= 0:
            # return align1
        # return ''

    
def has_result(item):
    return isinstance(item, dict) and 'text_list' in item

while 1:
    index = 0
    jsonList = glob.glob('./dataset/kd_page_*.json')
    for jsonName in jsonList:
        items = json.load(codecs.open('./dataset/kd_page_1.json', 'r', 'utf-8'))
        for item in items[:1000]:
            line_data = {}
            index += 1
            print(index)
            if item['depponOcrResult']['isReturn'].lower() == 'y': continue
            if item['url'][-7:] == '161.jpg':
                # continue
                fname = os.path.basename(item['url'])
                img = ancillary.get_img(item['url'])
                print(item['inputId'])
                detectResult = item['detectResult']
                query_list = ['deliveryCustomerName', 'deliveryCustomerPhone']
                for query in query_list:
                    if has_result(detectResult[query]):
                        print(query)
                        if query == 'deliveryCustomerPhone':
                            line_data['isNumber'] = True
                        else:
                            line_data['isNumber'] = False
                        text_list = detectResult[query]['text_list']
                        text_list.reverse()
                        for text in text_list:
                            line_data['text_ocr_prob'] = text['text_ocr_prob']
                            pred = unicode(text['text'])
                            truth = unicode(item['depponOcrResult'][query])
                            # print(type(truth), type(pred))
                            correct_str = main(truth, pred, line_data)
                            print('Final result:'+ correct_str)
                            x1, y1, x2, y2 = text['text_area']
                            cv2.rectangle(img, (x1,y1), (x2,y2), (0,0,255), 3)
                            if line_data['isNumber'] and not is_phoneNum(correct_str): continue
                            if correct_str:
                                img = ancillary.draw_image(img, x1, y1, x2, y2, correct_str)
                            # print(type(correct_str))
                            if truth == correct_str: break 
                cv2.imwrite('./dataset/kd_result_161/{}.vis.jpg'.format(fname), img)
            # elif item['url'][-7:] == '163.jpg':
                # fname = os.path.basename(item['url'])
                # img = ancillary.get_img(item['url'])
                # print(item['inputId'])
                # detectResult = item['detectResult']
                # query_list = ['receiveCustomerPhone', 'receiveCustomerName', 'goodsName']
                'rcProvName', 'rcCityName', 'rcDistName', 'receiveCustomerAddress',
                # if has_result(detectResult['rcProvName'])
                # for query in query_list:
                    # if has_result(detectResult[query]):
                        # print(query)
                        # if query == 'receiveCustomerPhone':
                            # line_data['isNumber'] = True
                        # else:
                            # line_data['isNumber'] = False
                        # text_list = detectResult[query]['text_list']
                        # for text in text_list:
                            # line_data['text_ocr_prob'] = text['text_ocr_prob']
                            # pred = unicode(text['text'])
                            # truth = unicode(item['depponOcrResult'][query])
                            # correct_str = main(truth, pred, line_data)
                            # print('Final result:'+ correct_str)
                            # x1, y1, x2, y2 = text['text_area']
                            # cv2.rectangle(img, (x1,y1), (x2,y2), (0,0,255), 3)
                            # if correct_str:
                                # img = ancillary.draw_image(img, x1, y1, x2, y2, correct_str)
                            # if truth == correct_str: break 
                # cv2.imwrite('./dataset/kd_result_163/{}.vis.jpg'.format(fname), img)
