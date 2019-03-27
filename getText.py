import glob
import codecs
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

f = codecs.open('data161.txt', 'w', 'utf-8')
names = glob.glob('./dataset/kd_block_161/*')
for name in names:
    name = name.split('/')[-1]
    text = unicode(re.search('jpg_\d_(.*).jpg', name).group(1))
    print(text, len(text))
    f.write('{} {} {}\n'.format(len(text), ' '.join(text), name))