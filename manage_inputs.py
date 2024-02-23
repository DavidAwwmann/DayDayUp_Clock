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
        self.path_timetable = 'timetable.txt'
        self.readTimetable()
        self.doTimetableSearch = True

    def readTimetable(self):
        try:
            file_timetable=open(self.path_timetable)
        except:
            file_timetable=open(self.path_timetable,'w')
            file_timetable.write('[[114,514,\'\',\'\',\'\',\'\',\'\',\'\',\'\']]\n[\'\',\'\']\n{\'darkMode\':True,\'compressLevel\':0,\'screenSize\':(600,600),\'doTimetableSearch\':True}')
            file_timetable.close()
            file_timetable=open(self.path_timetable)
        
        rawlines = file_timetable.readlines()
        self.timetable = eval(rawlines[0])
        self.sloganTexts = eval(rawlines[1])
        self.settingsDict = eval(rawlines[2])
        self.doTimetableSearch = self.settingsDict['doTimetableSearch']
        file_timetable.close()

    def searchTimeSchedule(self,h,m,weekday):
        hmTime = h*100+m
        subjectName = ''
        lastSchedIdx = 0
        schedFound = False
        for schedule in self.timetable:
            if schedule[1] <= hmTime:
                lastSchedIdx += 1
            if schedule[0] <= hmTime < schedule[1]:
                subjectName = schedule[weekday+2]
                if subjectName != '':
                    schedFound = True
                    break
        idx = self.timetable.index(schedule) if schedFound else lastSchedIdx
        timeStr = f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02} ~ {int(schedule[1]//100):02}:{int(schedule[1]%100):02}'
        return ((subjectName,timeStr) if schedFound else ('',''),idx)