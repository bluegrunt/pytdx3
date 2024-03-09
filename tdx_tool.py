#!/usr/bin/python
#-*- encoding: utf-8 -*- 
## 使用新的日期格式

## TODO: 名称文件的解读
##       通达信股本变迁文件(复权) gbbq .

from __future__ import division
import struct   
import os,time ,datetime,string,sys,math,re,shutil,glob
from io import StringIO
import zipfile,getopt
from tdx_const import *
from tdx_utils import *

b_have_wx = True
b_have_sg = True
try :
    import wx
except ImportError :
    b_have_wx = False

try :
    import PySimpleGUI as sg
except ImportError :
    b_have_sg = False

def myputs(sss,obj=None):
    if b_have_wx and obj != None:
        obj.AppendText(sss)
        obj.AppendText('\n')
    elif type(obj) == list:
        obj.append(sss)
    else:
        print(sss)

def progress_percent(count,window):
    if b_have_sg:
        window['-PROCESSBAR-'].update(count)


## file format error
class TdxFileTypeError(Exception):
    pass

## Tdx Error
class TDXError(Exception):
    pass


## Tdx 基本文件目录
class Tdx():
    def __init__(self,root,verNew = True):
        self._setpath(root,verNew)

    def _setpath(self,root,verNew = True):
        self.root= root
        self.ExportPath =  os.path.join(root,r'T0002\export')
        self.DayBinPaths = {
                'SH' : os.path.join(root,'Vipdoc','sh','lday'),
                'SZ' : os.path.join(root,'Vipdoc','sz','lday')
                }
        self.Min5BinPaths = {
                'SH' : os.path.join(root,'Vipdoc','sh','fzline'),
                'SZ' : os.path.join(root,'Vipdoc','sz','fzline')
                }
        self.Min1BinPaths = {
                'SH' : os.path.join(root,'Vipdoc','sh','minline'),
                'SZ' : os.path.join(root,'Vipdoc','sz','minline')
                }
        if verNew :
            self.LineFile = os.path.join(root,'T0002','tdxline.dat')
        else:
            self.linefile = os.path.join(root,'T0002','line.dat')
        self.NamesFile = {
                'SH' : os.path.join(root,r'T0002\hq_cache\shex.tnf'),
                'SZ' : os.path.join(root,r'T0002\hq_cache\szex.tnf')                
                }
        self.NamesFile_m = {
                'SH' : os.path.join(root,r'T0002\hq_cache\shm.tnf'),
                'SZ' : os.path.join(root,r'T0002\hq_cache\szm.tnf')                
                }        


