import pygame
import pygame.freetype as freetype
import tkinter as tk
import tkinter.filedialog as tkfile
import tkinter.messagebox as tkmessage
from typing import Union,List,Tuple,Optional
from manage_edit import TimetableEditTools

pygame.init()

root = tk.Tk()
root.withdraw()


DOUBLE_CLICK_TIMER_EVENT = pygame.USEREVENT+3

class Inputs_Manager():
    def __init__(self,master:pygame.Surface):
        self.master = master
        self.doubleClickOnTimer = False
        self.doubleClickGap = 200   # milliseconds

    def checkDoubleClick(self,state:int,timeout:bool=False):
        if not timeout:
            if state == 0:
                pygame.time.set_timer(DOUBLE_CLICK_TIMER_EVENT,self.doubleClickGap,loops=1)
                self.doubleClickOnTimer = True
                return 1
            elif state == 1:
                return 3
            elif state == 3:
                return 0
        else:
            self.doubleClickOnTimer = False
            if state == 1:
                return 2
            elif state == 3:
                return 0
            elif state == 0:
                return 0
        
class File_Manager():
    def __init__(self):
        self.timetable = []
        self.sloganTexts = []
        self.settingsDict = {}
        self.path_timetable = 'timetable3.txt'
        self.readTimetable()
        self.doTimetableSearch = True
        self.et = TimetableEditTools(self.path_timetable,False)

    def readTimetable(self):
        try:
            file_timetable=open(self.path_timetable)
        except:
            file_timetable=open(self.path_timetable,'w')
            file_timetable.write('[[],[],[],[],[],[],[]]\n{\'darkMode\':True,\'compressLevel\':0,\'screenSize\':(600,600),\'doTimetableSearch\':True,\'textFonts\':[\'C:/Windows/Fonts/stxinwei.ttf\',\'C:/Windows/Fonts/roccb___.ttf\',\'C:/Windows/Fonts/simhei.ttf\',\'C:/Windows/Fonts/rock.ttf\',\'C:/Windows/Fonts/stzhongs.ttf\'],\'colorfuncs\':[[\'(47/51)*x+20\',\'(15/17)*x+20\',\'(38/51)*x+20\'],[\'(-41/51)*x+225\',\'(-41/51)*x+225\',\'(-41/51)*x+225\']],\'doBackgroundImgDisplay\':[False,False],\'backgroundImgPaths\':[\'\',\'\'],\'backgroundAlpha\':60,\'language\': \'Chinese中文\',\'timeOffset\': [0,0,0,0,0], \'sidebarDisplayStyle\': 0, \'columnarGapMergeThreshold\': 2401, \'retrenchMode\': False, \'maxTps\': 60}\n# Timetable version: 3')
            file_timetable.close()
            file_timetable=open(self.path_timetable)
        
        rawlines = file_timetable.readlines()
        if self.path_timetable[-4:] == '.txt':
            self.timetable = eval(rawlines[0])
            self.settingsDict = eval(rawlines[1])
            self.doTimetableSearch = self.settingsDict['doTimetableSearch']
        else:
            rawTimetable = ''.join(rawlines)
            self.timetable, self.settingsDict = self.et.json_to_timetable(rawTimetable,loadToSelf=False)
            self.doTimetableSearch = self.settingsDict['doTimetableSearch']
        file_timetable.close()
        self.sortTimetable()

    def sortTimetable(self):
        for dayIdx in range(len(self.timetable)):
            day = self.timetable[dayIdx]
            schedIdx = 0
            while schedIdx < len(day):
                if day[schedIdx][2] == "''":
                    self.timetable[dayIdx].pop(schedIdx)
                    schedIdx -= 1
                schedIdx += 1
            for j in range(len(day)-1):
                for i in range(j,-1,-1):
                    if self.timetable[dayIdx][i] > self.timetable[dayIdx][i+1]:
                        self.timetable[dayIdx][i],self.timetable[dayIdx][i+1] = self.timetable[dayIdx][i+1],self.timetable[dayIdx][i]

    def saveTimetable(self):
        file_timetable = open(self.path_timetable)
        rawlines = file_timetable.readlines()
        otherTexts = '\n'.join(rawlines[1:])
        savingTexts = f'{self.timetable}\n{otherTexts}'
        file_timetable.close()
        file_timetable = open(self.path_timetable,'w')
        file_timetable.write(savingTexts)


    def searchTimeSchedule(self,h,m,weekday):
        if self.doTimetableSearch:
            hmTime = h*100+m
            subjectName = "''"
            lastSchedIdx = 0
            schedFound = False
            for schedule in self.timetable[weekday]:
                if schedule[0] <= hmTime:
                    lastSchedIdx += 1
                if schedule[0] <= hmTime < schedule[1]:
                    subjectName = schedule[2]
                    # if subjectName != '':
                    schedFound = True
                    break
            idx = self.timetable[weekday].index(schedule) if schedFound else lastSchedIdx
            try:
                timeStr = f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02} ~ {int(schedule[1]//100):02}:{int(schedule[1]%100):02}'
            except UnboundLocalError:
                timeStr = ''
            return ((subjectName,timeStr) if schedFound else ("''",''),idx)
        else:
            return (("''","''"),0)
    

class CoordZone():
    '''A zone of coordinates, receives a series of tuples as ((fromX, fromY),(toX, toY))'''
    def __init__(self,*subzones):
        self.subzones = set(subzones)

    def add(self,*subzones):
        for subzone in subzones:
            self.subzones.add(subzone)

    def remove(self,*subzones):
        for subzone in subzones:
            self.subzones.remove(subzone)

    def include(self,coord:Tuple[int]) -> bool:
        result = False
        for zone in self.subzones:
            if (coord[0] in range(zone[0][0],zone[1][0])) and (coord[1] in range(zone[0][1],zone[1][1])):
                result = True
        return result
    
    def clear(self):
        self.subzones = set([])
    
    def __str__(self):
        return str(self.subzones)