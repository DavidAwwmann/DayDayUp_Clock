import pygame
import sys
from typing import List

import GUI.manage_GUI as GUI
import manage_inputs as INPUTS
import manage_time as TIMER

class RtnValDoes():
    def __init__(self):
        pass

    def switchDarkMode(self):
        gui.darkMode = not(gui.darkMode)

    def switchCompressLevel(self):
        if gui.compressLevel in [0,1]:
            gui.compressLevel += 1
        else:
            gui.compressLevel = 0

    def deliverClockHandAngles(self,s:float,m:float,h:float):
        gui.nowTimeAngle = (s,m,h)

    def switchDoTimetableSearch(self):
        gui.doTimetableSearch = not(gui.doTimetableSearch)
        files.doTimetableSearch = gui.doTimetableSearch

    def rereadSettings(self):
        files.readTimetable()
        gui.settingsInput(files.settingsDict)

if __name__ == '__main__':
    pygame.init()
    mainscreen = pygame.display.set_mode((600,600),flags=pygame.RESIZABLE)
    pygame.display.set_caption('DDU Schedule Clock')
    icon = pygame.image.load('GUI/icon.png')
    pygame.display.set_icon(icon)
    gui = GUI.GUI_Manager(mainscreen)
    inputs = INPUTS.Inputs_Manager(mainscreen)
    files = INPUTS.File_Manager()
    timer = TIMER.Time_manager(mainscreen)
    rtns = RtnValDoes()

    timer.tick()
    gui.settingsInput(files.settingsDict)
    mousex,mousey = 0,0
    mouseBtns = [False,False,False,False] # left=1,mid=2,up=3
    nowSchedInfo,nowScheduleIdx = files.searchTimeSchedule(timer.today.hour,timer.today.minute,timer.today.weekday())

    shallLoop = 1
    while shallLoop:
        leftClickSignal = 0
        mouseScrollSignal = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                shallLoop = 0
                break
            elif event.type == pygame.VIDEORESIZE:
                gui.screenSize = size = (event.w,event.h)
            elif event.type == pygame.KEYDOWN:
                eval(inputs.keyEvent(event.key))
            elif event.type == TIMER.TIMEREVENT:
                eval(timer.tick())
                gui.clockDigitTexts = timer.updateDigitalTexts()
                if timer.today.second == 0:
                    rtn = files.searchTimeSchedule(timer.today.hour,timer.today.minute,timer.today.weekday())
                    nowSchedInfo = rtn[0]
                    nowScheduleIdx = rtn[1]
            elif event.type == GUI.IMPERATIVERESIZE:
                mainscreen = pygame.display.set_mode(event.size,flags=pygame.RESIZABLE)
            elif event.type == pygame.MOUSEMOTION:
                mousex,mousey = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouseBtns[event.button-1 if event.button-1 in [0,1,2] else 3] = True
                if event.button == 1:
                    leftClickSignal = 1
                elif event.button == 4:
                    mouseScrollSignal = 1
                elif event.button == 5:
                    mouseScrollSignal = -1
            elif event.type == pygame.MOUSEBUTTONUP:
                mouseBtns[event.button-1 if event.button-1 in [0,1,2] else 3] = False

        gui.drawScreenBg()
        gui.generateClock()
        gui.writeTimetableSchedules(files.timetable,timer.today.weekday(),nowScheduleIdx)
        gui.writeNowSchedule(nowSchedInfo[0],nowSchedInfo[1])

        rtn = gui.drawOptionBtns(mousex,mousey,mouseBtns)
        if rtn != None and leftClickSignal == 1:
            nowScheduleIdx = files.searchTimeSchedule(timer.today.hour,timer.today.minute,timer.today.weekday())[1]
            eval(rtn)
        if mouseScrollSignal != 0 and (gui.scheduleDisplayRect[0] < mousex < gui.scheduleDisplayRect[0]+gui.scheduleDisplayRect[2]) and (gui.scheduleDisplayRect[1] < mousey < gui.scheduleDisplayRect[1]+gui.scheduleDisplayRect[3]):
            gui.timetableScroll = (gui.timetableScroll+mouseScrollSignal) if (gui.timetableScroll+mouseScrollSignal)<=0 else 0
        elif leftClickSignal == 1 and (gui.scheduleDisplayRect[0] < mousex < gui.scheduleDisplayRect[0]+gui.scheduleDisplayRect[2]) and (gui.scheduleDisplayRect[1] < mousey < gui.scheduleDisplayRect[1]+int(gui.screenSize[1]/40)):
            gui.timetableScroll = (gui.timetableScroll+1) if (gui.timetableScroll+1)<=0 else 0
        elif leftClickSignal == 1 and (gui.scheduleDisplayRect[0] < mousex < gui.scheduleDisplayRect[0]+gui.scheduleDisplayRect[2]) and (gui.scheduleDisplayRect[1]+gui.scheduleDisplayRect[3]-int(gui.screenSize[1]/40) < mousey < gui.scheduleDisplayRect[1]+gui.scheduleDisplayRect[3]):
            gui.timetableScroll = (gui.timetableScroll-1) if (gui.timetableScroll-1)<=0 else 0

        pygame.display.flip()


    pygame.quit()
    sys.exit()