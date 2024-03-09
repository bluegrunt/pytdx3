#!/usr/bin/python
#-*- encoding: gbk -*- 
import ctypes
#import win32gui
#import win32con
import macro
import SendKeys
import os,time,re,sys,glob
import zipfile,datetime
import getopt,configparser


## todo : 存在文件的判断



#############################################################
# zipfiles 将export下的文件压缩为 zip文件
# 
#############################################################
def zipfiles(exp_dir , deltxt = False):
    tdx_newversion = False
    txtfiles = glob.glob(os.path.join(exp_dir,'*-*.TXT'))
    if len(txtfiles) == 0 :
        txtfiles = glob.glob(os.path.join(exp_dir,'*_*.txt'))
        txtfiles = list(map(lambda x:x.upper(),txtfiles))
        if len(txtfiles) > 0 :
            tdx_newversion = True
    splitby = '-'
    if tdx_newversion:
        splitby = '_'
    stkids = set(map(lambda x:os.path.splitext(os.path.split(x)[1])[0].split(splitby)[1],txtfiles))
    stkids = list(stkids)
    
    for n,txt in enumerate(txtfiles):
        if not txt.endswith('.TXT'):
            txtfiles[n] = os.path.splitext(txt)[0] + '.TXT'

    stkids.sort()
    #stkids = ['000002','000099']
    for i in stkids:
        print('build '+i+'.zip,please wait......')
        fout = os.path.join(exp_dir,i+'.zip')
        #zipfile 的bug:文件不存在时，a 去追加时，报错！
        if os.path.exists(fout):
            fzip  = zipfile.ZipFile(fout,'a' ,zipfile.ZIP_DEFLATED)
        else:
            fzip  = zipfile.ZipFile(fout,'w' ,zipfile.ZIP_DEFLATED)
        zipednames = fzip.namelist()
        zipedFiles = {}
        for ff in zipednames:
            zipedFiles[ff] = 1
        thisfiles = list(filter(lambda x: splitby + i in x and x.endswith('.TXT'),txtfiles))
        thisfiles.sort()
        b_succ = True
        try :
            for j in thisfiles:
                shortname = os.path.split(j)[1]
                shortname = shortname.replace('_','-')  #保持与旧系统一致
                #if shortname in zipednames:
                if zipedFiles.get(shortname,None) != None:
                    print('\t',shortname,'had ziped,pass')
                else:
                    fzip.write(j,shortname)
            fzip.close()
        except IOError:
            b_succ = False

        if deltxt and b_succ:
            for j in thisfiles:
                    try :
                        os.unlink(j)
                    except IOError :
                        pass

############################################################
#获取当前窗口Title
############################################################
def GetForegroundWindowName():
    #hwnd = win32gui.GetForegroundWindow()
    #return win32gui.GetWindowText(hwnd)
    GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    GetWindowText = ctypes.windll.user32.GetWindowTextW

    act_id = GetForegroundWindow()
    length = GetWindowTextLength(act_id)
    buff = ctypes.create_unicode_buffer(length + 1)
    GetWindowText(act_id, buff, length + 1)
    return buff.value

def get_zipedFileList(zipname):
    try :
        fzip = zipfile.ZipFile(zipname)
    except IOError as e:
        return []
    else:
        return fzip.namelist()

def get_lastDayCan():
    """获取最后一个可下载日期 """
    today = datetime.date.today()
    wkd = today.weekday()
    if wkd == 5 : # 周六
        return today - datetime.timedelta(days=2)
    elif wkd == 6 : # 周日
        return today - datetime.timedelta(days=3)
    elif wkd == 0 : # 周一
        return today - datetime.timedelta(days=3)
    else:
        return today - datetime.timedelta(days=1)

