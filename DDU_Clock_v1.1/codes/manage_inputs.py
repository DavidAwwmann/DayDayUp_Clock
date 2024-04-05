import pygame
import tkinter as tk
import tkinter.filedialog as tkfile
import tkinter.messagebox as tkmessage
from typing import Union,List,Tuple,Optional

pygame.init()

root = tk.Tk()
root.withdraw()

class Inputs_Manager():
    def __init__(self,master:pygame.Surface):
        self.master = master

    def keyEvent(self,keyName):
        if keyName == pygame.K_l:
            # return 'rtns.switchDarkMode()'
            return '0'
        elif keyName == pygame.K_p:
            # return 'rtns.switchCompressLevel()'
            return '0'
        else:
            return '0'
        
class File_Manager():
    def __init__(self):
        self.timetable = []
        self.sloganTexts = []
        self.settingsDict = {}
        self.path_timetable = 'timetable1.txt'
        self.readTimetable()
        self.doTimetableSearch = True

    def readTimetable(self):
        try:
            file_timetable=open(self.path_timetable)
        except:
            file_timetable=open(self.path_timetable,'w')
            file_timetable.write('[[],[],[],[],[],[],[]]\n{\'darkMode\':True,\'compressLevel\':0,\'screenSize\':(600,600),\'doTimetableSearch\':True,\'textFonts\':[\'C:/Windows/Fonts/stxinwei.ttf\',\'C:/Windows/Fonts/roccb___.ttf\',\'C:/Windows/Fonts/simhei.ttf\',\'C:/Windows/Fonts/rock.ttf\',\'C:/Windows/Fonts/stzhongs.ttf\']}')
            file_timetable.close()
            file_timetable=open(self.path_timetable)
        
        rawlines = file_timetable.readlines()
        self.timetable = eval(rawlines[0])
        # self.sloganTexts = eval(rawlines[1])
        self.settingsDict = eval(rawlines[1])   # in replace of rawlines[2]
        self.doTimetableSearch = self.settingsDict['doTimetableSearch']
        file_timetable.close()
        self.sortTimetable()

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
        hmTime = h*100+m
        subjectName = ''
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
        return ((subjectName,timeStr) if schedFound else ('',''),idx)