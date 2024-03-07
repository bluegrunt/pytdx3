#-*- encoding: utf-8 -*- 
from tdx_utils import *
from get_block import *
import re
import glob
import os
def MyFunction(x, y):
    res = {}
    res["sum"] = x + y
    res["sorted"] = (1,2,3,4)
    return res


if __name__ == '__main__':
    print('test')
    ss=re.compile(r'as(\d\d\d)\.mp3',flags=re.IGNORECASE)

    fo = open(r'E:/BaiduNetdiskDownload/name.txt',encoding="utf-8")
    lines = fo.readlines()
    fo.close()
    allName = []
    for line in lines:
        i,n = line.split('\t')
        n = n.strip() 
        allName.append(n)
         
    for i in glob.glob(r'E:/BaiduNetdiskDownload/*as*.mp3'):
        print(i)
        mm = ss.search(i)
        
        if mm == None:
            print ("Error " + i)
            exit
        else:
            num = mm.groups()[0]
        
        newName = r'E:/BaiduNetdiskDownload/阿含经的故事/' + num + ' ' + allName[int(num) -1]+'.mp3'
        print(newName)
        os.rename(i,newName)
        exit
    