def tdx_sendkeys(exp_dir,loghandle = sys.stderr,conf = None,lastday = None):
    """tdx send keys to download text files"""
    
    #                    名称     代码           年       月       日
    #pymd = re.compile(r'^(.*)\((\d{3,9})\)\s+(\d{4})年(\d{2})月(\d{2})日')
    pymd = re.compile(r'^(.*)\((\d{3,9})\)\s+(\d{4}).*(\d{2}).*(\d{2}).*')
    ## 默认的配置
    max_try = 3
    max_waitsecs = 10
    pos_caozuo = (418, 434)
    pos_daochu = (458, 647)    
    if lastday == None:
        lastday = get_lastDayCan()
    lastday_str = lastday.strftime('%Y%m%d')
    if conf != None:
        try :
            cfg = configparser.ConfigParser()
            cfg.read(conf)
            max_try = int(cfg.get('sendkey','max_try'))
            max_waitsecs = int(cfg.get('sendkey','max_waitsecs'))
            pos_caozuo = eval(cfg.get('sendkey','pos_caozuo'))
            pos_daochu = eval(cfg.get('sendkey','pos_daochu'))
        except :
            pass

    l_try = 0
    zipedFiles = {}
    b_has_entered = False
    if not os.path.isdir(exp_dir):
        sys.stderr.write('%s is not a dir\n ' % exp_dir)
        return

    while 1:
        title = GetForegroundWindowName()
        mm = pymd.search(title)
        if mm == None :
            print(title)
            zipedFiles = {}
            l_try = 0
            if b_has_entered : 
                zipfiles(exp_dir)
                break
            time.sleep(1)
        else: # 开始按键
            ##
            b_has_entered = True
            name1,stkid,stky,stkm,stkd=mm.groups()
            date_str = "%s%s%s" % (stky,stkm,stkd)
            if date_str > lastday_str:
                print('到指定日或最后一日了')
                zipfiles(exp_dir)
                return
            # 20050523-999999.TXT
            ftxt = stky+stkm+stkd+'-'+stkid+'.TXT'
            ftxt_new = stky+stkm+stkd+'_'+stkid+'.txt'  #新版文件有所改变
            ftxt_xls = stky+stkm+stkd+'_'+stkid+'.xls'  #新版文件有所改变
            longtxt = os.path.join(exp_dir,ftxt)
            longtxt_new = os.path.join(exp_dir,ftxt_new)
            longtxt_xls = os.path.join(exp_dir,ftxt_xls)
            if os.path.exists(longtxt_new) or os.path.exists(longtxt):
                SendKeys.SendKeys("{PGDN}",0.8)  #pagedown 换到下一日 
                continue
            elif os.path.exists(longtxt_xls):
                try:
                    os.rename(longtxt_xls,longtxt_new)
                except :
                    pass
                SendKeys.SendKeys("{PGDN}",0.8)  #pagedown 换到下一日 
                continue

            if len(zipedFiles) == 0:  ## 建立已有文件的ziplist
                zipname = os.path.join(exp_dir,stkid+'.zip')       
                for ff in get_zipedFileList(zipname):
                    zipedFiles[ff] = 1
            if zipedFiles.get(ftxt,None) != None:
               SendKeys.SendKeys("{PGDN}",0.8)  #pagedown 换到下一日 
               continue
            ## 否则正式下载文件
            macro.move(pos_caozuo[0], pos_caozuo[1])         #移动到操作处           
            time.sleep(0.4)
            macro.click()                #单击打开菜单
            time.sleep(0.4)
            macro.move(pos_daochu[0], pos_daochu[1])         #移动到导出数据处
            time.sleep(0.3)
            SendKeys.SendKeys("{ENTER}") #回车 弹出导出对话框
            SendKeys.SendKeys("{ENTER}") #回车 开始导出        
            l_j = 0
            print(os.path.join(exp_dir,ftxt_new))
            while l_j  < max_waitsecs * 10 :
                time.sleep(0.2)
                # if os.path.exists(os.path.join(exp_dir,ftxt_new)) or os.path.exists(os.path.join(exp_dir,ftxt)) : break 
                if os.path.exists(longtxt_xls) or os.path.exists(longtxt_new) or os.path.exists(longtxt):
                    break
                l_j += 1
                if l_j % 10 == 0 and  l_j / 10.0 >=3 : 
                    print('\t',l_j / 10.0)
            SendKeys.SendKeys("{ESC}",0.4)   #esc
            
            if os.path.exists(longtxt_new) or os.path.exists(longtxt): # 下载成功
                SendKeys.SendKeys("{PGDN}",0.8)  #pagedown 换到下一日
                l_try = 0 #归0！
                #icnt +=1
            elif os.path.exists(longtxt_xls):
                os.rename(longtxt_xls,longtxt_new)
                SendKeys.SendKeys("{PGDN}",0.8)  #pagedown 换到下一日
                l_try = 0 #归0！
            else:
                l_try += 1
                if l_try < max_try:
                    sys.stderr.write("尝试第 %d 次\n" % (l_try + 1 ))            
                else:
                    SendKeys.SendKeys("{PGDN}",0.4)   #pagedown 换到下一日
                    l_try = 0 #归0！
                    msg = "Fail: %s at %s%s%s can not download\n" % (stkid,stky,stkm,stkd)
                    loghandle.write(msg)
                    loghandle.flush()
                    if loghandle != sys.stderr:
                        sys.stderr.write(msg)

