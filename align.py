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
            alignments.append(pairwise2.align.globalms(list(truth), list(pred), 1, -1, -1, -1, gap_char = ['_'])[0])
        #print('----------')
        #对所有truth，选择得分最高的
        alignment = max(alignments, key=lambda x: x[2])
        print alignment
        align1, align2, score, begin, end = alignment
        #print align1, align2
        line_data['score'] = score
        correct_str = format_alignment_index(align1, align2, score, begin, end, line_data)
        # print('+++++++++')
        return correct_str
    except:
        print('ERROR!')
        print(traceback.format_exc())
        time.sleep(30)
        return ''
        
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
    return False if float(i)/len(str) < 0.8 else True

#进行纠正
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

#删除图片
def removeImg(url):
    splited_url = url.split('/')
    fpath = './dataset/kd_images/{}/{}'.format(splited_url[-2], splited_url[-1])
    os.remove(fpath)
    

#判断item是否是个dict且key是item的一个键
def has_result(item, key):
    return isinstance(item, dict) and key in item
    
#得到text的开头或者结尾相同的每个子串
def getTextList(text):
    List = []
    for i in range(len(text)):
        List.append(text[:i+1])
        List.append(text[-i-1:])
    List.reverse()
    return List
    
nations = codecs.open('nation.txt', 'r', 'utf-8')
nation = ''
for n in nations:
    nation = nation + n.strip() + '|'
    if len(n.strip()) > 2:
        nation = nation + n.strip()[:-1] + '|'
nation = nation[:-1]
def quHouzui(str):
    return re.sub(r'(省|市|(维吾尔|壮族|回族|)自治区|区|地区|街道|镇|乡)|(\B(%s)*(自治州|盟|县|旗|自治县|自治旗|矿区|特区|特别行政区))$'%(nation), '', str)
    
