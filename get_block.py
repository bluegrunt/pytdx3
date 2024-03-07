# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 20:22:50 2019

@author: wanghp
"""

import struct 
import os,time ,datetime,string,sys,math,re,shutil,glob
import pprint
import ctypes as ct
import re
from tdx_utils import *

#TDX_ROOT = r'E:\wanghp\guosen'

mkt = {'1':'SH','0':'SZ'}

class TDXError(Exception):
    pass

def getNameFromFile(fname):
    """从文件中获取名称 'T0002\hq_cache\shex.tnf' """
    fhandle = open(fname,'rb')
    context = fhandle.read()
    fhandle.close()
    IP = context[0:40]
    unkown = context[40:42]
    start = 50
    l_cnt = 0
    data = {}
    while True:
        l_cnt += 1
        end = start + 250 
        if end > len(context) : break 
        cc = context[start:end]
        stkid = cc[0:9].decode('gbk')
        stkname = cc[24:42].decode('gbk')
        shortname = cc[241:250].decode('gbk')
        
        stkid = stkid.rstrip('\0\n\r ')
        stkname = stkname.rstrip('\0\n\r ')
        lastclose = struct.unpack("I",cc[232:236])[0]
        shortname = shortname.rstrip('\0\n\r ')
        if stkid in data:
            e = 'double stockID ' + stkid
            raise TDXError(e)
        data[stkid] = (stkname,lastclose,shortname,l_cnt)
        start += 250 
    return data


class TdxinnerBlockName():
    """tdxzs.cfg 版块名称解析"""
    def __init__(self,root):
        self.root = root
        self.tdxBlockFile = os.path.join(self.root, r'T0002\hq_cache\tdxzs.cfg')        
        self.blockNames_det = []
        self.blockNames = {}
        self._fillBlockNames()
        
    def _fillBlockNames(self):
        try :
            f = open(self.tdxBlockFile)
            for line in f.readlines():
                line = line.strip()
                temp = line.split('|')
                if len(temp) >= 6:
                    self.blockNames_det.append(temp)
                    self.blockNames[temp[5]] = (temp[0],temp[1])
            f.close()
        except IOError as e:
            pass
        
    def getBlockName(self,innerBlockID):
        if self.blockNames.has_key(innerBlockID):
            return self.blockNames[innerBlockID][0]
        else:
            return ''
            
    def getBlockUserID(self,innerBlockID):
        """ 返回88啥的"""
        if innerBlockID in self.blockNames:
            return self.blockNames[innerBlockID][1]     
        else:
            return ''

def getTdxBlock(fname) :
        """通达信blcok_fg.dat 风格、概念等文件解析 """
        # 融资融券 在fg文件中有单在cfg中没有！
        #typ = string.lower(typ)
        #if not typ in ('fg','gn','zs') return []
        data = []
        #f = os.path.join(self.root,r'T0002\hq_cache' ,  'block_' + typ + '.dat' )
        start =386
        recordLen = 2813        
        try :
            fhand = open(fname,'rb')
            content = fhand.read()
            fhand.close()
            if len(content) < start + recordLen : 
                return []
            # 总板块数
            blockCnt = struct.unpack('H',content[384:386])[0] 
            while start + recordLen <= len(content):
                raw = content[start:start + recordLen]
                innerBlockID = raw[0:9].replace(b'\0',b'').decode('gbk')
                cnt = struct.unpack('H',raw[9:11])[0]
                un  = raw[11:13]
                i = 13
                stockItems=[]
                while i+7 <= recordLen :
                    tt = raw[i: i+7].replace(b'\0',b'')
                    tt = tt.decode('gbk')
                    if tt != '':
                        if tt.startswith('6') : 
                            tt = 'SH' + tt
                        else:
                            tt = 'SZ' + tt
                        stockItems.append(tt)
                    else:
                        break
                    
                    i+=7
                start += recordLen
                data.append({'innerID':innerBlockID, 'count': cnt ,'un':un,'stocks' : stockItems})
        except IOError as e:
            raise TDXError ('Can not open file ' + fname)
        return data 
 
    
def getStocksInUserBlock(fname):
        """用户自定义的版块"""
        data = []
        try:
            #lines =  file(os.path.join(self.root,r'T0002\blocknew', blockname  + '.blk')).readlines()
            with open(fname,encoding = 'gbk') as f:
                lines = f.readlines()
            for ll in lines:
                ll = ll.strip()
                if len(ll) <6 : continue
                data.append(ll)
            data = map(lambda x:mkt.get(x[0],'  ') + x[1:],data)
            data = list(data)        
        except IOError as e:
            pass
        return data    
 



class TdxUserBlock():
    """通达信用户定义板块解析 """
    def __init__(self,root):
        self.root = root
        self.blockNames = self.getBlockNames()
        
    def getZXG(self):
        """获取自选股"""
        data = []
        try:
            lines =  open(os.path.join(self.root,r'T0002\blocknew\ZXG.blk')).readlines()
            for ll in lines:
                ll = ll.strip()
                if len(ll) <6 : continue
                data.append(ll)
            data = map(lambda x:mkt.get(x[0],'  ') + x[1:],data)
                    
        except IOError as e:
            pass
        return list(data) 
    
    def getTJG(self):
        """获取条件选股"""
        data = []
        try:
            lines =  open(os.path.join(self.root,r'T0002\blocknew\TJG.blk')).readlines()
            for ll in lines:
                ll = ll.strip()
                if len(ll) <6 : continue
                data.append(ll)
            data = map(lambda x:mkt.get(x[0],'  ') + x[1:],data)
                    
        except IOError as e:
            pass
        return list(data)   
    
    def getUserBlock(self,blockname):
        """用户自定义的版块"""
        data = []
        try:
            lines =  open(os.path.join(self.root,r'T0002\blocknew', blockname  + '.blk')).readlines()
            for ll in lines:
                ll = ll.strip()
                if len(ll) <6 : continue
                data.append(ll)
            data = map(lambda x:mkt.get(x[0],'  ') + x[1:],data)
                    
        except IOError as e:
            pass
        return list(data)   
    
    def getBlock(self,blockNames):
        data_all = []
        if type(blockNames) == str:
            blockNames = [blockNames] 
        for ii in blockNames:
            if ii == 'ZXG' :
                data_all.extend(self.getZXG())
            elif ii == 'TJG':
                data_all.extend(self.getTJG())
            else:
                data_all.extend(self.getUserBlock(ii))
        return data_all
    
    def getTdxBlock(self,blockType) :
        blockType = blockType.lower()
        if not blockType in ('fg','gn','zs') : return []
        data = []
        f = os.path.join(self.root,r'T0002\hq_cache' ,  'block_' + blockType + '.dat' )
        for item in getTdxBlock(f):
            if item['innerID'] in self.blockNames:
                item['ID'] = self.blockNames[item['innerID']][1]
                data.append(item)
        return data
    
    def getJiejin(self):
        """检查自选股等是否是将要解禁的！"""
        TdxBlocks = self.getTdxBlock('fg')
        #本月解禁
        data = []
        JiejinBlock = filter(lambda x : x['innerID'] == '即将解禁',TdxBlocks)
        for item in JiejinBlock:
            data = item["stocks"]
        return data
        
    def getUsersBlockNames(self):
        data = {'ZXG':'自选股','TJG':'条件选股'}
        content = ''
        try :
            content = open(os.path.join(self.root,r'T0002\blocknew\blocknew.cfg' )).read()
            start = 0 
            length = 120
            while True:
                if start >= len(content):break
                raw = content[start:start+length]
                blockID   = raw[50:62].replace('\0','')
                blockName = raw[0:12].replace('\0','')
                data[blockID] = blockName
                start = start + length
        except IOError as e:               
            raise TDXError('no such user defined block')
        return data
    
    def getBlockNames(self):
        innerBlockName = TdxinnerBlockName(self.root)
        return innerBlockName.blockNames
        
#    def getBlockNames(self):
#        data = {'ZXG':'自选股','TJG':'条件选股'}
#        content = ''
#        try :
#            content = open(os.path.join(self.root,r'T0002\blocknew\blocknew.cfg' )).read()
#            start = 0 
#            length = 120
#            while True:
#                if start >= len(content):break
#                raw = content[start:start+length]
#                blockID = string.replace(raw[50:62] ,'\0','')
#                blockName = string.replace(raw[0:12], '\0','')
#                data[blockID] = blockName
#                start = start + length
#        except IOError as e:               
#            raise TDXError('no such user defined block')
#        return data
#
#    def getBlockName(self,blockID):
#        return self.blockNames.get(string.upper(blockID),'')        

###################################################################
## below function only used in EXCEL ##############################        
def getStocksInUserBlockAndNames(root,blockID):
    tdx_names = get_tdxNames_return_dict(root)
    fname = os.path.join(root,r'T0002\blocknew' , blockID + r'.blk')
    data =  getStocksInUserBlock(fname)
    res = []
    for item in data:
        res.append((item,tdx_names.get(item,'')))
    return res


def excel_getBlocks(root,blockIDs):
    """blockIDs为逗号分割开的 """
    blds = blockIDs.split(",")
    userblock = TdxUserBlock(root)
    jiejin_stocks = userblock.getJiejin()
    
    data = []
    for b in blds :
        stocks =  getStocksInUserBlockAndNames(root,b)
        for item in stocks:
            bool_jiejin = ''
            if item[0] in jiejin_stocks:
                bool_jiejin = 'Y'
            line = [b,item[0],item[1],bool_jiejin]
            data.append(line)
    return data        
        
def excel_getjiejin(root):
    userblock = TdxUserBlock(root)
    stks = userblock.getJiejin()
    tdx_names = get_tdxNames_return_dict(root)
    res = []
    for item in stks:
        res.append((item,tdx_names.get(item,'')))
    return res

def excel_getrate(root,year,month,day):
    fdirs = [os.path.join(root, r'vipdoc\sh\lday'),os.path.join(root,r'vipdoc\sz\lday')]
    data = []
    icnt = 0
    tdx_names = get_tdxNames_return_dict(root)
    for fdir in fdirs:
        flist = os.listdir(fdir)
        for f in flist:
            if len(f) <= 4 :
                continue
            icnt +=1
            stkid,fext = os.path.splitext(f)
            fext = fext.lower()
            stkid = stkid.upper()
            if id_is_stock(stkid) and fext.endswith('.day') :
                fullname = os.path.join(fdir,f)
                dd = readDayBinOn(fullname,datetime.date(year, month, day))
                if dd[0] == None or dd[1] == None:
                    pass
                else:
                    rate = (dd[1][M_CLOSE] - dd[0][M_CLOSE] ) / dd[0][M_CLOSE]
                    data.append((stkid,tdx_names.get(stkid,''),rate))
    return data


def getstockofblocks(root):
    """获取证券ID对应的所有概念板块:返回格式为 {}"""
    data_gn = getTdxBlock(os.path.join(root ,r"T0002\hq_cache\block_gn.dat"))
#    tdx_names = get_tdxNames_return_dict(root)
    data = {}
    for item in data_gn :
        for stk in item['stocks']:
            if stk in data:
                data[stk].append(item['innerID'])
            else:
                data[stk] = [item['innerID']]
    return data

def excel_getstockofblocks(root):
    """获取证券ID对应的所有概念板块 """
    data_gn = getTdxBlock(os.path.join(root ,r"T0002\hq_cache\block_gn.dat"))
    tdx_names = get_tdxNames_return_dict(root)
    data = {}
    for item in data_gn :
        for stk in item['stocks']:
            if stk in data:
                data[stk].append(item['innerID'])
            else:
                data[stk] = [item['innerID']]
    data_re = []
    for k,v in data.items():
        data_re.append([k,tdx_names.get(k,''),','.join(v)])
    return data_re

def excel_getzhangtingsofblocks(root,year,month,day,stk_count=15,rate1=0.097,rate2 = -0.07):
    """获取板块涨停的个数,并减去跌的比较厉害的如跌7%以下的"""
    stk_in_blocks = getstockofblocks(root)
    block_cnt = {}

    data_rate = excel_getrate(root,year,month,day)
    data_rate = filter(lambda x:x[2]>=rate1 or x[2]<= rate2,data_rate)
    data_rate = list(data_rate)
    for item in data_rate:
        stk = item[0]
        if stk in stk_in_blocks:
            for blk in stk_in_blocks[stk]:
                if blk in block_cnt:
                    if item[2] >0 :
                        block_cnt[blk] += 1
                    else:
                        block_cnt[blk] -= 1
                else:
                    if item[2] >0 :
                        block_cnt[blk]  = 1
                    else:
                        block_cnt[blk]  = -1
    
    data_tmp = []
    for k,v in block_cnt.items():
        data_tmp.append((k,v))
    data_tmp.sort(key = lambda x:x[1],reverse=True)
    data_re = []
    icnt = 0
    tdxName = TdxinnerBlockName(root)
    for item in data_tmp:
        if icnt > stk_count:
            break
        if len(data_re) == 0 :
            data_re=[[ item[0] + " " + tdxName.getBlockUserID(item[0])]]
        else:
            data_re[0].append( item[0] + " " + tdxName.getBlockUserID(item[0]) )
        icnt +=1
    return data_re
###################################################################


if __name__ == '__main__':
    TDX_ROOT = r'D:\stock\new_gxzq_v6'
    sys_blocks = []
    #data_gn = getTdxBlock(os.path.join(TDX_ROOT ,r"T0002\hq_cache\block_gn.dat"))
    #data_fg = getTdxBlock(os.path.join(TDX_ROOT ,r"T0002\hq_cache\block_fg.dat"))
    data1 = excel_getzhangtingsofblocks(TDX_ROOT,2022,11,9)
    pprint.pprint(data1)

## todo: 板块涨停个数
        #板块涨幅！！         
    #print(data_gn)
    #tdxBlName = excel_getBlocks (TDX_ROOT,'ZXG,CXGZ')
    #print(tdxBlName)
    #jj = excel_getjiejin(TDX_ROOT)
    #print(jj)
    #data = excel_getrate(TDX_ROOT,2021,9,3)
    
    #print(tdxBlName.getTdxBlock('fg'))
    #print(tdxBlName.getJiejin())
    
#    dd = TdxinnerBlockName(TDX_ROOT)
#    print(dd.blockNames)
#    for item in data_gn :
#        stk = {}
#        for i in item['stocks']:
#            stk[i] = 1
#        sys_blocks.append({'ID': 'GN_' + item['ID'] ,'stocks': stk })

#    for item in data_fg :
#        stk = {}
#        for i in item['stocks']:
#            stk[i] = 1
#        sys_blocks.append({'ID': 'FG_' + item['ID'] ,'stocks': stk })    
    
    #user_stocks = getStocksInUserBlock(r"D:\stock\new_gxzq_v6\T0002\blocknew\TEMP.blk")
    #统计结果 {板块名，stocks}
           
        

    
