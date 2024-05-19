import pygame
from typing import Union,List,Tuple,Dict,Any
from math import sin,cos,tan,radians
sin1 = lambda x:sin(radians(x))
cos1 = lambda x:cos(radians(x))
tan1 = lambda x:tan(radians(x))

DEBUG = True

def dbprint(*args,**kwargs):
    if DEBUG:
        print(*args,**kwargs)

pygame.init()

IMPERATIVERESIZE = pygame.USEREVENT+2

class GUI_Manager():
    def __init__(self,master:pygame.Surface):
        self.master = master
        self.darkMode = True
        self.screenSize = (600,600)
        self.compressLevel = 0
        self.nowTimeAngle = (0,0,0)
        self.doTimetableSearch = True
        self.clockDigitTexts = ['','','']
        self.btnActiveRects = {}
        self.timetableScroll = [0,0]
        self.scheduleDisplayRect = (0,0,0,0)
        self.clockCenter = (0,0)
        self.fullscreen = False
        self.textFonts = ['C:/Windows/Fonts/stxinwei.ttf','C:/Windows/Fonts/roccb___.ttf','C:/Windows/Fonts/simhei.ttf','C:/Windows/Fonts/rock.ttf','C:/Windows/Fonts/stzhongs.ttf']
        
    def drawScreenBg(self):
        if self.darkMode:
            self.master.fill((20,20,20))
            pygame.draw.rect(self.master,(50,50,50),(0,0)+self.screenSize,width=5)
            if self.compressLevel == 0:
                linex = int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6)
                pygame.draw.line(self.master,(50,50,50),(linex,0),(linex,self.screenSize[1]),width=2)
        else:
            self.master.fill((225,225,225))
            pygame.draw.rect(self.master,(180,180,180),(0,0)+self.screenSize,width=5)
            if self.compressLevel == 0:
                linex = int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6)
                pygame.draw.line(self.master,(180,180,180),(linex,0),(linex,self.screenSize[1]),width=2)

    def drawClockFace(self,rect:Tuple[int,int,int,int]):
        if self.darkMode:
            COLOR1 = (200,200,200)
            COLOR2 = (130,130,130)
            addon = 0
        else:
            COLOR1 = (20,20,20)
            COLOR2 = (80,80,80)
            addon = 1
        center = (rect[0]+rect[2]//2,rect[1]+rect[2]//2)
        self.clockCenter = center
        hourMarks = []
        minuteMarks = []
        for i in range(60):
            minuteMarks.append((int(sin1(6*i)*rect[2]//2+center[0]),int(cos1(6*i)*rect[2]//2+center[1])))
        for i in range(12):
            hourMarks.append((int(sin1(30*i)*rect[2]//2+center[0]),int(cos1(30*i)*rect[2]//2+center[1])))
            minuteMarks.remove((int(sin1(30*i)*rect[2]//2+center[0]),int(cos1(30*i)*rect[2]//2+center[1])))
        for cor in minuteMarks:
            pygame.draw.circle(self.master,COLOR2,cor,(rect[2]+30*addon)/150 if (rect[2]+30*addon)/150 >= 1 else 1)
        for cor in hourMarks:
            pygame.draw.circle(self.master,COLOR1,cor,(rect[2]+50*addon)/100 if (rect[2]+50*addon)/100 >= 2 else 2)

    def drawClockHands(self,ls,lm,lh,radius,center,ws,wm,wh):
        s,m,h = self.nowTimeAngle
        if self.darkMode:
            COLOR_S = (255,245,210)
            COLOR_M = (195,250,255)
            COLOR_H = (255,200,155)
        else:
            COLOR_S = (25,25,25)
            COLOR_M = (120,120,120)
            COLOR_H = (80,80,80)
        cor_h = (((int(sin1(h)*radius+center[0]),int(cos1(h)*radius+center[1]))),((int(sin1(h)*(radius-lh)+center[0]),int(cos1(h)*(radius-lh)+center[1]))))
        cor_m = (((int(sin1(m)*radius+center[0]),int(cos1(m)*radius+center[1]))),((int(sin1(m)*(radius-lm)+center[0]),int(cos1(m)*(radius-lm)+center[1]))))
        cor_s = (((int(sin1(s)*radius+center[0]),int(cos1(s)*radius+center[1]))),((int(sin1(s)*(radius-ls)+center[0]),int(cos1(s)*(radius-ls)+center[1]))))
        pygame.draw.line(self.master,COLOR_H,cor_h[0],cor_h[1],int(wh))
        pygame.draw.line(self.master,COLOR_M,cor_m[0],cor_m[1],int(wm))
        pygame.draw.line(self.master,COLOR_S,cor_s[0],cor_s[1],int(ws))

    def writeClockDigits(self,fontUp:pygame.font.Font,fontMid:pygame.font.Font,fontDown:pygame.font.Font,rectUp,rectMid,rectDown):
        if self.darkMode:
            COLOR_UP = (190,210,220)
            COLOR_MID = (255,250,220)
            COLOR_DOWN = (210,190,185)
        else:
            COLOR_UP = (60,60,60)
            COLOR_MID = (25,25,25)
            COLOR_DOWN = (80,80,80)
        textUp = fontUp.render(self.clockDigitTexts[0],True,COLOR_UP)
        textMid = fontMid.render(self.clockDigitTexts[1],True,COLOR_MID)
        textDown = fontDown.render(self.clockDigitTexts[2],True,COLOR_DOWN)
        self.master.blit(textUp,rectUp,)
        self.master.blit(textMid,rectMid)
        self.master.blit(textDown,rectDown)
        
    def generateClock(self):
        if self.compressLevel == 0:
            totalSize = (5,5,int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6),int(self.screenSize[1]-10))
            clockCenter = (int(totalSize[2]/2+5),int(totalSize[3]*0.375+5))
            radius = min(int(totalSize[2]*0.4),int(totalSize[3]*0.3))
        elif self.compressLevel == 1:
            totalSize = (5,5,self.screenSize[0]-10,self.screenSize[1]-10)
            clockCenter = (int(totalSize[2]/2+5),int(totalSize[3]*0.325+5))
            radius = min(int(totalSize[2]*0.4),int(totalSize[3]*0.275))
        elif self.compressLevel == 2:
            totalSize = (5,5,self.screenSize[0]-10,self.screenSize[1]-10)
            clockCenter = (int(totalSize[2]/2+5),int(totalSize[3]/2+5))
            radius = min(int(totalSize[2]*0.47),int(totalSize[3]*0.47))
        actualRect = (clockCenter[0]-radius,clockCenter[1]-radius,2*radius,2*radius)
        if self.darkMode:
            addon = 0
        else:
            addon = 1
        ls = int(radius*0.33)
        lm = int(radius*0.265)
        lh = int(radius*0.24)
        ws = int(radius*0.0113+0.7*addon) if int(radius*0.0113+0.7*addon) >= 1 else 1
        wm = int(radius*0.025+0.8*addon) if int(radius*0.025+0.8*addon) >= 1 else 1
        wh = int(radius*0.04+0.3*addon) if int(radius*0.04+0.3*addon) >= 1 else 1
        fontUp = pygame.font.Font(self.textFonts[0],int(radius*0.125))
        fontMid = pygame.font.Font(self.textFonts[1],int(radius*0.37))
        fontDown = pygame.font.Font(self.textFonts[0],int(radius*0.115))
        # fontUp.set_bold(True)
        # fontDown.set_bold(True)
        w0,h0 = fontUp.size(self.clockDigitTexts[0])
        w1,h1 = fontMid.size(self.clockDigitTexts[1])
        w2,h2 = fontDown.size(self.clockDigitTexts[2])
        rectUp = pygame.rect.Rect(clockCenter[0]-int(w0/2),clockCenter[1]-int((h0+h1)*0.47),w0,h0)
        rectMid = pygame.rect.Rect(clockCenter[0]-int(w1/2),clockCenter[1]-int(h1*0.45),w1,h1)
        rectDown = pygame.rect.Rect(clockCenter[0]-int(w2/2),clockCenter[1]-int((h2-h1)*0.6),w2,h2)
        self.drawClockFace(actualRect)
        self.drawClockHands(ls,lm,lh,radius,clockCenter,ws,wm,wh)
        self.writeClockDigits(fontUp,fontMid,fontDown,rectUp,rectMid,rectDown)
        
    def settingsInput(self,settingsDict:Dict[str,Any]):
        self.darkMode = settingsDict['darkMode']
        self.compressLevel = settingsDict['compressLevel']
        self.screenSize = settingsDict['screenSize']
        self.doTimetableSearch = settingsDict['doTimetableSearch']
        self.textFonts = settingsDict['textFonts']
        self.timetableScroll = [0,0]
        resizeEvent = pygame.event.Event(IMPERATIVERESIZE,size=self.screenSize)
        pygame.event.post(resizeEvent)

    def drawOptionBtns(self,mousex,mousey,mouseBtns):
        rawSize = min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))
        width = int(rawSize/64) if int(rawSize/64) >= 1 else 1
        b_radius = width*3 if width <= rawSize/9 else 0
        font_info = pygame.font.Font(self.textFonts[2],int(rawSize*0.02+12))
        self.btnActiveRects = {}
        rtn = None
        btnHoverTexts = {'switchCompressLevel': f"简略模式: {'0挡' if self.compressLevel==0 else '1挡' if self.compressLevel==1 else '2挡'}",
                         'switchDarkMode': f"暗色模式: {'开' if self.darkMode else '关'}",
                         'switchDoTimetableSearch': f"是否跟进计划: {'是' if self.doTimetableSearch else '否'}",
                         'rereadSettings': "重新读取数据"}
        if self.darkMode:
            COLOR0 = (20,20,20)
            COLOR1 = (110,105,90)
            COLOR2 = (130,120,95)
            COLOR3 = (180,175,150)
            COLOR4 = (40,40,30)
            COLOR5 = (60,60,40)
        else:
            COLOR0 = (225,225,225)
            COLOR1 = (140,140,140)
            COLOR2 = (95,95,95)
            COLOR3 = (40,40,40)
            COLOR4 = (200,200,200)
            COLOR5 = (170,170,170)

        showHoverTexts = {'switchCompressLevel': lambda:None,
                          'switchDarkMode': lambda:None,
                          'switchDoTimetableSearch': lambda:None,
                          'rereadSettings': lambda:None}

        # region switchCompressLevel
        rect_btn = (int(self.screenSize[0]-rawSize*1.2),int(self.screenSize[1]-rawSize*1.2),rawSize,rawSize)
        if rect_btn[0] <= mousex < rect_btn[0]+rect_btn[2] and rect_btn[1] <= mousey < rect_btn[1]+rect_btn[3]:
            if mouseBtns[0]:
                pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0+16*self.compressLevel,0,COLOR3)
                self.master.blit(btnimg,rect_btn)
                rtn = 'rtns.switchCompressLevel()'
            else:
                pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0+16*self.compressLevel,0,COLOR2)
                def showInfoText():
                    text_info = font_info.render(btnHoverTexts['switchCompressLevel'],True,COLOR3,COLOR0)
                    text_info.set_alpha(200)
                    self.master.blit(text_info,(mousex-font_info.size(btnHoverTexts['switchCompressLevel'])[0]+1,mousey-font_info.size('中')[1]-1))
                showHoverTexts['switchCompressLevel'] = showInfoText
                self.master.blit(btnimg,rect_btn)
        else:
            pygame.draw.rect(self.master,COLOR1,rect_btn,width*2,border_radius=b_radius)
            btnimg = self.getButtons(rawSize,0+16*self.compressLevel,0,COLOR1)
            self.master.blit(btnimg,rect_btn)
        self.btnActiveRects['switchCompressLevel'] = rect_btn
        # endregion

        # region switchDarkMode
        rect_btn = (int(self.screenSize[0]-rawSize*2.3),int(self.screenSize[1]-rawSize*1.2),rawSize,rawSize)
        if rect_btn[0] <= mousex < rect_btn[0]+rect_btn[2] and rect_btn[1] <= mousey < rect_btn[1]+rect_btn[3]:
            if mouseBtns[0]:
                pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0 if self.darkMode else 16,16,COLOR3)
                self.master.blit(btnimg,rect_btn)
                rtn = 'rtns.switchDarkMode()'
            else:
                pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0 if self.darkMode else 16,16,COLOR2)
                def showInfoText():
                    text_info = font_info.render(btnHoverTexts['switchDarkMode'],True,COLOR3,COLOR0)
                    text_info.set_alpha(200)
                    self.master.blit(text_info,(mousex+1,mousey-font_info.size('中')[1]-1))
                showHoverTexts['switchDarkMode'] = showInfoText
                self.master.blit(btnimg,rect_btn)
        else:
            pygame.draw.rect(self.master,COLOR1,rect_btn,width*2,border_radius=b_radius)
            btnimg = self.getButtons(rawSize,0 if self.darkMode else 16,16,COLOR1)
            self.master.blit(btnimg,rect_btn)
        self.btnActiveRects['switchDarkMode'] = rect_btn
        # endregion

        if self.compressLevel == 0:
            # region switchDoTimetableSearch
            rect_btn = (int(self.screenSize[0]-rawSize*3.4),int(self.screenSize[1]-rawSize*1.2),rawSize,rawSize)
            if rect_btn[0] <= mousex < rect_btn[0]+rect_btn[2] and rect_btn[1] <= mousey < rect_btn[1]+rect_btn[3]:
                if mouseBtns[0]:
                    pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0 if self.doTimetableSearch else 16,32,COLOR3)
                    self.master.blit(btnimg,rect_btn)
                    rtn = 'rtns.switchDoTimetableSearch()'
                else:
                    pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0 if self.doTimetableSearch else 16,32,COLOR2)
                    def showInfoText():
                        text_info = font_info.render(btnHoverTexts['switchDoTimetableSearch'],True,COLOR3,COLOR0)
                        text_info.set_alpha(200)
                        self.master.blit(text_info,(mousex+1,mousey-font_info.size('中')[1]-1))
                    showHoverTexts['switchDoTimetableSearch'] = showInfoText
                    self.master.blit(btnimg,rect_btn)
            else:
                pygame.draw.rect(self.master,COLOR1,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0 if self.doTimetableSearch else 16,32,COLOR1)
                self.master.blit(btnimg,rect_btn)
            self.btnActiveRects['switchDoTimetableSearch'] = rect_btn
        # endregion

            # region rereadSettings
            rect_btn = (int(self.screenSize[0]-rawSize*4.5),int(self.screenSize[1]-rawSize*1.2),rawSize,rawSize)
            if rect_btn[0] <= mousex < rect_btn[0]+rect_btn[2] and rect_btn[1] <= mousey < rect_btn[1]+rect_btn[3]:
                if mouseBtns[0]:
                    pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0,48,COLOR3)
                    self.master.blit(btnimg,rect_btn)
                    rtn = 'rtns.rereadSettings()'
                else:
                    pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0,48,COLOR2)
                    def showInfoText():
                        text_info = font_info.render(btnHoverTexts['rereadSettings'],True,COLOR3,COLOR0)
                        text_info.set_alpha(200)
                        self.master.blit(text_info,(mousex+1,mousey-font_info.size('中')[1]-1))
                    showHoverTexts['rereadSettings'] = showInfoText
                    self.master.blit(btnimg,rect_btn)
            else:
                pygame.draw.rect(self.master,COLOR1,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0,48,COLOR1)
                self.master.blit(btnimg,rect_btn)
            self.btnActiveRects['rereadSettings'] = rect_btn
        # endregion

        for fun in showHoverTexts.values():
            fun()

        return rtn

    def getButtons(self,size,x,y,color,w=15,h=15):
        rawimg = pygame.image.load('GUI/buttons.png')
        surface = pygame.Surface((w,h))
        surface.fill((255,255,255))
        surface.set_colorkey((255,255,255))
        surface.blit(rawimg,(0,0),(x,y,w,h))
        pixarr = pygame.PixelArray(surface)
        pixarr.replace((0,0,0),color)
        pixarr.close()
        surface = pygame.transform.scale(surface,(int(size*w/16),int(size*h/16)))
        return surface

    def writeTimetableSchedules(self,rawTimetable:List[List],weekday:int,nowSchedIdx:Union[int,None]=None,portValues:List[int]=[0,0,0,0,0,0,0,0,0]):
        # portValue: [<weekday>,<year>,<month>,<date>,<hour>,<minute>,<second>,<countDays>,<countWeeks>]
        w,y,n,d,h,m,s,cd,cw = portValues

        timetable = rawTimetable.copy()
        minus = 0
        popIdx = []
        for schedIdx in range(len(timetable[weekday])):
            sched = timetable[weekday][schedIdx]
            if eval(sched[2]) == '':
                popIdx.insert(0,schedIdx)
                if type(nowSchedIdx) == int:
                    # if nowSchedIdx > schedIdx:
                    #     minus += 1
                    # elif nowSchedIdx == schedIdx:
                    #     nowSchedIdx = None
                    minus += 1
        # if type(nowSchedIdx) == int:
        #     nowSchedIdx -= minus
        # for idx in popIdx:
        #     timetable[weekday].pop(idx)

        if self.compressLevel == 0:
            if self.darkMode:
                COLOR0 = (20,20,20)
                COLOR7 = (180,180,160)
                if self.doTimetableSearch:
                    COLOR1 = (100,100,100)
                    COLOR2 = (140,140,140)
                    COLOR3 = (215,195,185)
                    COLOR4 = (245,200,180)
                    COLOR5 = (180,170,160)
                    COLOR6 = (225,215,190)
                else:
                    COLOR1 = (167,165,160)
                    COLOR2 = (210,205,195)
                    COLOR3 = (175,170,163)
                    COLOR4 = (205,202,195)
                    COLOR5 = (168,165,160)
                    COLOR6 = (200,195,185)
                    nowSchedIdx = -1
            else:
                COLOR0 = (225,225,225)
                COLOR7 = (100,100,100)
                if self.doTimetableSearch:
                    COLOR1 = (180,180,180)
                    COLOR2 = (150,150,150)
                    COLOR3 = (40,40,40)
                    COLOR4 = (15,15,15)
                    COLOR5 = (120,120,120)
                    COLOR6 = (80,80,80)
                else:
                    COLOR1 = (140,140,140)
                    COLOR2 = (115,115,115)
                    COLOR3 = (180,180,180)
                    COLOR4 = (115,115,115)
                    COLOR5 = (140,140,140)
                    COLOR6 = (115,115,115)
                    nowSchedIdx = -1
            timetableTexts = []
            totalAreaLeft = int(self.screenSize[1]*0.625+6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625+6)
            totalAreaWidth = self.screenSize[0]-5-totalAreaLeft
            totalAreaUp = 5+int(min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)
            totalAreaHeight = int(self.screenSize[1]-2*min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)-10
            totalAreaWidth = totalAreaWidth if totalAreaWidth>=1 else 1
            totalAreaHeight = totalAreaHeight if totalAreaHeight>=1 else 1
            textSurface = pygame.Surface((totalAreaWidth,totalAreaHeight))
            textSurface.fill(COLOR0)
            self.scheduleDisplayRect = (totalAreaLeft,totalAreaUp,totalAreaWidth,totalAreaHeight)
            for schedule in timetable[weekday]:
                scheduleText = (f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02} ~ {int(schedule[1]//100):02}:{int(schedule[1]%100):02}  ',eval(schedule[2]))
                timetableTexts.append(scheduleText)
            
            fontSize_timetable = int(self.screenSize[0]/600*20) if int(self.screenSize[0]/600*20) <= 30 else 30
            font_timetable = (pygame.font.Font(self.textFonts[3],fontSize_timetable),pygame.font.Font(self.textFonts[4],fontSize_timetable))

            try:
                textNeedArea = (max(list(map(lambda a:a[0],map(font_timetable[0].size,map(lambda a:a[0]+'  '+a[1],timetableTexts))))),(font_timetable[0].size('文')[1]+int(self.screenSize[1]/180))*(len(timetableTexts)-minus)-5)
            except ValueError:
                textNeedArea = (0,0)
            if -self.timetableScroll[1]*self.screenSize[1]/30 >= textNeedArea[1]:
                self.timetableScroll[1] = -int(textNeedArea[1]*30/self.screenSize[1])
            if -self.timetableScroll[0]*self.screenSize[0]/30 >= textNeedArea[0]:
                self.timetableScroll[0] = -int(textNeedArea[0]*30/self.screenSize[0])

            idx = 0
            for text in timetableTexts:
                if text[1] == '':
                    continue
                try:
                    if idx < nowSchedIdx:
                        surface_text = (font_timetable[0].render(text[0],True,(COLOR1)),font_timetable[1].render(text[1],True,(COLOR2)))
                    elif idx == nowSchedIdx:
                        surface_text = (font_timetable[0].render(text[0],True,(COLOR3)),font_timetable[1].render(text[1],True,(COLOR4)))
                    else:
                        surface_text = (font_timetable[0].render(text[0],True,(COLOR5)),font_timetable[1].render(text[1],True,(COLOR6)))
                    lineDigitArea = font_timetable[0].size(text[0])
                    textSurface.blit(surface_text[0],(10,5+int(self.screenSize[1]/45)+idx*(lineDigitArea[1]+int(self.screenSize[1]/180))+int(self.timetableScroll[1]*self.screenSize[1]/30)))
                    textSurface.blit(surface_text[1],(10+lineDigitArea[0],2+int(self.screenSize[1]/45)+idx*(lineDigitArea[1]+int(self.screenSize[1]/180))+int(self.timetableScroll[1]*self.screenSize[1]/30)))
                    idx += 1
                except:
                    idx += 1
            clickActiveArea = pygame.Surface((self.scheduleDisplayRect[2],+int(self.screenSize[1]/45)))
            clickActiveArea.fill(COLOR7)
            clickActiveArea.set_alpha(40)
            textSurface.blit(clickActiveArea,(0,0))
            textSurface.blit(clickActiveArea,(0,self.scheduleDisplayRect[3]-int(self.screenSize[1]/42)))
            self.master.blit(textSurface,(totalAreaLeft,totalAreaUp))

    def writeNowSchedule(self,subjectName:str,timeAreaText:str,portValues:List[int]=[0,0,0,0,0,0,0,0,0]):
        # portValue: [<weekday>,<year>,<month>,<date>,<hour>,<minute>,<second>,<countDays>,<countWeeks>]
        w,y,n,d,h,m,s,cd,cw = portValues
        if eval(subjectName) == '':
            return None
        if self.darkMode:
            COLOR1 = (255,245,200)
            COLOR2 = (200,190,160)
        else:
            COLOR1 = (15,15,15)
            COLOR2 = (100,100,100)
        fontSize = min(int(self.screenSize[0]/50),int(self.screenSize[1]/50),int((self.clockCenter[0]-5)/15))
        subjectName = eval(subjectName)
        if self.compressLevel in [0,1]:
            if self.doTimetableSearch:
                font = (pygame.font.Font(self.textFonts[0],fontSize*4),pygame.font.Font(self.textFonts[3],fontSize*2))
                text = (font[0].render(subjectName,True,COLOR1),font[1].render(timeAreaText,True,COLOR1))
                size = (font[0].size(subjectName),font[1].size(timeAreaText))
                self.master.blit(text[0],(self.clockCenter[0]-int(size[0][0]/2),int(self.screenSize[1]*0.75-size[0][1])))
                self.master.blit(text[1],(self.clockCenter[0]-int(size[1][0]/2),int(self.screenSize[1]*0.75)))
            else:
                font = (pygame.font.Font(self.textFonts[0],fontSize*3),pygame.font.Font(self.textFonts[3],fontSize*2))
                text = (font[0].render('未开启跟进计划',True,COLOR1),font[1].render('',True,COLOR1))
                text[0].set_alpha(45)
                size = (font[0].size('未开启跟进计划'),font[1].size(''))
                self.master.blit(text[0],(self.clockCenter[0]-int(size[0][0]/2),int(self.screenSize[1]*0.75-size[0][1]/2)))
        else:
            if self.doTimetableSearch:
                font = (pygame.font.Font(self.textFonts[0],int(fontSize*3.5)),pygame.font.Font(self.textFonts[3],fontSize*3))
                text = (font[0].render(subjectName,True,COLOR1),font[1].render('',True,COLOR1))
                size = (font[0].size(subjectName),font[1].size(''))
                self.master.blit(text[0],(self.clockCenter[0]-int(size[0][0]/2),int(self.screenSize[1]*0.7-size[0][1]/2)))

