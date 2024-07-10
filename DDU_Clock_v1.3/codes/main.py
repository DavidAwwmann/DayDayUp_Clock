import pygame
import sys
import threading

import GUI.manage_GUI as GUI
import manage_inputs as INPUTS
import manage_time as TIMER
import manage_edit as EDIT
import manage_tk as TTKK
from time import sleep

class RtnValDoes():
    '''This class contains the funcs which <gui> will call via eval(str).'''

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

    def switchLanguage(self):
        if gui.language == 'Chinese':
            gui.language = '英文'
            timer.language = '英文'
        else:
            gui.language = 'Chinese'
            timer.language = 'Chinese'

    def rereadSettings(self):
        files.readTimetable()
        gui.settingsInput(files.settingsDict)
        timer.receiveTimeOffset(files.settingsDict['timeOffset'])
        timer.tickRate = files.settingsDict['maxTps']

    def reopenSettings(self):
        currentPath = files.path_timetable
        newPath = ttkk.reopenTimetable(currentPath,gui.language)
        if newPath == '*failed':
            if gui.language == 'Chinese':
                TTKK.tkmsg.showerror('打开失败',f'无法打开文件！\n请检查文件路径及版本是否正确')
            else:
                TTKK.tkmsg.showerror('Oops!',f'Failed to open file!\nPlease make sure the direction and version are correct')
        elif newPath == '*cancel':
            pass
        else:
            files.path_timetable = newPath
            self.rereadSettings()

    def reopenBackgroundImg(self,idx):
        if idx == 0:
            currentPath = gui.path_backgroundImg0
        else:
            currentPath = gui.path_backgroundImg1
        newPath = ttkk.reopenBackgroundImg(currentPath,gui.language)
        if newPath == '*cancel':
            pass
        else:
            if idx == 0:
                gui.path_backgroundImg0 = newPath
            else:
                gui.path_backgroundImg1 = newPath
            gui.doBackgroundImgDisplay[idx] = True
            gui.readBackgroundImg()

    def switchDoBackgroundImgDisplay(self,idx):
        gui.doBackgroundImgDisplay[idx] = not(gui.doBackgroundImgDisplay[idx])
        gui.readBackgroundImg()

    def switchSidebarDisplayStyle(self):
        if gui.sidebarDisplayStyle == 3:
            gui.sidebarDisplayStyle = 0
        else:
            gui.sidebarDisplayStyle += 1

    def switchRetrenchMode(self):
        gui.retrenchMode = not(gui.retrenchMode)

    def zoomSidebar(self,idx:int,direction:int):
        '''<direction>: -1 for minus, 1 for add, 0 for reset.'''
        if direction == 0:
            gui.sidebarZoomLevel[idx] = 0
        else:
            if gui.sidebarZoomLevel[idx]+direction in range(-11,12):
                gui.sidebarZoomLevel[idx] += direction
        if gui.sidebarZoomLevel[idx] == -11:
            gui.sidebarZoomChangable[idx] = [True,False]
        elif gui.sidebarZoomLevel[idx] == 11:
            gui.sidebarZoomChangable[idx] = [False,True]
        else:
            gui.sidebarZoomChangable[idx] = [True,True]

