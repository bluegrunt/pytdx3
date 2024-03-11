import PySimpleGUI as sg
import os.path
import configparser
from tdx_tool import Tdx,TdxMin,TdxNames

options = {
    'font': ('MS Sans Serif', 10, 'bold'),
    'button_color': ('red', 'white'),
    'format': '%Y-%m-%d',
    'close_when_date_chosen': True,
}


layout1 = [
    [sg.VPush()],
    [sg.Push(),sg.Text('ID:'),sg.Input(key='-INPUT_ID-',size=(10,1)),sg.Text('......',key='-STKNAME-',size=(16,1)),sg.Push()],
    [
        sg.Push(),
        sg.Push(),sg.Text('From:'),
        sg.Input(key='-DATE1-', enable_events=True,size=(10,1)),
        sg.CalendarButton('@', target='-DATE1-', key='CALENDAR1',size=(2,1), **options),
        sg.Push(),sg.Text('  To:'),
        sg.Input(key='-DATE2-', enable_events=True,size=(10,1)),
        sg.CalendarButton('@', target='-DATE2-', key='CALENDAR2',size=(2,1), **options),
        sg.Push()
    ],
    [
        sg.Push(),sg.Checkbox("1分钟",key='-MIN1-', default=True),
        sg.Checkbox("5分钟",key='-MIN5-',default=True),
        sg.Push(),
        sg.Checkbox("tdx240",key='-TDX240-',default=False),
        sg.Push()
    ],
    [sg.Push(),sg.Button("处理",key='-CONVERT-'),sg.Push()],
    [sg.ProgressBar(100,key='-PROCESSBAR-',expand_x=True,size=(16,3),bar_color='blue')],
    [sg.VPush()],
    [sg.Multiline(key='-OUTPUT-',expand_x=True,expand_y=True,size=(20,2))],
    [sg.VPush()]
]

## offline path is the work path 
## online path is a place where the txtfile from.
## if online path is None, it will be set equal to offline path.

layout2 = [
    [sg.VPush()],
    [sg.Text('Offline Path:'),sg.Input(expand_x=True,key='-INPUT_OFFLINE-'),sg.Button("@",size=(2,1),key="-BUTTON_OFFLINE-")],
    [sg.Text('Online Path:') ,sg.Input(expand_x=True,key='-INPUT_ONLINE-') ,sg.Button("@",size=(2,1),key="-BUTTON_ONLINE-") ],
    [sg.VPush()],
    [sg.Push(),sg.Button("保存配置",key='-SAVE-'),sg.Push()],
    [sg.VPush()],
]

layout = [
    [sg.TabGroup([[sg.Tab('process', layout1),sg.Tab('config',layout2)]])]
]

window = sg.Window('Tdx Minute data generator',layout,finalize=True)
window['-INPUT_ID-'].bind("<Return>", "_Enter")
eventBind1 = "-INPUT_ID-" + "_Enter"
#-----------------------

#-----------------------
offlinePath = ""
onlinePath  = ""
cfg_file = os.path.join(os.getcwd() ,'tdx_conf.ini')
cfg = configparser.ConfigParser()
stkid = "SH999999"
datefrom = ""
dateto = ""
stkname = ""
output_list = []
process_percent = 0
# offlinePath = os.getcwd()
# onlinePath  = os.getcwd()

try:
    cfg.read(cfg_file)
    offlinePath = cfg.get('config','offlinePath')
    onlinePath  = cfg.get('config','onlinePath')
    stkid = cfg.get('hist','stkid')
    datefrom = cfg.get('hist','datefrom')
    dateto = cfg.get('hist','dateto')
except:
    offlinePath = os.getcwd()
    onlinePath  = offlinePath

print(f"offline path is : {offlinePath}")
print(f"online  path is : {onlinePath}")
namedict = {}
if os.path.exists(offlinePath):
    offlineTdxNames = TdxNames(offlinePath)
# onlineTdxNames  = TdxNames(onlinePath)
    namedict = offlineTdxNames.get_id_mostuse()
stkname = namedict.get(stkid,'')
#-----------------------
window['-INPUT_ID-'].update(stkid)
window['-STKNAME-'].update(stkname)
window['-DATE1-'].update(datefrom)
window['-DATE2-'].update(dateto)

window['-INPUT_OFFLINE-'].update(offlinePath)
window['-INPUT_ONLINE-'].update(onlinePath)
#-----------------------

def after_ct_stkid():
    global stkid,namedict,window,stkname
    stkid = window['-INPUT_ID-'].get()
    if len(stkid) == 6 and not stkid.startswith('SH') and not stkid.startswith('SZ'):
        if namedict.get('SH' + stkid,'') != "":
            stkid = 'SH' + stkid
        elif namedict.get('SZ' + stkid,'') != "":
            stkid = 'SZ' + stkid
    stkname = namedict.get(stkid,'')