#############################################################
# usage 使用说明
# exec("1.12/12") exec 执行
#############################################################

def usage(p):
    print(r"""
python %s
-z --zip        压缩text to zip
-d --deltxt     压缩后并删除
-r --root=RootDIR          设置root，默认为 os.getcwd()
-l --logfile=logfile       设置log文件
-c --configfile=configfile 设置按键的配置文件
-e --endday=YYYYmmdd       设置按键的最后截止日
-g --getpostion            获得当前光标的位置
    """ % p)


if __name__ == '__main__':
    argv = sys.argv[1:]
    # root = r'D:\stock\new_gxzq_v6'  # default root
    root = os.getcwd()  # default root
    try:
        loghandle = open('autolog.txt','a')
    except IOError:
        loghandle = sys.stderr

    cfg_file = "tdx_conf.ini"
    endday = get_lastDayCan()

    cfg = configparser.ConfigParser()
    try:
        cfg.read(cfg_file)
        root  = cfg.get('config','onlinePath')
    except:
        root = os.getcwd()
    
    try : 
        opts, args = getopt.getopt(argv, "hzdgr:l:c:e:", ["help", "zip","deltxt","getpostion","root=","logfile=","configfile=","endday="])
    except getopt.GetoptError:
        usage(sys.argv[0])
        sys.exit(0)    
    
    for opt, arg in opts:
        if opt in ('-r','--root'):
            root = arg
        elif opt in ('-l','--logfile'):
            try :
                loghandle = open(arg,'a')
            except IOError:
                pass
        elif opt in ('-c','--configfile'):
            cfg_file = arg
        elif opt in ('-e','--endday'):
            try:
                endday = datetime.datetime.strptime(arg,"%Y%m%d").date()
            except :
                pass

    exp_dir = os.path.join(root,r'T0002\export')
    for opt, arg in opts:                
        if opt in ("-h", "--help"): 
            usage(sys.argv[0])
            sys.exit(0)
        elif opt in ('-z',"--zip"):
            # only 压缩
            zipfiles(exp_dir, False)
            sys.exit(0)
        elif opt in ('-d',"--deltxt"):
            # 压缩 删除
            zipfiles(exp_dir, True)
            gs_bak = os.path.join(root,r'T0002/gs_bak')
            try:
                for f in os.listdir(gs_bak):
                    fullName = os.path.join(gs_bak,f)
                    print(fullName)
                    os.remove(fullName)
            except IOError:
                pass
            sys.exit(0)
        elif opt in ('-g',"--getpostion"):
            try:
                while True:
                    print(macro.getpos())
                    time.sleep(0.5)
            except KeyboardInterrupt:
                print('Stop by User.')
                sys.exit(0)
                
    try:
        if loghandle != sys.stderr:
            loghandle.write("=====================%s=====================\n" % str(datetime.datetime.now()))
        tdx_sendkeys(exp_dir,loghandle,cfg_file,endday)
    except KeyboardInterrupt:
        print('Stop by User. Now zip the text:')
        zipfiles(exp_dir, True)
        print('=' * 72)
    finally :
        if loghandle != sys.stderr and not loghandle.closed:
            loghandle.close()



