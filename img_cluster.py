#coding=utf-8
import numpy as np
import argparse
import cv2
import scipy
import scipy.cluster.hierarchy as sch
import argparse
 
# ����������
ap = argparse.ArgumentParser()
ap.add_argument("-i","--image",required=True,help="path to input image")
args = vars(ap.parse_args())
 
# ����ͼƬ
oimage = cv2.imread(args["image"])
 
# ��ͼƬ������[150,200]�����;���ĸ��Ӷȣ���������ٶ�
orig = cv2.resize(oimage,(150,200),interpolation=cv2.INTER_CUBIC)
 
# ��ʼ����ʾģ��
vis = np.zeros(orig.shape[:2],dtype="float")
# ����ͼƬ���з�Χ�����
x=0
y=0
 
# ����ͼƬ
points = np.array(orig[x:,y:,:])
points.shape=((orig.shape[0]-x)*(orig.shape[1]-y),3)
print points.shape
 
 
# ��������
disMat =sch.distance.pdist(points,'euclidean')
Z = sch.linkage(disMat,method='average')
cluster = sch.fcluster(Z,t=1,criterion='inconsistent')
 
# ���ÿ��Ԫ�ص�����
print "original cluster by hierarchy clustering:\n:",cluster
print cluster.shape
 
# �ҳ�����Ԫ����Ŀ�������
cluster_tmp=cluster
print "max value: ",np.max(cluster)
count = np.bincount(cluster)
#index = np.argmax(count)
count[np.argmax(count)]=-1
#count[np.argmax(count)]=-1 # ��ÿ������n�Σ�����ȡ��Ԫ����Ŀ��n+1������
 
print "max count value: ",np.argmax(count)
cluster_tmp.shape=([orig.shape[0]-x,orig.shape[1]-y])
 
# ����Ӧ���ĵ�ӳ�䵽vis������
vis[cluster_tmp == np.argmax(count)] = 1
 
vis.shape=[orig.shape[0]-x,orig.shape[1]-y]
# Ϊ�˷���opencv��ʾ��������Ҫ��vis��ֵ��һ����0-255������
vis = rescale_intensity(vis, out_range=(0,255)).astype("uint8")
 
# ͼƬ��ʾ
cv2.imshow("Input",oimage) # ��ʾԭͼ
orig_cut = points
orig_cut.shape=(orig.shape[0]-x,orig.shape[1]-y,3)
 
# ��ʾ����ͼ
cv2.imshow("cut",cv2.resize(orig_cut,(oimage.shape[1],oimage.shape[0]),interpolation=cv2.INTER_CUBIC))
cv2.imshow("vis",cv2.resize(vis,(oimage.shape[1],oimage.shape[0]),interpolation=cv2.INTER_CUBIC))
cv2.waitKey(0)