#@ sdatefrom format YYYYMMDD
#@ sdateto   format YYYYMMDD
def convert(stkid,sdatefrom,sdateto,b_min1=True,b_min5=True,b_tdx240=True):
    """main convert function."""
    global window,output_list
    output_list = []
    mkt = stkid[0:2].upper()
    shortid = stkid[2:]
    if not mkt in ['SH','SZ']:
        sg.popup_error("仅支持市场代码SH SZ")
        return 
    output_list = []
    if not b_min1 and not b_min5 :
        sg.popup_error("请至少勾选min1 或者min5")
        return
    # onlineTdxMin = TdxMin(onlinePath,TdxOut=output_list,sgWindow=window)
    onlineTdxMin = TdxMin(onlinePath,TdxOut=None,sgWindow=window)
    offlineTdx   = Tdx(offlinePath)  
    onlineTdx    = Tdx(onlinePath)  
    onlineTdxMin.setID(mkt,shortid)
    cnt = onlineTdxMin.readFromText(sdatefrom,sdateto,b_tdx240)
    if b_min1:
        fname = os.path.join(offlineTdx.Min1BinPaths[onlineTdxMin.mkt],onlineTdxMin.mkt + onlineTdxMin.stkid + '.lc1')
        onlineTdxMin.writeMin1ToBin(fname)
    if b_min5:
        fname = os.path.join(offlineTdx.Min5BinPaths[onlineTdxMin.mkt],onlineTdxMin.mkt + onlineTdxMin.stkid + '.lc5')
        onlineTdxMin.writeMin5ToBin(fname)
    output_list.append(f"{cnt} days data converted!")

    
#-----------------------
while True:
    event,values = window.read()
    if event == sg.WIN_CLOSED:
        ## save history
        if not cfg.has_section('hist'):
            cfg.add_section('hist')
        cfg.set('hist','stkid',stkid)
        cfg.set('hist','datefrom',datefrom)
        cfg.set('hist','dateto',dateto)
        try:
            f = open(cfg_file,"w")
            cfg.write(f)
        except IOError:
            sg.popup_error(f"open file {cfg_file} error.")
        finally:
            f.close()
            # close(f)
        break
    # --------------
    if values['-INPUT_OFFLINE-'] != "":
        offlinePath = values['-INPUT_OFFLINE-']
    if values['-INPUT_ONLINE-']  != "":
        onlinePath  = values['-INPUT_ONLINE-']
    # --------------
    if onlinePath == "":
        onlinePath = offlinePath
        window['-INPUT_ONLINE-'].update(onlinePath)
    if event == '-CONVERT-':
        ## check the path 
        window['-OUTPUT-'].update("====================================")
        if offlinePath == "" :
            sg.popup_error("请先在config页签设定offline root path.")
            continue
        if not os.path.exists(offlinePath):
            sg.popup_error("Tdx root path not exists.")
            continue

        after_ct_stkid()
        stkid = values['-INPUT_ID-']
        datefrom = values['-DATE1-']
        dateto = values['-DATE2-']
        b_min1 = values['-MIN1-']
        b_min5 = values['-MIN5-']
        b_tdx240 = values['-TDX240-']
        stkname = namedict.get(stkid,'')
        if stkid == '' :
            sg.popup_error("请输入正确的stkid")
            continue
        sdatefrom = datefrom.replace("-","")
        sdateto   = dateto.replace("-","")
        if len(sdatefrom) != 8 or len(sdateto) != 8 :
            sg.popup_error(f"invalid datefrom or dateto: {datefrom} {dateto}")
            continue
        if sdatefrom > sdateto :
            sg.popup_error(f"datefrom {datefrom} must not bigger than dateto {dateto}")
            continue
        convert(stkid,sdatefrom,sdateto,b_min1,b_min5,b_tdx240)
        # print(output_list)
        window['-OUTPUT-'].update("\n".join(output_list))
    elif event == '-SAVE-':
        if not cfg.has_section('config'):
            cfg.add_section('config')
        offlinePath = window['-INPUT_OFFLINE-'].get()
        onlinePath  = window['-INPUT_ONLINE-'].get()
        cfg.set('config','offlinePath',values['-INPUT_OFFLINE-'])
        cfg.set('config','onlinePath' ,values['-INPUT_ONLINE-'])
        try:
            f = open(cfg_file,"w")
            cfg.write(f)
        except IOError:
            sg.popup_error(f"open file {cfg_file} error.")
        finally:
            f.close()
            # close(f)

    elif event == '-BUTTON_OFFLINE-':
        offlinePath = sg.popup_get_folder("Open",no_window=True)
        window['-INPUT_OFFLINE-'].update(offlinePath)
    elif event == '-BUTTON_ONLINE-':
        onlinePath = sg.popup_get_folder("Open",no_window=True)
        window['-INPUT_ONLINE-'].update(onlinePath)
    elif event == eventBind1 :
        # print('set stkid with prefix and get stk name. ')
        after_ct_stkid()
        window['-INPUT_ID-'].update(stkid)
        window['-STKNAME-'].update(stkname)
    
window.close()

if __name__ == "__main__":
    print('----------------------------')
