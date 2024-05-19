import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsg
import tkinter.filedialog as tkfile
from sys import exit
from os.path import exists
from typing import Callable,Tuple
from typing import Union as U
from typing_extensions import Literal,List

DEBUG = True

def dbprint(*args,**kwargs):
    if DEBUG:
        print(*args,**kwargs)

def deco(fun0:Callable):
    def fun1(*args):
        try:
            rtn = fun0(*args)
        except Exception as e:
            dbprint(f"\nException occurred in manage_edit.py:\n  {str(type(e))[8:-2]}: {e}")
            rtn = None
        finally:
            return rtn
    return fun1

class TimetableEditTools():
    def __init__(self, filepath: str = 'timetable2.txt', instantRead: bool = True):
        self.filepath_timetable = filepath
        self.timetable = []
        self.settings = {}
        self.filtered = []
        if instantRead:
            self.readTimetable()
            self.filtered = self.filterValidSchedules()
        self.undoList = []  #[('name',<datas>)]
        self.redoList = []
        self.notSavedYet = False

    @deco
    def readTimetable(self):
        file_timetable = open(self.filepath_timetable,'r')
        rawTimetable = file_timetable.readlines()
        file_timetable.close()
        self.timetable = eval(rawTimetable[0])
        self.settings = eval(rawTimetable[1])
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
    def uncoverSchedule(self,conqWeekday:Literal[0,1,2,3,4,5,6],orgnScheds:List[list],newScheds:List[list],conqSched:list,undoable:bool=True):
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
            else:
                task = False
            self.undoList.append(action)
            if task:
                self.notSavedYet = True

    def saveTimetable(self) -> bool:
        self.filterValidSchedules()
        file = open(self.filepath_timetable,mode='w')
        try:
            savingText = f'{self.timetable!r}\n{self.settings!r}\n# Timetable version: 2'
            file.write(savingText)
            self.notSavedYet = False
            file.close()
            return True
        except:
            file.close()
            return False
        
    def degradeTimetable(self,targetVersion:int) -> Tuple[bool,str]:
        wrappedSched = False
        timetable1 = self.timetable.copy()
        settings1 = self.settings.copy()
        if targetVersion in [0,1]:
            for weekday in timetable1:
                for sched in weekday:
                    sched1 = sched.copy()
                    try:
                        sched1[2] = eval(sched1[2])
                    except NameError:
                        sched1[2] = f'?=({sched1[2]})'
                        wrappedSched = True
        if targetVersion == 0:
            timetable0 = []
            timeAreas = []
            for weekdayIdx in range(7):
                weekday = timetable1[weekdayIdx]
                for sched in weekday:
                    if sched[0:2] not in timeAreas:
                        timetable0.append([sched[0],sched[1],'','','','','','',''])
                        timeAreas.append(sched[0:2])
                    schedIdx = timeAreas.index(sched[0:2])
                    timetable0[schedIdx][weekdayIdx+2] = sched[2]
            timetable1 = timetable0.copy()
            settings1.pop('textFonts')
        if targetVersion == 1:
            rawTimetableLines = [str(timetable1),str(settings1),'# Timetable version: 1']
        elif targetVersion == 0:
            rawTimetableLines = [str(timetable1),'[\'\',\'\']',str(settings1)]
        rawTimetableText = '\n'.join(rawTimetableLines)
        return (wrappedSched,rawTimetableText)


