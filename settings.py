from typing import Literal
import tkinter as tk
import keyring
import json
import requests

FLUSH_DEFAULTS_NOW = False # & then exit

modelsApiNames = {
    '3 flash': 'google/gemini-3-flash-preview', # $3 Good for everething
    '3 flash lite': 'google/gemini-3.1-flash-lite-preview', # $1.75 very quick, good for easy problems
    '2.5 flash': 'google/gemini-2.5-flash', # $2.5 I think better to use 3 flash for $0.5 more
    '3.1 pro': 'google/gemini-3.1-pro-preview', # $14 Expensive
}

modelsAvailable = Literal[
    '3 flash', '3 flash lite', '2.5 flash', '3.1 pro'
]

reasoningEfforts = Literal[
    'minimal', 'low', 'medium', 'high', 'none'
]

defaultSettings = {
    'selectedModel': '3 flash',
    'reasoningLevel': 'minimal',
    'closingDelay': 20,
    'soundWhenDone': True,
    'autoSubmitAnswer': False,
    'loopSolving': False,
    'autoScreenshot': False
}

def access(mode:Literal['get', 'set', 'del'], var:str, to:str|None=None):
    """Access to global variables. Stored in system keyring"""
    APP_NAME = '_HYPERSOLVER'
    if mode == 'get':
        return keyring.get_password(APP_NAME, var)
    elif mode == 'set':
        if to is None:
            print("Value to set must be provided")
            return
        keyring.set_password(APP_NAME, var, to)
    elif mode == 'del':
        try:
            keyring.delete_password(APP_NAME, var)
        except:
            pass

if FLUSH_DEFAULTS_NOW:
    access('set', 'settings', json.dumps(defaultSettings))
    print('Default settings flushed, exiting now')
    exit()

def getsettings():
    sett = access('get', 'settings')
    if sett is not None:
        try:
            sett = json.loads(sett)
        except:
            print('Failed to load settings, using default')
            sett = None
        
    if sett is None:
        sett = defaultSettings

    return sett

def saveSettings(settings:dict):
    access('set', 'settings', json.dumps(settings))

settings = getsettings()

BG = 'gray20'

se = tk.Tk()
se.title("HyperSolver | Labels are clickable | ⌘Q will also save")
se['bg'] = BG

windowW = 500
windowH = 155

screenW = se.winfo_screenwidth()
screenH = se.winfo_screenheight()

Cx = int(screenW / 2 - windowW / 2)
Cy = int(screenH / 2 - windowH / 2)

se.geometry(f"{windowW}x{windowH}+{Cx}+{Cy}")

tk.Label(se, text='select model:', bg=BG, fg='gray60').place(x=5, y=2)

def setModel(model:str):
    global selectedModel
    settings['selectedModel'] = model
    labelsModels[model].config(fg='lime')
    for m in modelsApiNames.keys():
        if m != model:
            labelsModels[m].config(fg='white')

labelsModels = {}
for model in modelsApiNames.keys():
    l = tk.Label(se, text=model, fg='lime' if model == settings['selectedModel'] else 'white', font=('Arial', 16), bg=BG)
    l.place(x=5, y=22 + 22*list(modelsApiNames.keys()).index(model))
    labelsModels[model] = l
    l.bind('<Button-1>', lambda e, m=model: setModel(m))

tk.Label(se, text='select reasoning:', bg=BG, fg='gray60').place(x=120, y=2)

def setReasoningLevel(level:str):
    global reasoningLevel
    settings['reasoningLevel'] = level
    labelsReasoning[level].config(fg='lime')
    for m in reasoningEfforts.__args__:
        if m != level:
            labelsReasoning[m].config(fg='white')

labelsReasoning = {}
for level in reasoningEfforts.__args__:
    l = tk.Label(se, text=level, fg='lime' if level == settings['reasoningLevel'] else 'white', font=('Arial', 15), bg=BG)
    l.place(x=120, y=22 + 21*list(reasoningEfforts.__args__).index(level))
    labelsReasoning[level] = l
    l.bind('<Button-1>', lambda e, lvl=level: setReasoningLevel(lvl))

def toggleSetting(setting:str):
    currentValue = settings[setting]
    new = not currentValue
    settings[setting] = new
    match setting:
        case 'soundWhenDone':    settings['soundWhenDone'] = new
        case 'autoSubmitAnswer': settings['autoSubmitAnswer'] = new
        case 'loopSolving':      settings['loopSolving'] = new
        case 'autoScreenshot':   settings['autoScreenshot'] = new

    labelsSettings[setting].config(fg='lime' if new else 'red')

tk.Label(se, text='settings:', bg=BG, fg='gray60').place(x=250, y=2)
labelsSettings = {}

def setClosingDelay(val:int):
    global closingDelay
    settings['closingDelay'] = val

tk.Label(se, text='closingDelay (s):', font=('Arial', 15), bg=BG).place(x=250, y=22)
tk.Scale(se, from_=0, to=60, orient='horizontal', command=lambda val: setClosingDelay(int(val)), bg=BG, variable=tk.IntVar(value=settings['closingDelay'])).place(x=370, y=6, width=120)

for setting in ['soundWhenDone', 'autoSubmitAnswer', 'loopSolving', 'autoScreenshot']:
    l = tk.Label(se, text=setting, fg='lime' if settings[setting] else 'red', font=('Arial', 15), bg=BG)
    l.place(x=250, y=47 + 27*['soundWhenDone', 'autoSubmitAnswer', 'loopSolving', 'autoScreenshot'].index(setting))
    labelsSettings[setting] = l
    l.bind('<Button-1>', lambda e, s=setting: toggleSetting(s))
    
def saveAndExit(e=None):
    saveSettings(settings)
    exit()


exitLbl = tk.Label(se, text='Save & Exit', font=('Arial', 15), bg=BG, fg='cyan')
exitLbl.place(x=412, y=130)
exitLbl.bind('<Button-1>', saveAndExit)

se.attributes('-topmost', True)
se.lift()
se.focus_force()

se.createcommand("tk::mac::Quit" , saveAndExit)
se.protocol("WM_DELETE_WINDOW", saveAndExit)

se.mainloop()