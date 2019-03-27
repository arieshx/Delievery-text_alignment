#coding=utf-8
import numpy as np
import argparse
import cv2
import scipy
import scipy.cluster.hierarchy as sch
import argparse
 
# 参数操作，
ap = argparse.ArgumentParser()
ap.add_argument("-i","--image",required=True,help="path to input image")
args = vars(ap.parse_args())
 
# 读入图片
oimage = cv2.imread(args["image"])
 
# 将图片缩放至[150,200]，降低聚类的复杂度，提高运行速度
orig = cv2.resize(oimage,(150,200),interpolation=cv2.INTER_CUBIC)
 
# 初始化显示模块
vis = np.zeros(orig.shape[:2],dtype="float")
# 定义图片剪切范围的起点
x=0
y=0
 
# 剪切图片
points = np.array(orig[x:,y:,:])
points.shape=((orig.shape[0]-x)*(orig.shape[1]-y),3)
print points.shape
 
 
# 级联聚类
disMat =sch.distance.pdist(points,'euclidean')
Z = sch.linkage(disMat,method='average')
cluster = sch.fcluster(Z,t=1,criterion='inconsistent')
 
# 输出每个元素的类别号
print "original cluster by hierarchy clustering:\n:",cluster
print cluster.shape
 
# 找出含有元素数目最多的类别
cluster_tmp=cluster
print "max value: ",np.max(cluster)
count = np.bincount(cluster)
#index = np.argmax(count)
count[np.argmax(count)]=-1
#count[np.argmax(count)]=-1 # 此每多运行n次，就是取含元素数目第n+1多的类别
 
print "max count value: ",np.argmax(count)
cluster_tmp.shape=([orig.shape[0]-x,orig.shape[1]-y])
 
# 将相应类别的点映射到vis矩阵中
vis[cluster_tmp == np.argmax(count)] = 1
 
vis.shape=[orig.shape[0]-x,orig.shape[1]-y]
# 为了方便opencv显示，我们需要将vis数值归一化到0-255的整形
vis = rescale_intensity(vis, out_range=(0,255)).astype("uint8")
 
# 图片显示
cv2.imshow("Input",oimage) # 显示原图
orig_cut = points
orig_cut.shape=(orig.shape[0]-x,orig.shape[1]-y,3)
 
# 显示剪切图
cv2.imshow("cut",cv2.resize(orig_cut,(oimage.shape[1],oimage.shape[0]),interpolation=cv2.INTER_CUBIC))
cv2.imshow("vis",cv2.resize(vis,(oimage.shape[1],oimage.shape[0]),interpolation=cv2.INTER_CUBIC))
cv2.waitKey(0)