@deco
def isFileOpenable(filepath:str) -> bool:
    try:
        open(filepath,'r').close()
    except FileNotFoundError:
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
            filepath = tkfile.askopenfilename(defaultextension='.txt',title='打开时间表文件',initialdir='./',initialfile='timetable2.txt')
            if isFileOpenable(filepath):
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

        self.filepath = filepath
        self.et = TimetableEditTools(filepath)
        self.timetable = self.et.timetable
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
            tkmsg.showwarning('提示','文件中有以下格式错误已被修改：\n'+'\n'.join(self.et.filtered))

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
                    print(f'{rawSched!r}')
                    print(f'{self.timetable[weekdayNameList.index(weekdayVar.get())]!r}')
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
                    print(f'{rawSched!r}')
                    print(f'{self.timetable[weekdayNameList.index(weekdayVar.get())]!r}')
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
        def btnRestoreDo():
            self.et.settings = self.et.originSettings.copy()
            self.et.undo(-1)
            self.et.notSavedYet = False
            self.updateTextFrames()
            tkmsg.showinfo('提示','所有更改已撤销，但计划仍可以通过“重做”恢复。')
        def btnExitDo():
            if self.et.notSavedYet:
                doFinalSave = tkmsg.askyesno('提示','发尚未保存的改动！\n是否保存？')
                if doFinalSave:
                    btnSaveDo()
            exit()
        def saveAsVersion():
            btnCancelDo()
            self.main_showDegradewin()
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
        btnExit = tk.Button(fileswin,text='另存为较低版本..',font=('Courier New',10),command=saveAsVersion)
        btnExit.grid(row=3,column=0,padx=5,pady=3,sticky='nesw')
        btnExit = tk.Button(fileswin,text='退出程序',font=('Courier New',10),fg='#C04000',command=btnExitDo)
        btnExit.grid(row=4,column=0,padx=5,pady=3,sticky='nesw')
        btnCancel = tk.Button(fileswin,text='继续编辑',font=('Courier New',10),command=btnCancelDo)
        btnCancel.grid(row=10,column=0,padx=5,pady=[15,0],sticky='nesw')

        fileswin.mainloop()

    def main_showDegradewin(self):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
        degradewin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=350)  #column0 weights 10

        degradewin.columnconfigure(0,weight=5)
        degradewin.columnconfigure(1,weight=5)
        degradewin.columnconfigure(2,weight=10)
        degradewin.rowconfigure(3,weight=10)
        tk.Label(degradewin,text=' 另存为较低版本',font=('Courier New',10),fg='#303030').grid(row=0,column=0,columnspan=2,sticky='nsw')
        tk.Label(degradewin,text='目标版本：',font=('Courier New',10),fg='#151515').grid(row=1,column=0,sticky='nse')
        def updateReviewText(*args):
            nonlocal wrapped
            wrapped, degradeText = self.et.degradeTimetable(targetVersionList.index(targetVersionVar.get()))
            rawReviewText = degradeText.splitlines()
            for idx in range(len(rawReviewText)):
                rawReviewText[idx] = f'  >Line {idx+1}>  ' + rawReviewText[idx]
            rawReviewText.insert(0,'  预览：')
            reviewText = '\n'.join(rawReviewText)
            textframe.delete('0.0','end')
            textframe.insert('0.0',reviewText)
        targetVersionVar = tk.StringVar()
        targetVersionVar.set('timetable1 (for clock 1.1)')
        targetVersionList = ['timetable (for clock 1.0)','timetable1 (for clock 1.1)']
        targetVersionMenu = ttk.OptionMenu(degradewin,targetVersionVar,'timetable1 (for clock 1.1)',*targetVersionList,command=updateReviewText)
        targetVersionMenu.grid(row=1,column=1,columnspan=3,sticky='nesw')
        
        textframe = tk.Text(degradewin,font=('Courier New',9),width=20)
        scrollBar = tk.Scrollbar(degradewin)
        def scrollEvent(*args):
            textframe.yview(*args)
        scrollBar.config(command=scrollEvent)
        scrollBar.grid(row=3,column=3,sticky='nesw')
        textframe.config(yscrollcommand=scrollBar.set)
        textframe.grid(row=3,column=0,columnspan=3,sticky='nesw')
        wrapped = False
        updateReviewText(0)
        def btnCancelDo():
            nonlocal degradewin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            degradewin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()
        def btnConfirmDo():
            targetVersion = targetVersionList.index(targetVersionVar.get())
            savingText = self.et.degradeTimetable(targetVersion)[1]
            if wrapped:
                doSaving = tkmsg.askokcancel('提示','由于时间表版本兼容问题，部分计划名称已被自动修改。\n是否确定保存？')
                if doSaving == False:
                    return None
            savingDir = tkfile.asksaveasfilename(defaultextension='.txt',title='另存为文件',initialdir='./',initialfile='timetable' if targetVersion==0 else 'timetable1')
            if savingDir == '':
                return None
            savingFile = open(savingDir,'w')
            try:
                savingFile.write(savingText)
            except:
                tkmsg.showerror('错误','保存失败！')
            else:
                tkmsg.showinfo('提示','保存成功！')
            finally:
                savingFile.close()
            btnCancelDo()
        btnConfirm = tk.Button(degradewin,text='确定',font=('Courier New',10),command=btnConfirmDo)
        btnConfirm.grid(row=10,column=0,columnspan=2,padx=2,pady=5,sticky='nesw')
        btnCancel = tk.Button(degradewin,text='取消',font=('Courier New',10),command=btnCancelDo)
        btnCancel.grid(row=10,column=2,padx=2,pady=5,sticky='nesw')
            

    def main_showSettingswin(self):
        self.mainwin.columnconfigure(1,weight=0,minsize=0)
        self.area_sidewin.destroy()
        self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
        self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
        settwin = self.area_sidewin
        self.mainwin.columnconfigure(1,weight=8,minsize=360)  #column0 weights 10

        settwin.columnconfigure(0,weight=10)
        settwin.columnconfigure(1,weight=10)
        settwin.columnconfigure(2,weight=20)
        settingsDict = self.et.settings.copy()

        settwin.columnconfigure(0,weight=1)
        invalidCode = [0,0,0,0,0,0]
        tk.Label(settwin,text=' 编辑设置项',font=('Courier New',10),fg='#404040').grid(row=0,column=0,columnspan=10,sticky='nsw')

        #region frameDarkMode (row=1,column=0)
        frameDarkMode = tk.Frame(settwin,relief='ridge',bd=3)
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
        frameCompressLevel = tk.Frame(settwin,relief='ridge',bd=3)
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
        frameDoTimetableSearch = tk.Frame(settwin,relief='ridge',bd=3)
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
        frameScreenSize = tk.Frame(settwin,relief='ridge',bd=3)
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
        frameTextFonts = tk.Frame(settwin,relief='ridge',bd=3)
        frameTextFonts.columnconfigure(0,weight=1)
        frameTextFonts.columnconfigure(1,weight=20)
        frameTextFonts.columnconfigure(2,weight=3)
        tk.Label(frameTextFonts,text='自定义字体:',font=('Courier New',10),fg='#161616').grid(row=0,column=0,columnspan=2,sticky='nsw')
        colorsTextFonts = ['#204010','#F04030']

        tk.Label(frameTextFonts,text='1.',font=('Courier New',10),fg='#505050').grid(row=1,column=0,sticky='nse',pady=2)
        fgColor1 = colorsTextFonts[0]
        def entryFont1_callback(*args):
            font1 = varFont1.get()
            if exists(font1):
                entryFont1.config(fg=colorsTextFonts[0])
                invalidCode[1] = 0
            else:
                entryFont1.config(fg=colorsTextFonts[1])
                invalidCode[1] = 1
        varFont1 = tk.StringVar()
        varFont1.set(settingsDict['textFonts'][0])
        varFont1.trace_add('write',entryFont1_callback)
        entryFont1 = tk.Entry(frameTextFonts,textvariable=varFont1,font=('Courier New',10,'bold'),fg=fgColor1,bg='#EFEFEF',bd=1)
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
            if exists(font2):
                entryFont2.config(fg=colorsTextFonts[0])
                invalidCode[2] = 0
            else:
                entryFont2.config(fg=colorsTextFonts[1])
                invalidCode[2] = 1
        varFont2 = tk.StringVar()
        varFont2.set(settingsDict['textFonts'][1])
        varFont2.trace_add('write',entryFont2_callback)
        entryFont2 = tk.Entry(frameTextFonts,textvariable=varFont2,font=('Courier New',10,'bold'),fg=fgColor2,bg='#EFEFEF',bd=1)
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
            if exists(font3):
                entryFont3.config(fg=colorsTextFonts[0])
                invalidCode[3] = 0
            else:
                entryFont3.config(fg=colorsTextFonts[1])
                invalidCode[3] = 1
        varFont3 = tk.StringVar()
        varFont3.set(settingsDict['textFonts'][2])
        varFont3.trace_add('write',entryFont3_callback)
        entryFont3 = tk.Entry(frameTextFonts,textvariable=varFont3,font=('Courier New',10,'bold'),fg=fgColor3,bg='#EFEFEF',bd=1)
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
            if exists(font4):
                entryFont4.config(fg=colorsTextFonts[0])
                invalidCode[4] = 0
            else:
                entryFont4.config(fg=colorsTextFonts[1])
                invalidCode[4] = 1
        varFont4 = tk.StringVar()
        varFont4.set(settingsDict['textFonts'][3])
        varFont4.trace_add('write',entryFont4_callback)
        entryFont4 = tk.Entry(frameTextFonts,textvariable=varFont4,font=('Courier New',10,'bold'),fg=fgColor4,bg='#EFEFEF',bd=1)
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
            if exists(font5):
                entryFont5.config(fg=colorsTextFonts[0])
                invalidCode[5] = 0
            else:
                entryFont5.config(fg=colorsTextFonts[1])
                invalidCode[5] = 1
        varFont5 = tk.StringVar()
        varFont5.set(settingsDict['textFonts'][4])
        varFont5.trace_add('write',entryFont5_callback)
        entryFont5 = tk.Entry(frameTextFonts,textvariable=varFont5,font=('Courier New',10,'bold'),fg=fgColor5,bg='#EFEFEF',bd=1)
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

        frameFinal = tk.Frame(settwin,relief='flat',bd=0)
        frameFinal.columnconfigure(0,weight=10)
        frameFinal.columnconfigure(1,weight=10)
        def btnConfirmDo():
            if (1 in invalidCode):
                tkmsg.showerror('错误','设置项格式存在错误！')
            else:
                settingsDict['screenSize'] = (int(entryScreenSizeX.get()),int(entryScreenSizeY.get()))
                settingsDict['textFonts'] = [entryFont1.get(),entryFont2.get(),entryFont3.get(),entryFont4.get(),entryFont5.get()]
                if self.et.settings != settingsDict:
                    self.et.notSavedYet = True
                self.et.settings = settingsDict
                btnCancelDo()
        def btnCancelDo():
            nonlocal settwin
            self.mainwin.columnconfigure(1,weight=0,minsize=0)
            settwin.destroy()
            self.area_sidewin = tk.Frame(self.mainwin,relief='sunken',bd=3)
            self.area_sidewin.grid(row=0,column=1,rowspan=10,sticky='nswe',padx=[3,0])
            self.updateTextFrames()

        btnConfirm = tk.Button(frameFinal,text='确认本次修改',font=('Courier New',11),bd=3,command=btnConfirmDo)
        btnConfirm.grid(row=0,column=0,padx=2,pady=5,sticky='nesw')
        btnCancel = tk.Button(frameFinal,text='放弃本次修改',font=('Courier New',11),bd=3,fg='#C04000',command=btnCancelDo)
        btnCancel.grid(row=0,column=1,padx=2,pady=5,sticky='nesw')
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