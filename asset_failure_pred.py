import pandas as pd
from numba import stencil
from dtw import dtw
import numpy as np
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform
import datetime as dt
#import impyute
from sklearn.preprocessing import MinMaxScaler,StandardScaler
import os
import glob
from sklearn.metrics import silhouette_score
from sklearn.cluster import AgglomerativeClustering


@stencil
def kernel1(a):
    return ((-a[2,0] + 8*a[1,0] - 8*a[-1,0] + a[-2,0] )/12)+a[0,0]

def mh(x,y):
    return abs(x-y)

def dyntimwar1(d):
    dist_mat=np.zeros((len(d),len(d)))
    df={}
    for m in range(len(d)):
        for n in range(m+1,len(d)):
            min_dist,_,_,path=dtw(d[m],d[n],dist=mh)
            dist_mat[m][n]=min_dist
            df[(m,n)]=path
    return dist_mat+dist_mat.T - np.diag(np.diag(dist_mat)),df

def link(dist_mat):
    dists = squareform(dist_mat)
    linkage_matrix = linkage(dists, "single")
    return linkage_matrix
    
def hdtw(linkage_matrix,d,df):
    for o in range(len(linkage_matrix)):
       p,q=int(linkage_matrix[o][0]),int(linkage_matrix[o][1])
       if (p,q) in df:
         path=df[(p,q)]
       else:
         _,_,_,path=dtw(d[p],d[q],dist=mh)
       #resampling the warping path
       pp=[]
       for r,s in zip(path[0],path[1]):
           pp.append([(r+s)/2,float((d[p][r]+d[q][s])/2)])
       pp=np.vstack(pp)
       cs=np.arange(max(len(d[p]),len(d[q])))
       ss=np.interp(cs,pp[:,0],pp[:,1]).reshape(-1,1)
       d.append(MinMaxScaler().fit_transform((StandardScaler().fit_transform(kernel1(ss)+ss))))
    return d

def data_model(w,s,e):
    l=[[],[],[],[],[]]
    while(s<=e):
       f=[pd.read_csv(name,usecols=[0]) for name in glob.glob(os.path.join("/home/vauser/pcp/data/"+w+"/dt="+str(s)+"/","*.csv"))if name.endswith(('MI0001.csv','MSI0001.csv','MSUI0001.csv','PT0001.csv','S0001.csv'))]
       for j in range(len(f)):
           l[j].append(f[j])
       s+=dt.timedelta(days=1)
    d=[[],[],[],[],[]]
    for k in range(len(l)):
        if(len(l[k][0])>1):
            y=pd.concat(l[k]).values.reshape(-1,1)
            d[k]=MinMaxScaler().fit_transform((StandardScaler().fit_transform(kernel1(y)+y)))
    dd=[x for x in d if len(x)>1]
    return dd

# read failure details
tt=pd.read_excel("/home/vauser/pcp/tag.xlsx",sheet_name='Sheet1',parse_dates=[2,3])
h=[]
for i in range(0,len(tt)):
   # read each instance sequentially where w= well id, s= few hours befor abnormality started, e = failure date
   w,inst,s,e=tt.iloc[i,0],tt.iloc[i,1],tt.iloc[i,2].date(),tt.iloc[i,3].date()
   print(w,inst,s,e)
   # data modeling
   d=data_model(w,s,e)
   # computing the distance between pair wise
   dist_mat,df=dyntimwar1(d)
   # computing the linkage matrix
   linkage_matrix = link(dist_mat)
   # aggregating all signals into one
   dd=hdtw(linkage_matrix,d,df)
   # storing it 
   pd.DataFrame(dd[-1],index=None).to_excel("/home/vauser/pcp/hdtw_op/tr/54/"+w+"_"+str(int(inst))+".xlsx")
   # appending well wise aggregeted signals
   h.append(dd[-1])
# computing the distance between pair wise
dist_mat=pd.DataFrame(dyntimwar1(h),index=None)
# storing it
dist_mat.to_excel("/home/vauser/pcp/hdtw_op/tr/dm/dist_mat_54.xlsx",index=None)
# finding optimal no of clusters
sil=[]
for z in range(2,10):
    labels = AgglomerativeClustering(n_clusters=z,affinity='precomputed',linkage='single').fit(dist_mat).labels_
    sil.append(silhouette_score(dist_mat, labels, metric = 'precomputed'))
nc=np.argmax(sil)+2
print(nc)
labels = AgglomerativeClustering(n_clusters=nc,affinity='precomputed',linkage='single').fit(dist_mat).labels_
test=[np.flatnonzero(labels==i) for i in np.unique(labels)]
print(test)
# re-aggregating all well's aggregated signals based on cluster labels 
for y in range(len(test)):
    # computing the linkage matrix cluster wise 
    lm=link(dist_mat.filter(test[y], axis=1).filter(test[y], axis=0))
    # filtering signals belonging to respective cluster
    b=[h[a] for a in test[y]]
    # actual re-aggregation is done and stored
    pd.DataFrame(hdtw(lm,b)[-1],index=None).to_excel("/home/vauser/pcp/hdtw_op/op/modified/54/clust"+str(y)+".xlsx")