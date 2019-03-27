# -*-coding:utf-8-*-
import os, json, cv2, re, time, signal, codecs
import base64, glob, itertools, traceback
import Levenshtein as lvst
import math

import ancillary
from Bio.pairwise2 import format_alignment
from Bio import pairwise2
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


# 判断是否是电话
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




def main(truths, pred, line_data):
    # truth = "湖南省娄底市新化县南正街金属藏衣"
    # pred = "湖南底新化南正街金面放"
    print('\n'.join(truths))
    print(pred)
    # print line_data['pic_path']
    try:
        print('RUNNING!')
        alignments = []
        for truth in truths:
            if truth == '': continue
            alignments.append(pairwise2.align.globalms(list(truth), list(pred), 1, -1, -1, -1, gap_char=['_'])[0])
        # print('----------')
        # 对所有truth，选择得分最高的
        alignment = max(alignments, key=lambda x: x[2])
        print alignment
        align1, align2, score, begin, end = alignment
        # print align1, align2
        line_data['score'] = score
        correct_str = format_alignment_index(align1, align2, score, begin, end, line_data)
        # 找到详细地址
        c_num = 0
        for i in range(len(align2)-1, 0, -1):
            if align2[i] == '_':
                break
            else:
                continue
        for j in range(i, 0, -1):
            if align2[j] == '_':
                c_num += 1
                continue
            else:
                break
        if c_num>3:
            detail_address = align1[j+1:]
            detail_address = ''.join(detail_address)
        print('详细地址：')
        print(detail_address)
        # print('+++++++++')
        return correct_str
    except:
        print('ERROR!')
        print(traceback.format_exc())
        time.sleep(30)
        return ''


def get_detail_add(addr1, addr2):
    alignments = []
    alignments.append(pairwise2.align.globalms(list(addr1), list(addr2), 1, -1, -1, -1, gap_char=['_'])[0])
    alignment = max(alignments, key=lambda x: x[2])
    print alignment
    align1, align2, score, begin, end = alignment
    # 找到详细地址
    c_num = 0
    for i in range(len(align2) - 1, 0, -1):
        if align2[i] == '_':
            break
        else:
            continue
    for j in range(i, 0, -1):
        if align2[j] == '_':
            c_num += 1
            continue
        else:
            break
    if c_num > 3:
        detail_address = align1[j + 1:]
        detail_address = ''.join(detail_address)

    else:
        detail_address = addr1
    print('详细地址：')
    print(detail_address)
    return detail_address


truths = u"浙江杭州江干四季青钱江船江大厦1-1904"
pred = u"浙江省杭州市江干区四季青街道"
a = get_detail_add(truths, pred)
print(a)


# 将align1和align2对齐
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


# 判断是否是中文
def isChinese(str):
    if not isinstance(str, unicode):
        str = str.decode('utf-8')
    for ch in str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


# 80%以上的字符是数字，则str是数字
def isNumber(str):
    i = 0
    for ch in str:
        if ch.isdigit():
            i += 1
    return False if float(i) / len(str) < 0.8 else True


# 进行纠正
def correction(align1, align2, line_data):
    # weights = line_data['prob']
    text_ocr_prob = line_data['text_ocr_prob']
    index = 0
    correct_str = []
    # if line_data['isNumber']:
    if (isNumber(align1) and line_data['score'] / len(align1) >= 0.6) \
            or (not isNumber(align1) and line_data['score'] >= 0):
        print '-------------------'
        # if (align1[-2:] == '先生' or align1[-2:] == '小姐') and line_data['score'] == 0:
        # print align1
        # print align2
        # print(line_data['score'])
        # time.sleep(2)
        # return ''
        for t, p in zip(list(align1), list(align2)):
            if t == p:
                index += 1
                correct_str.append(t)
            elif t == '_':
                if text_ocr_prob[index] > 0.85:
                    correct_str.append(p)
                index += 1
            elif p == '_':
                correct_str.append(t)
            else:
                if text_ocr_prob[index] > 0.9:
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


# 删除图片
def removeImg(url):
    splited_url = url.split('/')
    fpath = './dataset/kd_images/{}/{}'.format(splited_url[-2], splited_url[-1])
    os.remove(fpath)


# 判断item是否是个dict且key是item的一个键
def has_result(item, key):
    return isinstance(item, dict) and key in item


# 得到text的开头或者结尾相同的每个子串
def getTextList(text):
    List = []
    for i in range(len(text)):
        List.append(text[:i + 1])
        List.append(text[-i - 1:])
    List.reverse()
    return List


def quHouzui(str):
    return re.sub(r'(省|市|(维吾尔|壮族|回族|)自治区|区|地区|街道|镇|乡)|(\B(%s)*(自治州|盟|县|旗|自治县|自治旗|矿区|特区|特别行政区))$' % (nation), '', str)



