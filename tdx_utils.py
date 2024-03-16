# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 21:56:00 2019

@author: wanghp
"""
import struct   
import os,time ,datetime,string,sys,math,re,shutil,glob
from tdx_const import *
import ctypes as ct


###################################
## 整数转化为日期
###################################
def int2date(p_int):
    y = p_int // 10000
    m = (p_int - y*10000 ) // 100
    d = p_int % 100
    return datetime.date(y,m,d)

###################################
## 日期转化为整数
###################################
def date2int(p_date):
    return p_date.year * 10000 + p_date.month * 100 + p_date.day

###################################
## 整数转化为日期时间(没有年的tuple)
###################################
def int2datetime(p_int):
    """高十六位为时间，低十六位为日期 """
    mins = (p_int >> 16) & 0xffff
    mds  = p_int & 0xffff
    month = int(mds / 100)
    day   = mds % 100
    hour = int(mins / 60)
    minute = mins % 60
    return (month,day,hour,minute)

###################################
## 整数转化为日期时间有年，
## 而且这个数据结构也不同
## 在低16位中用5为表示年(要加2004才是真实的)
## 在低16位的其他11位表示月日
###################################
def int2datetime_new(p_int):
    mask = 0xFFF - (1 << 11)  # 11位的1
    mins = (p_int >> 16) & 0xffff
    ymds  = p_int & 0xffff
    tmpdd = ymds & mask
    month = int( tmpdd / 100 )
    day   = tmpdd % 100
    year =  ( ymds >> 11 ) + 2004
    hour = int(mins / 60)
    minute = mins % 60            
    return datetime.datetime(year,month,day,hour,minute)

###################################
## 日期时间转化为整数
###################################
def datetime2int(p_dt):
    if type(p_dt) == datetime.datetime:
        return p_dt.month*100 + p_dt.day + ( (p_dt.hour * 60 + p_dt.minute) << 16)
    else:
        return p_dt[0]*100 + p_dt[1] + ( (p_dt[2] * 60 + p_dt[3]) << 16)

###################################
## 日期时间转化为整数
###################################
def datetime2int_new(p_dt):
    return ((p_dt.year-2004) << 11 ) + p_dt.month*100 + p_dt.day + ( (p_dt.hour * 60 + p_dt.minute) << 16)



##################################
### struct 结构操作###############
##################################
def struct2stream(s):
    length  = ct.sizeof(s)
    p       = ct.cast(ct.pointer(s), ct.POINTER(ct.c_char * length))
    return p.contents.raw

def stream2struct(string, stype):
    if not issubclass(stype, ct.Structure):
        raise ValueError('The type of the struct is not a ctypes.Structure')
    length      = ct.sizeof(stype)
    stream      = (ct.c_char * length)()
    stream.raw  = string
    p           = ct.cast(stream, ct.POINTER(stype))
    return p.contents



## gen
def gen_tdx1min_aday():
    tdx1min_aday = []
    tdx1min_aday.append(datetime.datetime(2014,1,1,9,25).time())
    t0 = datetime.datetime(2014,1,1,9,30)
    i = 1
    while True:
        temp = t0 + datetime.timedelta(minutes = i)
        tt = temp.time()
        if tt >= datetime.time(11,30) : break
        tdx1min_aday.append(tt)
        i += 1

    t0 = datetime.datetime(2014,1,1,13,0)
    i = 0
    while True:
        temp = t0 + datetime.timedelta(minutes = i)
        tt = temp.time()
        if tt > datetime.time(15,0) : break
        tdx1min_aday.append(tt)
        i += 1
    return tdx1min_aday

# 通达信1F一天有240根K线，同花顺的有242根
# 通达信的从9:31到11：29 ，13:00到15:00
tdx1min_aday = gen_tdx1min_aday()
tdx1min_index  = {}
for n,item in enumerate(tdx1min_aday):
    tdx1min_index[item] = n
def gen_tdx1min_struct(p_id,p_dt):
    sample = []
    for i in tdx1min_aday:
        sample.append({M_ID: p_id ,
                      M_DT: datetime.datetime(p_dt.year,p_dt.month,p_dt.day,i.hour,i.minute) ,
                      M_OPEN : None ,
                      M_HIGH : None ,
                      M_LOW  : None ,
                      M_CLOSE: None,
                      M_VOL  : 0  ,
                      M_AMT  : 0           
        }  
        )
    
    return sample

#############################################################
# read 通达信分笔数据
# example readfbtxt(readlines(),'20100831-600000.TXT')
# 返回的data格式为
# list of dict [{'ID':'stock id','DT':datetime.datetime(),
#  'CLOSE':Price,'VOL':vol,'AMT':amout}] 
# vol 为股而不是手！
#############################################################
def readfbtxt(p_lines,p_name):
        """读通达信分笔数据 """
        shortname = os.path.basename(p_name)
        shortname = os.path.splitext(shortname)[0]
        sDay,stkid = shortname.split('-')
        if len(sDay) != 8 : return []
        stky = int(sDay[0:4])
        stkm = int(sDay[4:6])
        stkd = int(sDay[6:8])    
        line_no = 0
        data = []
        re_hour_minute = re.compile(r'(\d\d):(\d\d)')
        b_first = True
        for l in p_lines:
            line_no += 1
            # if line_no <=3: continue 
            l = l.strip()
            t = re.split('\s+',l)
            if len(t) < 4 : continue
            k = None
            hm = re_hour_minute.search(t[0])
            if hm == None: 
                continue
            hour,minute = hm.groups() 
            try:
                # k =  datetime.datetime(stky,stkm,stkd,int(t[0][0:2]),int(t[0][3:5]))
                hour = int(hour)
                minute = int(minute)
                if b_first :
                    b_first = False
                    if hour == 9 and minute == 30:
                        minute = 25
                k =  datetime.datetime(stky,stkm,stkd,hour,minute)
            except ValueError as e :
                if DEBUG :
                    print(e)
                continue
            p = float(t[1])      #price
            vol = int(t[2])*100  #股数
            amt = p * vol        #成交量
            bscnt = 0            #笔数
            bstag = ''           #buy or sale
            try:
                bscnt = int(t[3])    #笔数
                bstag = t[4]         #buy or sale
            except IndexError as e:
                pass
            data.append({M_ID:stkid,
                        M_DT:k,
                        M_CLOSE:p,
                        M_VOL:vol,
                        M_AMT:amt,
                        'BSCNT':bscnt,
                        'BSTAG':bstag})               
        return data

#############################################################
# 将分笔数据转化为分笔数据
# p_data:传入参数 为readfbtxt所返回
# data:  返回的数据格式为
# 返回的data格式为
# list of dict [{'ID':'stock id','DT':datetime.datetime(),
#  'OPEN':OpenPrice,'HIGH':HighPrice,'LOW':LowPrice,'CLOSE':Price,
#  'VOL':vol,'AMT':amout}] 
# vol 为股而不是手！
#############################################################
def fbtxt2lc0(p_data):
    """分笔数据转化为分笔数据的OHLC"""
    data = []
    for i in p_data:
        data.append({ M_ID: i[M_ID] ,
                      M_DT: i[M_DT] ,
                      M_OPEN : i[M_CLOSE] ,
                      M_HIGH : i[M_CLOSE] ,
                      M_LOW  : i[M_CLOSE] ,
                      M_CLOSE: i[M_CLOSE],
                      M_VOL  : i[M_VOL]  ,
                      M_AMT  : i[M_AMT]
            })
    return data



#############################################################
# 将分笔数据转化为1分钟数据
# p_data:传入参数 为readfbtxt所返回
# p_convfq 为复权处理列表[(日期,比率)]
# data:  返回的数据格式为
# list of dict [{'ID':'stock id','DT':datetime.datetime(),
#  'OPEN':OpenPrice,'HIGH':HighPrice,'LOW':LowPrice,'CLOSE':Price,
#  'VOL':vol,'AMT':amout}] 
# vol 为股而不是手！
#############################################################
def fbtxt2lc1(p_data):
    """分笔数据转化为1分钟数据"""
    data = []
    for i in p_data:
        t = i[M_DT]        #datetime
        p = i[M_CLOSE]     #price
        lend = len(data)
        j = lend - 1
        
        if j >= 0 and data[j][M_DT] == t : #找到该时间
            if p > data[j][M_HIGH]:  #high
                data[j][M_HIGH] = p
            if p < data[j][M_LOW]:  #low
                data[j][M_LOW] = p
            data[j][M_CLOSE] = p      #close
            data[j][M_AMT] += i[M_AMT]  #amout
            data[j][M_VOL] += i[M_VOL]  #vol
        else: #没有找到该时间
            data.append({ M_ID: i[M_ID] ,
                  M_DT: i[M_DT] ,
                  M_OPEN : i[M_CLOSE] ,
                  M_HIGH : i[M_CLOSE] ,
                  M_LOW  : i[M_CLOSE] ,
                  M_CLOSE: i[M_CLOSE],
                  M_VOL  : i[M_VOL]  ,
                  M_AMT  : i[M_AMT] })  
        # end if                  
    # end for i in p_data:                      
                                      
    return data

def txtTime2KTime(dt):
    """
       其对应比较奇怪：
       文本      1F K线
       9:00      9:31
       11:28     11:29 
       
       11:29     13:00
       11:30     13:00
       
       13:00     13:01
       14:59     15:00
       15:00     15:00    
    """
    if type(dt) != datetime.datetime:        
        raise ValueError('para must be datetime.datetime')
    if dt.hour == 15 and dt.minute > 0 :
        raise ValueError('the time of para must not grate than 15:00 ')
    elif dt.hour == 15 and dt.minute == 0 :
        return dt
    elif dt.hour == 11 and dt.minute >= 29:
        return datetime.datetime(dt.year,dt.month,dt.day,13,0) 
    elif dt.hour == 9 and dt.minute == 25 :
        return dt
    else :
        return dt + datetime.timedelta(minutes =1)
        
#############################################################
# 将分笔数据转化为1分钟数据
# tdxlc1_240 将1分钟数据进行修正，保证每天有240根K线
#############################################################
def tdxlc1_240(p_data,p_lastclose = 0):
    """分笔数据转化为1分钟数据， 保证一天240:
    换成硬办法写吧
    """
    data = []     # 一天的数据
    all_data = [] # 整个的数据
    last_day = None
    day = None
    for item in p_data:
        day = item[M_DT].date()
        if day != last_day: # a new day begin
            all_data.extend(data)
            data = gen_tdx1min_struct(item[M_ID],item[M_DT])
        newt = txtTime2KTime(item[M_DT])
        ind = tdx1min_index.get(newt.time())
        if data[ind][M_OPEN] == None:
            data[ind][M_OPEN] = item[M_OPEN]
            data[ind][M_HIGH] = item[M_HIGH]
            data[ind][M_LOW]  = item[M_LOW]
            data[ind][M_CLOSE] = item[M_CLOSE]
            data[ind][M_VOL] = item[M_VOL]
            data[ind][M_AMT] = item[M_AMT]
        else:
            if item[M_HIGH] > data[ind][M_HIGH]:
                data[ind][M_HIGH] = item[M_HIGH]
            if item[M_LOW] < data[ind][M_LOW] :
                data[ind][M_LOW] = item[M_LOW]
            data[ind][M_CLOSE] = item[M_CLOSE]
            data[ind][M_VOL] += item[M_VOL]
            data[ind][M_AMT] += item[M_AMT]
        
        last_day = day
    # end for
    all_data.extend(data)
    for n,item in enumerate(all_data):
        if item[M_OPEN] == None:
            if n == 0:
                all_data[n][M_OPEN] = p_lastclose
                all_data[n][M_HIGH] = p_lastclose
                all_data[n][M_LOW]  = p_lastclose
                all_data[n][M_CLOSE] = p_lastclose
            else:
                all_data[n][M_OPEN] = all_data[n-1][M_CLOSE]
                all_data[n][M_HIGH] = all_data[n-1][M_CLOSE]
                all_data[n][M_LOW]  = all_data[n-1][M_CLOSE]
                all_data[n][M_CLOSE] = all_data[n-1][M_CLOSE]
    # endfor
    return all_data
    
    
#############################################################
# 将1分钟数据转为5分钟数据
# p_data:传入参数 为fbtxt2lc1所返回
# data:  返回的数据格式为
# list of dict [{'ID':'stock id','DT':datetime.datetime(),
#  'OPEN':OpenPrice,'HIGH':HighPrice,'LOW':LowPrice,'CLOSE':Price,
#  'VOL':vol,'AMT':amout}] 
# vol 为股而不是手！
#############################################################
def lc1tolc5(p_data):
    """1分钟数据转化为5分钟数据 """
    if len(p_data) <= 0: return []
    data = []
    for i in p_data:
        t = which5min(i[M_DT])   #找对应5分钟的区段
        if t == None:
            raise ValueError('time out of range: %s' % i[M_DT])
        lend = len(data)
        j = lend - 1
        if j >= 0 and data[j][M_DT] == t:
            if i[M_HIGH] > data[j][M_HIGH]:  #high
                data[j][M_HIGH] = i[M_HIGH]
            if i[M_LOW] < data[j][M_LOW]:  #low
                data[j][M_LOW] = i[M_LOW]
            data[j][M_CLOSE] = i[M_CLOSE]      #close
            data[j][M_AMT] += i[M_AMT]     #amout
            data[j][M_VOL] += i[M_VOL]     #vol
        else:
            data.append({ M_ID: i[M_ID] ,
                      M_DT: t ,
                      M_OPEN : i[M_OPEN] ,
                      M_HIGH : i[M_HIGH] ,
                      M_LOW  : i[M_LOW] ,
                      M_CLOSE: i[M_CLOSE],
                      M_VOL  : i[M_VOL]  ,
                      M_AMT  : i[M_AMT] })
                      
#        while j >= 0:
#            if data[j][M_DT] == t:break
#            j -= 1
#        if j < 0:  #没有找到该时间
#            data.append({ M_ID: i[M_ID] ,
#                      M_DT: t ,
#                      M_OPEN : i[M_OPEN] ,
#                      M_HIGH : i[M_HIGH] ,
#                      M_LOW  : i[M_LOW] ,
#                      M_CLOSE: i[M_CLOSE],
#                      M_VOL  : i[M_VOL]  ,
#                      M_AMT  : i[M_AMT] })
#        else:         #找到该时间
#            if i[M_HIGH] > data[j][M_HIGH]:  #high
#                data[j][M_HIGH] = i[M_HIGH]
#            if i[M_LOW] < data[j][M_LOW]:  #low
#                data[j][M_LOW] = i[M_LOW]
#            data[j][M_CLOSE] = i[M_CLOSE]      #close
#            data[j][M_AMT] += i[M_AMT]     #amout
#            data[j][M_VOL] += i[M_VOL]     #vol
    #data.sort(key = lambda x:x[1])  #以datetime 排序
    return data




#############################################################
# 一个时间对应的5分钟区间段
# dt 传入参数 为一个datetime.datetime or datetime.time
# 返回datetime 或time 
#############################################################
def which5min(dt):
    """5 分钟时间划分 """
    if type(dt) != datetime.datetime and  type(dt) != datetime.time:
        return None
    t = dt
    ret = None
    if type(dt) == datetime.datetime:
        t = datetime.time(dt.hour,dt.minute,dt.second)

    if t < datetime.time(9,25) : return None 
    if   t < datetime.time(9,35): ret = datetime.time(9,35)
    elif t < datetime.time(9,40): ret = datetime.time(9,40)
    elif t < datetime.time(9,45): ret = datetime.time(9,45)
    elif t < datetime.time(9,50): ret = datetime.time(9,50)
    elif t < datetime.time(9,55): ret = datetime.time(9,55)
    elif t < datetime.time(10,0): ret = datetime.time(10,0)
    elif t < datetime.time(10,5): ret = datetime.time(10,5)
    elif t < datetime.time(10,10): ret = datetime.time(10,10)
    elif t < datetime.time(10,15): ret = datetime.time(10,15)
    elif t < datetime.time(10,20): ret = datetime.time(10,20)
    elif t < datetime.time(10,25): ret = datetime.time(10,25)
    elif t < datetime.time(10,30): ret = datetime.time(10,30)
    elif t < datetime.time(10,35): ret = datetime.time(10,35)
    elif t < datetime.time(10,40): ret = datetime.time(10,40)
    elif t < datetime.time(10,45): ret = datetime.time(10,45)
    elif t < datetime.time(10,50): ret = datetime.time(10,50)
    elif t < datetime.time(10,55): ret = datetime.time(10,55)
    elif t < datetime.time(11,0): ret = datetime.time(11,0)
    elif t < datetime.time(11,5): ret = datetime.time(11,5)
    elif t < datetime.time(11,10): ret = datetime.time(11,10)
    elif t < datetime.time(11,15): ret = datetime.time(11,15)
    elif t < datetime.time(11,20): ret = datetime.time(11,20)
    elif t < datetime.time(11,25): ret = datetime.time(11,25)
    elif t <= datetime.time(11,30): ret = datetime.time(11,30)
    #elif t < datetime.time(13,0): ret = datetime.time(13,0)
    elif t < datetime.time(13,5): ret = datetime.time(13,5)
    elif t < datetime.time(13,10): ret = datetime.time(13,10)
    elif t < datetime.time(13,15): ret = datetime.time(13,15)
    elif t < datetime.time(13,20): ret = datetime.time(13,20)
    elif t < datetime.time(13,25): ret = datetime.time(13,25)
    elif t < datetime.time(13,30): ret = datetime.time(13,30)
    elif t < datetime.time(13,35): ret = datetime.time(13,35)
    elif t < datetime.time(13,40): ret = datetime.time(13,40)
    elif t < datetime.time(13,45): ret = datetime.time(13,45)
    elif t < datetime.time(13,50): ret = datetime.time(13,50)
    elif t < datetime.time(13,55): ret = datetime.time(13,55)
    elif t < datetime.time(14,0): ret = datetime.time(14,0)
    elif t < datetime.time(14,5): ret = datetime.time(14,5)
    elif t < datetime.time(14,10): ret = datetime.time(14,10)
    elif t < datetime.time(14,15): ret = datetime.time(14,15)
    elif t < datetime.time(14,20): ret = datetime.time(14,20)
    elif t < datetime.time(14,25): ret = datetime.time(14,25)
    elif t < datetime.time(14,30): ret = datetime.time(14,30)
    elif t < datetime.time(14,35): ret = datetime.time(14,35)
    elif t < datetime.time(14,40): ret = datetime.time(14,40)
    elif t < datetime.time(14,45): ret = datetime.time(14,45)
    elif t < datetime.time(14,50): ret = datetime.time(14,50)
    elif t < datetime.time(14,55): ret = datetime.time(14,55)
    elif t <= datetime.time(15,0):  ret = datetime.time(15,0)
    else : return None
    if type(dt) == datetime.datetime:
        return datetime.datetime(dt.year,dt.month,dt.day,ret.hour,ret.minute,ret.second)
    else: return ret 

def which5min_all(dt):
    """时间划分"""
    if type(dt) != datetime.datetime and  type(dt) != datetime.time:
        return None
    t = dt
    ret = None
    if type(dt) == datetime.datetime:
        t = datetime.time(dt.hour,dt.minute,dt.second)

    h = t.hour
    m = t.minute
    if h == 23 and m >=55 :
        min5 = 59
    elif h < 23 and m >= 55 :
        min5 = 0
        h += 1
    else:
        min5 = (int(m / 5) + 1) * 5
    if type(dt) == datetime.datetime:
        return datetime.datetime(dt.year,dt.month,dt.day,h,min5,0)
    else:
        return datetime.time(h,min5,0)
    

#############################################################
# read 日线数据文件
# example readDayBin(r'E:\new_gxzq_v6\Vipdoc\sh\lday\sh600000.day')
# return data 格式
# list of dict [{'ID':'stock id','DT':datetime.date,
#  'OPEN':OpenPrice,'HIGH':HighPrice,'LOW':LowPrice,'CLOSE':Price,
#  'VOL':vol,'AMT':amout}] 
# vol 为股而不是手！
#############################################################
def readDayBin(p_name):
    """读日线二进制文件"""
    f = open(p_name,'rb')
    stkid = os.path.split(p_name)[1]
    stkid = os.path.splitext(stkid)[0]
    if stkid[0:2].upper() == 'SH' or stkid[0:2].upper() == 'SZ':
        stkid = stkid[2:]
    icnt = 0
    data = []
    while 1:
        raw = f.read(4*8)
        if len(raw) <= 0 : break
        tmp = struct.unpack('IIIIIfII',raw)
        y = tmp[0] // 10000
        m = (tmp[0] - y*10000 ) // 100
        d = tmp[0] % 100
        data.append({M_ID:stkid,
                     M_DT:datetime.date(y,m,d),
                     M_OPEN:tmp[1] / 100.0,
                     M_HIGH:tmp[2] / 100.0,
                     M_LOW:tmp[3] / 100.0,
                     M_CLOSE:tmp[4] / 100.0,
                     M_AMT:tmp[5] ,
                     M_VOL:tmp[6] ,
                     'UNKOWN':tmp[7]
            
            })
    #end while
    f.close()
    return data

def readDayBinOn(p_name,date):
    """读取某天数据的和前一天的数据 """
    f = open(p_name,'rb')
    stkid = os.path.split(p_name)[1]
    stkid = os.path.splitext(stkid)[0]
    if stkid[0:2].upper() == 'SH' or stkid[0:2].upper() == 'SZ':
        stkid = stkid[2:]
    data = [None,None]
    
    pos = f.seek(-4*8,2) # 从文件末尾向前移动1个记录的位置。

    while 1:
        if pos <= -1:
            break        
        raw = f.read(4*8)
        if len(raw) <= 0 : break
        tmp = struct.unpack('IIIIIfII',raw)
        y = tmp[0] // 10000
        m = (tmp[0] - y*10000 ) // 100
        d = tmp[0] % 100
        dt_tmp = datetime.date(y,m,d)
        if dt_tmp == date :
            data[1]  =  {M_ID:stkid,
                         M_DT:datetime.date(y,m,d),
                         M_OPEN:tmp[1] / 100.0,
                         M_HIGH:tmp[2] / 100.0,
                         M_LOW:tmp[3] / 100.0,
                         M_CLOSE:tmp[4] / 100.0,
                         M_AMT:tmp[5] ,
                         M_VOL:tmp[6] ,
                         'UNKOWN':tmp[7]
            }            
            break
        elif dt_tmp > date :
            try:
                pos = f.seek(-4*8*2,1) # 从当前向前移动2个记录的位置
            except OSError:
                break
        elif dt_tmp < date :
            break
        
    if  data[1] != None:
        try:
            pos = f.seek(-4*8*2,1) # 从当前向前移动2个记录的位置
        except OSError:
            f.close()
            return data    
        raw = f.read(4*8)
        if len(raw) <= 0 : return data
        tmp = struct.unpack('IIIIIfII',raw)
        y = tmp[0] // 10000
        m = (tmp[0] - y*10000 ) // 100
        d = tmp[0] % 100
        dt_tmp = datetime.date(y,m,d)
        data[0]  =  {M_ID:stkid,
                     M_DT:datetime.date(y,m,d),
                     M_OPEN:tmp[1] / 100.0,
                     M_HIGH:tmp[2] / 100.0,
                     M_LOW:tmp[3] / 100.0,
                     M_CLOSE:tmp[4] / 100.0,
                     M_AMT:tmp[5] ,
                     M_VOL:tmp[6] ,
                     'UNKOWN':tmp[7]
        }
        
    f.close()
    return data
        
       
          
    
#############################################################
# write 日线数据文件
# example writeDayBin(p_data,r'E:\new_gxzq_v6\Vipdoc\sh\lday\sh600000.day')
# p_data格式
# list of dict [{'ID':'stock id','DT':datetime.date,
#  'OPEN':OpenPrice,'HIGH':HighPrice,'LOW':LowPrice,'CLOSE':Price,
#  'VOL':vol,'AMT':amout}] 
# vol 为股而不是手！
#############################################################
def writeDayBin(p_data,p_name):
    """写日线二进制文件"""
    f = open(p_name,'wb')
    for i in p_data:
        t = i[M_DT].year * 10000 + i[M_DT].month * 100 + i[M_DT].day
        raw = struct.pack('IIIIIfII',t, round(i[M_OPEN]*100,0),
                                        round(i[M_HIGH]*100,0),
                                        round(i[M_LOW]*100,0),
                                        round(i[M_CLOSE]*100,0),
                                        float(i[M_AMT]),
                                        i[M_VOL],
                                        i.get('UNKOWN',0))
        f.write(raw)    
    # end for
    f.close()





#############################################################
# read 分钟数据文件
# example readlc5(r'E:\new_gxzq_v6\Vipdoc\sh\fzline\sh600000.lc5')
# return data 格式
# list of dict [{'ID':'stock id','DT':(月,日,时,分),
#  'OPEN':OpenPrice,'HIGH':HighPrice,'LOW':LowPrice,'CLOSE':Price,
#  'VOL':vol,'AMT':amout}] 
# vol 为股而不是手！lc5根本就没有记录年！
#############################################################
def readMinBin(p_name):
        """tdx 5min 数据 
           日期上低16位表示月日，高16位表示分钟
           这个结构个人感觉就不如同花顺做的巧妙
               在一个4字节中把 年 月 日 时 分 都记录下来了
        """
        f = open(p_name,'rb')
        stkid = os.path.split(p_name)[1]
        stkid = os.path.splitext(stkid)[0]
        # if string.lower(stkid[0:2]) == 'sh' or string.lower(stkid[0:2]) == 'sz':
        if stkid[0:2].upper() in ['SH','SZ']:
            stkid = stkid[2:]
        icnt = 0
        data = []
        while 1:
            raw = f.read(4*8)
            if len(raw) <= 0 : break
            t = struct.unpack('IfffffII',raw)
            mins = (t[0] >> 16) & 0xffff
            mds  = t[0] & 0xffff
            month = int(mds / 100)
            day   = mds % 100
            hour = int(mins / 60)
            minute = mins % 60
            data.append({M_ID:stkid,
                         M_DT:(month,day,hour,minute),
                         M_OPEN:t[1],
                         M_HIGH:t[2],
                         M_LOW:t[3],
                         M_CLOSE:t[4],
                         M_AMT:t[5],
                         M_VOL:t[6],
                         'UNKOWN':t[7]})
            icnt += 1
        ## end while
        f.close()
        return data

#############################################################
# write通达信5min数据文件
# 传入p_data 结构 如readMinBin 所返回的结构 
#   M_DT 或者为datetime.datetime
#############################################################
def writeMinBin(p_data,p_name):
    fout = open(p_name,'wb')
    for i in p_data:
        if type(i[M_DT]) == datetime.datetime:
            t = i[M_DT].month*100 + i[M_DT].day + ( (i[M_DT].hour * 60 + i[M_DT].minute) << 16)
        else:
            t = i[M_DT][0]*100+i[M_DT][1] + ( (i[M_DT][2] * 60 + i[M_DT][3]) << 16)
        raw = struct.pack('IfffffII',t,i[M_OPEN],i[M_HIGH],i[M_LOW],i[M_CLOSE],i[M_AMT],i[M_VOL],i.get('UNKOWN',0))
        fout.write(raw)
    ## end for
    fout.close()


#############################################################
# read 分钟数据文件
# example readlc5(r'E:\new_gxzq_v6\Vipdoc\sh\fzline\sh600000.lc5')
# return data 格式
# list of dict [{'ID':'stock id','DT':datetime.datetime,
#  'OPEN':OpenPrice,'HIGH':HighPrice,'LOW':LowPrice,'CLOSE':Price,
#  'VOL':vol,'AMT':amout}] 
# vol 为股而不是手！新版本的lc5文件有记录年
#############################################################
def readMinBin_new(p_name):
        """tdx 5min 数据 
           日期上低16位表示年月日，高16位表示分钟
        """
        f = open(p_name,'rb')
        stkid = os.path.split(p_name)[1]
        stkid = os.path.splitext(stkid)[0]
        # if string.lower(stkid[0:2]) == 'sh' or string.lower(stkid[0:2]) == 'sz':
        if stkid[0:2].upper() in ['SH','SZ']:
            stkid = stkid[2:]
        icnt = 0
        data = []
        while 1:
            raw = f.read(4*8)
            if len(raw) <= 0 : break
            t = struct.unpack('IfffffII',raw)
            data.append({M_ID:stkid,
                         M_DT:int2datetime_new(t[0]),
                         M_OPEN:t[1],
                         M_HIGH:t[2],
                         M_LOW:t[3],
                         M_CLOSE:t[4],
                         M_AMT:t[5],
                         M_VOL:t[6],
                         'UNKOWN':t[7]})
            icnt += 1
        ## end while
        f.close()
        return data


#############################################################
# write通达信5min数据文件
# 传入p_data 结构 如readMinBin 所返回的结构 
#   M_DT 或者为datetime.datetime
#############################################################
def writeMinBin_new(p_data,p_name):
    fout = open(p_name,'wb')
    for i in p_data:
        raw = struct.pack('IfffffII',datetime2int_new(i[M_DT]),i[M_OPEN],i[M_HIGH],i[M_LOW],i[M_CLOSE],i[M_AMT],i[M_VOL],i.get('UNKOWN',0))
        fout.write(raw)
    #endfor
    fout.close()



#############################################################
#TODO:
#画线文件的读写增删 使用union也可以
#名称文件的读写增删
#复权文件的解读
#zip TXTFile and
#auto download
#############################################################
## 名称文件的解析
#############################################################
NAME_FILE_HEAD_LEN = 50
class T_TdxNames(ct.Structure):
    """ 
    这个结构使用于shex.tnf szex.tnf
    """
    _pack_      = 1
    _fields_ = [
                ("stkid", ct.c_char * 9),  # stkid
                ("un1", ct.c_byte ),
                ("un2", ct.c_char*2), 
                ("un3", ct.c_float), # 未知
                ("un4", ct.c_int), # 
                ("un5", ct.c_int), # 
                ("stkname", ct.c_char * 18), # name
                ("un6", ct.c_int), # 
                ("un7", ct.c_char * 186),
                ("lastclose", ct.c_float), # 前日收盘
                ("un8", ct.c_byte),
                ("un9", ct.c_int),
                ("shortname", ct.c_char*9)   #缩写
                ]       

class T_TdxNames_m(ct.Structure):
    """ 
    这个结构使用于shm.tnf szm.tnf
    """
    _pack_      = 1
    _fields_ = [
                ("stkid", ct.c_char * 23),  # stkid
                ("stkname", ct.c_char * 49), # name
                ("un1", ct.c_byte * 205), # 
                ("lastclose", ct.c_float), # 前日收盘
                ("un2", ct.c_int), # 
                ("shortname", ct.c_char* 29)   #缩写
                ]       


def get_tdxNames(fname,Bsimple = True):
    data = []
    try:
        f = open(fname,'rb')
    except IOError as e:
        return data
    else:
        f.seek(NAME_FILE_HEAD_LEN)
        itemlen = ct.sizeof(T_TdxNames)
        while True:
            raw = f.read(itemlen)
            if len(raw) <= 0 : break
            nn = stream2struct(raw,T_TdxNames)
            if Bsimple:
                data.append((nn.stkid.decode('gbk'),nn.stkname.decode('gbk'),nn.shortname.decode('gbk')))
            else:
                data.append((nn.stkid.decode('gbk'),nn.un1,nn.un2,nn.un3,nn.un4,nn.un5,
                    nn.un6,nn.un7,nn.lastclose,nn.stkname.decode('gbk'),nn.un8,nn.un9,
                    nn.shortname.decode('gbk')))

        f.close()
        return data

## 沪深两市的股票代码
## 沪市 6*
## 深市 0* 30*        
def id_is_stock(x):
    if x.startswith('SH6') or x.startswith('SZ0') or x.startswith('SZ30'):
        return True
    else:
        return False

def get_tdxNames_return_list(root,filt = True):
    res = []
    fname1 = os.path.join(root,r'T0002\hq_cache\shm.tnf')
    fname2 = os.path.join(root,r'T0002\hq_cache\szm.tnf')
    data = get_tdxNames_m(fname1)
    for item in data:
        stkid = 'SH' + item[0]
        if filt == True and id_is_stock(stkid) or filt == False:
            res.append((stkid,item[1]))
    data = get_tdxNames_m(fname2)
    for item in data:
        stkid = 'SZ' + item[0]
        if filt == True and id_is_stock(stkid) or filt == False:
            res.append((stkid,item[1]))
    return res 
    
def get_tdxNames_return_dict(root,filt = True):
    res = {}
    data = get_tdxNames_return_list(root,filt = True)
    for item in data:
        res[item[0]] = item[1]
    return res 

def bin2gbk(bin:bytes):
    ss = ""
    try:
        ss = bin.decode('gbk')
    except UnicodeDecodeError:
        if len(bin) > 2:
            ss = bin[0:-1].decode('gbk')
    return ss

def get_tdxNames_m(fname,Bsimple = True):
    data = []
    try:
        f = open(fname,'rb')
    except IOError as e:
        return data
    else:
        f.seek(NAME_FILE_HEAD_LEN)
        itemlen = ct.sizeof(T_TdxNames_m)
        while True:
            raw = f.read(itemlen)
            if len(raw) <= 0 : break
            nn = stream2struct(raw,T_TdxNames_m)
            stkid     = bin2gbk(nn.stkid)
            stkname   = bin2gbk(nn.stkname)
            shortname = bin2gbk(nn.shortname)
            data.append((stkid,stkname,shortname))
            # try:
            #     data.append((nn.stkid.decode('gbk'),nn.stkname.decode('gbk'),nn.shortname.decode('gbk')))
            # except UnicodeDecodeError as e:
            #     print(f"ID:{nn.stkid} name:{nn.stkname} shortname:{nn.shortname}  with error:{e}" )
            #     continue
            #data.append((nn.stkid,nn.stkname,nn.shortname))

        f.close()
        return data




if __name__ == '__main__':
    print( 'test begin ')
    TDX_ROOT = r'D:\stock\new_gxzq_v6'
    fname = os.path.join(TDX_ROOT,r'T0002\hq_cache\shex.tnf')
    fname2 = os.path.join(TDX_ROOT,r'T0002\hq_cache\shm.tnf')
    fdir = r'D:\stock\new_gxzq_v6\vipdoc\sz\lday'
    data = []
    icnt = 0
    flist = os.listdir(fdir)
    #flist = [r'SZ000018.day']
    for f in flist:
        if len(f) <= 4 :
            continue
        icnt +=1
        stkid,fext = os.path.splitext(f)
        fext = fext.lower()
        stkid = stkid.upper()

        if fext.endswith('.day') :
            fullname = os.path.join(fdir,f)
            dd = readDayBinOn(fullname,datetime.date(2021, 8, 27))
            if dd[0] == None or dd[1] == None:
                pass
            else:
                rate = (dd[1][M_CLOSE] - dd[0][M_CLOSE] ) / dd[0][M_CLOSE]
                data.append((stkid,rate))
    data.sort()
    for item in data:
         print(item)
    #data = readDayBinOn(fname,datetime.date(2021, 8, 27))
    #data = get_tdxNames_return_dict(TDX_ROOT)
    #data = get_tdxNames_return_dict(TDX_ROOT)
    #print(data)