## Tdx 名称文件解读
class TdxNames(Tdx):
    def __init__(self,root):
        Tdx.__init__(self,root)
        self.namedict = {}
        self.namelist = []
        self._readname()

    def _readname(self):
        self.namedict.clear() # clear
        self.namelist = []    # clear
        if os.path.exists(self.NamesFile_m['SH']) :
            fname = self.NamesFile_m['SH']
            data = get_tdxNames_m(fname)
        else:
            fname = self.NamesFile['SH']
            data = get_tdxNames(fname)

        for ii in data :
            self.namelist.append(('SH' + ii[0],ii[1],ii[2]))


        if os.path.exists(self.NamesFile_m['SZ']) :
            fname = self.NamesFile_m['SZ']
            data = get_tdxNames_m(fname)
        else:
            fname = self.NamesFile['SZ']
            data = get_tdxNames(fname)

        for ii in data :
            self.namelist.append(('SZ' + ii[0],ii[1],ii[2]))
            
        for i in self.namelist:
            self.namedict[i[0]] = i[1]
        
        data = None

    def get_id_like_list(self,pattern):
        """pattern可以为 SH9|SH6|SH58|SH77|SZ39|SZ30|SZ0"""
        # pats = string.split(pattern,'|')
        pats = pattern.split('|')
        if len(pats) == 0 :
            return self.namelist
        namelist = []
        def _is_stkid_like(stkid,plist):
            for p in plist:
                if stkid.startswith(p):
                    return True
            return False
            
        namelist = list(filter(lambda x : _is_stkid_like(x[0],pats),self.namelist))
        return namelist

    def get_id_like_dict(self,pattern):
        """pattern可以为 SH9|SH6|SH58|SH77|SZ39|SZ30|SZ0"""
        pats = pattern.split('|')
        if len(pats) == 0 :
            return self.namedict
        namedict = {}
        def _is_stkid_like(stkid,plist):
            for p in plist:
                if stkid.startswith(p):
                    return True
            return False
            
        for k,v in self.namedict.items():
            if _is_stkid_like(k,pats):             
                namedict[k] = v
        return namedict
   
    def get_id_onlystock(self,typ = 'dict'):
        if typ == 'dict':
            return self.get_id_like_dict('SH6|SZ30|SZ0')
        return self.get_id_like_list('SH6|SZ30|SZ0')
     
    def get_id_mostuse(self,typ = 'dict'):
        if typ == 'dict':
            return self.get_id_like_dict('SH9|SH6|SH58|SH77|SZ39|SZ30|SZ0')
        return self.get_id_like_list('SH9|SH6|SH58|SH77|SZ39|SZ30|SZ0')
        
    def get_anlylike(self,pattern):
        """支持正则 return list"""
        rec = re.compile(pattern)
        data = []
        for ii in self.namelist:
            if rec.search(ii[0]):
                data.append(ii)
            elif rec.search(ii[1]):
                data.append(ii)
            elif rec.search(ii[2]):
                data.append(ii)
        return data
        
    def updateName(self,idnames):
        """依据ID,name 更改文件"""
        sh_items = []
        sz_items = []
        for ii in idnames:
            if len(ii) < 3 :
                continue
            if ii[0].startswith('SH')   and len(ii[0]) >=3 :
                sh_items.append((ii[0][2:],ii[1],ii[2]))
            elif ii[0].startswith('SZ') and len(ii[0]) >=3 :
                sz_items.append((ii[0][2:],ii[1],ii[2]))
                
        if len(sh_items) > 0 :
            # do update sh_file
            sh_file = self.NamesFile['SH']
            if os.path.exists(sh_file):
                sh_NamesFile = NamesFile(sh_file)
                sh_NamesFile.update(sh_items)

            sh_file = self.NamesFile_m['SH']
            if os.path.exists(sh_file):
                sh_NamesFile = NamesFile_m(sh_file)
                sh_NamesFile.update(sh_items)

            
        if len(sz_items) > 0 :
            # do update sz_file
            sz_file = self.NamesFile['SZ']
            if os.path.exists(sz_file):
                sz_NamesFile = NamesFile(sz_file)
                sz_NamesFile.update(sz_items)

            sz_file = self.NamesFile_m['SZ']
            if os.path.exists(sz_file):
                sz_NamesFile = NamesFile_m(sz_file)
                sz_NamesFile.update(sz_items)
        
        ## re read the names
        self._readname()

    #endupdateName

