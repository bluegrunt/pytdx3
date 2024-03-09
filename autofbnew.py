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


## todo : �����ļ����ж�



#############################################################
# zipfiles ��export�µ��ļ�ѹ��Ϊ zip�ļ�
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
        #zipfile ��bug:�ļ�������ʱ��a ȥ׷��ʱ������
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
                shortname = shortname.replace('_','-')  #�������ϵͳһ��
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
#��ȡ��ǰ����Title
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
    """��ȡ���һ������������ """
    today = datetime.date.today()
    wkd = today.weekday()
    if wkd == 5 : # ����
        return today - datetime.timedelta(days=2)
    elif wkd == 6 : # ����
        return today - datetime.timedelta(days=3)
    elif wkd == 0 : # ��һ
        return today - datetime.timedelta(days=3)
    else:
        return today - datetime.timedelta(days=1)

def tdx_sendkeys(exp_dir,loghandle = sys.stderr,conf = None,lastday = None):
    """tdx send keys to download text files"""
    
    #                    ����     ����           ��       ��       ��
    #pymd = re.compile(r'^(.*)\((\d{3,9})\)\s+(\d{4})��(\d{2})��(\d{2})��')
    pymd = re.compile(r'^(.*)\((\d{3,9})\)\s+(\d{4}).*(\d{2}).*(\d{2}).*')
    ## Ĭ�ϵ�����
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
        else: # ��ʼ����
            ##
            b_has_entered = True
            name1,stkid,stky,stkm,stkd=mm.groups()
            date_str = "%s%s%s" % (stky,stkm,stkd)
            if date_str > lastday_str:
                print('��ָ���ջ����һ����')
                zipfiles(exp_dir)
                return
            # 20050523-999999.TXT
            ftxt = stky+stkm+stkd+'-'+stkid+'.TXT'
            ftxt_new = stky+stkm+stkd+'_'+stkid+'.txt'  #�°��ļ������ı�
            ftxt_xls = stky+stkm+stkd+'_'+stkid+'.xls'  #�°��ļ������ı�
            longtxt = os.path.join(exp_dir,ftxt)
            longtxt_new = os.path.join(exp_dir,ftxt_new)
            longtxt_xls = os.path.join(exp_dir,ftxt_xls)
            if os.path.exists(longtxt_new) or os.path.exists(longtxt):
                SendKeys.SendKeys("{PGDN}",0.8)  #pagedown ������һ�� 
                continue
            elif os.path.exists(longtxt_xls):
                try:
                    os.rename(longtxt_xls,longtxt_new)
                except :
                    pass
                SendKeys.SendKeys("{PGDN}",0.8)  #pagedown ������һ�� 
                continue

            if len(zipedFiles) == 0:  ## ���������ļ���ziplist
                zipname = os.path.join(exp_dir,stkid+'.zip')       
                for ff in get_zipedFileList(zipname):
                    zipedFiles[ff] = 1
            if zipedFiles.get(ftxt,None) != None:
               SendKeys.SendKeys("{PGDN}",0.8)  #pagedown ������һ�� 
               continue
            ## ������ʽ�����ļ�
            macro.move(pos_caozuo[0], pos_caozuo[1])         #�ƶ���������           
            time.sleep(0.4)
            macro.click()                #�����򿪲˵�
            time.sleep(0.4)
            macro.move(pos_daochu[0], pos_daochu[1])         #�ƶ����������ݴ�
            time.sleep(0.3)
            SendKeys.SendKeys("{ENTER}") #�س� ���������Ի���
            SendKeys.SendKeys("{ENTER}") #�س� ��ʼ����        
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
            
            if os.path.exists(longtxt_new) or os.path.exists(longtxt): # ���سɹ�
                SendKeys.SendKeys("{PGDN}",0.8)  #pagedown ������һ��
                l_try = 0 #��0��
                #icnt +=1
            elif os.path.exists(longtxt_xls):
                os.rename(longtxt_xls,longtxt_new)
                SendKeys.SendKeys("{PGDN}",0.8)  #pagedown ������һ��
                l_try = 0 #��0��
            else:
                l_try += 1
                if l_try < max_try:
                    sys.stderr.write("���Ե� %d ��\n" % (l_try + 1 ))            
                else:
                    SendKeys.SendKeys("{PGDN}",0.4)   #pagedown ������һ��
                    l_try = 0 #��0��
                    msg = "Fail: %s at %s%s%s can not download\n" % (stkid,stky,stkm,stkd)
                    loghandle.write(msg)
                    loghandle.flush()
                    if loghandle != sys.stderr:
                        sys.stderr.write(msg)

#############################################################
# usage ʹ��˵��
# exec("1.12/12") exec ִ��
#############################################################

def usage(p):
    print(r"""
python %s
-z --zip        ѹ��text to zip
-d --deltxt     ѹ����ɾ��
-r --root=RootDIR          ����root��Ĭ��Ϊ os.getcwd()
-l --logfile=logfile       ����log�ļ�
-c --configfile=configfile ���ð����������ļ�
-e --endday=YYYYmmdd       ���ð���������ֹ��
-g --getpostion            ��õ�ǰ����λ��
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
            # only ѹ��
            zipfiles(exp_dir, False)
            sys.exit(0)
        elif opt in ('-d',"--deltxt"):
            # ѹ�� ɾ��
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