while 1:
    jsonList = glob.glob('./dataset/kd_page_*.json')
    haveRead = json.load(codecs.open('haveRead.json', 'r', 'utf-8'))
    haveRead = []
    data = codecs.open('data.txt', 'a', 'utf-8')
    for jsonName in jsonList[:]:
        index = 0
        if jsonName in haveRead: continue
        haveRead.append(jsonName)
        block_text = []
        items = json.load(codecs.open(jsonName, 'r', 'utf-8'))
        try:
            for item in items[:]:
                line_data = {}
                index += 1
                print(index)
                #若是退单类型，则跳过
                if item['depponOcrResult']['isReturn'].lower() == 'y': continue
                i = 0
                try:
                    if item['url'][-7:] == '161.jpg':
                        # continue
                        fname = os.path.basename(item['url'])
                        img = ancillary.get_img(item['url'])
                        print(item['inputId'])
                        detectResult = item['detectResult']
                        query_list = ['deliveryCustomerName', 'deliveryCustomerPhone']
                        deliveryCustomerPhone = unicode(item['depponOcrResult']['deliveryCustomerPhone'])
                        #德邦的电话总会漏掉最前面的0，需要判断并加上
                        if not is_phoneNum(deliveryCustomerPhone) and is_phoneNum('0'+deliveryCustomerPhone) \
                        and '-' not in deliveryCustomerPhone:
                            deliveryCustomerPhone = '0' + deliveryCustomerPhone
                        #对寄件人姓名和电话进行align
                        for query in query_list:
                            if has_result(detectResult, query) and has_result(detectResult[query], 'text_list'):
                                print(query)
                                # if query == 'deliveryCustomerPhone':
                                    # line_data['isNumber'] = True
                                # else:
                                    # line_data['isNumber'] = False
                                text_list = detectResult[query]['text_list']
                                text_list.reverse()
                                for text in text_list:
                                    line_data['text_ocr_prob'] = text['text_ocr_prob']
                                    pred = unicode(text['text'])
                                    truths = [unicode(item['depponOcrResult']['deliveryCustomerName']), unicode(item['depponOcrResult']['deliveryCustomerPhone']), \
                                    unicode(item['depponOcrResult']['deliveryCustomerName'])+unicode(item['depponOcrResult']['deliveryCustomerPhone']), \
                                    unicode(item['depponOcrResult']['deliveryCustomerPhone'])+unicode(item['depponOcrResult']['deliveryCustomerName'])]
                                    # print(type(truths), type(pred))
                                    correct_str = main(truths, pred, line_data)
                                    print('Final result:'+ correct_str)
                                    x1, y1, x2, y2 = text['text_area']
                                    # img_copy = img.copy()
                                    # cv2.rectangle(img_copy, (x1,y1), (x2,y2), (0,0,255), 3)
                                    if query == 'deliveryCustomerPhone' and (not is_phoneNum(correct_str) or isChinese(pred)): continue
                                    if correct_str:
                                        i += 1
                                        block_text.append('{} {} {}_{}_{}.jpg\n'.format(str(len(correct_str)),' '.join(correct_str.replace(' ', '$')),fname,i,correct_str))
                                        block = img[y1:y2, x1:x2]
                                        cv2.imwrite('./dataset/kd_block/{}_{}_{}.jpg'.format(fname,i,correct_str), block)
                                    # if correct_str:
                                        # img_copy = ancillary.draw_image(img_copy, x1, y1, x2, y2, correct_str)
                                        
                                    # print(type(correct_str))
                                    # if truths[1] == '57768119949': time.sleep(30)
                                    # if pred == '春0257-82128583': time.sleep(30)
                                    if truths[0] == correct_str: break 
                        # cv2.imwrite('./dataset/kd_result/{}.vis.jpg'.format(fname), img_copy)
                    elif item['url'][-7:] == '163.jpg':
                        fname = os.path.basename(item['url'])
                        img = ancillary.get_img(item['url'])
                        print(item['inputId'])
                        detectResult = item['detectResult']
                        query_list = ['receiveCustomerPhone', 'receiveCustomerName']
                        # 'rcProvName', 'rcCityName', 'rcDistName', 'receiveCustomerAddress',
                        if item['depponOcrResult']['rcDistName'] == '*' or item['depponOcrResult']['rcDistName'] == 'NULL':
                            item['depponOcrResult']['rcDistName'] = ''
                        if item['depponOcrResult']["rcTownName"] == '*' or item['depponOcrResult']["rcTownName"] == 'NULL':
                            item['depponOcrResult']["rcTownName"] = ''
                        query_list1 = ['rcProvName', 'rcCityName', 'rcDistName', 'rcTownName']
                        query_list2 = []
                        # query_list2 = ['rcProvName', 'rcCityName', 'rcDistName', 'rcTownName', 'receiveCustomerAddress']
                        query_list3 = ['receiveCustomerAddress', 'goodsName']
                        province = item['depponOcrResult']['rcProvName']
                        city = item['depponOcrResult']['rcCityName']
                        area = item['depponOcrResult']['rcDistName']
                        street = item['depponOcrResult']['rcTownName']
                        province_sim = quHouzui(item['depponOcrResult']['rcProvName'])
                        city_sim = quHouzui(item['depponOcrResult']['rcCityName'])
                        area_sim = quHouzui(item['depponOcrResult']['rcDistName'])
                        street_sim = quHouzui(item['depponOcrResult']['rcTownName'])
                        detailAddress = item['depponOcrResult']['receiveCustomerAddress'].replace(' ', '')
                        goods = item['depponOcrResult']['goodsName']
                        # img_copy = img.copy()
                        for query in query_list1:
                            if has_result(detectResult, query) and has_result(detectResult[query], 'text_list'):
                                text_list = detectResult[query]['text_list']
                                for text in text_list:
                                    line_data['text_ocr_prob'] = text['text_ocr_prob']
                                    pred = unicode(text['text'])
                                    truths = [quHouzui(item['depponOcrResult'][query]), item['depponOcrResult'][query], \
                                    province_sim, city_sim, area_sim, street_sim, province, city, area, street]
                                    correct_str = main(truths, pred, line_data)
                                    print('Final result:'+ correct_str)
                                    x1, y1, x2, y2 = text['text_area']
                                    # cv2.rectangle(img_copy, (x1,y1), (x2,y2), (0,0,255), 3)
                                    if correct_str:
                                        query_list2.append(item['depponOcrResult'][query])
                                        query_list2.append(quHouzui(item['depponOcrResult'][query]))
                                        i += 1
                                        block_text.append('{} {} {}_{}_{}.jpg\n'.format(str(len(correct_str)),' '.join(correct_str.replace(' ', '$')),fname,i,correct_str))
                                        block = img[y1:y2, x1:x2]
                                        cv2.imwrite('./dataset/kd_block/{}_{}_{}.jpg'.format(fname,i,correct_str), block)
                                        # img_copy = ancillary.draw_image(img_copy, x1, y1, x2, y2, correct_str)
                        # address = ''
                        # address_sim = ''
                        # List = []
                        # for query in query_list2:
                            # address += item['depponOcrResult'][query]
                            # address_sim += re.sub(r'(省|市|(维吾尔|壮族|回族|)自治区|区|地区|镇|街道|乡)|(\B(%s)*(自治州|盟|县|旗|自治县|自治旗|矿区|特区|特别行政区))$'%(nation), '', item['depponOcrResult'][query])
                            # if item['depponOcrResult'][query]:
                                # List.append(item['depponOcrResult'][query])
                                # List.append(re.sub(r'(省|市|(维吾尔|壮族|回族|)自治区|区|地区|镇|街道|乡)|(\B(%s)*(自治州|盟|县|旗|自治县|自治旗|矿区|特区|特别行政区))$'%(nation), '', item['depponOcrResult'][query]))
                        for query in query_list3:
                            if has_result(detectResult, query) and has_result(detectResult[query], 'text_list'):
                                print(query)
                                text_list = detectResult[query]['text_list']
                                for text in text_list:
                                    line_data['text_ocr_prob'] = text['text_ocr_prob']
                                    if sum(text['text_ocr_prob'])/len(text['text_ocr_prob']) < 0.5: continue
                                    pred = unicode(text['text']).replace(' ', '')
                                    if len(pred) <= 4:
                                        truths = [province_sim+city_sim, city_sim+area_sim, area_sim+street_sim, province_sim, city_sim, area_sim, street_sim, \
                                        province, city, area, street, detailAddress[-4:], detailAddress[-3:], detailAddress[-2:], detailAddress[-1:], \
                                        province_sim+detailAddress[:2], city_sim+detailAddress[:2], area_sim+detailAddress[:2], street_sim+detailAddress[:2], \
                                        detailAddress[:4], detailAddress[:3], detailAddress[:2], detailAddress[:1], goods]
                                    else:
                                        #省市区、市区街道、区街道详细地址、#省市区街道、#市区街道详细地址、#详细地址、#省市区街道详细地址
                                        # truths = getTextList(province+city+area+province+city+area+street+detailAddress) + getTextList(province+area+street+detailAddress) + \
                                        # getTextList(province+city+street+detailAddress) + getTextList(province+city+area+city+area+street+detailAddress) + \
                                        # getTextList(province+city+area+city+detailAddress) + getTextList(province+city+area+area+detailAddress) + \
                                        # [province_sim, city_sim, area_sim, street_sim, province, city, area, street, goods]
                                        truths = [province_sim+city_sim+area_sim, city_sim+area_sim+street_sim, area_sim+street_sim+detailAddress, \
                                        province+city+area, city+area+street, area+street+detailAddress, street+detailAddress, \
                                        province+city+area+city, province+city+area+city[:1], province+city+area+area, province+city+area+area[:1],province+city+province+city+area,  \
                                        province+city+area+province+city[:1], province+city+area+city+area[:1], province+city+area+province+city, province+city+area+city+area, \
                                        province+city+area+city[:1], province+city+area+area[:1], province+city+area+city, province+city+area+area, province+city+area+province[:1], province+city+area+province, \
                                        province+city+area+city+detailAddress[:3], province+city+area+area+detailAddress[:3], province+city+area+province+area+detailAddress[:2], \
                                        province+city+area+city+detailAddress[:1], province+city+area+area+detailAddress[:1], \
                                        province_sim+city_sim+area_sim+street_sim, province+city+area+street, \
                                        detailAddress, detailAddress[1:], detailAddress[2:], detailAddress[3:], detailAddress[4:], detailAddress[5:], \
                                        detailAddress[-len(pred)-2:], detailAddress[:len(pred)+2], \
                                        province_sim, city_sim, area_sim, street_sim, province, city, area, street]
                                        for address in getTextList(detailAddress):
                                            truths.append(province_sim+city_sim+area_sim+street_sim+address)
                                            truths.append(province+city+area+street+address)
                                            truths.append(city_sim+area_sim+street_sim+address)
                                            truths.append(city+area+street+address)
                                            truths.append(province_sim+area_sim+street_sim+address)
                                            truths.append(province+area+street+address)
                                            truths.append(area_sim+street_sim+address)
                                            truths.append(area+street+address)
                                        for t in truths:
                                            if '' not in truths: break
                                            truths.remove('')
                                        # print truths[-1]
                                        truths = sorted(truths, key=lambda x: len(x), reverse=True)
                                        result = min(truths, key=lambda x: lvst.distance(x,pred)-math.sqrt(len(x)))
                                        truths = getTextList(result)
                                    correct_str = main(truths, pred, line_data)
                                    if province in [(province[0] + correct_str)[:3], (province[0] + correct_str)[:4], (province[0] + correct_str)[:5], (province[0] + correct_str)[:6]]:
                                        correct_str = province[0] + correct_str
                                    print('Final result:'+ correct_str)
                                    # if pred == '秀苑/8栋401': time.sleep(30)
                                    # time.sleep(10)
                                    x1, y1, x2, y2 = text['text_area']
                                    # cv2.rectangle(img_copy, (x1,y1), (x2,y2), (0,0,255), 3)
                                    if correct_str and correct_str not in query_list2:
                                        i += 1
                                        block_text.append('{} {} {}_{}_{}.jpg\n'.format(str(len(correct_str)),' '.join(correct_str.replace(' ', '$')),fname,i,correct_str))
                                        block = img[y1:y2, x1:x2]
                                        cv2.imwrite('./dataset/kd_block/{}_{}_{}.jpg'.format(fname,i,correct_str), block)
                                        # img_copy = ancillary.draw_image(img_copy, x1, y1, x2, y2, correct_str)
                        
                        for query in query_list:
                            if has_result(detectResult, query) and has_result(detectResult[query], 'text_list'):
                                print(query)
                                text_list = detectResult[query]['text_list']
                                for text in text_list:
                                    line_data['text_ocr_prob'] = text['text_ocr_prob']
                                    pred = unicode(text['text'])
                                    truths = [unicode(item['depponOcrResult'][query])]
                                    correct_str = main(truths, pred, line_data)
                                    print('Final result:'+ correct_str)
                                    x1, y1, x2, y2 = text['text_area']
                                    # cv2.rectangle(img_copy, (x1,y1), (x2,y2), (0,0,255), 3)
                                    if query == 'receiveCustomerPhone' and (not is_phoneNum(correct_str) or isChinese(pred)): continue
                                    if correct_str:
                                        i += 1
                                        block_text.append('{} {} {}_{}_{}.jpg\n'.format(str(len(correct_str)),' '.join(correct_str.replace(' ', '$')),fname,i,correct_str))
                                        block = img[y1:y2, x1:x2]
                                        cv2.imwrite('./dataset/kd_block/{}_{}_{}.jpg'.format(fname,i,correct_str), block)
                                        # img_copy = ancillary.draw_image(img_copy, x1, y1, x2, y2, correct_str)
                                    # if pred == '家印电热水瓶C': time.sleep(30)
                                    if truths[0] == correct_str: break 
                        # cv2.imwrite('./dataset/kd_result/{}.vis.jpg'.format(fname), img_copy)
                    removeImg(item['url'])
                except:
                    print 'something failed!'
                    time.sleep(1)
        except:
            print(traceback.format_exc())
            print jsonName
            time.sleep(30)
        json.dump(haveRead, codecs.open('haveRead.json', 'w', 'utf-8'), ensure_ascii=False)
        for b in block_text:
            data.write(b)
    print 'Done,take a rest!\n' + jsonName
    time.sleep(30)