## 分钟数据转换等等
class TdxMin(Tdx):
    def __init__(self,root,TdxOut=None,sgWindow=None):
        Tdx.__init__(self,root)
        self.clear()
        self.stkdict = {}
        self.stkid = '999999'
        self.mkt   = 'SH'
        self.TdxOut = TdxOut
        self.sgWindow = sgWindow

    def clear(self):
        self.data_orig = [] #文本数据
        self.data_fb   = [] #分笔OHLC数据
        self.data_01   = [] #1分钟OHLC数据
        self.data_05   = [] #5分钟OHLC数据
        self.data_day  = [] #日线数据OHLC数据

    def setID(self,p_mkt , p_stkid):
        self.mkt   = p_mkt 
        self.stkid = p_stkid
        self.clear()

    def readFromText(self,dt1 = None,dt2 = None,tdx240 = False):
        """对给定的ID号和日期进行读取数据
           优先从ZIP文件中读取然后再读取TXT文本
        """ 
        thesefiles = {}
        if dt1 and dt2 : 
            if type(dt1) == datetime.date:
                dt1 = dt1.strftime('%Y%m%d')
            if type(dt2) == datetime.date: 
                dt2 = dt2.strftime('%Y%m%d')
        zipedfiles = []
        try:
            fzip = zipfile.ZipFile(os.path.join(self.ExportPath,self.stkid+'.zip'))
        except IOError as e:
            myputs('Warning Can not open file! ' + str(e),self.TdxOut)
            #return 
        else:
            zipedfiles = fzip.namelist()
            zipedfiles = list(map(lambda x : os.path.basename(x),zipedfiles))
            if dt1 and dt2 :
                zipedfiles = list(filter(lambda x : len(x) >= 8 and x[0:8] >= dt1 and x[0:8] <= dt2,zipedfiles))
            for f in zipedfiles:
                thesefiles[f.upper()] = 'ZIP'

        #处理textfile 
        txtfiles = glob.glob(os.path.join(self.ExportPath,'*-'+self.stkid+'.TXT')) 
        txtfiles = list(map(lambda x : os.path.basename(x),txtfiles))
        if dt1 and dt2 :
            txtfiles = list(filter(lambda x : len(x) >= 8 and x[0:8] >= dt1 and x[0:8] <= dt2,txtfiles))
        #txtfiles = filter(lambda x : not thesefiles.has_key(string.upper(x)),txtfiles)
        for f in txtfiles:
            if not thesefiles.get(f.upper(),None):
                thesefiles[f.upper()] = 'TXT'

        self.file_names = list(thesefiles.keys())
        self.file_names.sort()
        lastclose = 0
        file_cnt = len(self.file_names)
        i = 0
        for f in self.file_names: # 这些都是短文件名
            i += 1
            if self.sgWindow:
                count = i / file_cnt * 100
                progress_percent(count,self.sgWindow)
            else:
                myputs(f,self.TdxOut)
            if thesefiles[f] == 'ZIP': # Frome ziped files
                doc = fzip.read(f).decode(encoding="gbk")
                # print(doc)
                # doc_lines = StringIO.StringIO(doc).readlines()
                doc_lines = StringIO(doc).readlines()
            else:                      # Frome Text  files
                try : 
                    doc_lines = file(os.path.join(self.ExportPath,f)).readlines()
                except IOError as e :
                    myputs('Error'+str(e) ,self.TdxOut)
                    doc_lines = []
            #end if zip or txt
            
            data_orig = readfbtxt(doc_lines,f)
            # data_fb   = fbtxt2lc0(data_orig) 
            data_01   = fbtxt2lc1(data_orig)
            if tdx240 : ## 保证每日240跟K线的处理
                data_01 = tdxlc1_240(data_01,lastclose)
            data_05   = lc1tolc5(data_01)
            #self.data_orig.extend(data_orig)
            #self.data_fb.extend(data_fb)
            self.data_01.extend(data_01)
            self.data_05.extend(data_05)
            if len(data_orig) > 0 :
                lastclose = data_orig[-1][M_CLOSE]
        if len(zipedfiles) > 0 :    
            fzip.close()
            
        return len(thesefiles)
        
        #分别转化分笔、1分钟、5分钟数据  # 由于while 循环的原因，放在这里太慢
        #因为要检索已经存入的整个Data
        #self.data_fb = fbtxt2lc0(self.data_orig)
        #self.data_01 = fbtxt2lc1(self.data_orig)
        #self.data_05 = lc1tolc5(self.data_01)
         

    
    def readDaydata(self,dt1=None,dt2=None):
        """读日线数据"""
        fname = os.path.join(self.DayBinPaths[self.mkt],self.mkt + self.stkid + '.day')
        self.data_day = readDayBin(fname)
        if dt1 and dt2 :
            if type(dt1) == str :
                tt = time.strptime(dt1,"%Y%m%d")
                dt1 = datetime.date(tt.tm_year,tt.tm_mon,tt.tm_mday)
            if type(dt2) == str :
                tt = time.strptime(dt2,"%Y%m%d")
                dt2 = datetime.date(tt.tm_year,tt.tm_mon,tt.tm_mday)
            self.data_day = list(filter(lambda x : x[M_DT] >= dt1 and x[M_DT] <= dt2,self.data_day))


    def fuQuan(self,p_convfq):
        """对数据进行复权,仅仅作前复权 
           p_convfq 为复权处理列表[(日期,比率)]
        """
        ## TODO : 当前的复权仅仅处理一个，以后要处理多个情况
        ##        并考虑成交量等的关系
        l_fq = p_convfq[0]
        for i,dd in enumerate(self.data_fb):
            if dd[M_DT].date()   <= l_fq[0] : # 前复权 
                self.data_fb[i][M_OPEN]  /= l_fq[1] 
                self.data_fb[i][M_HIGH]  /= l_fq[1] 
                self.data_fb[i][M_LOW]   /= l_fq[1] 
                self.data_fb[i][M_CLOSE] /= l_fq[1] 

        for i,dd in enumerate(self.data_01):
            if dd[M_DT].date()   <= l_fq[0] : # 前复权 
                self.data_01[i][M_OPEN]  /= l_fq[1] 
                self.data_01[i][M_HIGH]  /= l_fq[1] 
                self.data_01[i][M_LOW]   /= l_fq[1] 
                self.data_01[i][M_CLOSE] /= l_fq[1] 


        for i,dd in enumerate(self.data_05):
            if dd[M_DT].date()   <= l_fq[0] : # 前复权 
                self.data_05[i][M_OPEN]  /= l_fq[1] 
                self.data_05[i][M_HIGH]  /= l_fq[1] 
                self.data_05[i][M_LOW]   /= l_fq[1] 
                self.data_05[i][M_CLOSE] /= l_fq[1] 


        for i,dd in enumerate(self.data_day):
            if dd[M_DT]          <= l_fq[0] : # 前复权 
                self.data_day[i][M_OPEN]  /= l_fq[1] 
                self.data_day[i][M_HIGH]  /= l_fq[1] 
                self.data_day[i][M_LOW]   /= l_fq[1] 
                self.data_day[i][M_CLOSE] /= l_fq[1] 

    def writeMin1ToBin(self,fname= None):
        """将1分钟数据写入文件 """
        if len(self.data_01) == 0 : 
            return 
        if fname == None:
            fname = os.path.join(self.Min1BinPaths[self.mkt],self.mkt + self.stkid + '.lc1')
        writeMinBin_new(self.data_01,fname)
        myputs( 'Write to ' + fname,self.TdxOut)

    def writeMin5ToBin(self,fname= None):
        """将5分钟数据写入文件名p_file """
        if len(self.data_05) == 0 : 
            return 
        if fname == None :
            fname = os.path.join(self.Min5BinPaths[self.mkt],self.mkt + self.stkid + '.lc5')
        writeMinBin_new(self.data_05,fname)
        myputs( 'Write to ' + fname,self.TdxOut)