if __name__ == '__main__':
    pygame.init()
    mainscreen = pygame.display.set_mode((600,600),flags=pygame.RESIZABLE)
    pygame.display.set_caption('DDU Schedule Clock')
    icon = pygame.image.load('GUI/icon.png')
    pygame.display.set_icon(icon)

    threadShareValues = {}

    gui = GUI.GUI_Manager(mainscreen)           # Instantiate the objects.
    inputs = INPUTS.Inputs_Manager(mainscreen)
    files = INPUTS.File_Manager()
    timer = TIMER.Time_manager(mainscreen)
    ttkk = TTKK.Tk_Manager()
    rtns = RtnValDoes()

    timer.tick()    # does this as an init.
    gui.settingsInput(files.settingsDict)
    timer.receiveTimeOffset(files.settingsDict['timeOffset'])
    timer.tickRate = files.settingsDict['maxTps']
    mousex,mousey = 0,0
    mouseBtns = [False,False,False,False,False] # [left, mid, up, else, leftUp]
    doubleClickState = 0    # 0=initial, 1=leftClick1, 2=timeout(singleClick), 3=leftClick2(doubleClick)
    nowSchedInfo,nowScheduleIdx = files.searchTimeSchedule(timer.today.hour,timer.today.minute,timer.today.weekday())

    shallLoop = 1
    while shallLoop:
        leftClickSignal = 0
        mouseScrollSignal = 0
        shallTick = False
        mouseBtns[4] = False
        if doubleClickState in [2,3]:   # initialize when click activated
            doubleClickState = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:   # observes QUIT event
                shallLoop = 0
                break
            elif event.type == pygame.VIDEORESIZE:  # observes the resize of window
                gui.screenSize = size = (event.w,event.h)
            # elif event.type == pygame.KEYDOWN:
            #     eval(inputs.keyEvent(event.key))
            elif event.type == TIMER.TIMEREVENT:    # update the clock for each tick
                eval(timer.tick())
                gui.clockDigitTexts = timer.updateDigitalTexts()
                rtn = files.searchTimeSchedule(timer.today.hour,timer.today.minute,timer.today.weekday())
                nowSchedInfo = rtn[0]
                nowScheduleIdx = rtn[1]
                shallTick = True
            elif event.type == GUI.IMPERATIVERESIZE:
                mainscreen = pygame.display.set_mode(event.size,flags=pygame.RESIZABLE)
            elif event.type == pygame.MOUSEMOTION:
                mousex,mousey = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouseBtns[event.button-1 if event.button-1 in [0,1,2] else 3] = True
                if event.button == 1:
                    leftClickSignal = 1
                    if gui.doubleClickDetectZone.include((mousex,mousey)):
                        rtn = inputs.checkDoubleClick(doubleClickState)
                        doubleClickState = rtn
                elif event.button == 4:
                    mouseScrollSignal = 1
                elif event.button == 5:
                    mouseScrollSignal = -1
            elif event.type == INPUTS.DOUBLE_CLICK_TIMER_EVENT:
                rtn = inputs.checkDoubleClick(doubleClickState,True)
                doubleClickState = rtn
            elif event.type == pygame.MOUSEBUTTONUP:    # event.button: left=1, mid=2, right=3
                mouseBtns[event.button-1 if event.button-1 in [0,1,2] else 3] = False
                if event.button == 1:
                    mouseBtns[4] = True

        portValues = [timer.today.weekday(),
                      timer.today.year,
                      timer.today.month,
                      timer.today.day,
                      timer.today.hour,
                      timer.today.minute,
                      timer.today.second,
                      timer.get_dateDelta().days,   # the sum of the days between today and January_1st, vary between [0,365]
                      timer.get_weeksDelta()        # the sum of the weeks between today and January_1st, vary between [0,52]
                      ]     # takes '1919/8/10 11:45:14' as [6, 1919, 8, 10, 11, 45, 14, 221, 31]
        
        if shallTick:
            gui.drawScreenBg()
            gui.generateClock()
            rtn = gui.writeTimetableSchedules(files.timetable,timer.today.weekday(),nowScheduleIdx,portValues,mousex,mousey,mouseBtns)
            gui.writeNowSchedule(nowSchedInfo[0],nowSchedInfo[1],portValues)
            eval(rtn)

        rtn = gui.drawOptionBtns(mousex,mousey,mouseBtns,doubleClickState)
        if rtn != None and (leftClickSignal == 1 or doubleClickState == 2):
            nowScheduleIdx = files.searchTimeSchedule(timer.today.hour,timer.today.minute,timer.today.weekday())[1]
            eval(rtn)
        if mouseScrollSignal != 0 and (gui.scheduleDisplayRect[0] < mousex < gui.scheduleDisplayRect[0]+gui.scheduleDisplayRect[2]) and (gui.scheduleDisplayRect[1] < mousey < gui.scheduleDisplayRect[1]+gui.scheduleDisplayRect[3]):
            gui.timetableScroll[1] = (gui.timetableScroll[1]+mouseScrollSignal) if (gui.timetableScroll[1]+mouseScrollSignal)<=0 else 0

        if gui.sidebarLeftsideOffset < (20-(int(gui.screenSize[1]*0.625-6) if gui.screenSize[0]/gui.screenSize[1]>=1 else int(gui.screenSize[0]*0.625-6)))/gui.screenSize[0]:
            gui.sidebarLeftsideOffset = (20-(int(gui.screenSize[1]*0.625-6) if gui.screenSize[0]/gui.screenSize[1]>=1 else int(gui.screenSize[0]*0.625-6)))/gui.screenSize[0]
        elif gui.sidebarLeftsideOffset > (gui.screenSize[0]-40-(int(gui.screenSize[1]*0.625-6) if gui.screenSize[0]/gui.screenSize[1]>=1 else int(gui.screenSize[0]*0.625-6)))/gui.screenSize[0]:
            gui.sidebarLeftsideOffset = (gui.screenSize[0]-40-(int(gui.screenSize[1]*0.625-6) if gui.screenSize[0]/gui.screenSize[1]>=1 else int(gui.screenSize[0]*0.625-6)))/gui.screenSize[0]

        if gui.retrenchMode:
            if pygame.display.get_active():
                sleep(0.2)
            else:
                sleep(1)
        pygame.display.flip()


    pygame.quit()   # These should be outside the while_True loop, otherwise the background-programe won't exit properly.
    sys.exit()