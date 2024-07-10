import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsg
import tkinter.filedialog as tkfile
import tkinter.colorchooser as tkcolor
from sys import exit
from os.path import exists
import json
from typing import Callable,Tuple
from typing import Union as U
from typing_extensions import Literal,List
import pygame


DEBUG = False

def dbprint(*args,**kwargs):
    if DEBUG:
        print(*args,**kwargs)

def deco(fun0:Callable):
    def fun1(*args,**kwargs):
        try:
            rtn = fun0(*args,**kwargs)
        except Exception as e:
            dbprint(f"\nException occurred in manage_edit.py:\n  {str(type(e))[8:-2]}: {e}")
            rtn = None
        finally:
            return rtn
    return fun1

def get_all_pg_fonts():
        pygame.init()
        pgFontNames = pygame.font.get_fonts()
        pygame.quit()
        return pgFontNames

class TimetableEditTools():
    def __init__(self, filepath: str = 'timetable3.txt', instantRead: bool = True, allowJson: bool = True):
        self.filepath_timetable = filepath
        self.timetable = []
        self.settings = {}
        self.filtered = []
        self.undoList = []  #[('name',<datas>)]
        self.redoList = []
        self.notSavedYet = False
        self.isJson = False
        self.originSettings = {}
        self.originIndentLevel = 0
        if instantRead:
            self.readTimetable(allowJson)
            self.filtered = self.filterValidSchedules()

    @deco
    def readTimetable(self,allowJson=True):
        file_timetable = open(self.filepath_timetable,'r')
        rawTimetable = file_timetable.readlines()
        countLines = len(rawTimetable)
        file_timetable.close()
        if self.filepath_timetable[-4:] == '.txt':
            self.timetable = eval(rawTimetable[0])
            self.settings = eval(rawTimetable[1])
        else:
            rawTimetable = ''.join(rawTimetable)
            self.json_to_timetable(rawTimetable,loadToSelf=True)
            self.isJson = True
            TAB = '    '
            if countLines == 1:
                self.originIndentLevel = 0
            elif f'"screenSize": [\n{TAB*3}' in rawTimetable:
                self.originIndentLevel = 2
            else:
                self.originIndentLevel = 1
        self.originSettings = self.settings.copy()

    def sortTimetable(self):
        for dayIdx in range(len(self.timetable)):
            day = self.timetable[dayIdx]
            schedIdx = 0
            while schedIdx < len(day):
                if day[schedIdx][2] == '':
                    self.timetable[dayIdx].pop(schedIdx)
                    schedIdx -= 1
                schedIdx += 1
            for j in range(len(day)-1):
                for i in range(j,-1,-1):
                    if self.timetable[dayIdx][i][0] > self.timetable[dayIdx][i+1][0]:
                        self.timetable[dayIdx][i],self.timetable[dayIdx][i+1] = self.timetable[dayIdx][i+1],self.timetable[dayIdx][i]

    @deco
    def filterValidSchedules(self) -> list:
        invalidScheds = []
        timetable = self.timetable.copy()
        self.timetable = [[],[],[],[],[],[],[]]
        for weekday in range(0,7):
            for sched in timetable[weekday]:
                val = self.addSchedule(weekday,sched[0],sched[1],sched[2],False)
                if val != None:
                    if val[0] == 'joint':
                        invalidScheds.append(sched)
                        # if val[1][0] >= sched[0]:
                        #     sched[1] = val[1][0]
                        # elif val[1][1] <= sched[1]:
                        #     sched[0] = val[1][1]
                        # self.addSchedule(weekday,sched[0],sched[1],sched[2],False)
        if invalidScheds != []:
            self.notSavedYet = True
        return invalidScheds
        
    @deco
    def addSchedule(self,weekday:Literal[0,1,2,3,4,5,6],timeFr:int,timeTo:int,name:str,undoable:bool=True) -> U[list,str,None]:
        isAddable = self.isScheduleAddable(weekday,timeFr,timeTo,name)
        if isAddable[0] == False:
            return isAddable[1]
        else:
            self.timetable[weekday].append([timeFr,timeTo,name])
            self.sortTimetable()
            if undoable:
                self.redoList = []
                self.undoList.append(('addSchedule',[weekday,timeFr,timeTo,name]))
                self.notSavedYet = True

    @deco
    def removeSchedule(self,weekday:Literal[0,1,2,3,4,5,6],timeFr:int,timeTo:int,name:str,undoable:bool=True) -> U[Literal[True],None]:
        self.timetable[weekday].remove([timeFr,timeTo,name])
        self.sortTimetable()
        if undoable:
            self.redoList = []
            self.undoList.append(('removeSchedule',[weekday,timeFr,timeTo,name]))
            self.notSavedYet = True
        return True

    @deco
    def editSchedule(self,originWeekday:Literal[0,1,2,3,4,5,6],originIdx:int,newWeekday:Literal[0,1,2,3,4,5,6],newFr:int,newTo:int,newname:str,undoable:bool=True) -> U[list,str,None]:
        sched = self.timetable[originWeekday][originIdx]
        self.removeSchedule(originWeekday,sched[0],sched[1],sched[2],False)
        rtn = self.addSchedule(newWeekday,newFr,newTo,newname,False)
        if rtn == None:
            self.sortTimetable()
            if undoable:
                self.redoList = []
                self.undoList.append(('editSchedule',[[originWeekday,sched[0],sched[1],sched[2]],[newWeekday,newFr,newTo,newname]]))
                self.notSavedYet = True
        else:
            self.addSchedule(originWeekday,sched[0],sched[1],sched[2],False)
            return rtn
        
    @deco
    def coverSchedule(self,orgnScheds:List[list],conqWeekday:Literal[0,1,2,3,4,5,6],conqFr:int,conqTo:int,conqName:str,undoable:bool=True) -> U[list,str,None]:
        '''Conq for conqueror, while orgn for original. \nConqueror sched covers original sched into new sched.\n In undolist shows ('coverSchedule',[conqWeekday,orgnScheds,newScheds,conqSched])'''
        # orgnScheds:List[list] = [self.timetable[conqWeekday][orgnIdx] for orgnIdx in orgnIdxs]
        conqSched = [conqFr,conqTo,conqName]
        newScheds = []
        for sched in orgnScheds:                                        # [ ] for conq, ( ) for orgn
            sched = sched.copy()
            if sched[0] >= conqSched[0] and sched[1] <= conqSched[1]:   # [ ( ) ] -> [ ]
                pass
            elif sched[0] < conqSched[0] and sched[1] <= conqSched[1]:  # ( [ ) ] -> ( ) [ ]
                sched[1] = conqSched[0]
                newScheds.append(sched)
            elif sched[0] >= conqSched[0] and sched[1] > conqSched[1]:  # [ ( ] ) -> [ ] ( )
                sched[0] = conqSched[1]
                newScheds.append(sched)
            elif sched[0] < conqSched[0] and sched[1] > conqSched[1]:   # ( [ ] ) -> ( ) [ ] (2)
                sched2 = sched.copy()
                sched[1] = conqSched[0]
                sched2[0] = conqSched[1]
                newScheds.append(sched)
                newScheds.append(sched2)
        for sched in orgnScheds:
            self.removeSchedule(conqWeekday,*sched,False)
        rtn = self.addSchedule(conqWeekday,*conqSched,False)
        if rtn == None:
            for sched in newScheds:
                self.addSchedule(conqWeekday,*sched,False)
            if undoable:
                self.redoList = []
                self.undoList.append(('coverSchedule',[conqWeekday,orgnScheds,newScheds,conqSched]))
                self.notSavedYet = True
            else:
                return [None,newScheds.copy()]
        else:
            for sched in orgnScheds:
                self.addSchedule(conqWeekday,*sched,False)
            return rtn
        
    @deco
    def uncoverSchedule(self,conqWeekday:Literal[0,1,2,3,4,5,6],orgnScheds:List[list],newScheds:List[list],conqSched:list):
        '''The opposite process of self.coverSchedule.'''
        self.removeSchedule(conqWeekday,*conqSched,False)
        for sched in newScheds:
            self.removeSchedule(conqWeekday,*sched,False)
        for sched in orgnScheds:
            self.addSchedule(conqWeekday,*sched,False)

    # @deco
    def edit_coverSchedule(self,conqOriginWeekday:Literal[0,1,2,3,4,5,6],conqOriginSched:list,conqNewWeekday:Literal[0,1,2,3,4,5,6],conqNewSched:list,orgnScheds:List[list],undoable:bool=True) -> U[list,str,None]:
        self.removeSchedule(conqOriginWeekday,*conqOriginSched,False)
        rtn = self.coverSchedule(orgnScheds,conqNewWeekday,*conqNewSched,False)
        if rtn[0] == None:
            newScheds = rtn[1]
            if undoable:
                self.redoList = []
                self.undoList.append(('edit_coverSchedule',[conqOriginWeekday,conqOriginSched,conqNewWeekday,conqNewSched,orgnScheds,newScheds]))
                self.notSavedYet = True
        else:
            self.addSchedule(conqOriginWeekday,*conqOriginSched,False)
            return rtn

    def isScheduleAddable(self,weekday:Literal[0,1,2,3,4,5,6],timeFr:int,timeTo:int,name:str,portValues:List[int]=[0,0,0,0,0,0,0,0,0]) -> Tuple[bool,U[list,str,Literal[0]]]:
        '''Check whether the schedule is valid and whether the existing schedules pardons it. \nReturn values (in priority order): (False, 'syntax') | (False, ('value', 'time')) | (False, ('value', 'name')) | (False, ('joint', <sched>)) | (True, 0)'''
        w,y,m,d,h,m,s,cd,cw = portValues
        try:
            if not ((timeFr%100 in range(0,61)) and (timeFr//100 in range(0,25)) and 
                    (timeTo%100 in range(0,61)) and (timeTo//100 in range(0,25)) and
                    (0 <= timeFr < timeTo <= 2400)):
                return (False,('value','time'))
            if type(eval(name)) != str:
                return (False,('value','name'))
            jointScheds = []
            for sched in self.timetable[weekday]:
                if (sched[0] in range(timeFr,timeTo)) or (sched[1] in range(timeFr+1,timeTo+1)) or (timeFr in range(sched[0],sched[1])) or (timeTo in range(sched[0]+1,sched[1]+1)):
                    jointScheds.append(sched.copy())
            if jointScheds != []:
                return (False,('joint',jointScheds))
        except:
            return (False,'syntax')
        else:
            return (True,0)
        
    def editSettings(self,newSettings:dict,undoable:bool=True):
        oldSettings = self.settings.copy()
        self.settings = newSettings
        if undoable:
            self.redoList = []
            self.undoList.append(('editSettings',oldSettings,newSettings))
            self.notSavedYet = True
        
    # @deco
    def undo(self,loop:int=1):
        loop = loop if (0<=loop<=len(self.undoList)) else len(self.undoList)
        for _ in range(loop):
            task = True
            action = self.undoList.pop(-1)
            if action[0] == 'addSchedule':
                self.removeSchedule(*action[1],False)
            elif action[0] == 'removeSchedule':
                self.addSchedule(*action[1],False)
            elif action[0] == 'editSchedule':   # ('editSchedule',[[originWeekday,sched[0],sched[1],sched[2]],[newWeekday,newFr,newTo,newname]])
                idx = self.timetable[action[1][1][0]].index(action[1][1][1:])
                self.editSchedule(action[1][1][0],idx,*action[1][0],False)
            elif action[0] == 'coverSchedule':   # ('coverSchedule',[conqWeekday,orgnScheds,newScheds,conqSched])
                self.uncoverSchedule(action[1][0],action[1][1],action[1][2],action[1][3],False)
            elif action[0] == 'edit_coverSchedule': # ('edit_coverSchedule',[conqOriginWeekday,conqOriginSched,conqNewWeekday,conqNewSched,orgnScheds,newScheds])
                self.uncoverSchedule(action[1][2],action[1][4],action[1][5],action[1][3],False)
                self.addSchedule(action[1][0],*action[1][1],False)
            elif action[0] == 'editSettings':   # ('editSettings',oldSettings,newSettings)
                self.editSettings(action[1],False)
            else:
                task = False
            self.redoList.append(action)
            if task:
                self.notSavedYet = True
            if self.undoList == []:
                self.notSavedYet = False

    # @deco
    def redo(self,loop:int=1):
        loop = loop if (0<=loop<=len(self.redoList)) else len(self.redoList)
        for _ in range(loop):
            task = True
            action = self.redoList.pop(-1)
            if action[0] == 'addSchedule':
                self.addSchedule(*action[1],False)
            elif action[0] == 'removeSchedule':
                self.removeSchedule(*action[1],False)
            elif action[0] == 'editSchedule':
                idx = self.timetable[action[1][0][0]].index(action[1][0][1:])
                self.editSchedule(action[1][0][0],idx,*action[1][1],False)
            elif action[0] == 'coverSchedule':
                self.coverSchedule(action[1][1],action[1][0],*action[1][3],False)
            elif action[0] == 'edit_coverSchedule':
                self.edit_coverSchedule(action[1][0],action[1][1],action[1][2],action[1][3],action[1][4],False)
            elif action[0] == 'editSettings':   # ('editSettings',oldSettings,newSettings)
                self.editSettings(action[2],False)
            else:
                task = False
            self.undoList.append(action)
            if task:
                self.notSavedYet = True

    def saveTimetable(self) -> bool:
        self.filterValidSchedules()
        if self.isJson:
            with open(self.filepath_timetable,mode='w') as file:
                try:
                    savingText = self.timetable_to_json(indentLevel=self.originIndentLevel)
                    file.write(savingText)
                    self.notSavedYet = False
                    return True
                except:
                    return False
        else:
            with open(self.filepath_timetable,mode='w') as file:
                try:
                    savingText = f'{self.timetable!r}\n{self.settings!r}\n# Timetable version: 3'
                    file.write(savingText)
                    self.notSavedYet = False
                    return True
                except:
                    return False
    
    def timetable_to_json(self,timetable=None,settings=None,indentLevel:int=0) -> str:
        if timetable == None:
            timetable = self.timetable.copy()
        if settings == None:
            settings = self.settings.copy()
        if indentLevel == 0:
            doIndent = None
        else:
            doIndent = 4
        jsonDict = {'schedules':{'Mon':[],'Tue':[],'Wed':[],'Thu':[],'Fri':[],'Sat':[],'Sun':[]},'settings':settings,'version':3}
        weekdayKeys = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        for weekdayIdx in [0,1,2,3,4,5,6]:
            if indentLevel==1:
                weekday = [[0, 0, "''"]] + timetable[weekdayIdx]
            else:
                weekday = timetable[weekdayIdx]
            jsonDict['schedules'][weekdayKeys[weekdayIdx]] = weekday
        jsonStr = json.dumps(jsonDict,ensure_ascii=False,indent=doIndent)
        if indentLevel == 1:
            TAB = '    '
            jsonStr = jsonStr.replace(f'"screenSize": [\n{TAB*3}{settings["screenSize"][0]},\n{TAB*3}{settings["screenSize"][1]}\n{TAB*2}],',
                                      f'"screenSize": [{settings["screenSize"][0]}, {settings["screenSize"][1]}],')
            jsonStr = jsonStr.replace(f'"doBackgroundImgDisplay": [\n{TAB*3}{"true" if settings["doBackgroundImgDisplay"][0] else "false"},\n{TAB*3}{"true" if settings["doBackgroundImgDisplay"][1] else "false"}\n{TAB*2}],',
                                      f'"doBackgroundImgDisplay": [{"true" if settings["doBackgroundImgDisplay"][0] else "false"}, {"true" if settings["doBackgroundImgDisplay"][1] else "false"}],')
            jsonStr = jsonStr.replace(f'"timeOffset": [\n{TAB*3}{settings["timeOffset"][0]},\n{TAB*3}{settings["timeOffset"][1]},\n{TAB*3}{settings["timeOffset"][2]},\n{TAB*3}{settings["timeOffset"][3]},\n{TAB*3}{settings["timeOffset"][4]}\n{TAB*2}],',
                                      f'"timeOffset": [{settings["timeOffset"][0]}, {settings["timeOffset"][1]}, {settings["timeOffset"][2]}, {settings["timeOffset"][3]}, {settings["timeOffset"][4]}],')
            jsonStr = jsonStr.replace(f'"colorfuncs": [\n{TAB*3}[\n{TAB*4}{json.dumps(settings["colorfuncs"][0][0])},\n{TAB*4}{json.dumps(settings["colorfuncs"][0][1])},\n{TAB*4}{json.dumps(settings["colorfuncs"][0][2])}\n{TAB*3}],\n{TAB*3}[\n{TAB*4}{json.dumps(settings["colorfuncs"][1][0])},\n{TAB*4}{json.dumps(settings["colorfuncs"][1][1])},\n{TAB*4}{json.dumps(settings["colorfuncs"][1][2])}\n{TAB*3}]',
                                      f'"colorfuncs": [\n{TAB*3}[\n{TAB*4}{json.dumps(settings["colorfuncs"][0][0])},\n\n{TAB*4}{json.dumps(settings["colorfuncs"][0][1])},\n\n{TAB*4}{json.dumps(settings["colorfuncs"][0][2])}\n\n{TAB*3}],\n{TAB*3}[\n{TAB*4}{json.dumps(settings["colorfuncs"][1][0])},\n\n{TAB*4}{json.dumps(settings["colorfuncs"][1][1])},\n\n{TAB*4}{json.dumps(settings["colorfuncs"][1][2])}\n{TAB*3}]')  # protecting this from being mis-replaced
            jsonStr = jsonStr.replace(f'"\n{TAB*3}],\n{TAB*3}[\n{TAB*4}', f'"],\n{TAB*3}[')
            jsonStr = jsonStr.replace(f',\n{TAB*4}', f', ')
            jsonStr = jsonStr.replace(f'"Mon": [\n{TAB*3}[\n{TAB*4}', f'"Mon": [\n{TAB*3}[')
            jsonStr = jsonStr.replace(f'"\n{TAB*3}]\n{TAB*2}],\n{TAB*2}"Tue": [\n{TAB*3}[\n{TAB*4}', 
                                      f'"]\n{TAB*2}],\n{TAB*2}"Tue": [\n{TAB*3}[')
            jsonStr = jsonStr.replace(f'"\n{TAB*3}]\n{TAB*2}],\n{TAB*2}"Wed": [\n{TAB*3}[\n{TAB*4}', 
                                      f'"]\n{TAB*2}],\n{TAB*2}"Wed": [\n{TAB*3}[')
            jsonStr = jsonStr.replace(f'"\n{TAB*3}]\n{TAB*2}],\n{TAB*2}"Thu": [\n{TAB*3}[\n{TAB*4}', 
                                      f'"]\n{TAB*2}],\n{TAB*2}"Thu": [\n{TAB*3}[')
            jsonStr = jsonStr.replace(f'"\n{TAB*3}]\n{TAB*2}],\n{TAB*2}"Fri": [\n{TAB*3}[\n{TAB*4}', 
                                      f'"]\n{TAB*2}],\n{TAB*2}"Fri": [\n{TAB*3}[')
            jsonStr = jsonStr.replace(f'"\n{TAB*3}]\n{TAB*2}],\n{TAB*2}"Sat": [\n{TAB*3}[\n{TAB*4}', 
                                      f'"]\n{TAB*2}],\n{TAB*2}"Sat": [\n{TAB*3}[')
            jsonStr = jsonStr.replace(f'"\n{TAB*3}]\n{TAB*2}],\n{TAB*2}"Sun": [\n{TAB*3}[\n{TAB*4}', 
                                      f'"]\n{TAB*2}],\n{TAB*2}"Sun": [\n{TAB*3}[')
            jsonStr = jsonStr.replace(f'\n{TAB*3}[0, 0, "\'\'"],\n{TAB*3}', f'\n{TAB*3}')
            jsonStr = jsonStr.replace(f'\n{TAB*3}[0, 0, "\'\'"]\n{TAB*2}', '')
            jsonStr = jsonStr.replace(f'"\n{TAB*3}]\n{TAB*2}]\n{TAB}{"},"}', f'"]\n{TAB*2}]\n{TAB}{"},"}')
            jsonStr = jsonStr.replace(f'"colorfuncs": [\n{TAB*3}[\n{TAB*4}{json.dumps(settings["colorfuncs"][0][0])},\n\n{TAB*4}{json.dumps(settings["colorfuncs"][0][1])},\n\n{TAB*4}{json.dumps(settings["colorfuncs"][0][2])}\n\n{TAB*3}],\n{TAB*3}[\n{TAB*4}{json.dumps(settings["colorfuncs"][1][0])},\n\n{TAB*4}{json.dumps(settings["colorfuncs"][1][1])},\n\n{TAB*4}{json.dumps(settings["colorfuncs"][1][2])}\n{TAB*3}]',
                                      f'"colorfuncs": [\n{TAB*3}[\n{TAB*4}{json.dumps(settings["colorfuncs"][0][0])},\n{TAB*4}{json.dumps(settings["colorfuncs"][0][1])},\n{TAB*4}{json.dumps(settings["colorfuncs"][0][2])}\n{TAB*3}],\n{TAB*3}[\n{TAB*4}{json.dumps(settings["colorfuncs"][1][0])},\n{TAB*4}{json.dumps(settings["colorfuncs"][1][1])},\n{TAB*4}{json.dumps(settings["colorfuncs"][1][2])}\n{TAB*3}]')  # recover the protected part
        return jsonStr

    def json_to_timetable(self,jsonStr:str,loadToSelf=True) -> Tuple[list,dict]:
        jsonDict = json.loads(jsonStr)
        rawtimetable = jsonDict['schedules']
        settings = jsonDict['settings']
        weekdayKeys = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        timetable = [[],[],[],[],[],[],[]]
        for weekdayIdx in [0,1,2,3,4,5,6]:
            weekdayKey = weekdayKeys[weekdayIdx]
            timetable[weekdayIdx] = rawtimetable[weekdayKey]
        settings['screenSize'] = tuple(settings['screenSize'])
        if loadToSelf:
            self.timetable = timetable
            self.settings = settings
        return (timetable,settings)
    
    def separate_dir_and_filename(self,path:str) -> Tuple[int]:
        '''Accepts a string path, which can be relative or absolute, and may include '/' or  '\\' as folder structures.\n
        Returns a tuple of (dir, filename).'''
        if '/' in path:
            dir = '/'.join(path.split('/')[:-1])
            filename = path.split('/')[-1]
        elif '\\' in path:
            dir = '/'.join(path.split('\\')[:-1])
            filename = path.split('\\')[-1]
        else:
            dir = './'
            filename = path
        return (dir,filename)

@deco
def isFileOpenable(filepath:str,versionCheck=False,allowJson=False) -> bool:
    try:
        if allowJson:
            if not((filepath[-5:] == '.json') or (filepath[-4:] == '.txt')):
                return False
        else:
            if not(filepath[-4:] == '.txt'):
                return False
        open(filepath,'r').close()
    except FileNotFoundError:
        return False
    else:
        if versionCheck:
            with open(filepath,'r') as f:
                if filepath[-4:] == '.txt':
                    versionMark = f.readlines()[-1]
                    if versionMark == '# Timetable version: 3':
                        return True
                    else:
                        return False
                else:
                    try:
                        versionMark = json.loads(''.join(f.readlines()))['version']
                        if versionMark == 3:
                            return True
                    except SyntaxWarning:
                        return False
        else:
            return True
    
@deco
def timetableScheduleFormat(timetable:list) -> str:
    maxRows = max(map(len,timetable))
    timetable = [list(map(lambda schedule:f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02}~{int(schedule[1]//100):02}:{int(schedule[1]%100):02} {eval(schedule[2])}',weekday)) for weekday in timetable]
    maxCols = list(map(lambda x:max(map(len,x)),timetable))
    timetable = list(map(lambda x:list(x)+(['']*maxRows),timetable))
    rawRows = []
    for rowIdx in range(maxRows):
        rawRows.append(f'{timetable[0][rowIdx]: <{maxCols[0]}} | {timetable[1][rowIdx]: <{maxCols[1]}} | {timetable[2][rowIdx]: <{maxCols[2]}} | {timetable[3][rowIdx]: <{maxCols[3]}} | {timetable[4][rowIdx]: <{maxCols[4]}} | {timetable[5][rowIdx]: <{maxCols[5]}} | {timetable[6][rowIdx]: <{maxCols[6]}}')
    finalText = '\n'.join(rawRows)+'\n'
    return finalText

class RunDirectly():
    def __init__(self):
        pass
        
    def main(self):
        self.mainwin = tk.Tk()
        self.mainwin.geometry('650x450')
        self.mainwin.title('编辑时间表')
        
        shouldExit = False
        while True:
            filepath = tkfile.askopenfilename(defaultextension='.txt',title='打开时间表文件 (<.txt>或<.json>)',initialdir='./',initialfile='timetable3.txt')
            if isFileOpenable(filepath,allowJson=True):
                break
            elif filepath == '':
                shouldExit = tkmsg.askyesno('提示','必须打开一个文件！\n是否关闭程序？')
                if shouldExit:
                    break
                else:
                    continue
            else:
                tkmsg.showerror('错误','文件无法打开')
        if shouldExit:
            exit()

        def checkExit():
            if self.et.notSavedYet:
                doFinalSave = tkmsg.askyesnocancel('提示','发尚未保存的改动！\n是否保存？')
                if doFinalSave == None:
                    return None
                if doFinalSave:
                    rtn = self.et.saveTimetable()
                    if rtn:
                        self.updateTextFrames()
                        tkmsg.showinfo('提示','保存成功！')
                    else:
                        tkmsg.showerror('错误','保存失败！')
            self.mainwin.destroy()
            exit()
        self.mainwin.protocol('WM_DELETE_WINDOW',checkExit)

        self.filepath = filepath
        self.et = TimetableEditTools(filepath)
        self.timetable = self.et.timetable      # Strong copy
        self.mainwin.title(f'{"*" if self.et.notSavedYet else ""}{filepath} - 编辑时间表')

        area1 = tk.Frame(self.mainwin)
        area2 = tk.Frame(self.mainwin)
        area3 = tk.Frame(self.mainwin)
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        area1.grid(row=0,column=0,sticky='nwe')
        area2.grid(row=1,column=0,sticky='nesw')
        area3.grid(row=2,column=0,sticky='swe')
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])

        self.mainwin.rowconfigure(1,weight=20)
        self.mainwin.columnconfigure(0,weight=10)
        self.mainwin.columnconfigure(1,weight=0)
        
        area1.rowconfigure(0,weight=20)
        area1.columnconfigure(0,weight=7)
        area1.columnconfigure(1,weight=10)
        area1.columnconfigure(2,weight=10)
        area1.columnconfigure(3,weight=10)
        area1.columnconfigure(4,weight=5)
        area1.columnconfigure(5,weight=5)
        
        area2.columnconfigure(0,weight=10)
        area2.columnconfigure(1,weight=10)
        area2.columnconfigure(2,weight=10)
        area2.columnconfigure(3,weight=10)
        area2.columnconfigure(4,weight=10)
        area2.columnconfigure(5,weight=10)
        area2.columnconfigure(6,weight=10)
        area2.rowconfigure(0,weight=20)
        
        area3.columnconfigure(0,weight=8)
        area3.columnconfigure(1,weight=10)

        # objects in area2
        texts = self.weekdayScheduleFormat(self.timetable)
        fontSizeVar = tk.StringVar(self.mainwin)
        fontSizeList = ['字号5','字号6','字号7','字号8','字号9','字号10','字号11','字号12','字号14','字号16','字号18','字号20','字号24']
        fontSizeVar.set('字号9')
        self.textFrames = [tk.Text(area2,font=('Courier New',9),width=20,wrap='none') for _ in range(7)]
        scrollBar = tk.Scrollbar(area2)
        def scrollEvent(*args):
            for frame in self.textFrames:
                frame.yview(*args)
        scrollBar.config(command=scrollEvent)
        scrollBar.grid(row=0,column=7,sticky='nesw')
        for frameIdx in range(7):
            frame=self.textFrames[frameIdx]
            frame.config(yscrollcommand=scrollBar.set)
            frame.grid(row=0,column=frameIdx,sticky='nesw')
            frame.insert('0.0',texts[frameIdx])

        def optionMenuDo(var:tk.StringVar):
            size = eval(fontSizeVar.get()[2:])
            for frame in self.textFrames:
                frame.config(font=('Courier New',size))

        def btnUndoDo():
            self.et.undo()
            self.updateTextFrames()
        def btnRedoDo():
            self.et.redo()
            self.updateTextFrames()
        
        # objects in area1
        optionMenu = ttk.OptionMenu(area1,fontSizeVar,'字号9',*fontSizeList,command=optionMenuDo)
        optionMenu.grid(row=0,column=0,sticky='nesw')

        btnAdd = tk.Button(area1,text='添加计划..',font=('Courier New',10),command=self.main_showAddwin)
        btnAdd.grid(row=0,column=1,sticky='nesw')
        btnRemove = tk.Button(area1,text='删除计划..',font=('Courier New',10),command=self.main_showRemovewin)
        btnRemove.grid(row=0,column=2,sticky='nesw')
        btnEdit = tk.Button(area1,text='修改计划..',font=('Courier New',10),command=self.main_showEditwin_chooseSchedule)
        btnEdit.grid(row=0,column=3,sticky='nesw')

        btnUndo = tk.Button(area1,text='撤销',font=('Courier New',10),command=btnUndoDo)
        btnUndo.grid(row=0,column=4,sticky='nesw')
        btnRedo = tk.Button(area1,text='重做',font=('Courier New',10),command=btnRedoDo)
        btnRedo.grid(row=0,column=5,sticky='nesw')

        # objects in area3
        btnSettings = tk.Button(area3,text='修改设置项..',font=('Courier New',10),command=self.main_showSettingswin)
        btnSettings.grid(row=0,column=0,sticky='nesw',padx=[2,1],pady=[3,1])
        btnUndo = tk.Button(area3,text='文件操作..',font=('Courier New',11),bg='#D0D0D0',fg='#3530A0',bd=3,command=self.main_showFileswin)
        btnUndo.grid(row=0,column=1,sticky='nesw',padx=[1,2],pady=[3,1])


        if self.et.filtered == []:
            tkmsg.showinfo('提示','文件打开成功！')
        else:
            tkmsg.showwarning('提示','文件中有以下格式错误已被自动修改：\n'+'\n'.join(self.et.filtered))

        self.mainwin.mainloop()
        
    def main_showAddwin(self):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
        addwin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=280)  #column0 weights 10

        addwin.columnconfigure(0,weight=4)
        addwin.columnconfigure(1,weight=3)
        addwin.columnconfigure(3,weight=3)
        addwin.columnconfigure(5,weight=3)
        addwin.columnconfigure(7,weight=3)

        tk.Label(addwin,text=' 添加计划',font=('Courier New',10),fg='#202020').grid(row=0,column=0,columnspan=10,sticky='nsw')

        weekdayVar = tk.StringVar()
        weekdayNameList = ['周一','周二','周三','周四','周五','周六','周日']
        weekdayVar.set('周一')
        weekdayMenu = ttk.OptionMenu(addwin,weekdayVar,'周一',*weekdayNameList)
        weekdayMenu.grid(row=1,column=0,sticky='nesw')

        entry_timeFrHour = tk.Entry(addwin,width=3,font=('Courier New',12))
        entry_timeFrMinu = tk.Entry(addwin,width=3,font=('Courier New',12))
        entry_timeToHour = tk.Entry(addwin,width=3,font=('Courier New',12))
        entry_timeToMinu = tk.Entry(addwin,width=3,font=('Courier New',12))
        entry_schedName = tk.Entry(addwin,width=15,font=('Courier New',12))
        entry_schedName.insert(0,'计划名称')
        entry_timeFrHour.grid(row=1,column=1)
        tk.Label(addwin,text=':',font=('Courier New',12)).grid(row=1,column=2)
        entry_timeFrMinu.grid(row=1,column=3)
        tk.Label(addwin,text=' ~ ',font=('Courier New',12)).grid(row=1,column=4)
        entry_timeToHour.grid(row=1,column=5)
        tk.Label(addwin,text=':',font=('Courier New',12)).grid(row=1,column=6)
        entry_timeToMinu.grid(row=1,column=7)

        def inputModeMenuDo(var):
            nonlocal oldNameMode
            nameMode = inputModeList.index(inputModeVar.get())
            if nameMode == 1 and oldNameMode == 0:
                oldName = entry_schedName.get()
                if oldName[:3] == '?=(' and oldName[-1] == ')':
                    oldName = oldName[3:-1]
                else:
                    oldName = f'"\'{oldName}\'"'
                entry_schedName.delete(0,'end')
                entry_schedName.insert(0,oldName)
                oldNameMode = 1
                entry_schedName.config(font=('Courier New',9))
            elif nameMode == 0 and oldNameMode == 1:
                oldName = entry_schedName.get()
                try:
                    if (oldName[0:2] == '"\'') and (oldName[-2:] == '\'"') and ("'" not in oldName[2:-2]):
                        entry_schedName.delete(0,'end')
                        entry_schedName.insert(0,oldName[2:-2])
                        oldNameMode = 0
                        entry_schedName.config(font=('Courier New',12))
                    else:
                        doModeSwitch = tkmsg.askokcancel('警告','您已在该计划名称中使用表达式，\n强制转换为普通模式可能导致信息遗漏！\n请确定仍要转换？')
                        if doModeSwitch:
                            entry_schedName.delete(0,'end')
                            entry_schedName.insert(0,f"?=({oldName})")
                            oldNameMode = 0
                            entry_schedName.config(font=('Courier New',12))
                        else:
                            inputModeVar.set(inputModeList[1])
                except IndexError:
                    oldNameMode = 0
                    entry_schedName.config(font=('Courier New',12))
            if oldNameMode == 1:
                portInfoVar.set(portInfo)
            else:
                portInfoVar.set('')

        portInfoVar = tk.StringVar()
        portInfo = '''“高级输入”模式下，计划名称可为一个可eval()
的字符串。
可用的变量：
  w — 星期几，周一为0，周日为6；
  y — 年份，四位整数；
  n — 月份，1~12；
  d — 日期，1~31；
  h — 小时数，0~23；
  m — 分钟数，0~59；
  s — 秒数，0~59；
  cd — 自本年1月1日的累计天数，0~365；
  cw — 自本年1月1日所在星期的累计星期数，
       0~52。'''
        portInfoVar.set('')
        tk.Label(addwin,textvariable=portInfoVar,fg='#909090',font=('Courier New',9),justify='left').grid(row=11,column=0,columnspan=10,sticky='nsw')

        inputModeVar = tk.StringVar()
        inputModeList = ['普通输入','高级输入']
        inputModeVar.set('普通输入')
        oldNameMode = 0
        inputModeMenu = ttk.OptionMenu(addwin,inputModeVar,'普通输入',*inputModeList,command=inputModeMenuDo)
        entry_schedName.grid(row=2,column=0,columnspan=5,sticky='nesw',padx=[5,0])
        inputModeMenu.grid(row=2,column=5,columnspan=3,sticky='nesw')

        def btnConfirmDo(entryContents=None):
            if entryContents == None:
                entryContents = [entry_timeFrHour.get(),entry_timeFrMinu.get(),entry_timeToHour.get(),entry_timeToMinu.get(),entry_schedName.get()]
            try:
                if inputModeList.index(inputModeVar.get()) == 0:
                    entryContents[4] = f"'{entryContents[4]}'"
                else:
                    entryContents[4] = eval(entryContents[4])
                val = self.et.addSchedule(weekdayNameList.index(weekdayVar.get()),
                                          int(entryContents[0]+entryContents[1]),
                                          int(entryContents[2]+entryContents[3]),
                                          entryContents[4])
            except:
                val = 'syntax'
            if val == None:
                btnCancelDo()
            else:
                if val == 'syntax':
                    tkmsg.showerror('错误','请检查输入内容！')
                elif val == ('value','time'):
                    tkmsg.showerror('错误','请检查时间格式！')
                elif val == ('value','name'):
                    tkmsg.showerror('错误','请检查计划名称格式！')
                elif val[0] == 'joint':
                    jointSchedTexts = []
                    for otherSched in val[1]:
                        try:
                            eval(otherSched[2])
                        except NameError:
                            otherSched[2] = f'?=({otherSched[2]})'
                            otherSched[2] = f"{otherSched[2]!r}"
                        jointSchedTexts.append(f'{int(otherSched[0]//100):02}:{int(otherSched[0]%100):02}~{int(otherSched[1]//100):02}:{int(otherSched[1]%100):02} {eval(otherSched[2])}')
                    jointSchedText = '；\n'.join(jointSchedTexts)
                    doCover = tkmsg.askokcancel('警告',f'该计划时段与已有计划有重叠。是否覆盖？\n若选择“确定”，则该计划将覆盖原计划的重叠时段；\n若选择“取消”，则返回“添加计划”窗口进行修改。\n重叠的计划为：\n{jointSchedText}')
                    if doCover == True:
                        jointScheds = [self.main_textToTuple(text)[:3] for text in jointSchedTexts]
                        self.et.coverSchedule(jointScheds,
                                              weekdayNameList.index(weekdayVar.get()),
                                              int(entryContents[0]+entryContents[1]),
                                              int(entryContents[2]+entryContents[3]),
                                              entryContents[4])
                        btnCancelDo()
                    elif doCover == False:
                        pass
                    
        def btnCancelDo():
            nonlocal addwin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            addwin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()
                      
        btnConfirm = tk.Button(addwin,text='确定',font=('Courier New',10),width=12,command=btnConfirmDo)
        btnConfirm.grid(row=10,column=0,columnspan=4)
        btnCancel = tk.Button(addwin,text='取消',font=('Courier New',10),width=12,command=btnCancelDo)
        btnCancel.grid(row=10,column=4,columnspan=4)

        addwin.mainloop()

    def main_showRemovewin(self):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
        removewin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=220)  #column0 weights 10

        removewin.columnconfigure(0,weight=5)
        removewin.columnconfigure(1,weight=5)

        tk.Label(removewin,text=' 删除计划',font=('Courier New',10),fg='#202020').grid(row=0,column=0,columnspan=10,sticky='nsw')

        weekdayVar = tk.StringVar()
        weekdayNameList = ['周一','周二','周三','周四','周五','周六','周日']
        weekdayVar.set('周一')

        schedsVar = tk.StringVar()
        schedsNameList = self.getWeekdayScheduleTexts(self.timetable[weekdayNameList.index(weekdayVar.get())])
        schedsVar.set('')
        def weekdayMenuDo(arg):
            nonlocal schedsMenu
            schedsMenu.destroy()
            schedsNameList = self.getWeekdayScheduleTexts(self.timetable[weekdayNameList.index(weekdayVar.get())])
            schedsVar.set('')
            schedsMenu = ttk.OptionMenu(removewin,schedsVar,'',*schedsNameList)
            schedsMenu.grid(row=2,column=0,columnspan=2,sticky='nesw',padx=5,pady=5)
        weekdayMenu = ttk.OptionMenu(removewin,weekdayVar,'周一',*weekdayNameList,command=weekdayMenuDo)
        schedsMenu = ttk.OptionMenu(removewin,schedsVar,'',*schedsNameList)
        weekdayMenu.grid(row=1,column=0,columnspan=2,sticky='nesw',padx=5,pady=5)
        schedsMenu.grid(row=2,column=0,columnspan=2,sticky='nesw',padx=5,pady=5)

        def btnConfirmDo():
            rawSched = self.main_textToTuple(schedsVar.get())[:3]
            try:
                if '"?=(' in rawSched[2]:   # "\"?=(<sched>)\""
                    rawSched[2] = f"{rawSched[2][4:-2]!r}"
                if self.et.removeSchedule(weekdayNameList.index(weekdayVar.get()),*rawSched):
                    btnCancelDo()
                else:
                    tkmsg.showerror('错误','无法找到该计划！')
            except TypeError or ValueError:
                tkmsg.showerror('错误','无法解析该计划选项！')
        def btnCancelDo():
            nonlocal removewin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            removewin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()
                      
        btnConfirm = tk.Button(removewin,text='确定',font=('Courier New',10),width=12,command=btnConfirmDo)
        btnConfirm.grid(row=10,column=0,padx=[5,2],pady=10)
        btnCancel = tk.Button(removewin,text='取消',font=('Courier New',10),width=12,command=btnCancelDo)
        btnCancel.grid(row=10,column=1,padx=[2,5],pady=10)
        removewin.mainloop()

    def main_showEditwin_chooseSchedule(self):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
        editwin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=220)  #column0 weights 10

        editwin.columnconfigure(0,weight=5)
        editwin.columnconfigure(1,weight=5)

        tk.Label(editwin,text=' 修改计划',font=('Courier New',10),fg='#202020').grid(row=0,column=0,columnspan=10,sticky='nsw')
        tk.Label(editwin,text=' 请选择要修改的计划',font=('Courier New',9),fg='#808080').grid(row=1,column=0,columnspan=10,sticky='nsw')

        weekdayVar = tk.StringVar()
        weekdayNameList = ['周一','周二','周三','周四','周五','周六','周日']
        weekdayVar.set('周一')

        schedsVar = tk.StringVar()
        schedsNameList = self.getWeekdayScheduleTexts(self.timetable[weekdayNameList.index(weekdayVar.get())])
        schedsVar.set('')
        def weekdayMenuDo(arg):
            nonlocal schedsMenu
            schedsMenu.destroy()
            schedsNameList = self.getWeekdayScheduleTexts(self.timetable[weekdayNameList.index(weekdayVar.get())])
            schedsVar.set('')
            schedsMenu = ttk.OptionMenu(editwin,schedsVar,'',*schedsNameList)
            schedsMenu.grid(row=3,column=0,columnspan=2,sticky='nesw',padx=5,pady=5)
        weekdayMenu = ttk.OptionMenu(editwin,weekdayVar,'周一',*weekdayNameList,command=weekdayMenuDo)
        schedsMenu = ttk.OptionMenu(editwin,schedsVar,'',*schedsNameList)
        weekdayMenu.grid(row=2,column=0,columnspan=2,sticky='nesw',padx=5,pady=5)
        schedsMenu.grid(row=3,column=0,columnspan=2,sticky='nesw',padx=5,pady=5)

        def btnConfirmDo():
            try:
                rawRawSched = self.main_textToTuple(schedsVar.get())
                rawSched = rawRawSched[:3]
                nameMode = rawRawSched[3]
                if rawSched in self.timetable[weekdayNameList.index(weekdayVar.get())]:
                    self.main_showEditwin_inputNew(weekdayNameList.index(weekdayVar.get()),schedsVar.get(),rawSched,nameMode)
                else:
                    tkmsg.showerror('错误','无法找到该计划！')
            except TypeError or ValueError:
                tkmsg.showerror('错误','无法解析该计划选项！')
        def btnCancelDo():
            nonlocal editwin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            editwin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()
                      
        btnConfirm = tk.Button(editwin,text='继续..',font=('Courier New',10),width=12,command=btnConfirmDo)
        btnConfirm.grid(row=10,column=0,padx=[5,2],pady=10)
        btnCancel = tk.Button(editwin,text='取消',font=('Courier New',10),width=12,command=btnCancelDo)
        btnCancel.grid(row=10,column=1,padx=[2,5],pady=10)
        editwin.mainloop()

    def main_showEditwin_inputNew(self,originSchedWeekday:Literal[0,1,2,3,4,5,6],originSchedText:str,originRawSched:Tuple[int,int,str],originNameMode:Literal[0,1]):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
        editwin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=280)  #column0 weights 10

        editwin.columnconfigure(0,weight=4)
        editwin.columnconfigure(1,weight=3)
        editwin.columnconfigure(3,weight=3)
        editwin.columnconfigure(5,weight=3)
        editwin.columnconfigure(7,weight=3)

        weekdayNameList = ['周一','周二','周三','周四','周五','周六','周日']
        tk.Label(editwin,text=' 修改计划',font=('Courier New',10),fg='#202020').grid(row=0,column=0,columnspan=10,sticky='nsw')
        tk.Label(editwin,text=' 请输入修改后的计划',font=('Courier New',9),fg='#808080').grid(row=1,column=0,columnspan=10,sticky='nsw')
        # tk.Label(editwin,text=f' 原计划：\n  {weekdayNameList[originSchedWeekday]} {originSchedText}',font=('Courier New',9),fg='#808080').grid(row=2,column=0,columnspan=10,sticky='nsw')

        weekdayVar = tk.StringVar()
        weekdayVar.set(weekdayNameList[originSchedWeekday])
        weekdayMenu = ttk.OptionMenu(editwin,weekdayVar,weekdayVar.get(),*weekdayNameList)
        weekdayMenu.grid(row=3,column=0,sticky='nesw')

        entry_timeFrHour = tk.Entry(editwin,width=3,font=('Courier New',12))
        entry_timeFrMinu = tk.Entry(editwin,width=3,font=('Courier New',12))
        entry_timeToHour = tk.Entry(editwin,width=3,font=('Courier New',12))
        entry_timeToMinu = tk.Entry(editwin,width=3,font=('Courier New',12))
        entry_schedName = tk.Entry(editwin,width=15,font=('Courier New',12))
        entry_timeFrHour.grid(row=3,column=1)
        tk.Label(editwin,text=':',font=('Courier New',12)).grid(row=3,column=2)
        entry_timeFrMinu.grid(row=3,column=3)
        tk.Label(editwin,text=' ~ ',font=('Courier New',12)).grid(row=3,column=4)
        entry_timeToHour.grid(row=3,column=5)
        tk.Label(editwin,text=':',font=('Courier New',12)).grid(row=3,column=6)
        entry_timeToMinu.grid(row=3,column=7)
        
        if originNameMode == 0:
            originSchedName = eval(originRawSched[2])
        else:
            originSchedName = f"{originRawSched[2]!r}"
            entry_schedName.config(font=('Courier New',9))
        entry_schedName.insert(0,originSchedName)
        originSchedTimes = [f'{originRawSched[0]//100:0>2}',
                            f'{originRawSched[0]%100:0>2}',
                            f'{originRawSched[1]//100:0>2}',
                            f'{originRawSched[1]%100:0>2}',]
        entry_timeFrHour.insert(0,originSchedTimes[0])
        entry_timeFrMinu.insert(0,originSchedTimes[1])
        entry_timeToHour.insert(0,originSchedTimes[2])
        entry_timeToMinu.insert(0,originSchedTimes[3])

        def inputModeMenuDo(var):
            nonlocal oldNameMode
            nameMode = inputModeList.index(inputModeVar.get())
            if nameMode == 1 and oldNameMode == 0:
                oldName = entry_schedName.get()
                if oldName[:3] == '?=(' and oldName[-1] == ')':
                    oldName = oldName[3:-1]
                else:
                    oldName = f'"\'{oldName}\'"'
                entry_schedName.delete(0,'end')
                entry_schedName.insert(0,oldName)
                oldNameMode = 1
                entry_schedName.config(font=('Courier New',9))
            elif nameMode == 0 and oldNameMode == 1:
                oldName = entry_schedName.get()
                try:
                    if (oldName[0:2] == '"\'') and (oldName[-2:] == '\'"') and ("'" not in oldName[2:-2]):
                        entry_schedName.delete(0,'end')
                        entry_schedName.insert(0,oldName[2:-2])
                        oldNameMode = 0
                        entry_schedName.config(font=('Courier New',12))
                    else:
                        doModeSwitch = tkmsg.askokcancel('警告','您已在该计划名称中使用表达式，\n强制转换为普通模式可能导致信息遗漏！\n请确定仍要转换？')
                        if doModeSwitch:
                            entry_schedName.delete(0,'end')
                            entry_schedName.insert(0,f"?=({oldName})")
                            oldNameMode = 0
                            entry_schedName.config(font=('Courier New',12))
                        else:
                            inputModeVar.set(inputModeList[1])
                except IndexError:
                    oldNameMode = 0
                    entry_schedName.config(font=('Courier New',12))
            if oldNameMode == 1:
                portInfoVar.set(portInfo)
            else:
                portInfoVar.set('')

        portInfoVar = tk.StringVar()
        portInfo = '''“高级输入”模式下，计划名称可为一个可eval()
的字符串。
可用的变量：
  w — 星期几，周一为0，周日为6；
  y — 年份，四位整数；
  n — 月份，1~12；
  d — 日期，1~31；
  h — 小时数，0~23；
  m — 分钟数，0~59；
  s — 秒数，0~59；
  cd — 自本年1月1日的累计天数，0~365；
  cw — 自本年1月1日所在星期的累计星期数，
       0~52。'''
        portInfoVar.set(portInfo if originNameMode==1 else '')
        tk.Label(editwin,textvariable=portInfoVar,fg='#909090',font=('Courier New',9),justify='left').grid(row=11,column=0,columnspan=10,sticky='nsw')

        inputModeVar = tk.StringVar()
        inputModeList = ['普通输入','高级输入']
        inputModeVar.set(inputModeList[originNameMode])
        oldNameMode = originNameMode
        inputModeMenu = ttk.OptionMenu(editwin,inputModeVar,inputModeVar.get(),*inputModeList,command=inputModeMenuDo)
        entry_schedName.grid(row=4,column=0,columnspan=5,sticky='nesw',padx=[5,0])
        inputModeMenu.grid(row=4,column=5,columnspan=3,sticky='nesw')

        def btnConfirmDo(entryContents=None):
            if entryContents == None:
                entryContents = [entry_timeFrHour.get(),entry_timeFrMinu.get(),entry_timeToHour.get(),entry_timeToMinu.get(),entry_schedName.get()]
            try:
                if inputModeList.index(inputModeVar.get()) == 0:
                    entryContents[4] = f"'{entryContents[4]}'"
                else:
                    entryContents[4] = eval(entryContents[4])
                val = self.et.editSchedule(originSchedWeekday,
                                           self.timetable[originSchedWeekday].index(originRawSched),
                                           weekdayNameList.index(weekdayVar.get()),
                                           int(entryContents[0]+entryContents[1]),
                                           int(entryContents[2]+entryContents[3]),
                                           entryContents[4])
            except:
                val = 'syntax'
            if val == None:
                btnCancelDo()
            else:
                if val == 'syntax':
                    tkmsg.showerror('错误','请检查输入内容！')
                elif val == ('value','time'):
                    tkmsg.showerror('错误','请检查时间格式！')
                elif val == ('value','name'):
                    tkmsg.showerror('错误','请检查计划名称格式！')
                elif val[0] == 'joint':
                    jointSchedTexts = []
                    for otherSched in val[1]:
                        try:
                            eval(otherSched[2])
                        except NameError:
                            otherSched[2] = f"?=({otherSched[2]})"
                            otherSched[2] = f"{otherSched[2]!r}"
                        jointSchedTexts.append(f'{int(otherSched[0]//100):02}:{int(otherSched[0]%100):02}~{int(otherSched[1]//100):02}:{int(otherSched[1]%100):02} {eval(otherSched[2])}')
                    jointSchedText = '；\n'.join(jointSchedTexts)
                    doCover = tkmsg.askokcancel('警告',f'该计划时段与已有计划有重叠。是否覆盖？\n若选择“确定”，则该计划将覆盖原计划的重叠时段；\n若选择“取消”，则返回“添加计划”窗口进行修改。\n重叠的计划为：\n{jointSchedText}')
                    if doCover == True:
                        jointScheds = [self.main_textToTuple(text)[:3] for text in jointSchedTexts]
                        conqNewSched = [int(entryContents[0]+entryContents[1]),int(entryContents[2]+entryContents[3]),entryContents[4]]
                        self.et.edit_coverSchedule(originSchedWeekday,
                                                   originRawSched,
                                                   weekdayNameList.index(weekdayVar.get()),
                                                   conqNewSched,
                                                   jointScheds)
                        btnCancelDo()
                    elif doCover == False:
                        pass
                    
        def btnCancelDo():
            nonlocal editwin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            editwin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()
                      
        btnConfirm = tk.Button(editwin,text='确定',font=('Courier New',10),width=12,command=btnConfirmDo)
        btnConfirm.grid(row=10,column=0,columnspan=4)
        btnCancel = tk.Button(editwin,text='取消',font=('Courier New',10),width=12,command=btnCancelDo)
        btnCancel.grid(row=10,column=4,columnspan=4)

        editwin.mainloop()

    def main_showFileswin(self):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
        fileswin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=180)  #column0 weights 10

        fileswin.columnconfigure(0,weight=1)
        tk.Label(fileswin,text=' 文件操作',font=('Courier New',10),fg='#202020').grid(row=0,column=0,sticky='nsw')

        def btnSaveDo():
            rtn = self.et.saveTimetable()
            if rtn:
                self.updateTextFrames()
                tkmsg.showinfo('提示','保存成功！')
            else:
                tkmsg.showerror('错误','保存失败！')
            self.timetable = self.et.timetable
        def btnRestoreDo():
            self.et.settings = self.et.originSettings.copy()
            self.et.undo(-1)
            self.et.notSavedYet = False
            self.updateTextFrames()
            tkmsg.showinfo('提示','所有更改已撤销，但计划仍可以通过“重做”恢复。')
        def saveAsJson():
            btnCancelDo()
            self.main_showJsonwin()
        def saveAsTxt():
            btnCancelDo()
            self.main_showTxtwin()
        def btnExitDo():
            if self.et.notSavedYet:
                doFinalSave = tkmsg.askyesnocancel('提示','发尚未保存的改动！\n是否保存？')
                if doFinalSave == None:
                    return None
                if doFinalSave:
                    btnSaveDo()
            self.mainwin.destroy()
            exit()
        def btnCancelDo():
            nonlocal fileswin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            fileswin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()

        btnSave = tk.Button(fileswin,text='保存更改',font=('Courier New',10),command=btnSaveDo)
        btnSave.grid(row=1,column=0,padx=5,pady=3,sticky='nesw')
        btnRestore = tk.Button(fileswin,text='撤销所有更改',font=('Courier New',10),command=btnRestoreDo)
        btnRestore.grid(row=2,column=0,padx=5,pady=3,sticky='nesw')
        if self.et.isJson:
            btnSaveAs = tk.Button(fileswin,text='导出为TXT..',font=('Courier New',10),fg='#3540A0',command=saveAsTxt)
        else:
            btnSaveAs = tk.Button(fileswin,text='导出为JSON..',font=('Courier New',10),fg='#3540A0',command=saveAsJson)
        btnSaveAs.grid(row=3,column=0,padx=5,pady=3,sticky='nesw')
        btnExit = tk.Button(fileswin,text='退出程序',font=('Courier New',10),fg='#C04000',command=btnExitDo)
        btnExit.grid(row=4,column=0,padx=5,pady=3,sticky='nesw')
        btnCancel = tk.Button(fileswin,text='继续编辑',font=('Courier New',10),command=btnCancelDo)
        btnCancel.grid(row=10,column=0,padx=5,pady=[15,0],sticky='nesw')

        fileswin.mainloop()

    def main_showTxtwin(self):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
        txtwin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=350)  #column0 weights 10

        txtwin.columnconfigure(0,weight=5)
        txtwin.columnconfigure(1,weight=5)
        txtwin.columnconfigure(2,weight=10)
        txtwin.rowconfigure(3,weight=10)
        tk.Label(txtwin,text=' 导出为TXT',font=('Courier New',10),fg='#303030').grid(row=0,column=0,columnspan=2,sticky='nsw')
        tk.Label(txtwin,text='目标版本: ',font=('Courier New',10),fg='#151515').grid(row=1,column=0,sticky='nse')
        tk.Label(txtwin,text='timetable3 (适用于DDU_Clock_v1.3)',font=('Courier New',10),fg='#404040').grid(row=1,column=1,columnspan=3,sticky='nesw')
        def updatePreviewText(*args):
            self.et.filterValidSchedules()
            savingText = f'{self.et.timetable!r}\n{self.et.settings!r}\n# Timetable version: 3'
            previewText = '  预览：\n' + savingText
            textframe.delete('0.0','end')
            textframe.insert('0.0',previewText)
        
        textframe = tk.Text(txtwin,font=('Courier New',9),width=20)
        scrollBar = tk.Scrollbar(txtwin)
        def scrollEvent(*args):
            textframe.yview(*args)
        scrollBar.config(command=scrollEvent)
        scrollBar.grid(row=3,column=3,sticky='nesw')
        textframe.config(yscrollcommand=scrollBar.set)
        textframe.grid(row=3,column=0,columnspan=3,sticky='nesw')
        updatePreviewText(0)
        def btnCancelDo():
            nonlocal txtwin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            txtwin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()
        def btnConfirmDo():
            savingText = f'{self.et.timetable!r}\n{self.et.settings!r}\n# Timetable version: 3'
            savingDir = tkfile.asksaveasfilename(defaultextension='.txt',title='导出为TXT',initialdir='./',initialfile='timetable3')
            if savingDir == '':
                return None
            with open(savingDir,'w') as savingFile:
                try:
                    savingFile.write(savingText)
                except:
                    tkmsg.showerror('错误','保存失败！')
                else:
                    tkmsg.showinfo('提示','保存成功！')
            btnCancelDo()
        btnConfirm = tk.Button(txtwin,text='导出..',font=('Courier New',10),command=btnConfirmDo)
        btnConfirm.grid(row=10,column=0,columnspan=2,padx=2,pady=5,sticky='nesw')
        btnCancel = tk.Button(txtwin,text='取消',font=('Courier New',10),command=btnCancelDo)
        btnCancel.grid(row=10,column=2,padx=2,pady=5,sticky='nesw')

    def main_showJsonwin(self):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
        jsonwin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=350)  #column0 weights 10

        jsonwin.columnconfigure(0,weight=5)
        jsonwin.columnconfigure(1,weight=5)
        jsonwin.columnconfigure(2,weight=10)
        jsonwin.rowconfigure(3,weight=10)
        tk.Label(jsonwin,text=' 导出为JSON',font=('Courier New',10),fg='#303030').grid(row=0,column=0,columnspan=2,sticky='nsw')
        tk.Label(jsonwin,text='格式化展开程度: ',font=('Courier New',10),fg='#151515').grid(row=1,column=0,sticky='nse')
        def updatePreviewText(*args):
            previewText = self.et.timetable_to_json(indentLevel=targetIndentList.index(targetIndentVar.get()))
            previewText = '  预览：\n' + previewText
            textframe.delete('0.0','end')
            textframe.insert('0.0',previewText)
        targetIndentVar = tk.StringVar()
        targetIndentVar.set('部分展开(推荐)')
        targetIndentList = ['不展开','部分展开(推荐)','完全展开']
        targetIndentMenu = ttk.OptionMenu(jsonwin,targetIndentVar,'部分展开(推荐)',*targetIndentList,command=updatePreviewText)
        targetIndentMenu.grid(row=1,column=1,columnspan=3,sticky='nesw')
        
        textframe = tk.Text(jsonwin,font=('Courier New',9),width=20)
        scrollBar = tk.Scrollbar(jsonwin)
        def scrollEvent(*args):
            textframe.yview(*args)
        scrollBar.config(command=scrollEvent)
        scrollBar.grid(row=3,column=3,sticky='nesw')
        textframe.config(yscrollcommand=scrollBar.set)
        textframe.grid(row=3,column=0,columnspan=3,sticky='nesw')
        updatePreviewText(0)
        def btnCancelDo():
            nonlocal jsonwin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            jsonwin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()
        def btnConfirmDo():
            targetIndent = targetIndentList.index(targetIndentVar.get())
            savingText = self.et.timetable_to_json(indentLevel=targetIndent)
            savingDir = tkfile.asksaveasfilename(defaultextension='.json',title='导出为JSON',initialdir='./',initialfile='timetable3')
            if savingDir == '':
                return None
            with open(savingDir,'w') as savingFile:
                try:
                    savingFile.write(savingText)
                except:
                    tkmsg.showerror('错误','保存失败！')
                else:
                    tkmsg.showinfo('提示','保存成功！')
            btnCancelDo()
        btnConfirm = tk.Button(jsonwin,text='导出..',font=('Courier New',10),command=btnConfirmDo)
        btnConfirm.grid(row=10,column=0,columnspan=2,padx=2,pady=5,sticky='nesw')
        btnCancel = tk.Button(jsonwin,text='取消',font=('Courier New',10),command=btnCancelDo)
        btnCancel.grid(row=10,column=2,padx=2,pady=5,sticky='nesw')

    def main_showSettingswin(self):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nesw',padx=[3,0])
        settwin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=360)  #column0 weights 10

        settwin.rowconfigure(0,weight=10)
        settingsDict = self.et.settings.copy()

        settwin.columnconfigure(0,weight=1)
        invalidCode = [0,0,0,0,0,0,0,0,0,0,0,0,0]   # [0=screenSize, 1=textFont1, 2=textFont2, 3=textFont3, 4=textFont4, 5=textFont5, 6=bgpicPath0, 7=bgpicPath1, 8=bgAlpha, 9=columnarGapMergeThreshold, 10=maxTps, 11=colorfuncsX0, 12=colorfuncsX1]
        tk.Label(settwin,text=' 编辑设置项',font=('Courier New',10),fg='#404040').grid(row=0,column=0,columnspan=10,sticky='nw')

        #region page0
        settPage0 = tk.Frame(settwin,relief='flat',bd=0)
        settPage0.columnconfigure(0,weight=10)
        settPage0.columnconfigure(1,weight=10)
        settPage0.columnconfigure(2,weight=20)

        #region frameDarkMode (row=1,column=0)
        frameDarkMode = tk.Frame(settPage0,relief='ridge',bd=3)
        frameDarkMode.columnconfigure(0,weight=10)
        frameDarkMode.columnconfigure(1,weight=5)
        tk.Label(frameDarkMode,text='暗色模式:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nse')
        varDarkMode = tk.StringVar()
        varDarkMode.set('开' if settingsDict['darkMode'] else '关')
        fgColor = '#209610' if settingsDict['darkMode'] else '#943015'
        def btnDarkModeDo():
            settingsDict['darkMode'] = not(settingsDict['darkMode'])
            varDarkMode.set('开' if settingsDict['darkMode'] else '关')
            fgColor = '#209610' if settingsDict['darkMode'] else '#943015'
            btnDarkMode.config(fg=fgColor)
        btnDarkMode = tk.Button(frameDarkMode,textvariable=varDarkMode,font=('Courier New',10,'bold'),fg=fgColor,bd=1,command=btnDarkModeDo)
        btnDarkMode.grid(row=0,column=1,sticky='nesw',padx=1.5,pady=1.5)
        frameDarkMode.grid(row=1,column=0,padx=2,pady=1,sticky='nesw')
        #endregion

        #region frameCompressLevel (row=1,column=1)
        frameCompressLevel = tk.Frame(settPage0,relief='ridge',bd=3)
        frameCompressLevel.columnconfigure(0,weight=10)
        frameCompressLevel.columnconfigure(1,weight=5)
        tk.Label(frameCompressLevel,text='简略模式:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nse')
        varCompressLevel = tk.StringVar()
        varCompressLevel.set(f"{settingsDict['compressLevel']}挡")
        colorsCompressLevel = ['#202590','#4560CC','#6680FF']
        fgColor = colorsCompressLevel[settingsDict['compressLevel']]
        def btnCompressLevelDo():
            if settingsDict['compressLevel'] in [0,1]:
                settingsDict['compressLevel'] += 1
            else:
                settingsDict['compressLevel'] = 0
            varCompressLevel.set(f"{settingsDict['compressLevel']}挡")
            fgColor = colorsCompressLevel[settingsDict['compressLevel']]
            btnCompressLevel.config(fg=fgColor)
        btnCompressLevel = tk.Button(frameCompressLevel,textvariable=varCompressLevel,font=('Courier New',10,'bold'),fg=fgColor,bd=1,command=btnCompressLevelDo)
        btnCompressLevel.grid(row=0,column=1,sticky='nesw',padx=1.5,pady=1.5)
        frameCompressLevel.grid(row=1,column=1,padx=2,pady=1,sticky='nesw')
        #endregion

        #region frameDoTimetableSearch (row=1,column=2)
        frameDoTimetableSearch = tk.Frame(settPage0,relief='ridge',bd=3)
        frameDoTimetableSearch.columnconfigure(0,weight=10)
        frameDoTimetableSearch.columnconfigure(1,weight=5)
        tk.Label(frameDoTimetableSearch,text='是否跟进计划:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nse')
        varDoTimetableSearch = tk.StringVar()
        varDoTimetableSearch.set('是' if settingsDict['doTimetableSearch'] else '否')
        fgColor = '#209610' if settingsDict['doTimetableSearch'] else '#943015'
        def btnDoTimetableSearchDo():
            settingsDict['doTimetableSearch'] = not(settingsDict['doTimetableSearch'])
            varDoTimetableSearch.set('是' if settingsDict['doTimetableSearch'] else '否')
            fgColor = '#209610' if settingsDict['doTimetableSearch'] else '#943015'
            btnDoTimetableSearch.config(fg=fgColor)
        btnDoTimetableSearch = tk.Button(frameDoTimetableSearch,textvariable=varDoTimetableSearch,font=('Courier New',9,'bold'),fg=fgColor,bd=1,command=btnDoTimetableSearchDo)
        btnDoTimetableSearch.grid(row=0,column=1,sticky='nesw',padx=1.5,pady=1.5)
        frameDoTimetableSearch.grid(row=1,column=2,padx=2,pady=1,sticky='nesw')
        #endregion

        #region frameScreenSize (row=2,column=0,columnspan=3)
        frameScreenSize = tk.Frame(settPage0,relief='ridge',bd=3)
        frameScreenSize.columnconfigure(0,weight=8)
        frameScreenSize.columnconfigure(1,weight=10)
        frameScreenSize.columnconfigure(2,weight=4)
        frameScreenSize.columnconfigure(3,weight=10)
        tk.Label(frameScreenSize,text='窗口大小(/像素): x=',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nesw')
        tk.Label(frameScreenSize,text=', y=',font=('Courier New',10),fg='#161616').grid(row=0,column=2,sticky='nesw')
        colorsScreenSize = ['#204010','#F04030']
        fgColor = colorsScreenSize[0]
        def entryX_callback(*args):
            rawSizeX = entryScreenSizeX.get()
            valid = False
            try:
                sizeX = eval(rawSizeX)
                if type(sizeX) == int and sizeX>0:
                    valid = True
            except:
                pass
            if valid:
                entryScreenSizeX.config(fg=colorsScreenSize[0])
                invalidCode[0] = 0
            else:
                entryScreenSizeX.config(fg=colorsScreenSize[1])
                invalidCode[0] = 1
        def entryY_callback(*args):
            rawSizeY = entryScreenSizeY.get()
            valid = False
            try:
                sizeY = eval(rawSizeY)
                if type(sizeY) == int and sizeY>0:
                    valid = True
            except:
                pass
            if valid:
                entryScreenSizeY.config(fg=colorsScreenSize[0])
            else:
                entryScreenSizeY.config(fg=colorsScreenSize[1])
        varScreenSizeX = tk.StringVar()
        varScreenSizeY = tk.StringVar()
        varScreenSizeX.set(str(settingsDict['screenSize'][0]))
        varScreenSizeY.set(str(settingsDict['screenSize'][1]))
        varScreenSizeX.trace_add('write',entryX_callback)
        varScreenSizeY.trace_add('write',entryY_callback)

        entryScreenSizeX = tk.Entry(frameScreenSize,textvariable=varScreenSizeX,font=('Courier New',11,'bold'),fg=fgColor,bg='#EFEFEF',bd=1,width=5)
        entryScreenSizeX.grid(row=0,column=1,sticky='nesw',padx=0,pady=3)
        entryScreenSizeY = tk.Entry(frameScreenSize,textvariable=varScreenSizeY,font=('Courier New',11,'bold'),fg=fgColor,bg='#EFEFEF',bd=1,width=5)
        entryScreenSizeY.grid(row=0,column=3,sticky='nesw',padx=[0,1.5],pady=3)
        frameScreenSize.grid(row=2,column=0,columnspan=3,padx=2,pady=1,sticky='nesw')
        #endregion

        #region frameTextFonts (row=3,column=0,columnspan=3)
        rawAllPgFonts = get_all_pg_fonts()
        allPgFonts = get_all_pg_fonts()
        for font in settingsDict['textFonts'][::-1]:
            if not (font in rawAllPgFonts):
                allPgFonts.insert(0,font)

        frameTextFonts = tk.Frame(settPage0,relief='ridge',bd=3)
        frameTextFonts.columnconfigure(0,weight=1)
        frameTextFonts.columnconfigure(1,weight=20)
        frameTextFonts.columnconfigure(2,weight=3)
        tk.Label(frameTextFonts,text='自定义字体:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,columnspan=2,sticky='nsw')
        colorsTextFonts = ['#204010','#F04030']

        tk.Label(frameTextFonts,text='1.',font=('Courier New',10),fg='#505050').grid(row=1,column=0,sticky='nse',pady=2)
        fgColor1 = colorsTextFonts[0]
        def entryFont1_callback(*args):
            font1 = varFont1.get()
            if exists(font1) or (font1 in rawAllPgFonts):
                entryFont1.config(foreground=colorsTextFonts[0])
                invalidCode[1] = 0
            else:
                entryFont1.config(foreground=colorsTextFonts[1])
                invalidCode[1] = 1
        varFont1 = tk.StringVar()
        varFont1.set(settingsDict['textFonts'][0])
        varFont1.trace_add('write',entryFont1_callback)
        entryFont1 = ttk.Combobox(frameTextFonts,textvariable=varFont1,values=allPgFonts,font=('Courier New',10,'bold'),foreground=fgColor1,background='#EFEFEF')
        entryFont1_callback(0)
        entryFont1.grid(row=1,column=1,sticky='nesw',pady=2)
        def btnBrowse1Do():
            path = tkfile.askopenfilename(defaultextension='.ttf',title='选择一个字体文件',initialdir='C:/Windows/Fonts/')
            if exists(path):
                varFont1.set(path)
        btnBrowse1 = tk.Button(frameTextFonts,text='浏览..',font=('Courier New',9),fg='#404070',bd=1,command=btnBrowse1Do)
        btnBrowse1.grid(row=1,column=2,sticky='nesw',padx=1.5,pady=2)

        tk.Label(frameTextFonts,text='2.',font=('Courier New',10),fg='#505050').grid(row=2,column=0,sticky='nse',pady=2)
        fgColor2 = colorsTextFonts[0]
        def entryFont2_callback(*args):
            font2 = varFont2.get()
            if exists(font2) or (font2 in rawAllPgFonts):
                entryFont2.config(foreground=colorsTextFonts[0])
                invalidCode[2] = 0
            else:
                entryFont2.config(foreground=colorsTextFonts[1])
                invalidCode[2] = 1
        varFont2 = tk.StringVar()
        varFont2.set(settingsDict['textFonts'][1])
        varFont2.trace_add('write',entryFont2_callback)
        entryFont2 = ttk.Combobox(frameTextFonts,textvariable=varFont2,values=allPgFonts,font=('Courier New',10,'bold'),foreground=fgColor2,background='#EFEFEF')
        entryFont2_callback(0)
        entryFont2.grid(row=2,column=1,sticky='nesw',pady=2)
        def btnBrowse2Do():
            path = tkfile.askopenfilename(defaultextension='.ttf',title='选择一个字体文件',initialdir='C:/Windows/Fonts/')
            if exists(path):
                varFont2.set(path)
        btnBrowse2 = tk.Button(frameTextFonts,text='浏览..',font=('Courier New',9),fg='#404070',bd=1,command=btnBrowse2Do)
        btnBrowse2.grid(row=2,column=2,sticky='nesw',padx=1.5,pady=2)

        tk.Label(frameTextFonts,text='3.',font=('Courier New',10),fg='#505050').grid(row=3,column=0,sticky='nse',pady=2)
        fgColor3 = colorsTextFonts[0]
        def entryFont3_callback(*args):
            font3 = varFont3.get()
            if exists(font3) or (font3 in rawAllPgFonts):
                entryFont3.config(foreground=colorsTextFonts[0])
                invalidCode[3] = 0
            else:
                entryFont3.config(foreground=colorsTextFonts[1])
                invalidCode[3] = 1
        varFont3 = tk.StringVar()
        varFont3.set(settingsDict['textFonts'][2])
        varFont3.trace_add('write',entryFont3_callback)
        entryFont3 = ttk.Combobox(frameTextFonts,textvariable=varFont3,values=allPgFonts,font=('Courier New',10,'bold'),foreground=fgColor3,background='#EFEFEF')
        entryFont3_callback(0)
        entryFont3.grid(row=3,column=1,sticky='nesw',pady=2)
        def btnBrowse3Do():
            path = tkfile.askopenfilename(defaultextension='.ttf',title='选择一个字体文件',initialdir='C:/Windows/Fonts/')
            if exists(path):
                varFont3.set(path)
        btnBrowse3 = tk.Button(frameTextFonts,text='浏览..',font=('Courier New',9),fg='#404070',bd=1,command=btnBrowse3Do)
        btnBrowse3.grid(row=3,column=2,sticky='nesw',padx=1.5,pady=2)

        tk.Label(frameTextFonts,text='4.',font=('Courier New',10),fg='#505050').grid(row=4,column=0,sticky='nse',pady=2)
        fgColor4 = colorsTextFonts[0]
        def entryFont4_callback(*args):
            font4 = varFont4.get()
            if exists(font4) or (font4 in rawAllPgFonts):
                entryFont4.config(foreground=colorsTextFonts[0])
                invalidCode[4] = 0
            else:
                entryFont4.config(foreground=colorsTextFonts[1])
                invalidCode[4] = 1
        varFont4 = tk.StringVar()
        varFont4.set(settingsDict['textFonts'][3])
        varFont4.trace_add('write',entryFont4_callback)
        entryFont4 = ttk.Combobox(frameTextFonts,textvariable=varFont4,values=allPgFonts,font=('Courier New',10,'bold'),foreground=fgColor4,background='#EFEFEF')
        entryFont4_callback(0)
        entryFont4.grid(row=4,column=1,sticky='nesw',pady=2)
        def btnBrowse4Do():
            path = tkfile.askopenfilename(defaultextension='.ttf',title='选择一个字体文件',initialdir='C:/Windows/Fonts/')
            if exists(path):
                varFont4.set(path)
        btnBrowse4 = tk.Button(frameTextFonts,text='浏览..',font=('Courier New',9),fg='#404070',bd=1,command=btnBrowse4Do)
        btnBrowse4.grid(row=4,column=2,sticky='nesw',padx=1.5,pady=2)

        tk.Label(frameTextFonts,text='5.',font=('Courier New',10),fg='#505050').grid(row=5,column=0,sticky='nse',pady=2)
        fgColor5 = colorsTextFonts[0]
        def entryFont5_callback(*args):
            font5 = varFont5.get()
            if exists(font5) or (font5 in rawAllPgFonts):
                entryFont5.config(foreground=colorsTextFonts[0])
                invalidCode[5] = 0
            else:
                entryFont5.config(foreground=colorsTextFonts[1])
                invalidCode[5] = 1
        varFont5 = tk.StringVar()
        varFont5.set(settingsDict['textFonts'][4])
        varFont5.trace_add('write',entryFont5_callback)
        entryFont5 = ttk.Combobox(frameTextFonts,textvariable=varFont5,values=allPgFonts,font=('Courier New',10,'bold'),foreground=fgColor5,background='#EFEFEF')
        entryFont5_callback(0)
        entryFont5.grid(row=5,column=1,sticky='nesw',pady=2)
        def btnBrowse5Do():
            path = tkfile.askopenfilename(defaultextension='.ttf',title='选择一个字体文件',initialdir='C:/Windows/Fonts/')
            if exists(path):
                varFont5.set(path)
        btnBrowse5 = tk.Button(frameTextFonts,text='浏览..',font=('Courier New',9),fg='#404070',bd=1,command=btnBrowse5Do)
        btnBrowse5.grid(row=5,column=2,sticky='nesw',padx=1.5,pady=2)

        frameTextFonts.grid(row=3,column=0,columnspan=3,padx=2,sticky='nesw')
        #endregion

        #region bgpics
        frameBgs = tk.Frame(settPage0,relief='ridge',bd=3)
        frameBgs.grid_columnconfigure(1,weight=10)
        tk.Label(frameBgs,text='背景图片:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nsw')
        
        frame1 = tk.Frame(frameBgs,relief='flat',bd=0)
        frame1.grid_columnconfigure(0,weight=10)
        frame1.grid_columnconfigure(1,weight=10)

        varBg0 = tk.StringVar()
        varBg0.set('①暗色模式下：开' if settingsDict['doBackgroundImgDisplay'][0] else '①暗色模式下：关')
        fgColor = '#209610' if settingsDict['doBackgroundImgDisplay'][0] else '#943015'
        def btnBg0Do():
            settingsDict['doBackgroundImgDisplay'][0] = not(settingsDict['doBackgroundImgDisplay'][0])
            varBg0.set('①暗色模式下：开' if settingsDict['doBackgroundImgDisplay'][0] else '①暗色模式下：关')
            fgColor = '#209610' if settingsDict['doBackgroundImgDisplay'][0] else '#943015'
            btnBg0.config(fg=fgColor)
        btnBg0 = tk.Button(frame1,textvariable=varBg0,font=('Courier New',10,'bold'),fg=fgColor,bd=1,command=btnBg0Do)
        btnBg0.grid(row=0,column=0,sticky='nesw',padx=1.5,pady=1.5)
        
        varBg1 = tk.StringVar()
        varBg1.set('②亮色模式下：开' if settingsDict['doBackgroundImgDisplay'][1] else '②亮色模式下：关')
        fgColor = '#209610' if settingsDict['doBackgroundImgDisplay'][1] else '#943015'
        def btnBg1Do():
            settingsDict['doBackgroundImgDisplay'][1] = not(settingsDict['doBackgroundImgDisplay'][1])
            varBg1.set('②亮色模式下：开' if settingsDict['doBackgroundImgDisplay'][1] else '②亮色模式下：关')
            fgColor = '#209610' if settingsDict['doBackgroundImgDisplay'][1] else '#943015'
            btnBg1.config(fg=fgColor)
        btnBg1 = tk.Button(frame1,textvariable=varBg1,font=('Courier New',10,'bold'),fg=fgColor,bd=1,command=btnBg1Do)
        btnBg1.grid(row=0,column=1,sticky='nesw',padx=1.5,pady=1.5)

        frame1.grid(row=0,column=1,columnspan=10)
        
        tk.Label(frameBgs,text='①路径:',font=('Courier New',10),fg='#505050').grid(row=2,column=0,sticky='nse',pady=2)
        fgColor0 = colorsTextFonts[0]
        def entryPath0_callback(*args):
            path0 = varPath0.get()
            if exists(path0) or (path0 in rawAllPgFonts):
                entryPath0.config(foreground=colorsTextFonts[0])
                invalidCode[6] = 0
            else:
                entryPath0.config(foreground=colorsTextFonts[1])
                invalidCode[6] = 1
        varPath0 = tk.StringVar()
        varPath0.set(settingsDict['backgroundImgPaths'][0])
        varPath0.trace_add('write',entryPath0_callback)
        entryPath0 = ttk.Entry(frameBgs,textvariable=varPath0,font=('Courier New',10,'bold'),foreground=fgColor0,background='#EFEFEF')
        entryPath0_callback(0)
        entryPath0.grid(row=2,column=1,sticky='nesw',pady=2)
        def btnBrowseBg0Do():
            path = tkfile.askopenfilename(defaultextension='.ttf',title='选择一个图片文件',initialdir=self.et.separate_dir_and_filename(varPath0.get())[0])
            if exists(path):
                varPath0.set(path)
        btnBrowseBg0 = tk.Button(frameBgs,text='浏览..',font=('Courier New',9),fg='#404070',bd=1,command=btnBrowseBg0Do)
        btnBrowseBg0.grid(row=2,column=2,sticky='nesw',padx=1.5,pady=2)

        tk.Label(frameBgs,text='②路径:',font=('Courier New',10),fg='#505050').grid(row=3,column=0,sticky='nse',pady=2)
        fgColor1 = colorsTextFonts[0]
        def entryPath1_callback(*args):
            path1 = varPath1.get()
            if exists(path1) or (path1 in rawAllPgFonts):
                entryPath1.config(foreground=colorsTextFonts[0])
                invalidCode[7] = 0
            else:
                entryPath1.config(foreground=colorsTextFonts[1])
                invalidCode[7] = 1
        varPath1 = tk.StringVar()
        varPath1.set(settingsDict['backgroundImgPaths'][1])
        varPath1.trace_add('write',entryPath1_callback)
        entryPath1 = ttk.Entry(frameBgs,textvariable=varPath1,font=('Courier New',10,'bold'),foreground=fgColor1,background='#EFEFEF')
        entryPath1_callback(0)
        entryPath1.grid(row=3,column=1,sticky='nesw',pady=2)
        def btnBrowseBg1Do():
            path = tkfile.askopenfilename(defaultextension='.ttf',title='选择一个图片文件',initialdir=self.et.separate_dir_and_filename(varPath1.get())[0])
            if exists(path):
                varPath1.set(path)
        btnBrowseBg1 = tk.Button(frameBgs,text='浏览..',font=('Courier New',9),fg='#404070',bd=1,command=btnBrowseBg1Do)
        btnBrowseBg1.grid(row=3,column=2,sticky='nesw',padx=1.5,pady=2)

        tk.Label(frameBgs,text='背景不透明度:',font=('Courier New',9),fg='#505050').grid(row=4,column=0,sticky='nse',pady=2)
        colorsColumnarGapMergeThreshold = ['#204010','#F04030']
        def bgAlphaSpinbox_callback(*args):
            rawBgAlpha = bgAlphaSpinbox.get()
            valid = False
            try:
                bgAlpha = eval(rawBgAlpha)
                if bgAlpha in range(0,101):
                    valid = True
            except:
                pass
            if valid:
                bgAlphaSpinbox.config(foreground=colorsColumnarGapMergeThreshold[0])
                invalidCode[8] = 0
            else:
                bgAlphaSpinbox.config(oreground=colorsColumnarGapMergeThreshold[1])
                invalidCode[8] = 1
        varBgAlpha = tk.StringVar()
        varBgAlpha.trace_add('write',bgAlphaSpinbox_callback)
        bgAlphaSpinbox = ttk.Spinbox(frameBgs,from_=0,to=100,increment=5,textvariable=varBgAlpha,font=('Courier New',10))
        bgAlphaSpinbox.set(settingsDict['backgroundAlpha'])
        bgAlphaSpinbox.grid(row=4,column=1)
        
        frameBgs.grid(row=4,column=0,columnspan=3,padx=2,pady=1,sticky='nesw')
        #endregion

        #endregion

        #region page1
        settPage1 = tk.Frame(settwin,relief='flat',bd=0)
        settPage1.columnconfigure(0,weight=10)
        settPage1.columnconfigure(1,weight=10)
        settPage1.columnconfigure(2,weight=20)

        #region language
        frameLanguage = tk.Frame(settPage1,relief='ridge',bd=3)
        frameLanguage.columnconfigure(1,weight=10)
        tk.Label(frameLanguage,text='默认语言:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,padx=[5,0],sticky='nse')
        varLanguage = tk.StringVar()
        varLanguage.set(settingsDict['language'])
        def btnLanguageDo():
            if settingsDict['language'] == 'Chinese中文':
                settingsDict['language'] = 'English英文'
            else:
                settingsDict['language'] = 'Chinese中文'
            varLanguage.set(settingsDict['language'])
        btnLanguage = tk.Button(frameLanguage,textvariable=varLanguage,font=('Courier New',10,'bold'),fg='#081060',bd=1,command=btnLanguageDo)
        btnLanguage.grid(row=0,column=1,sticky='nesw',padx=2,pady=1.5)
        frameLanguage.grid(row=0,column=0,columnspan=5,padx=2,pady=1,sticky='nesw')
        #endregion

        #region timeOffset
        frameTimeOffset = tk.Frame(settPage1,relief='ridge',bd=3)
        frameTimeOffset.columnconfigure(0,weight=8)
        frameTimeOffset.columnconfigure(1,weight=10)
        frameTimeOffset.columnconfigure(2,weight=4)
        frameTimeOffset.columnconfigure(3,weight=10)
        tk.Label(frameTimeOffset,text='时间纠差：',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nesw')
        colorsTimeOffset = ['#204010','#F04030']
        fgColor = colorsTimeOffset[0]

        varTimeOffsetDirection = tk.StringVar()
        varTimeOffsetDirection.set('延后')
        def btnTimeOffsetDirectionDo():
            if varTimeOffsetDirection.get() == '延后':
                varTimeOffsetDirection.set('提前')
            else:
                varTimeOffsetDirection.set('延后')
        btnTimeOffsetDirection = tk.Button(frameTimeOffset,textvariable=varTimeOffsetDirection,font=('Courier New',9),fg='#081060',bd=1,command=btnTimeOffsetDirectionDo)
        btnTimeOffsetDirection.grid(row=0,column=1,columnspan=2,sticky='nesw',padx=[0,4],pady=1)

        entryTimeOffsetDays = ttk.Spinbox(frameTimeOffset,from_=0,to=999,font=('Courier New',11,'bold'),width=5)
        entryTimeOffsetDays.set(0)
        entryTimeOffsetDays.grid(row=0,column=3,sticky='nesw',padx=0,pady=1)
        tk.Label(frameTimeOffset,text='天 ',font=('Courier New',9),fg='#161616').grid(row=0,column=4,sticky='nesw')
        entryTimeOffsetHours = ttk.Spinbox(frameTimeOffset,from_=0,to=23,font=('Courier New',11,'bold'),width=5)
        entryTimeOffsetHours.set(0)
        entryTimeOffsetHours.grid(row=0,column=5,sticky='nesw',padx=0,pady=1)
        tk.Label(frameTimeOffset,text='时 ',font=('Courier New',9),fg='#161616').grid(row=0,column=6,sticky='nesw')
        entryTimeOffsetMinutes = ttk.Spinbox(frameTimeOffset,from_=0,to=59,font=('Courier New',11,'bold'),width=5)
        entryTimeOffsetMinutes.set(0)
        entryTimeOffsetMinutes.grid(row=1,column=1,sticky='nesw',padx=0,pady=1)
        tk.Label(frameTimeOffset,text='分 ',font=('Courier New',9),fg='#161616').grid(row=1,column=2,sticky='nesw')
        entryTimeOffsetSeconds = ttk.Spinbox(frameTimeOffset,from_=0,to=59,font=('Courier New',11,'bold'),width=5)
        entryTimeOffsetSeconds.set(0)
        entryTimeOffsetSeconds.grid(row=1,column=3,sticky='nesw',padx=0,pady=1)
        tk.Label(frameTimeOffset,text='秒 ',font=('Courier New',9),fg='#161616').grid(row=1,column=4,sticky='nesw')
        entryTimeOffsetMilliseconds = ttk.Spinbox(frameTimeOffset,from_=0,to=999,increment=50,font=('Courier New',11,'bold'),width=5)
        entryTimeOffsetMilliseconds.set(0)
        entryTimeOffsetMilliseconds.grid(row=1,column=5,sticky='nesw',padx=0,pady=1)
        tk.Label(frameTimeOffset,text='毫秒 ',font=('Courier New',9),fg='#161616').grid(row=1,column=6,sticky='nesw')
        frameTimeOffset.grid(row=1,column=0,columnspan=3,padx=2,pady=1,sticky='nesw')
        #endregion

        #region colorfuncs
        def rgb_to_hex(r:int,g:int,b:int) -> str:
            hexNumberNames = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
            if r < 0:
                r = 0
            elif r > 255:
                r = 255
            if g < 0:
                g = 0
            elif g > 255:
                g = 255
            if b < 0:
                b = 0
            elif b > 255:
                b = 255
            hexColor = '#'+hexNumberNames[r//16]+hexNumberNames[r%16]+hexNumberNames[g//16]+hexNumberNames[g%16]+hexNumberNames[b//16]+hexNumberNames[b%16]
            return hexColor
        def hex_to_rgb(hexColor:str) -> Tuple[int,int,int]:
            hexNumberNames = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
            r = hexNumberNames.index(hexColor[1])*16+hexNumberNames.index(hexColor[2])
            g = hexNumberNames.index(hexColor[3])*16+hexNumberNames.index(hexColor[4])
            b = hexNumberNames.index(hexColor[5])*16+hexNumberNames.index(hexColor[6])
            if r < 0:
                r = 0
            elif r > 255:
                r = 255
            if g < 0:
                g = 0
            elif g > 255:
                g = 255
            if b < 0:
                b = 0
            elif b > 255:
                b = 255
            return (r,g,b)
        def workOutFuncs(rgb0:Tuple[int,int,int],rgb1:Tuple[int,int,int]) -> List[str]:
            funcs = ['','','']
            for i in range(3):
                a = rgb1[i]-rgb0[i]
                b = rgb0[i]
                funcs[i] = f'({a}/255)*x+{b}'
            return funcs
        colorsTextFonts = ['#204010','#F04030']
        frameColorfuncs = tk.Frame(settPage1,relief='ridge',bd=3)
        frameColorfuncs.columnconfigure(0,weight=10)
        frameColorfuncs.columnconfigure(1,weight=10)
        tk.Label(frameColorfuncs,text='界面前景色: 暗色模式下',font=('Courier New',9),fg='#161616').grid(row=0,column=0,padx=[5,0],sticky='nsw')
        tk.Label(frameColorfuncs,text='亮色模式下',font=('Courier New',9),fg='#161616').grid(row=0,column=1,padx=[5,0],sticky='nesw')

        #region under_darkmode
        frameFuncDisplays0 = tk.Frame(frameColorfuncs)
        frameFuncDisplays0.columnconfigure(1,weight=10)
        tk.Label(frameFuncDisplays0,text='R:',font=('Courier New',9),fg='#A02020').grid(row=0,column=0,sticky='nse',pady=2)
        varFuncR0 = tk.StringVar()
        varFuncR0.set(settingsDict['colorfuncs'][0][0])
        entryFuncR0 = ttk.Entry(frameFuncDisplays0,textvariable=varFuncR0,font=('Courier New',9),foreground='#204010',background='#EFEFEF')
        entryFuncR0.grid(row=0,column=1,sticky='nesw',pady=2)
        tk.Label(frameFuncDisplays0,text='G:',font=('Courier New',9),fg='#20A020').grid(row=1,column=0,sticky='nse',pady=2)
        varFuncG0 = tk.StringVar()
        varFuncG0.set(settingsDict['colorfuncs'][0][1])
        entryFuncG0 = ttk.Entry(frameFuncDisplays0,textvariable=varFuncG0,font=('Courier New',9),foreground='#204010',background='#EFEFEF')
        entryFuncG0.grid(row=1,column=1,sticky='nesw',pady=2)
        tk.Label(frameFuncDisplays0,text='B:',font=('Courier New',9),fg='#2020A0').grid(row=2,column=0,sticky='nse',pady=2)
        varFuncB0 = tk.StringVar()
        varFuncB0.set(settingsDict['colorfuncs'][0][2])
        entryFuncB0 = ttk.Entry(frameFuncDisplays0,textvariable=varFuncB0,font=('Courier New',9),foreground='#204010',background='#EFEFEF')
        entryFuncB0.grid(row=2,column=1,sticky='nesw',pady=2)
        frameFuncDisplays0.grid(row=2,column=0,padx=[2,5])

        frameColorDisplays0 = tk.Frame(frameColorfuncs,relief='sunken',bd=2)
        for i in range(1,16):
            frameColorDisplays0.columnconfigure(i,weight=10)
        x = 0
        color00 = rgb_to_hex(int(eval(settingsDict['colorfuncs'][0][0])),int(eval(settingsDict['colorfuncs'][0][1])),int(eval(settingsDict['colorfuncs'][0][2])))
        x = 255
        color01 = rgb_to_hex(int(eval(settingsDict['colorfuncs'][0][0])),int(eval(settingsDict['colorfuncs'][0][1])),int(eval(settingsDict['colorfuncs'][0][2])))
        def btn00_do():
            nonlocal color00
            colorResult = tkcolor.askcolor(color00,title='选择颜色')
            if colorResult == (None,None):
                return None
            else:
                color00 = colorResult[1].upper()
            btn00 = tk.Button(frameColorDisplays0,text=' ',font=('Courier New',6),bg=color00,height=1,width=1,command=btn00_do)
            btn00.grid(row=0,column=0,padx=[1,0],pady=1,sticky='nsw')
            settingsDict['colorfuncs'][0] = workOutFuncs(hex_to_rgb(color00),hex_to_rgb(color01))
            for i in range(1,16):
                x = 16*i
                color = rgb_to_hex(int(eval(settingsDict['colorfuncs'][0][0])),int(eval(settingsDict['colorfuncs'][0][1])),int(eval(settingsDict['colorfuncs'][0][2])))
                tk.Label(frameColorDisplays0,text=' ',font=('Courier New',1),height=2,width=1,bg=color).grid(row=0,column=i,sticky='ew')
            varFuncR0.set(settingsDict['colorfuncs'][0][0])
            varFuncG0.set(settingsDict['colorfuncs'][0][1])
            varFuncB0.set(settingsDict['colorfuncs'][0][2])
        btn00 = tk.Button(frameColorDisplays0,text=' ',font=('Courier New',6),bg=color00,height=1,width=1,command=btn00_do)
        btn00.grid(row=0,column=0,padx=[1,0],pady=1,sticky='nsw')
        def btn01_do():
            nonlocal color01
            colorResult = tkcolor.askcolor(color01,title='选择颜色')
            if colorResult == (None,None):
                return None
            else:
                color01 = colorResult[1].upper()
            btn01 = tk.Button(frameColorDisplays0,text=' ',font=('Courier New',6),bg=color01,height=1,width=1,bd=1,command=btn01_do)
            btn01.grid(row=0,column=16,padx=[0,1],pady=1,sticky='nsw')
            settingsDict['colorfuncs'][0] = workOutFuncs(hex_to_rgb(color00),hex_to_rgb(color01))
            for i in range(1,16):
                x = 16*i
                color = rgb_to_hex(int(eval(settingsDict['colorfuncs'][0][0])),int(eval(settingsDict['colorfuncs'][0][1])),int(eval(settingsDict['colorfuncs'][0][2])))
                tk.Label(frameColorDisplays0,text=' ',font=('Courier New',1),height=2,width=1,bg=color).grid(row=0,column=i,sticky='ew')
            varFuncR0.set(settingsDict['colorfuncs'][0][0])
            varFuncG0.set(settingsDict['colorfuncs'][0][1])
            varFuncB0.set(settingsDict['colorfuncs'][0][2])
        btn01 = tk.Button(frameColorDisplays0,text=' ',font=('Courier New',6),bg=color01,height=1,width=1,bd=1,command=btn01_do)
        btn01.grid(row=0,column=16,padx=[0,1],pady=1,sticky='nse')
        for i in range(1,16):
            x = 16*i
            color = rgb_to_hex(int(eval(settingsDict['colorfuncs'][0][0])),int(eval(settingsDict['colorfuncs'][0][1])),int(eval(settingsDict['colorfuncs'][0][2])))
            tk.Label(frameColorDisplays0,text=' ',font=('Courier New',1),height=2,width=1,bg=color).grid(row=0,column=i,sticky='ew')

        def entryFuncX0_callback(idx:int):
            '''idx: (R0 = 0, G0 = 1, B0 = 2)'''
            nonlocal invalidCode,color00,color01
            varName = [varFuncR0,varFuncG0,varFuncB0][idx]
            entryName = [entryFuncR0,entryFuncG0,entryFuncB0][idx]
            func = varName.get()
            x = 0
            try:
                eval(func)
            except:
                entryName.config(foreground='#F04030')
                invalidCode[11] = 1
            else:
                entryName.config(foreground='#204010')
                invalidCode[11] = 0
                settingsDict['colorfuncs'][0][idx] = func
                x = 0
                color00 = rgb_to_hex(int(eval(settingsDict['colorfuncs'][0][0])),int(eval(settingsDict['colorfuncs'][0][1])),int(eval(settingsDict['colorfuncs'][0][2])))
                x = 255
                color01 = rgb_to_hex(int(eval(settingsDict['colorfuncs'][0][0])),int(eval(settingsDict['colorfuncs'][0][1])),int(eval(settingsDict['colorfuncs'][0][2])))
                btn00.config(bg=color00)
                btn01.config(bg=color01)
                for i in range(1,16):
                    x = 16*i
                    color = rgb_to_hex(int(eval(settingsDict['colorfuncs'][0][0])),int(eval(settingsDict['colorfuncs'][0][1])),int(eval(settingsDict['colorfuncs'][0][2])))
                    tk.Label(frameColorDisplays0,text=' ',font=('Courier New',1),height=2,width=1,bg=color).grid(row=0,column=i,sticky='ew')
        def entryFuncR0_callback(*args):
            entryFuncX0_callback(0)
        varFuncR0.trace_add('write',entryFuncR0_callback)
        def entryFuncG0_callback(*args):
            entryFuncX0_callback(1)
        varFuncG0.trace_add('write',entryFuncG0_callback)
        def entryFuncB0_callback(*args):
            entryFuncX0_callback(2)
        varFuncB0.trace_add('write',entryFuncB0_callback)
        frameColorDisplays0.grid(row=1,column=0,padx=[2,5],pady=2,sticky='nesw')
        #endregion

        #region under_lightmode
        frameFuncDisplays1 = tk.Frame(frameColorfuncs)
        frameFuncDisplays1.columnconfigure(1,weight=10)
        tk.Label(frameFuncDisplays1,text='R:',font=('Courier New',9),fg='#A02020').grid(row=0,column=0,sticky='nse',pady=2)
        varFuncR1 = tk.StringVar()
        varFuncR1.set(settingsDict['colorfuncs'][1][0])
        entryFuncR1 = ttk.Entry(frameFuncDisplays1,textvariable=varFuncR1,font=('Courier New',9),foreground='#204010',background='#EFEFEF')
        entryFuncR1.grid(row=0,column=1,sticky='nesw',pady=2)
        tk.Label(frameFuncDisplays1,text='G:',font=('Courier New',9),fg='#20A020').grid(row=1,column=0,sticky='nse',pady=2)
        varFuncG1 = tk.StringVar()
        varFuncG1.set(settingsDict['colorfuncs'][1][1])
        entryFuncG1 = ttk.Entry(frameFuncDisplays1,textvariable=varFuncG1,font=('Courier New',9),foreground='#204010',background='#EFEFEF')
        entryFuncG1.grid(row=1,column=1,sticky='nesw',pady=2)
        tk.Label(frameFuncDisplays1,text='B:',font=('Courier New',9),fg='#2020A0').grid(row=2,column=0,sticky='nse',pady=2)
        varFuncB1 = tk.StringVar()
        varFuncB1.set(settingsDict['colorfuncs'][1][2])
        entryFuncB1 = ttk.Entry(frameFuncDisplays1,textvariable=varFuncB1,font=('Courier New',9),foreground='#204010',background='#EFEFEF')
        entryFuncB1.grid(row=2,column=1,sticky='nesw',pady=2)
        frameFuncDisplays1.grid(row=2,column=1,padx=[5,2])

        frameColorDisplays1 = tk.Frame(frameColorfuncs,relief='sunken',bd=2)
        for i in range(1,16):
            frameColorDisplays1.columnconfigure(i,weight=10)
        x = 0
        color10 = rgb_to_hex(int(eval(settingsDict['colorfuncs'][1][0])),int(eval(settingsDict['colorfuncs'][1][1])),int(eval(settingsDict['colorfuncs'][1][2])))
        x = 255
        color11 = rgb_to_hex(int(eval(settingsDict['colorfuncs'][1][0])),int(eval(settingsDict['colorfuncs'][1][1])),int(eval(settingsDict['colorfuncs'][1][2])))
        def btn10_do():
            nonlocal color10
            colorResult = tkcolor.askcolor(color10,title='选择颜色')
            if colorResult == (None,None):
                return None
            else:
                color10 = colorResult[1].upper()
            btn10 = tk.Button(frameColorDisplays1,text=' ',font=('Courier New',6),bg=color10,height=1,width=1,command=btn10_do)
            btn10.grid(row=0,column=0,padx=[1,0],pady=1,sticky='nsw')
            settingsDict['colorfuncs'][1] = workOutFuncs(hex_to_rgb(color10),hex_to_rgb(color11))
            for i in range(1,16):
                x = 16*i
                color = rgb_to_hex(int(eval(settingsDict['colorfuncs'][1][0])),int(eval(settingsDict['colorfuncs'][1][1])),int(eval(settingsDict['colorfuncs'][1][2])))
                tk.Label(frameColorDisplays1,text=' ',font=('Courier New',1),height=2,width=1,bg=color).grid(row=0,column=i,sticky='ew')
            varFuncR1.set(settingsDict['colorfuncs'][1][0])
            varFuncG1.set(settingsDict['colorfuncs'][1][1])
            varFuncB1.set(settingsDict['colorfuncs'][1][2])
        btn10 = tk.Button(frameColorDisplays1,text=' ',font=('Courier New',6),bg=color10,height=1,width=1,command=btn10_do)
        btn10.grid(row=0,column=0,padx=[1,0],pady=1,sticky='nsw')
        def btn11_do():
            nonlocal color11
            colorResult = tkcolor.askcolor(color11,title='选择颜色')
            if colorResult == (None,None):
                return None
            else:
                color11 = colorResult[1].upper()
            btn11 = tk.Button(frameColorDisplays1,text=' ',font=('Courier New',6),bg=color11,height=1,width=1,bd=1,command=btn11_do)
            btn11.grid(row=0,column=16,padx=[0,1],pady=1,sticky='nsw')
            settingsDict['colorfuncs'][1] = workOutFuncs(hex_to_rgb(color10),hex_to_rgb(color11))
            for i in range(1,16):
                x = 16*i
                color = rgb_to_hex(int(eval(settingsDict['colorfuncs'][1][0])),int(eval(settingsDict['colorfuncs'][1][1])),int(eval(settingsDict['colorfuncs'][1][2])))
                tk.Label(frameColorDisplays1,text=' ',font=('Courier New',1),height=2,width=1,bg=color).grid(row=0,column=i,sticky='ew')
            varFuncR1.set(settingsDict['colorfuncs'][1][0])
            varFuncG1.set(settingsDict['colorfuncs'][1][1])
            varFuncB1.set(settingsDict['colorfuncs'][1][2])
        btn11 = tk.Button(frameColorDisplays1,text=' ',font=('Courier New',6),bg=color11,height=1,width=1,bd=1,command=btn11_do)
        btn11.grid(row=0,column=16,padx=[0,1],pady=1,sticky='nse')
        for i in range(1,16):
            x = 16*i
            color = rgb_to_hex(int(eval(settingsDict['colorfuncs'][1][0])),int(eval(settingsDict['colorfuncs'][1][1])),int(eval(settingsDict['colorfuncs'][1][2])))
            tk.Label(frameColorDisplays1,text=' ',font=('Courier New',1),height=2,width=1,bg=color).grid(row=0,column=i,sticky='ew')

        def entryFuncX1_callback(idx:int):
            '''idx: (R1 = 0, G1 = 1, B1 = 2)'''
            nonlocal invalidCode,color10,color11
            varName = [varFuncR1,varFuncG1,varFuncB1][idx]
            entryName = [entryFuncR1,entryFuncG1,entryFuncB1][idx]
            func = varName.get()
            x = 0
            try:
                eval(func)
            except:
                entryName.config(foreground='#F04030')
                invalidCode[12] = 1
            else:
                entryName.config(foreground='#204010')
                invalidCode[12] = 0
                settingsDict['colorfuncs'][1][idx] = func
                x = 0
                color10 = rgb_to_hex(int(eval(settingsDict['colorfuncs'][1][0])),int(eval(settingsDict['colorfuncs'][1][1])),int(eval(settingsDict['colorfuncs'][1][2])))
                x = 255
                color11 = rgb_to_hex(int(eval(settingsDict['colorfuncs'][1][0])),int(eval(settingsDict['colorfuncs'][1][1])),int(eval(settingsDict['colorfuncs'][1][2])))
                btn10.config(bg=color10)
                btn11.config(bg=color11)
                for i in range(1,16):
                    x = 16*i
                    color = rgb_to_hex(int(eval(settingsDict['colorfuncs'][1][0])),int(eval(settingsDict['colorfuncs'][1][1])),int(eval(settingsDict['colorfuncs'][1][2])))
                    tk.Label(frameColorDisplays1,text=' ',font=('Courier New',1),height=2,width=1,bg=color).grid(row=0,column=i,sticky='ew')
        def entryFuncR1_callback(*args):
            entryFuncX1_callback(0)
        varFuncR1.trace_add('write',entryFuncR1_callback)
        def entryFuncG1_callback(*args):
            entryFuncX1_callback(1)
        varFuncG1.trace_add('write',entryFuncG1_callback)
        def entryFuncB1_callback(*args):
            entryFuncX1_callback(2)
        varFuncB1.trace_add('write',entryFuncB1_callback)
        frameColorDisplays1.grid(row=1,column=1,padx=[5,2],pady=2,sticky='nesw')
        #endregion

        frameColorfuncs.grid(row=2,column=0,columnspan=5,padx=2,pady=1,sticky='nesw')
        #endregion

        #region sidebarDisplayStyle
        frameSidebarDisplayStyle = tk.Frame(settPage1,relief='ridge',bd=3)
        frameSidebarDisplayStyle.columnconfigure(1,weight=5)
        tk.Label(frameSidebarDisplayStyle,text='计划单样式:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nse')
        varSidebarDisplayStyle = tk.StringVar()
        varSidebarDisplayStyle.set(f"{['当天列表','本周列表','当天柱状','本周柱状'][settingsDict['sidebarDisplayStyle']]}")
        colorsSidebarDisplayStyle = ['#0860AF','#044590','#086055','#044535']
        fgColor = colorsSidebarDisplayStyle[settingsDict['sidebarDisplayStyle']]
        def btnSidebarDisplayStyleDo():
            if settingsDict['sidebarDisplayStyle'] in [0,1,2]:
                settingsDict['sidebarDisplayStyle'] += 1
            else:
                settingsDict['sidebarDisplayStyle'] = 0
            varSidebarDisplayStyle.set(f"{['当天列表','本周列表','当天柱状','本周柱状'][settingsDict['sidebarDisplayStyle']]}")
            fgColor = colorsSidebarDisplayStyle[settingsDict['sidebarDisplayStyle']]
            btnSidebarDisplayStyle.config(fg=fgColor)
        btnSidebarDisplayStyle = tk.Button(frameSidebarDisplayStyle,textvariable=varSidebarDisplayStyle,font=('Courier New',10,'bold'),fg=fgColor,bd=1,command=btnSidebarDisplayStyleDo)
        btnSidebarDisplayStyle.grid(row=0,column=1,sticky='nesw',padx=1.5,pady=1.5)
        frameSidebarDisplayStyle.grid(row=3,column=0,columnspan=3,padx=2,pady=1,sticky='nesw')
        #endregion

        #region columnarGapMergeThreshold
        frameColumnarGapMergeThreshold = tk.Frame(settPage1,relief='ridge',bd=3)
        frameColumnarGapMergeThreshold.columnconfigure(0,weight=8)
        frameColumnarGapMergeThreshold.columnconfigure(1,weight=10)
        frameColumnarGapMergeThreshold.columnconfigure(2,weight=4)
        frameColumnarGapMergeThreshold.columnconfigure(3,weight=10)
        tk.Label(frameColumnarGapMergeThreshold,text='计划间隙压缩阈值(/分钟):',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nesw')
        tk.Label(frameColumnarGapMergeThreshold,text='(1441=永不)',font=('Courier New',8),fg='#161616').grid(row=0,column=2,sticky='nesw')
        colorsColumnarGapMergeThreshold = ['#204010','#F04030']
        def entryColumnarGapMergeThreshold_callback(*args):
            rawGap = entryColumnarGapMergeThreshold.get()
            valid = False
            try:
                gap = eval(rawGap)
                if gap in range(0,1442):
                    valid = True
            except:
                pass
            if valid:
                entryColumnarGapMergeThreshold.config(foreground=colorsColumnarGapMergeThreshold[0])
                invalidCode[9] = 0
            else:
                entryColumnarGapMergeThreshold.config(foreground=colorsColumnarGapMergeThreshold[1])
                invalidCode[9] = 1
        varColumnarGapMergeThreshold = tk.StringVar()
        varColumnarGapMergeThreshold.trace_add('write',entryColumnarGapMergeThreshold_callback)
        entryColumnarGapMergeThreshold = ttk.Spinbox(frameColumnarGapMergeThreshold,from_=0,to=1441,textvariable=varColumnarGapMergeThreshold,font=('Courier New',9),foreground=fgColor,background='#EFEFEF',width=8)
        entryColumnarGapMergeThreshold.set((settingsDict['columnarGapMergeThreshold']//100*60+settingsDict['columnarGapMergeThreshold']%100))
        entryColumnarGapMergeThreshold.grid(row=0,column=1,sticky='nesw',padx=0,pady=3)
        frameColumnarGapMergeThreshold.grid(row=4,column=0,columnspan=3,padx=2,pady=1,sticky='nesw')
        #endregion

        #region retrenchMode
        frameRetrenchMode = tk.Frame(settPage1,relief='ridge',bd=3)
        frameRetrenchMode.columnconfigure(1,weight=5)
        tk.Label(frameRetrenchMode,text='节能模式:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nse')
        varRetrenchMode = tk.StringVar()
        varRetrenchMode.set('开' if settingsDict['retrenchMode'] else '关')
        fgColor = '#209610' if settingsDict['retrenchMode'] else '#943015'
        def btnRetrenchModeDo():
            settingsDict['retrenchMode'] = not(settingsDict['retrenchMode'])
            varRetrenchMode.set('开' if settingsDict['retrenchMode'] else '关')
            fgColor = '#209610' if settingsDict['retrenchMode'] else '#943015'
            btnRetrenchMode.config(fg=fgColor)
        btnRetrenchMode = tk.Button(frameRetrenchMode,textvariable=varRetrenchMode,font=('Courier New',10,'bold'),fg=fgColor,bd=1,command=btnRetrenchModeDo)
        btnRetrenchMode.grid(row=0,column=1,sticky='nesw',padx=1.5,pady=1.5)
        frameRetrenchMode.grid(row=5,column=0,padx=2,pady=1,sticky='nesw')
        #endregion

        #region maxTps
        frameMaxTps = tk.Frame(settPage1,relief='ridge',bd=3)
        frameMaxTps.columnconfigure(0,weight=8)
        frameMaxTps.columnconfigure(1,weight=10)
        frameMaxTps.columnconfigure(2,weight=4)
        frameMaxTps.columnconfigure(3,weight=10)
        tk.Label(frameMaxTps,text='最大刷新率:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,sticky='nesw')
        colorsColumnarGapMergeThreshold = ['#204010','#F04030']
        def entryMaxTps_callback(*args):
            rawTps = entryMaxTps.get()
            valid = False
            try:
                tps = eval(rawTps)
                if tps in range(5,101):
                    valid = True
            except:
                pass
            if valid:
                entryMaxTps.config(foreground=colorsColumnarGapMergeThreshold[0])
                invalidCode[10] = 0
            else:
                entryMaxTps.config(foreground=colorsColumnarGapMergeThreshold[1])
                invalidCode[10] = 1
        varMaxTps = tk.StringVar()
        varMaxTps.trace_add('write',entryMaxTps_callback)
        entryMaxTps = ttk.Spinbox(frameMaxTps,from_=5,to=100,increment=5,textvariable=varMaxTps,font=('Courier New',9),foreground=fgColor,background='#EFEFEF',width=8)
        entryMaxTps.set(settingsDict['maxTps'])
        entryMaxTps.grid(row=0,column=1,sticky='nesw',padx=0,pady=3)
        frameMaxTps.grid(row=5,column=1,columnspan=3,padx=2,pady=1,sticky='nesw')
        #endregion

        #endregion

        frameFinal = tk.Frame(settwin,relief='flat',bd=0)
        frameFinal.columnconfigure(0,weight=10)
        frameFinal.columnconfigure(1,weight=10)
        frameFinal.columnconfigure(2,weight=8)
        def btnConfirmDo():
            if (1 in invalidCode) or not((int(bgAlphaSpinbox.get()) in range(101)) and 
                                          (int(entryTimeOffsetDays.get()) >= 0) and
                                          (int(entryTimeOffsetHours.get()) in range(0,60)) and
                                          (int(entryTimeOffsetMinutes.get()) in range(0,60)) and
                                          (int(entryTimeOffsetSeconds.get()) in range(0,60)) and
                                          (int(entryTimeOffsetMilliseconds.get()) in range(0,1000))):
                tkmsg.showerror('错误','设置项格式存在错误！')
            else:
                for darkmodeColorfuncs in settingsDict['colorfuncs']:
                    for colorfunc in darkmodeColorfuncs:
                        for x in range(0,256):
                            try:
                                n = int(eval(colorfunc))
                            except:
                                tkmsg.showerror('错误',f"“界面前景色”中表达式 {colorfunc} 在 x={x} 时出现错误！")
                                return None
                            else:
                                if n not in range(0,256):
                                    tkmsg.showerror('错误',f"“界面前景色”中表达式 {colorfunc} 在 x={x} 时值不在 0~255 内！")
                                    return None
                settingsDict['screenSize'] = (int(entryScreenSizeX.get()),int(entryScreenSizeY.get()))
                settingsDict['textFonts'] = [entryFont1.get(),entryFont2.get(),entryFont3.get(),entryFont4.get(),entryFont5.get()]
                settingsDict['backgroundImgPaths'] = (varPath0.get(),varPath1.get())
                settingsDict['backgroundAlpha'] = int(bgAlphaSpinbox.get())
                k = 1 if varTimeOffsetDirection.get()=='延后' else -1
                settingsDict['timeOffset'] = [int(entryTimeOffsetDays.get())*k,
                                              int(entryTimeOffsetHours.get())*k,
                                              int(entryTimeOffsetMinutes.get())*k,
                                              int(entryTimeOffsetSeconds.get())*k,
                                              int(entryTimeOffsetMilliseconds.get())*k]
                settingsDict['columnarGapMergeThreshold'] = int(entryColumnarGapMergeThreshold.get())//60*100+int(entryColumnarGapMergeThreshold.get())%60
                settingsDict['maxTps'] = int(entryMaxTps.get())
                if self.et.settings != settingsDict:
                    self.et.editSettings(settingsDict)
                btnCancelDo()
        def btnCancelDo():
            nonlocal settwin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            settwin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()
        pageUpdnVar = tk.StringVar()
        pageUpdnVar.set('下一页..')
        def pageUpdnDo():
            if pageUpdnVar.get() == '下一页..':
                settPage0.grid_remove()
                settPage1.grid()
                pageUpdnVar.set('上一页..')
            else:
                settPage1.grid_remove()
                settPage0.grid()
                pageUpdnVar.set('下一页..')
        btnConfirm = tk.Button(frameFinal,text='确认本次修改',font=('Courier New',11),bd=3,fg='#089000',command=btnConfirmDo)
        btnConfirm.grid(row=0,column=0,padx=2,pady=5,sticky='nesw')
        btnCancel = tk.Button(frameFinal,text='放弃本次修改',font=('Courier New',11),bd=3,fg='#C04000',command=btnCancelDo)
        btnCancel.grid(row=0,column=1,padx=[0,5],pady=5,sticky='nesw')
        btnPageUpdn = tk.Button(frameFinal,textvariable=pageUpdnVar,font=('Courier New',11),bg='#E0E0E0',command=pageUpdnDo)
        btnPageUpdn.grid(row=0,column=2,padx=[5,2],pady=5,sticky='nesw')

        settPage1.grid(row=1,column=0,columnspan=10,padx=2,pady=2,sticky='nwe')
        settPage1.grid_remove()
        settPage0.grid(row=1,column=0,columnspan=10,padx=2,pady=2,sticky='nwe')
        frameFinal.grid(row=10,column=0,columnspan=10,pady=5,sticky='nesw')


        settwin.mainloop()

    def updateTextFrames(self):
        self.et.sortTimetable()
        self.mainwin.title(f'{"*" if self.et.notSavedYet else ""}{self.filepath} - 编辑时间表')
        texts = self.weekdayScheduleFormat(self.timetable)
        for frameIdx in range(7):
            frame = self.textFrames[frameIdx]
            frame.delete('0.0',tk.END)
            frame.insert('0.0',texts[frameIdx])

    def getWeekdayScheduleTexts(self,weekday:list) -> list:
        weekdayTexts = []
        for rawschedule in weekday:
            schedule = rawschedule.copy()
            try:
                eval(schedule[2])
            except NameError:
                schedule[2] = f"?=({schedule[2]})"
                schedule[2] = f"{schedule[2]!r}"
            text = f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02}~{int(schedule[1]//100):02}:{int(schedule[1]%100):02} {eval(schedule[2])}'
            weekdayTexts.append(text)
        return weekdayTexts

    def weekdayScheduleFormat(self,timetable:list,do_scheduleText_break_into_2_lines:bool=True) -> list:
        maxRows = max(map(len,timetable))
        # timetable = [list(map(lambda schedule:f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02}~{int(schedule[1]//100):02}:{int(schedule[1]%100):02}\n {eval(schedule[2])}',weekday)) for weekday in timetable]
        newTimetable = [[],[],[],[],[],[],[]]
        for weekdayIdx in [0,1,2,3,4,5,6]:
            weekday = timetable[weekdayIdx]
            for rawschedule in weekday:
                schedule = rawschedule.copy()
                try:
                    eval(schedule[2])
                except NameError:
                    schedule[2] = f"?=({schedule[2]})"
                    schedule[2] = f"{schedule[2]!r}"
                if do_scheduleText_break_into_2_lines:
                    text = f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02}~{int(schedule[1]//100):02}:{int(schedule[1]%100):02}\n {eval(schedule[2])}'
                else:
                    text = f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02}~{int(schedule[1]//100):02}:{int(schedule[1]%100):02} {eval(schedule[2])}'
                newTimetable[weekdayIdx].append(text)
        timetable = newTimetable
        for weekday in timetable:
            while len(weekday) < maxRows:
                weekday += ['\n']
        finalText = list(map(lambda l:'\n'.join(l)+'\n',timetable))
        weekdayNames = ['周一','周二','周三','周四','周五','周六','周日']
        for i in range(7):
            finalText[i] = f' {weekdayNames[i]}计划：\n'+finalText[i]
        return finalText

    @deco
    def main_textToTuple(self,text:str) -> Tuple[int,int,str,Literal[0,1]]:
        '''text example:   '09:30~10:15 计划'
        output example: [930,1015,"'计划'"]
        special sched:  "09:30~10:15 ?=('A' if a else 'B')"'''
        timeFr = int(text[0:2]+text[3:5])
        timeTo = int(text[6:8]+text[9:11])
        name = text[12:]
        if name[:3] == '?=(' and name[-1] == ')':
            name = name[3:-1]
            nameMode = 1
        else:
            name = f"'{name}'"
            nameMode = 0
        return [timeFr,timeTo,name,nameMode]
    

if __name__ == '__main__':
    run = RunDirectly()
    run.main()