if __name__ == '__main__':
    import pprint
    #aa = TdxMin(r'E:\cwork\tdx_study')
    #aa.setID('SH','999999')
    ##aa.readDaydata('999999','sh',dt1='20130101',dt2='20130131')
    #aa.readFromText(dt1='20070101',dt2='20070131')
    #aa.writeMin1ToBin()
    #fname = os.path.join(aa.Min1BinPaths[aa.mkt],aa.mkt + aa.stkid + '.lc1')
    #data = readMinBin_new(fname)
    #for i in data:
        #pprint.pprint(i)
    
    
    print( '='*70)
    # nn=TdxNames(r'D:\stock\new_gxzq_v6')
    # tdx = readDayBin(r'D:\stock\new_gxzq_v6')
    adict = {
        'col1':1,
        'col2':2
    }
    skey = list(adict.keys())
    skey.sort()
    ss = ''
    #with open('shex.txt','r',encoding='gbk') as f1:

    #nn.updateName([('SH770002','标普指数','BPZS'),('SZ370001','其他指数','QTZS')])
    #for ii in nn.namelist:
        #print('\t'.join( ii))

    #nn.get_id_like_list('SH77|SZ37')
    #keys = nn.namedict.keys()
    #keys.sort()
    #for k in keys:
        #print k,nn.namedict[k]
    print( '='*70)
    #data = nn.get_anlylike(r'.*')
    #for i in data :
        #print i[0],i[1],i[2]
    

