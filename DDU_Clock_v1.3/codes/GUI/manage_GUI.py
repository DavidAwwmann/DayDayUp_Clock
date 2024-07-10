import pygame
from manage_inputs import CoordZone
from typing import Union,List,Tuple,Dict,Any
from math import sin,cos,tan,radians
from manage_edit import deco
from typing_extensions import Literal
sin1 = lambda x:sin(radians(x))
cos1 = lambda x:cos(radians(x))
tan1 = lambda x:tan(radians(x))

DEBUG = False

def dbprint(*args,**kwargs):
    if DEBUG:
        print(*args,**kwargs)

pygame.init()

IMPERATIVERESIZE = pygame.USEREVENT+2

class GUI_Manager():
    def __init__(self,master:pygame.Surface):   # vars below with '#*#' should be in timetable3.txt
        self.master = master
        self.darkMode = True                    #*#
        self.screenSize = (600,600)             #*#
        self.compressLevel = 0                  #*#
        self.nowTimeAngle = (0,0,0)
        self.doTimetableSearch = True           #*#
        self.clockDigitTexts = ['','','']
        self.btnActiveRects = {}
        self.timetableScroll = [0,0]
        self.scheduleDisplayRect = (0,0,0,0)
        self.clockCenter = (0,0)
        self.textFonts = ['C:/Windows/Fonts/stxinwei.ttf',
                          'C:/Windows/Fonts/roccb___.ttf',
                          'C:/Windows/Fonts/simhei.ttf',
                          'C:/Windows/Fonts/rock.ttf',
                          'C:/Windows/Fonts/stzhongs.ttf']  #*#
        self.colorfuncs:List[List[str]] = [['(12/17)*x+20','(46/51)*x+20','(28/51)*x+20'],
                                           ['(-41/51)*x+225','(-41/51)*x+225','(-41/51)*x+225']] #*#
        self.doBackgroundImgDisplay = [True,True]   #*#
        self.path_backgroundImg0 = ''               #*#
        self.path_backgroundImg1 = ''               #*#
        self.backgroundAlpha = 60                   #*#
        self.readBackgroundImg()
        self.scrollbarUnderDrag = [False,False]
        self.scrollbarOndragLastMousepos = [-1,-1]  # the x|y pos of the mouse in the previous tick, -1 for not-under-drag
        self.doubleClickDetectZone = CoordZone()
        self.language = 'Chinese'   # Chinese | 英文  #*#
        self.sidebarLeftsideOffset = 0.0  # right+, left-.
        self.sidebarLeftsideOndrag = False
        self.sidebarLeftsideOndragLastMouseX = -1
        self.sidebarDisplayStyle = 0    # 0: DayList, 1: WeekList, 2: DayColumnar, 3: WeekColumnar  #*#
        self.emptyColumnarMergeThreshold = 2401   # The least time between Two columnars to be merged (minutes). 2401 for never_merge    #*#
        self.sidebarZoomLevel = [0,0,0]   # [columnarX,columnarY,textFontsize], actualZoomRate[0|1] = (5/4)**self.sidebarZoomLevel[0|1]
        self.sidebarZoomChangable = [[True,True],[True,True],[True,True]]   # zoomLevels all in range(-11,12). [[+,-]].
        self.retrenchMode = False                         #*#
        self.maxTps = 1000  # milliseconds   #*#

    def readBackgroundImg(self):
        if self.doBackgroundImgDisplay[0]:
            try:
                self.backgroundImg0 = pygame.image.load(self.path_backgroundImg0)  
            except:
                self.doBackgroundImgDisplay[0] = False
        if self.doBackgroundImgDisplay[1]:
            try:
                self.backgroundImg1 = pygame.image.load(self.path_backgroundImg1)  
            except:
                self.doBackgroundImgDisplay[1] = False

    def ceiling(self,n:float) -> int:
        if n%1 == 0.0:
            return n
        else:
            return int(n)+1

    def loadBackgroundImg(self) -> Tuple[pygame.Surface, pygame.rect.Rect]:
        if self.darkMode:
            backgroundImg = self.backgroundImg0
        else:
            backgroundImg = self.backgroundImg1
        w,h = backgroundImg.get_size()
        zoom = max([self.screenSize[0]/w,self.screenSize[1]/h])
        w,h = self.ceiling(zoom*w),self.ceiling(zoom*h)
        backgroundSurface = pygame.transform.scale(backgroundImg,(w,h))
        backgroundSurface.set_alpha(self.backgroundAlpha)
        x,y = (self.screenSize[0]-w)//2,(self.screenSize[1]-h)//2
        rect = pygame.rect.Rect(x,y,w,h)
        return (backgroundSurface,rect)

    def getColor(self,darkMode:bool,x:int) -> Tuple[int,int,int]:
        if darkMode:
            colorfunc = self.colorfuncs[0]
        else:
            colorfunc = self.colorfuncs[1]
        r,g,b = int(eval(colorfunc[0])),int(eval(colorfunc[1])),int(eval(colorfunc[2]))
        return (r,g,b)
        
    def drawScreenBg(self):
        self.master.fill(self.getColor(self.darkMode,x=0))
        pygame.draw.rect(self.master,self.getColor(self.darkMode,x=55),(0,0)+self.screenSize,width=5)
        if self.compressLevel == 0:
            linex = (int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6)) + int(self.sidebarLeftsideOffset*self.screenSize[0])
            pygame.draw.line(self.master,self.getColor(self.darkMode,x=55),(linex,0),(linex,self.screenSize[1]),width=2)
        if self.doBackgroundImgDisplay[1-int(self.darkMode)]:
            surface,rect = self.loadBackgroundImg()
            self.master.blit(surface,rect)

    def drawClockFace(self,rect:Tuple[int,int,int,int]):
        COLOR1 = self.getColor(self.darkMode,x=255)
        COLOR2 = self.getColor(self.darkMode,x=175)
        addon = 0 if self.darkMode else 1

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
        COLOR_S = self.getColor(self.darkMode,x=252)
        COLOR_M = self.getColor(self.darkMode,x=120)
        COLOR_H = self.getColor(self.darkMode,x=181)

        cor_h = (((int(sin1(h)*radius+center[0]),int(cos1(h)*radius+center[1]))),((int(sin1(h)*(radius-lh)+center[0]),int(cos1(h)*(radius-lh)+center[1]))))
        cor_m = (((int(sin1(m)*radius+center[0]),int(cos1(m)*radius+center[1]))),((int(sin1(m)*(radius-lm)+center[0]),int(cos1(m)*(radius-lm)+center[1]))))
        cor_s = (((int(sin1(s)*radius+center[0]),int(cos1(s)*radius+center[1]))),((int(sin1(s)*(radius-ls)+center[0]),int(cos1(s)*(radius-ls)+center[1]))))
        pygame.draw.line(self.master,COLOR_H,cor_h[0],cor_h[1],int(wh))
        pygame.draw.line(self.master,COLOR_M,cor_m[0],cor_m[1],int(wm))
        pygame.draw.line(self.master,COLOR_S,cor_s[0],cor_s[1],int(ws))

    def writeClockDigits(self,fontUp:pygame.font.Font,fontMid:pygame.font.Font,fontDown:pygame.font.Font,rectUp,rectMid,rectDown):
        COLOR_UP = self.getColor(self.darkMode,x=205)
        COLOR_MID = self.getColor(self.darkMode,x=249)
        COLOR_DOWN = self.getColor(self.darkMode,x=179)

        textUp = fontUp.render(self.clockDigitTexts[0],True,COLOR_UP)
        textMid = fontMid.render(self.clockDigitTexts[1],True,COLOR_MID)
        textDown = fontDown.render(self.clockDigitTexts[2],True,COLOR_DOWN)
        self.master.blit(textUp,rectUp,)
        self.master.blit(textMid,rectMid)
        self.master.blit(textDown,rectDown)
        
    def generateClock(self):
        if self.compressLevel == 0:
            totalSize = (5,5,(int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6))+int(self.sidebarLeftsideOffset*self.screenSize[0]),int(self.screenSize[1]-10))
            clockCenter = (int(totalSize[2]/2+5),int(totalSize[3]*0.35+5))
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
        fontUp = self.getPygameFont(self.textFonts[0],int(radius*0.125))
        fontMid = self.getPygameFont(self.textFonts[1],int(radius*0.37))
        fontDown = self.getPygameFont(self.textFonts[0],int(radius*0.115))
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
        for fontIdx in range(len(self.textFonts)):
            font = self.textFonts[fontIdx]
            try:
                self.getPygameFont(font,8)
            except FileNotFoundError:
                self.textFonts[fontIdx] = None
        self.colorfuncs = settingsDict['colorfuncs']
        self.doBackgroundImgDisplay = settingsDict['doBackgroundImgDisplay']
        self.path_backgroundImg0,self.path_backgroundImg1 = settingsDict['backgroundImgPaths']
        self.backgroundAlpha = settingsDict['backgroundAlpha']
        self.sidebarDisplayStyle = settingsDict['sidebarDisplayStyle']
        self.emptyColumnarMergeThreshold = settingsDict['columnarGapMergeThreshold']
        self.retrenchMode = settingsDict['retrenchMode']
        self.maxTps = settingsDict['maxTps']
        if settingsDict['language'] == 'Chinese中文':
            self.language = 'Chinese'
        else:                        # 'English英文'
            self.language = '英文'
        self.timetableScroll = [0,0]
        self.sidebarLeftsideOffset = 0.0
        self.readBackgroundImg()
        resizeEvent = pygame.event.Event(IMPERATIVERESIZE,size=self.screenSize)
        pygame.event.post(resizeEvent)

    def getPygameFont(self,fontPath_or_SysFontName,size:int) -> pygame.font.Font:
        try:
            pgfont = pygame.font.Font(fontPath_or_SysFontName,size)
        except FileNotFoundError:
            pgfont = pygame.font.SysFont(fontPath_or_SysFontName,size)
        return pgfont

    def drawOptionBtns(self,mousex,mousey,mouseBtns,doubleClickState):
        self.doubleClickDetectZone.clear()
        totalWidth = self.screenSize[0]
        rawSize = min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))
        width = int(rawSize/64) if int(rawSize/64) >= 1 else 1
        b_radius = width*3 if width <= rawSize/9 else 0
        font_info = self.getPygameFont(self.textFonts[2],int(rawSize*0.02+12))
        self.btnActiveRects = {}
        rtn = None
        if self.language == 'Chinese':
            btnHoverTexts = {'switchCompressLevel': f"简略模式: {'0挡' if self.compressLevel==0 else '1挡' if self.compressLevel==1 else '2挡'}",
                            'switchDarkMode': f"暗色模式: {'开' if self.darkMode else '关'}",
                            'switchDoTimetableSearch': f"是否跟进计划: {'是' if self.doTimetableSearch else '否'}",
                            'rereadSettings': ("重新读取数据","双击以打开文件.."),
                            'switchLanguage': "Language: Chinese",
                            'switchDoBackgroundImgDisplay': (f"背景图片({'暗色模式' if self.darkMode else '亮色模式'}): {'显示' if self.doBackgroundImgDisplay[1-int(self.darkMode)] else '隐藏'}","双击以选择图片.."),
                            'switchSidebarDisplayStyle': f"计划单样式: {['当天列表','本周列表','当天柱状','本周柱状'][self.sidebarDisplayStyle]}",
                            'switchRetrenchMode': f"节能模式: {'开' if self.retrenchMode else '关'}"}
        else:
            btnHoverTexts = {'switchCompressLevel': f"Brief GUI: {'Lv0' if self.compressLevel==0 else 'Lv1' if self.compressLevel==1 else 'Lv2'}",
                            'switchDarkMode': f"Dark mode: {'ON' if self.darkMode else 'OFF'}",
                            'switchDoTimetableSearch': f"Schedule followed: {'Yes' if self.doTimetableSearch else 'No'}",
                            'rereadSettings': ("Re-read settings","Double-click to browse.."),
                            'switchLanguage': "语言: 英文",
                            'switchDoBackgroundImgDisplay': (f"Bg image({'dark mode' if self.darkMode else 'bright mode'}): {'Show' if self.doBackgroundImgDisplay[1-int(self.darkMode)] else 'Hide'}","Double-click to browse.."),
                            'switchSidebarDisplayStyle': f"Schedule sheet style: {['Today-list','Week-list','Today-columnar','Week-columnar'][self.sidebarDisplayStyle]}",
                            'switchRetrenchMode': f"Retrench mode: {'ON' if self.retrenchMode else 'OFF'}"}
        
        COLOR0 = self.getColor(self.darkMode,x=0)
        COLOR1 = self.getColor(self.darkMode,x=105)
        COLOR2 = self.getColor(self.darkMode,x=162)
        COLOR3 = self.getColor(self.darkMode,x=229)
        COLOR4 = self.getColor(self.darkMode,x=31)
        COLOR5 = self.getColor(self.darkMode,x=68)

        showHoverTexts = {'switchCompressLevel': lambda:None,
                          'switchDarkMode': lambda:None,
                          'switchDoTimetableSearch': lambda:None,
                          'rereadSettings': lambda:None,
                          'switchLanguage': lambda:None}

        # region switchCompressLevel
        rect_btn = (int(self.screenSize[0]-rawSize*1.2),int(self.screenSize[1]-rawSize*1.2),rawSize,rawSize)    # The rect of the button
        if rect_btn[0] <= mousex < rect_btn[0]+rect_btn[2] and rect_btn[1] <= mousey < rect_btn[1]+rect_btn[3]:
            if mouseBtns[0]:                                                                                        # when clicked
                pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)                      # draw button bg
                pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)                # draw button border
                btnimg = self.getButtons(rawSize,0+16*self.compressLevel,0,COLOR3)                          # get btn_img as a surface
                self.master.blit(btnimg,rect_btn)
                rtn = 'rtns.switchCompressLevel()'
            else:                                                                                                   # when hovered
                pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0+16*self.compressLevel,0,COLOR2)
                def showInfoText():                                                                         # always shows hover_texts last to ensure they are top-layered
                    text_info = font_info.render(btnHoverTexts['switchCompressLevel'],True,COLOR3,COLOR0)
                    text_info.set_alpha(200)
                    self.master.blit(text_info,(mousex-font_info.size(btnHoverTexts['switchCompressLevel'])[0]+1,mousey-font_info.size('中')[1]-1))
                showHoverTexts['switchCompressLevel'] = showInfoText
                self.master.blit(btnimg,rect_btn)
        else:                                                                                                       # when else
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

        # region switchLanguage
        rect_btn = (int(self.screenSize[0]-rawSize*1.2),int(rawSize*0.2),rawSize,rawSize)
        rect_btn1 = (rect_btn[0]+int(rawSize/25),rect_btn[1]+int(rawSize/25),rect_btn[2],rect_btn[3])
        if rect_btn[0] <= mousex < rect_btn[0]+rect_btn[2] and rect_btn[1] <= mousey < rect_btn[1]+rect_btn[3]:
            if mouseBtns[0]:
                pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0,80,COLOR3)
                self.master.blit(btnimg,rect_btn1)
                rtn = 'rtns.switchLanguage()'
            else:
                pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0,80,COLOR2)
                def showInfoText():
                    text_info = font_info.render(btnHoverTexts['switchLanguage'],True,COLOR3,COLOR0)
                    text_info.set_alpha(200)
                    self.master.blit(text_info,(mousex-font_info.size(btnHoverTexts['switchLanguage'])[0]+1,mousey-font_info.size('中')[1]-1))
                showHoverTexts['switchLanguage'] = showInfoText
                self.master.blit(btnimg,rect_btn1)
        else:
            pygame.draw.rect(self.master,COLOR1,rect_btn,width*2,border_radius=b_radius)
            btnimg = self.getButtons(rawSize,0,80,COLOR1)
            self.master.blit(btnimg,rect_btn1)
        self.btnActiveRects['switchLanguage'] = rect_btn
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
                if doubleClickState == 2:                                                           # single_click
                    pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0,48,COLOR3)
                    self.master.blit(btnimg,rect_btn)
                    rtn = 'rtns.rereadSettings()'
                elif doubleClickState == 3:                                                         # double_click
                    pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0,48,COLOR3)
                    self.master.blit(btnimg,rect_btn)
                    rtn = 'rtns.reopenSettings()'
                else:
                    pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0,48,COLOR2)
                    def showInfoText():
                        text_info0 = font_info.render(btnHoverTexts['rereadSettings'][0],True,COLOR3,COLOR0)
                        text_info0.set_alpha(200)
                        self.master.blit(text_info0,(mousex+1,mousey-2*font_info.size('中')[1]-1))
                        text_info1 = font_info.render(btnHoverTexts['rereadSettings'][1],True,COLOR3,COLOR0)
                        text_info1.set_alpha(200)
                        self.master.blit(text_info1,(mousex+1,mousey-font_info.size('中')[1]-1))
                    showHoverTexts['rereadSettings'] = showInfoText
                    self.master.blit(btnimg,rect_btn)
            else:
                pygame.draw.rect(self.master,COLOR1,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0,48,COLOR1)
                self.master.blit(btnimg,rect_btn)
            self.btnActiveRects['rereadSettings'] = rect_btn
            self.doubleClickDetectZone.add(((rect_btn[0],rect_btn[1]),(rect_btn[0]+rect_btn[2],rect_btn[1]+rect_btn[3])))
            # endregion

            # region switchDoBackgroundImgDisplay
            rect_btn = (int(self.screenSize[0]-rawSize*2.3),int(rawSize*0.2),rawSize,rawSize)
            rect_btn1 = (rect_btn[0]+int(rawSize/25),rect_btn[1]+int(rawSize/25),rect_btn[2],rect_btn[3])
            if self.darkMode:
                idx=0
            else:
                idx=1
            if rect_btn[0] <= mousex < rect_btn[0]+rect_btn[2] and rect_btn[1] <= mousey < rect_btn[1]+rect_btn[3]:
                if doubleClickState == 2:
                    pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,(idx*2+(1-int(self.doBackgroundImgDisplay[idx])))*16,96,COLOR3)
                    self.master.blit(btnimg,rect_btn1)
                    rtn = f'rtns.switchDoBackgroundImgDisplay({idx})'
                elif doubleClickState == 3:
                    pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,(idx*2+(1-int(self.doBackgroundImgDisplay[idx])))*16,96,COLOR3)
                    self.master.blit(btnimg,rect_btn1)
                    rtn = f'rtns.reopenBackgroundImg({idx})'
                else:
                    pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,(idx*2+(1-int(self.doBackgroundImgDisplay[idx])))*16,96,COLOR2)
                    def showInfoText():
                        text_info0 = font_info.render(btnHoverTexts['switchDoBackgroundImgDisplay'][0],True,COLOR3,COLOR0)
                        text_info0.set_alpha(200)
                        self.master.blit(text_info0,(mousex-font_info.size(btnHoverTexts['switchDoBackgroundImgDisplay'][0])[0]+1,mousey-2*font_info.size('中')[1]-1))
                        text_info1 = font_info.render(btnHoverTexts['switchDoBackgroundImgDisplay'][1],True,COLOR3,COLOR0)
                        text_info1.set_alpha(200)
                        self.master.blit(text_info1,(mousex-font_info.size(btnHoverTexts['switchDoBackgroundImgDisplay'][1])[0]+1,mousey-font_info.size('中')[1]-1))
                    showHoverTexts['switchDoBackgroundImgDisplay'] = showInfoText
                    self.master.blit(btnimg,rect_btn1)
            else:
                pygame.draw.rect(self.master,COLOR1,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,(idx*2+(1-int(self.doBackgroundImgDisplay[idx])))*16,96,COLOR1)
                self.master.blit(btnimg,rect_btn1)
            self.btnActiveRects['switchDoBackgroundImgDisplay'] = rect_btn
            self.doubleClickDetectZone.add(((rect_btn[0],rect_btn[1]),(rect_btn[0]+rect_btn[2],rect_btn[1]+rect_btn[3])))
            # endregion
            
            # region switchSidebarDisplayStyle
            rect_btn = (int(self.screenSize[0]-rawSize*3.4),int(rawSize*0.2),rawSize,rawSize)
            if rect_btn[0] <= mousex < rect_btn[0]+rect_btn[2] and rect_btn[1] <= mousey < rect_btn[1]+rect_btn[3]:
                if mouseBtns[0]:
                    pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,self.sidebarDisplayStyle*16,112,COLOR3)
                    self.master.blit(btnimg,rect_btn)
                    rtn = 'rtns.switchSidebarDisplayStyle()'
                else:
                    pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,self.sidebarDisplayStyle*16,112,COLOR2)
                    def showInfoText():
                        text_info = font_info.render(btnHoverTexts['switchSidebarDisplayStyle'],True,COLOR3,COLOR0)
                        text_info.set_alpha(200)
                        self.master.blit(text_info,(mousex+1,mousey-font_info.size('中')[1]-1))
                    showHoverTexts['switchSidebarDisplayStyle'] = showInfoText
                    self.master.blit(btnimg,rect_btn)
            else:
                pygame.draw.rect(self.master,COLOR1,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,self.sidebarDisplayStyle*16,112,COLOR1)
                self.master.blit(btnimg,rect_btn)
            self.btnActiveRects['switchSidebarDisplayStyle'] = rect_btn
            # endregion

            # region switchRetrenchMode
            rect_btn = (int(self.screenSize[0]-rawSize*4.5),int(rawSize*0.2),rawSize,rawSize)
            if rect_btn[0] <= mousex < rect_btn[0]+rect_btn[2] and rect_btn[1] <= mousey < rect_btn[1]+rect_btn[3]:
                if mouseBtns[0]:
                    pygame.draw.rect(self.master,COLOR5,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR3,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0 if self.retrenchMode else 16,128,COLOR3)
                    self.master.blit(btnimg,rect_btn)
                    rtn = 'rtns.switchRetrenchMode()'
                else:
                    pygame.draw.rect(self.master,COLOR4,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(self.master,COLOR2,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0 if self.retrenchMode else 16,128,COLOR2)
                    def showInfoText():
                        text_info = font_info.render(btnHoverTexts['switchRetrenchMode'],True,COLOR3,COLOR0)
                        text_info.set_alpha(200)
                        self.master.blit(text_info,(mousex+1,mousey-font_info.size('中')[1]-1))
                    showHoverTexts['switchRetrenchMode'] = showInfoText
                    self.master.blit(btnimg,rect_btn)
            else:
                pygame.draw.rect(self.master,COLOR1,rect_btn,width*2,border_radius=b_radius)
                btnimg = self.getButtons(rawSize,0 if self.retrenchMode else 16,128,COLOR1)
                self.master.blit(btnimg,rect_btn)
            self.btnActiveRects['switchRetrenchMode'] = rect_btn
        # endregion


        for fun in showHoverTexts.values():
            fun()

        return rtn

    def getButtons(self,size:int,x:int,y:int,color:Tuple[int],color1:Tuple[int]=(-1,-1,-1),w:int=15,h:int=15):
        rawimg = pygame.image.load('GUI/buttons.png')
        if color1 == (-1,-1,-1):
            color1 = ((self.getColor(self.darkMode,x=0)[0]+color[0])//2,
                      (self.getColor(self.darkMode,x=0)[1]+color[1])//2,
                      (self.getColor(self.darkMode,x=0)[2]+color[2])//2,)

        surface = pygame.Surface((w,h))     # The black part
        surface.fill((255,255,255))
        surface.set_colorkey((255,255,255))
        surface.blit(rawimg,(0,0),(x,y,w,h))
        pixarr = pygame.PixelArray(surface)
        pixarr.replace((0,0,0),color)
        pixarr.replace((127,127,127),color1)
        pixarr.close()
        try:
            surface = pygame.transform.scale(surface,(int(size*w/16),int(size*h/16)))
        except:
            pass
        return surface

    # @deco
    def writeTimetableSchedules(self,rawTimetable:List[List],weekday:int,nowSchedIdx:Union[int,None]=None,portValues:List[int]=[0,0,0,0,0,0,0,0,0],mousex:int=0,mousey:int=0,mouseBtns:List[bool]=[False,False,False,False,False]):
        # portValue: [<weekday>,<year>,<month>,<date>,<hour>,<minute>,<second>,<countDays>,<countWeeks>]
        w,y,n,d,h,m,s,cd,cw = portValues

        timetable = rawTimetable.copy()

        minus = 0
        popIdx = []
        for schedIdx in range(len(timetable[weekday])): # gets the numbers of the should_ignore scheds as <minus>
            sched = timetable[weekday][schedIdx]
            if eval(sched[2]) == '':
                popIdx.insert(0,schedIdx)
                if type(nowSchedIdx) == int:
                    minus += 1

        if self.compressLevel == 0:
            COLOR0 = self.getColor(self.darkMode,x=0)
            COLOR7 = self.getColor(self.darkMode,x=155)
            COLOR8 = self.getColor(self.darkMode,x=40)
            if self.doTimetableSearch:
                COLOR1 = self.getColor(self.darkMode,x=83)
                COLOR2 = self.getColor(self.darkMode,x=126)
                COLOR3 = self.getColor(self.darkMode,x=230)
                COLOR4 = self.getColor(self.darkMode,x=253)
                COLOR5 = self.getColor(self.darkMode,x=131)
                COLOR6 = self.getColor(self.darkMode,x=190)
            else:
                COLOR1 = self.getColor(self.darkMode,x=106)
                COLOR2 = self.getColor(self.darkMode,x=137)
                COLOR3 = self.getColor(self.darkMode,x=57)
                COLOR4 = self.getColor(self.darkMode,x=137)
                COLOR5 = self.getColor(self.darkMode,x=106)
                COLOR6 = self.getColor(self.darkMode,x=137)
                nowSchedIdx = -1

            if self.sidebarDisplayStyle == 0:   # DayList
                timetableTexts = []
                totalAreaLeft = (int(self.screenSize[1]*0.625+6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625+6)) + int(self.sidebarLeftsideOffset*self.screenSize[0])
                totalAreaWidth = self.screenSize[0]-5-totalAreaLeft
                totalAreaUp = 5+int(min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)
                totalAreaHeight = int(self.screenSize[1]-2*min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)-10
                totalAreaWidth = totalAreaWidth if totalAreaWidth>=1 else 1
                totalAreaHeight = totalAreaHeight if totalAreaHeight>=1 else 1
                textSurface = pygame.Surface((totalAreaWidth,totalAreaHeight))
                textSurface.fill(COLOR0)
                pygame.draw.line(textSurface,COLOR8,(0,0),(totalAreaWidth,0),width=2)
                pygame.draw.line(textSurface,COLOR8,(0,0),(0,totalAreaHeight),width=2)
                pygame.draw.line(textSurface,COLOR8,(0,totalAreaHeight-2),(totalAreaWidth,totalAreaHeight-2),width=2)
                if self.doBackgroundImgDisplay[1-int(self.darkMode)]:
                    surface,rect = self.loadBackgroundImg()
                    rect.x -= totalAreaLeft
                    rect.y -= totalAreaUp
                    textSurface.blit(surface,rect)
                self.scheduleDisplayRect = (totalAreaLeft,totalAreaUp,totalAreaWidth,totalAreaHeight)
                for schedule in timetable[weekday]:
                    scheduleText = (f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02} ~ {int(schedule[1]//100):02}:{int(schedule[1]%100):02}  ',eval(schedule[2]))
                    timetableTexts.append(scheduleText)
                
                fontSize_timetable = int(self.screenSize[0]/450*(16+self.sidebarZoomLevel[2])) if self.screenSize[0]/450 <= 2 else 2*(16+self.sidebarZoomLevel[2])
                font_timetable = (self.getPygameFont(self.textFonts[3],fontSize_timetable),self.getPygameFont(self.textFonts[4],fontSize_timetable))

                try:
                    textNeedArea = (max(list(map(lambda a:a[0],map(font_timetable[0].size,map(lambda a:a[0]+'  '+a[1],timetableTexts))))),(font_timetable[0].size('文')[1]+int(self.screenSize[1]/180))*(len(timetableTexts)-minus)-5)
                except ValueError:
                    textNeedArea = (1,1)
                
                if -self.timetableScroll[1]*self.screenSize[1]/30 >= textNeedArea[1]:
                    self.timetableScroll[1] = -int(textNeedArea[1]*30/self.screenSize[1])
                if -self.timetableScroll[0]*self.screenSize[0]/30 >= textNeedArea[0]:
                    self.timetableScroll[0] = -int(textNeedArea[0]*30/self.screenSize[0])
                if self.timetableScroll[1] > 0:
                    self.timetableScroll[1] = 0
                if self.timetableScroll[0] > 0:
                    self.timetableScroll[0] = 0

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
                        textSurface.blit(surface_text[0],(10+int(self.timetableScroll[0]*self.screenSize[0]/30),5+int(self.screenSize[1]/45)+idx*(lineDigitArea[1]+int(self.screenSize[1]/180))+int(self.timetableScroll[1]*self.screenSize[1]/30)))
                        textSurface.blit(surface_text[1],(10+lineDigitArea[0]+int(self.timetableScroll[0]*self.screenSize[0]/30),2+int(self.screenSize[1]/45)+idx*(lineDigitArea[1]+int(self.screenSize[1]/180))+int(self.timetableScroll[1]*self.screenSize[1]/30)))
                        idx += 1
                    except:
                        idx += 1
                
            elif self.sidebarDisplayStyle == 1: # WeekList
                timetableWeekTexts = [[(' ',' ')],[(' ',' ')],[(' ',' ')],[(' ',' ')],[(' ',' ')],[(' ',' ')],[(' ',' ')]]
                totalAreaLeft = (int(self.screenSize[1]*0.625+6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625+6)) + int(self.sidebarLeftsideOffset*self.screenSize[0])
                totalAreaWidth = self.screenSize[0]-5-totalAreaLeft
                totalAreaUp = 5+int(min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)
                totalAreaHeight = int(self.screenSize[1]-2*min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)-10
                totalAreaWidth = totalAreaWidth if totalAreaWidth>=1 else 1
                totalAreaHeight = totalAreaHeight if totalAreaHeight>=1 else 1
                textSurface = pygame.Surface((totalAreaWidth,totalAreaHeight))
                textSurface.fill(COLOR0)
                pygame.draw.line(textSurface,COLOR8,(0,0),(totalAreaWidth,0),width=2)
                pygame.draw.line(textSurface,COLOR8,(0,0),(0,totalAreaHeight),width=2)
                pygame.draw.line(textSurface,COLOR8,(0,totalAreaHeight-2),(totalAreaWidth,totalAreaHeight-2),width=2)
                if self.doBackgroundImgDisplay[1-int(self.darkMode)]:
                    surface,rect = self.loadBackgroundImg()
                    rect.x -= totalAreaLeft
                    rect.y -= totalAreaUp
                    textSurface.blit(surface,rect)
                self.scheduleDisplayRect = (totalAreaLeft,totalAreaUp,totalAreaWidth,totalAreaHeight)
                for nowWeekday in [0,1,2,3,4,5,6]:
                    for schedule in timetable[nowWeekday]:
                        scheduleText = (f'{int(schedule[0]//100):02}:{int(schedule[0]%100):02} ~ {int(schedule[1]//100):02}:{int(schedule[1]%100):02}  ',eval(schedule[2]))
                        timetableWeekTexts[nowWeekday].append(scheduleText)
                
                fontSize_timetable = int(self.screenSize[0]/500*(16+self.sidebarZoomLevel[2])) if self.screenSize[0]/500 <= 2 else 2*(16+self.sidebarZoomLevel[2])
                font_timetable = (self.getPygameFont(self.textFonts[3],fontSize_timetable),self.getPygameFont(self.textFonts[4],fontSize_timetable))

                textNeedArea = (1,(font_timetable[0].size('文')[1]+int(self.screenSize[1]/180))*(max([len(timetableTexts) for timetableTexts in timetableWeekTexts])-minus)-5)

                wholeWeekTextNeedAreaX = 1
                for nowWeekday in [0,1,2,3,4,5,6]:
                    timetableTexts = timetableWeekTexts[nowWeekday]
                    timetableTextNeedAreas = []
                    timetableTextNeedAreas.append(font_timetable[1].size(' 周一     ')[0])
                    for schedText in timetableTexts:
                        timetableTextNeedAreas.append(font_timetable[1].size(schedText[0]+'  '+schedText[1])[0])
                    wholeWeekTextNeedAreaX += max(timetableTextNeedAreas)
                wholeWeekTextNeedArea = (wholeWeekTextNeedAreaX,textNeedArea[1])

                weekdayNamesSurface = pygame.Surface((totalAreaWidth,font_timetable[0].size('文')[1]+int(self.screenSize[1]/180)))
                weekdayNamesSurface.fill(COLOR0)
                pygame.draw.line(weekdayNamesSurface,COLOR8,(0,0),(totalAreaWidth,0),width=2)
                pygame.draw.line(weekdayNamesSurface,COLOR8,(0,0),(0,font_timetable[0].size('文')[1]+int(self.screenSize[1]/180)),width=2)
                if self.doBackgroundImgDisplay[1-int(self.darkMode)]:
                    surface,rect = self.loadBackgroundImg()
                    rect.x -= totalAreaLeft
                    rect.y -= totalAreaUp
                    weekdayNamesSurface.blit(surface,rect)
                if self.language == 'Chinese':
                    weekdayNames = ['周一','周二','周三','周四','周五','周六','周日']
                else:
                    weekdayNames = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
                    
                for nowWeekday in [0,1,2,3,4,5,6]:
                    timetableTexts = timetableWeekTexts[nowWeekday]
                    try:
                        timetableTextNeedAreas = []
                        timetableTextNeedAreas.append(font_timetable[1].size(' 周一     ')[0])
                        for schedText in timetableTexts:
                            timetableTextNeedAreas.append(font_timetable[1].size(schedText[0]+'  '+schedText[1])[0])
                        dayTextNeedArea = (max(timetableTextNeedAreas),textNeedArea[1])
                    except ValueError:
                        dayTextNeedArea = (1,1)    

                    if -self.timetableScroll[1]*self.screenSize[1]/30 >= wholeWeekTextNeedArea[1]:
                        self.timetableScroll[1] = -int(wholeWeekTextNeedArea[1]*30/self.screenSize[1])
                    if -self.timetableScroll[0]*self.screenSize[0]/30 >= wholeWeekTextNeedArea[0]:
                        self.timetableScroll[0] = -int(wholeWeekTextNeedArea[0]*30/self.screenSize[0])
                    if self.timetableScroll[1] > 0:
                        self.timetableScroll[1] = 0
                    if self.timetableScroll[0] > 0:
                        self.timetableScroll[0] = 0

                    idx = 0
                    for text in timetableTexts:
                        if text[1] == '':
                            continue
                        try:
                            if nowWeekday == weekday:
                                if idx < nowSchedIdx:
                                    surface_text = (font_timetable[0].render(text[0],True,(COLOR1)),font_timetable[1].render(text[1],True,(COLOR2)))
                                elif idx == nowSchedIdx:
                                    surface_text = (font_timetable[0].render(text[0],True,(COLOR3)),font_timetable[1].render(text[1],True,(COLOR4)))
                                else:
                                    surface_text = (font_timetable[0].render(text[0],True,(COLOR5)),font_timetable[1].render(text[1],True,(COLOR6)))
                            else:
                                surface_text = (font_timetable[0].render(text[0],True,(COLOR1)),font_timetable[1].render(text[1],True,(COLOR2)))
                            lineDigitArea = font_timetable[0].size(text[0])
                            textSurface.blit(surface_text[0],(10+int(self.timetableScroll[0]*self.screenSize[0]/30)+textNeedArea[0],5+int(self.screenSize[1]/45)+idx*(lineDigitArea[1]+int(self.screenSize[1]/180))+int(self.timetableScroll[1]*self.screenSize[1]/30)))
                            textSurface.blit(surface_text[1],(10+lineDigitArea[0]+int(self.timetableScroll[0]*self.screenSize[0]/30)+textNeedArea[0],2+int(self.screenSize[1]/45)+idx*(lineDigitArea[1]+int(self.screenSize[1]/180))+int(self.timetableScroll[1]*self.screenSize[1]/30)))
                            idx += 1
                        except:
                            idx += 1
                    textNeedArea = (textNeedArea[0] + int(dayTextNeedArea[0]*1.15), dayTextNeedArea[1])
                    weekdayNameText = font_timetable[1].render(weekdayNames[nowWeekday],True,(COLOR4))
                    weekdayNamesSurface.blit(weekdayNameText,((10+int(self.timetableScroll[0]*self.screenSize[0]/30)+textNeedArea[0]-int(dayTextNeedArea[0]*1.15)),int(self.screenSize[1]/360)))
                    pygame.draw.line(weekdayNamesSurface,COLOR8,(0,font_timetable[0].size('文')[1]+int(self.screenSize[1]/180)-2),(totalAreaWidth,font_timetable[0].size('文')[1]+int(self.screenSize[1]/180)-2),width=2)
                    if nowWeekday != 6:
                        linex = (int(self.timetableScroll[0]*self.screenSize[0]/30)+textNeedArea[0])
                        pygame.draw.line(textSurface,COLOR8,(linex,0),(linex,totalAreaHeight),width=2)
                        pygame.draw.line(weekdayNamesSurface,COLOR8,(linex,0),(linex,font_timetable[0].size('文')[1]+int(self.screenSize[1]/180)),width=2)
                textSurface.blit(weekdayNamesSurface,(0,0))

            elif self.sidebarDisplayStyle == 2: # DayColumnar
                timetablePeriods = []
                totalAreaLeft = (int(self.screenSize[1]*0.625+6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625+6)) + int(self.sidebarLeftsideOffset*self.screenSize[0])
                totalAreaWidth = self.screenSize[0]-5-totalAreaLeft
                totalAreaUp = 5+int(min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)
                totalAreaHeight = int(self.screenSize[1]-2*min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)-10
                totalAreaWidth = totalAreaWidth if totalAreaWidth>=1 else 1
                totalAreaHeight = totalAreaHeight if totalAreaHeight>=1 else 1
                textSurface = pygame.Surface((totalAreaWidth,totalAreaHeight))
                textSurface.fill(COLOR0)
                pygame.draw.line(textSurface,COLOR8,(0,0),(totalAreaWidth,0),width=2)
                pygame.draw.line(textSurface,COLOR8,(0,0),(0,totalAreaHeight),width=2)
                pygame.draw.line(textSurface,COLOR8,(0,totalAreaHeight-2),(totalAreaWidth,totalAreaHeight-2),width=2)
                if self.doBackgroundImgDisplay[1-int(self.darkMode)]:
                    surface,rect = self.loadBackgroundImg()
                    rect.x -= totalAreaLeft
                    rect.y -= totalAreaUp
                    textSurface.blit(surface,rect)
                self.scheduleDisplayRect = (totalAreaLeft,totalAreaUp,totalAreaWidth,totalAreaHeight)
                lastSchedEndTime = 0
                for scheduleIdx in range(len(timetable[weekday])):
                    schedule = timetable[weekday][scheduleIdx]
                    if schedule[0] > lastSchedEndTime:
                        if self.getPeriodLenth(lastSchedEndTime,schedule[0]) > self.emptyColumnarMergeThreshold:
                            timetablePeriods.append((lastSchedEndTime,schedule[0],'. . . ','mergedGap',-1))
                        else:
                            timetablePeriods.append((lastSchedEndTime,schedule[0],'','gap',-1))
                    timetablePeriods.append((schedule[0],schedule[1],eval(schedule[2]),'sched',scheduleIdx))
                    lastSchedEndTime = schedule[1]
                if lastSchedEndTime < 2400:
                    if self.getPeriodLenth(lastSchedEndTime,2400) > self.emptyColumnarMergeThreshold:
                        timetablePeriods.append((lastSchedEndTime,2400,'. . . ','mergedGap',-1))
                    else:
                        timetablePeriods.append((lastSchedEndTime,2400,'','gap',-1))
                columnarNeedAreaHeight = 0
                for period in timetablePeriods:
                    if period[3] == 'mergedGap':
                        columnarNeedAreaHeight += self.emptyColumnarMergeThreshold
                    else:
                        columnarNeedAreaHeight += self.getPeriodLenth(period[0],period[1])
                columnarNeedAreaHeight = self.ceiling(columnarNeedAreaHeight*((5/4)**self.sidebarZoomLevel[1]))
                columnarNeedArea = (totalAreaWidth,columnarNeedAreaHeight)
                textNeedArea = columnarNeedArea
                
                if -self.timetableScroll[1]*self.screenSize[1]/30 >= columnarNeedAreaHeight:
                    self.timetableScroll[1] = -int(columnarNeedAreaHeight*30/self.screenSize[1])
                if self.timetableScroll[1] > 0:
                    self.timetableScroll[1] = 0

                fontSize_timetable = int(totalAreaWidth/400*20) if int(totalAreaWidth/400*20) <= 30 else 30
                font_timetable = (self.getPygameFont(self.textFonts[3],fontSize_timetable),self.getPygameFont(self.textFonts[4],fontSize_timetable))

                accumulatedHeight = 0
                for periodIdx in range(len(timetablePeriods)):
                    period:Tuple[int,int,str,Literal['gap','sched','mergedGap'],int] = timetablePeriods[periodIdx]
                    if period[3] == 'mergedGap':
                        periodRect = (int(columnarNeedArea[0]*0.25),
                                      accumulatedHeight+int(self.timetableScroll[1]*self.screenSize[1]/30),
                                      self.ceiling(columnarNeedArea[0]*0.75),
                                      self.ceiling(self.emptyColumnarMergeThreshold*((5/4)**self.sidebarZoomLevel[1])))
                        accumulatedHeight += self.ceiling(self.emptyColumnarMergeThreshold*((5/4)**self.sidebarZoomLevel[1]))
                    else:
                        periodRect = (int(columnarNeedArea[0]*0.25),
                                      accumulatedHeight+int(self.timetableScroll[1]*self.screenSize[1]/30),
                                      self.ceiling(columnarNeedArea[0]*0.75),
                                      self.ceiling(self.getPeriodLenth(period[0],period[1])*((5/4)**self.sidebarZoomLevel[1])))
                        accumulatedHeight += self.ceiling(self.getPeriodLenth(period[0],period[1])*((5/4)**self.sidebarZoomLevel[1]))
                    if period[3] == 'sched':
                        if period[4] < nowSchedIdx:
                            periodSurface = pygame.Surface(periodRect[2:])
                            periodSurface.set_alpha(127)
                            pygame.draw.rect(periodSurface,COLOR1,(0,0,periodRect[2],periodRect[3]))
                            pygame.draw.rect(periodSurface,COLOR2,(0,0,periodRect[2],periodRect[3]),width=2)
                            textSurface.blit(periodSurface,periodRect)
                            schedNameSurface = font_timetable[1].render(period[2],True,COLOR2)
                            schedNamePos = (periodRect[0]+(periodRect[2]-font_timetable[1].size(period[2])[0])//2,periodRect[1]+(periodRect[3]-font_timetable[1].size(period[2])[1])//2)
                            textSurface.blit(schedNameSurface,schedNamePos)
                            schedTimeText = f'{int(period[1]//100):02}:{int(period[1]%100):02}'
                            schedTimeSurface = font_timetable[0].render(schedTimeText,True,COLOR1)
                            schedTimePos = (periodRect[0]-font_timetable[0].size(schedTimeText)[0],periodRect[1]+periodRect[3]-font_timetable[0].size(schedTimeText)[1]//2)
                            textSurface.blit(schedTimeSurface,schedTimePos)
                        elif period[4] == nowSchedIdx:
                            periodSurface = pygame.Surface(periodRect[2:])
                            periodSurface.set_alpha(127)
                            pygame.draw.rect(periodSurface,COLOR3,(0,0,periodRect[2],periodRect[3]))
                            pygame.draw.rect(periodSurface,COLOR4,(0,1,periodRect[2],periodRect[3]-2),width=2)
                            textSurface.blit(periodSurface,periodRect)
                            schedNameSurface = font_timetable[1].render(period[2],True,COLOR4)
                            schedNamePos = (periodRect[0]+(periodRect[2]-font_timetable[1].size(period[2])[0])//2,periodRect[1]+(periodRect[3]-font_timetable[1].size(period[2])[1])//2)
                            textSurface.blit(schedNameSurface,schedNamePos)
                            schedTimeText = f'{int(period[1]//100):02}:{int(period[1]%100):02}'
                            schedTimeSurface = font_timetable[0].render(schedTimeText,True,COLOR1)
                            schedTimePos = (periodRect[0]-font_timetable[0].size(schedTimeText)[0],periodRect[1]+periodRect[3]-font_timetable[0].size(schedTimeText)[1]//2)
                            textSurface.blit(schedTimeSurface,schedTimePos)
                        else:
                            periodSurface = pygame.Surface(periodRect[2:])
                            periodSurface.set_alpha(127)
                            pygame.draw.rect(periodSurface,COLOR1,(0,0,periodRect[2],periodRect[3]))
                            pygame.draw.rect(periodSurface,COLOR2,(0,0,periodRect[2],periodRect[3]),width=2)
                            textSurface.blit(periodSurface,periodRect)
                            schedNameSurface = font_timetable[1].render(period[2],True,COLOR6)
                            schedNamePos = (periodRect[0]+(periodRect[2]-font_timetable[1].size(period[2])[0])//2,periodRect[1]+(periodRect[3]-font_timetable[1].size(period[2])[1])//2)
                            textSurface.blit(schedNameSurface,schedNamePos)
                            schedTimeText = f'{int(period[1]//100):02}:{int(period[1]%100):02}'
                            schedTimeSurface = font_timetable[0].render(schedTimeText,True,COLOR1)
                            schedTimePos = (periodRect[0]-font_timetable[0].size(schedTimeText)[0],periodRect[1]+periodRect[3]-font_timetable[0].size(schedTimeText)[1]//2)
                            textSurface.blit(schedTimeSurface,schedTimePos)
                    elif period[3] == 'gap':
                            periodSurface = pygame.Surface(periodRect[2:])
                            periodSurface.set_alpha(127)
                            pygame.draw.rect(periodSurface,COLOR0,(0,0,periodRect[2],periodRect[3]))
                            pygame.draw.rect(periodSurface,COLOR2,(0,-2,periodRect[2],periodRect[3]+4),width=2)
                            textSurface.blit(periodSurface,periodRect)
                            schedTimeText = f'{int(period[1]//100):02}:{int(period[1]%100):02}'
                            schedTimeSurface = font_timetable[0].render(schedTimeText,True,COLOR1)
                            schedTimePos = (periodRect[0]-font_timetable[0].size(schedTimeText)[0],periodRect[1]+periodRect[3]-font_timetable[0].size(schedTimeText)[1]//2)
                            textSurface.blit(schedTimeSurface,schedTimePos)
                    else:   # period[3] == 'mergedGap'
                            periodSurface = pygame.Surface(periodRect[2:])
                            periodSurface.set_alpha(127)
                            pygame.draw.rect(periodSurface,COLOR0,(0,0,periodRect[2],periodRect[3]))
                            pygame.draw.rect(periodSurface,COLOR2,(0,-2,periodRect[2],periodRect[3]+4),width=2)
                            textSurface.blit(periodSurface,periodRect)
                            font_timetable[0].set_bold(True)
                            schedNameSurface = font_timetable[0].render(period[2],True,COLOR1)
                            schedNamePos = (periodRect[0]-font_timetable[0].size(period[2])[0],periodRect[1]+(periodRect[3]-font_timetable[0].size(period[2])[1])//2)
                            textSurface.blit(schedNameSurface,schedNamePos)
                            font_timetable[0].set_bold(False)
                            schedTimeText = f'{int(period[1]//100):02}:{int(period[1]%100):02}'
                            schedTimeSurface = font_timetable[0].render(schedTimeText,True,COLOR1)
                            schedTimePos = (periodRect[0]-font_timetable[0].size(schedTimeText)[0],periodRect[1]+periodRect[3]-font_timetable[0].size(schedTimeText)[1]//2)
                            textSurface.blit(schedTimeSurface,schedTimePos)

            else:   # WeekColumnar
                weekTimetablePeriods = [[],[],[],[],[],[],[]]
                totalAreaLeft = (int(self.screenSize[1]*0.625+6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625+6)) + int(self.sidebarLeftsideOffset*self.screenSize[0])
                totalAreaWidth = self.screenSize[0]-5-totalAreaLeft
                totalAreaUp = 5+int(min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)
                totalAreaHeight = int(self.screenSize[1]-2*min(int(self.screenSize[0]/12),int(self.screenSize[1]/12))*1.2)-10
                totalAreaWidth = totalAreaWidth if totalAreaWidth>=1 else 1
                totalAreaHeight = totalAreaHeight if totalAreaHeight>=1 else 1
                textSurface = pygame.Surface((totalAreaWidth,totalAreaHeight))
                textSurface.fill(COLOR0)
                pygame.draw.line(textSurface,COLOR8,(0,0),(totalAreaWidth,0),width=2)
                pygame.draw.line(textSurface,COLOR8,(0,0),(0,totalAreaHeight),width=2)
                pygame.draw.line(textSurface,COLOR8,(0,totalAreaHeight-2),(totalAreaWidth,totalAreaHeight-2),width=2)
                if self.doBackgroundImgDisplay[1-int(self.darkMode)]:
                    surface,rect = self.loadBackgroundImg()
                    rect.x -= totalAreaLeft
                    rect.y -= totalAreaUp
                    textSurface.blit(surface,rect)
                self.scheduleDisplayRect = (totalAreaLeft,totalAreaUp,totalAreaWidth,totalAreaHeight)
                for nowWeekday in [0,1,2,3,4,5,6]:
                    lastSchedEndTime = 0
                    timetablePeriods = weekTimetablePeriods[nowWeekday]
                    for scheduleIdx in range(len(timetable[nowWeekday])):
                        schedule = timetable[nowWeekday][scheduleIdx]
                        if schedule[0] > lastSchedEndTime:
                            timetablePeriods.append((lastSchedEndTime,schedule[0],'','gap',-1))
                        timetablePeriods.append((schedule[0],schedule[1],eval(schedule[2]),'sched',scheduleIdx))
                        lastSchedEndTime = schedule[1]
                    if lastSchedEndTime < 2400:
                        timetablePeriods.append((lastSchedEndTime,2400,'','gap',-1))
                    columnarNeedAreaHeight = 0
                    for period in timetablePeriods:
                        columnarNeedAreaHeight += self.getPeriodLenth(period[0],period[1])
                    columnarNeedAreaHeight = self.ceiling(columnarNeedAreaHeight*((5/4)**self.sidebarZoomLevel[1]))
                    weekColumnarNeedArea = (self.ceiling(totalAreaWidth*4.45*((5/4)**self.sidebarZoomLevel[0])),columnarNeedAreaHeight)
                    textNeedArea = weekColumnarNeedArea

                fontSize_timetable = int(totalAreaWidth/400*20*((5/4)**self.sidebarZoomLevel[0])) if int(totalAreaWidth/400*20*((5/4)**self.sidebarZoomLevel[0])) <= 30 else 30
                font_timetable = (self.getPygameFont(self.textFonts[3],fontSize_timetable),self.getPygameFont(self.textFonts[4],fontSize_timetable))

                weekdayNamesSurface = pygame.Surface((totalAreaWidth,font_timetable[1].size('文')[1]+int(self.screenSize[1]/180)))
                weekdayNamesSurface.fill(COLOR0)
                pygame.draw.line(weekdayNamesSurface,COLOR8,(0,0),(totalAreaWidth,0),width=2)
                pygame.draw.line(weekdayNamesSurface,COLOR8,(0,0),(0,font_timetable[1].size('文')[1]+int(self.screenSize[1]/180)),width=2)
                if self.doBackgroundImgDisplay[1-int(self.darkMode)]:
                    surface,rect = self.loadBackgroundImg()
                    rect.x -= totalAreaLeft
                    rect.y -= totalAreaUp
                    weekdayNamesSurface.blit(surface,rect)
                periodTimeSurface = pygame.Surface((totalAreaWidth*0.25*((5/4)**self.sidebarZoomLevel[0]),totalAreaHeight))
                periodTimeSurface.fill(COLOR0)
                if self.doBackgroundImgDisplay[1-int(self.darkMode)]:
                    surface,rect = self.loadBackgroundImg()
                    rect.x -= totalAreaLeft
                    rect.y -= totalAreaUp
                    periodTimeSurface.blit(surface,rect)
                if self.language == 'Chinese':
                    weekdayNames = ['周一','周二','周三','周四','周五','周六','周日']
                else:
                    weekdayNames = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
                    
                if -self.timetableScroll[1]*self.screenSize[1]/30 >= weekColumnarNeedArea[1]:
                    self.timetableScroll[1] = -int(weekColumnarNeedArea[1]*30/self.screenSize[1])
                if -self.timetableScroll[0]*self.screenSize[0]/30 >= weekColumnarNeedArea[0]:
                    self.timetableScroll[0] = -int(weekColumnarNeedArea[0]*30/self.screenSize[0])
                if self.timetableScroll[1] > 0:
                    self.timetableScroll[1] = 0
                if self.timetableScroll[0] > 0:
                    self.timetableScroll[0] = 0
                
                accumulatedWidth = self.ceiling(totalAreaWidth*0.25*((5/4)**self.sidebarZoomLevel[0]))
                for nowWeekday in [0,1,2,3,4,5,6]:
                    accumulatedHeight = font_timetable[1].size('文')[1]
                    timetablePeriods = weekTimetablePeriods[nowWeekday]
                    for periodIdx in range(len(timetablePeriods)):
                        period:Tuple[int,int,str,Literal['gap','sched'],int] = timetablePeriods[periodIdx]
                        periodRect = (accumulatedWidth+int(self.timetableScroll[0]*self.screenSize[0]/30),
                                      accumulatedHeight+int(self.timetableScroll[1]*self.screenSize[1]/30),
                                      self.ceiling(totalAreaWidth*0.6*((5/4)**self.sidebarZoomLevel[0])),
                                      self.ceiling(self.getPeriodLenth(period[0],period[1])*((5/4)**self.sidebarZoomLevel[1])))
                        accumulatedHeight += self.ceiling(self.getPeriodLenth(period[0],period[1])*((5/4)**self.sidebarZoomLevel[1]))
                        if period[3] == 'sched':
                            if nowWeekday == weekday:
                                if period[4] < nowSchedIdx:
                                    periodSurface = pygame.Surface(periodRect[2:])
                                    periodSurface.set_alpha(127)
                                    pygame.draw.rect(periodSurface,COLOR1,(0,0,periodRect[2],periodRect[3]))
                                    pygame.draw.rect(periodSurface,COLOR2,(0,0,periodRect[2],periodRect[3]),width=2)
                                    textSurface.blit(periodSurface,periodRect)
                                    schedNameSurface = font_timetable[1].render(period[2],True,COLOR2)
                                    schedNamePos = (periodRect[0]+(periodRect[2]-font_timetable[1].size(period[2])[0])//2,periodRect[1]+(periodRect[3]-font_timetable[1].size(period[2])[1])//2)
                                    textSurface.blit(schedNameSurface,schedNamePos)
                                    schedTimeText = f'{int(period[1]//100):02}:{int(period[1]%100):02}'
                                    schedTimeSurface = font_timetable[0].render(schedTimeText,True,COLOR1)
                                    schedTimePos = (self.ceiling(totalAreaWidth*0.25*((5/4)**self.sidebarZoomLevel[0]))-font_timetable[0].size(schedTimeText)[0],periodRect[1]+periodRect[3]-font_timetable[0].size(schedTimeText)[1]//2)
                                    periodTimeSurface.blit(schedTimeSurface,schedTimePos)
                                elif period[4] == nowSchedIdx:
                                    periodSurface = pygame.Surface(periodRect[2:])
                                    periodSurface.set_alpha(127)
                                    pygame.draw.rect(periodSurface,COLOR3,(0,0,periodRect[2],periodRect[3]))
                                    pygame.draw.rect(periodSurface,COLOR4,(0,1,periodRect[2],periodRect[3]-2),width=2)
                                    textSurface.blit(periodSurface,periodRect)
                                    schedNameSurface = font_timetable[1].render(period[2],True,COLOR4)
                                    schedNamePos = (periodRect[0]+(periodRect[2]-font_timetable[1].size(period[2])[0])//2,periodRect[1]+(periodRect[3]-font_timetable[1].size(period[2])[1])//2)
                                    textSurface.blit(schedNameSurface,schedNamePos)
                                    schedTimeText = f'{int(period[1]//100):02}:{int(period[1]%100):02}'
                                    schedTimeSurface = font_timetable[0].render(schedTimeText,True,COLOR1)
                                    schedTimePos = (self.ceiling(totalAreaWidth*0.25*((5/4)**self.sidebarZoomLevel[0]))-font_timetable[0].size(schedTimeText)[0],periodRect[1]+periodRect[3]-font_timetable[0].size(schedTimeText)[1]//2)
                                    periodTimeSurface.blit(schedTimeSurface,schedTimePos)
                                else:
                                    periodSurface = pygame.Surface(periodRect[2:])
                                    periodSurface.set_alpha(127)
                                    pygame.draw.rect(periodSurface,COLOR1,(0,0,periodRect[2],periodRect[3]))
                                    pygame.draw.rect(periodSurface,COLOR2,(0,0,periodRect[2],periodRect[3]),width=2)
                                    textSurface.blit(periodSurface,periodRect)
                                    schedNameSurface = font_timetable[1].render(period[2],True,COLOR6)
                                    schedNamePos = (periodRect[0]+(periodRect[2]-font_timetable[1].size(period[2])[0])//2,periodRect[1]+(periodRect[3]-font_timetable[1].size(period[2])[1])//2)
                                    textSurface.blit(schedNameSurface,schedNamePos)
                                    schedTimeText = f'{int(period[1]//100):02}:{int(period[1]%100):02}'
                                    schedTimeSurface = font_timetable[0].render(schedTimeText,True,COLOR1)
                                    schedTimePos = (self.ceiling(totalAreaWidth*0.25*((5/4)**self.sidebarZoomLevel[0]))-font_timetable[0].size(schedTimeText)[0],periodRect[1]+periodRect[3]-font_timetable[0].size(schedTimeText)[1]//2)
                                    periodTimeSurface.blit(schedTimeSurface,schedTimePos)
                            else:
                                    periodSurface = pygame.Surface(periodRect[2:])
                                    periodSurface.set_alpha(127)
                                    pygame.draw.rect(periodSurface,COLOR1,(0,0,periodRect[2],periodRect[3]))
                                    pygame.draw.rect(periodSurface,COLOR2,(0,0,periodRect[2],periodRect[3]),width=2)
                                    textSurface.blit(periodSurface,periodRect)
                                    schedNameSurface = font_timetable[1].render(period[2],True,COLOR2)
                                    schedNamePos = (periodRect[0]+(periodRect[2]-font_timetable[1].size(period[2])[0])//2,periodRect[1]+(periodRect[3]-font_timetable[1].size(period[2])[1])//2)
                                    textSurface.blit(schedNameSurface,schedNamePos)
                        else:   # period[3] == 'gap':
                                periodSurface = pygame.Surface(periodRect[2:])
                                periodSurface.set_alpha(127)
                                pygame.draw.rect(periodSurface,COLOR0,(0,0,periodRect[2],periodRect[3]))
                                pygame.draw.rect(periodSurface,COLOR2,(0,-2,periodRect[2],periodRect[3]+4),width=2)
                                textSurface.blit(periodSurface,periodRect)
                                if nowWeekday == weekday:
                                    schedTimeText = f'{int(period[1]//100):02}:{int(period[1]%100):02}'
                                    schedTimeSurface = font_timetable[0].render(schedTimeText,True,COLOR1)
                                    schedTimePos = (self.ceiling(totalAreaWidth*0.25*((5/4)**self.sidebarZoomLevel[0]))-font_timetable[0].size(schedTimeText)[0],periodRect[1]+periodRect[3]-font_timetable[0].size(schedTimeText)[1]//2)
                                    periodTimeSurface.blit(schedTimeSurface,schedTimePos)

                    linex = accumulatedWidth+int(self.timetableScroll[0]*self.screenSize[0]/30)
                    pygame.draw.line(weekdayNamesSurface,COLOR8,(linex,0),(linex,font_timetable[0].size('文')[1]+int(self.screenSize[1]/180)),width=2)
                    weekdayNameText = font_timetable[1].render(weekdayNames[nowWeekday],True,(COLOR4))
                    weekdayNamesSurface.blit(weekdayNameText,((linex+int(self.screenSize[1]/450),int(self.screenSize[1]/450))))
                    pygame.draw.line(weekdayNamesSurface,COLOR8,(0,font_timetable[0].size('文')[1]+int(self.screenSize[1]/180)-2),(totalAreaWidth,font_timetable[0].size('文')[1]+int(self.screenSize[1]/180)-2),width=2)
                    accumulatedWidth += self.ceiling(totalAreaWidth*0.6*((5/4)**self.sidebarZoomLevel[0]))
                textSurface.blit(weekdayNamesSurface,(0,0))
                textSurface.blit(periodTimeSurface,(0,0))

            #region yScrollBar
            yScrollbarTrack = pygame.Surface((15,self.scheduleDisplayRect[3]-18))
            yScrollbarTrack.fill(COLOR7)
            yScrollbarTrack.set_alpha(30)
            yScrollbarLength = ((self.scheduleDisplayRect[3]-18)**2)//(int(textNeedArea[1]*30/self.screenSize[1])+self.scheduleDisplayRect[3]-18)
            try:
                yScrollbarDistance = int((self.scheduleDisplayRect[3]-18-yScrollbarLength)*(-self.timetableScroll[1]/int(textNeedArea[1]*30/self.screenSize[1])))
            except ZeroDivisionError:
                yScrollbarDistance = 0
            yScrollbar = pygame.Surface((15,yScrollbarLength))
            yScrollbarActiveArea = [self.scheduleDisplayRect[0]+self.scheduleDisplayRect[2]-15,
                                    self.scheduleDisplayRect[1]+yScrollbarDistance,
                                    15,
                                    yScrollbarLength]
            if not mouseBtns[0]:
                self.scrollbarUnderDrag[1] = False
                self.scrollbarOndragLastMousepos[1] = -1
            if (yScrollbarActiveArea[0]< mousex <yScrollbarActiveArea[0]+yScrollbarActiveArea[2]) and (yScrollbarActiveArea[1]< mousey <yScrollbarActiveArea[1]+yScrollbarActiveArea[3])and not self.sidebarLeftsideOndrag:
                if mouseBtns[0]:
                    self.scrollbarUnderDrag[1] = True
                    xscrollbarAlpha = 100
                    if self.scrollbarOndragLastMousepos[1] == -1:
                        self.scrollbarOndragLastMousepos[1] = mousey
                else:
                    yscrollbarAlpha = 60
            else:
                yscrollbarAlpha = 30
            if self.scrollbarUnderDrag[1]:
                yscrollbarAlpha = 100
                mouseMoveDistance = mousey - self.scrollbarOndragLastMousepos[1]   # positive while upwards, negative while downwards
                try:
                    self.timetableScroll[1] -= int(textNeedArea[1]*30/self.screenSize[1])//(self.scheduleDisplayRect[3]-18-yScrollbarLength)*mouseMoveDistance
                except ZeroDivisionError:
                    self.timetableScroll[1] = 0
            self.scrollbarOndragLastMousepos[1] = mousey

            yScrollbar.fill(COLOR7)
            yScrollbar.set_alpha(yscrollbarAlpha)
            if yScrollbarLength < self.scheduleDisplayRect[3]-18:
                textSurface.blit(yScrollbarTrack,(self.scheduleDisplayRect[2]-15,0))
                textSurface.blit(yScrollbar,(self.scheduleDisplayRect[2]-15,yScrollbarDistance))
            #endregion

            #region xScrollBar
            if self.sidebarDisplayStyle != 2:
                xScrollbarTrack = pygame.Surface((self.scheduleDisplayRect[2]-18,15))
                xScrollbarTrack.fill(COLOR7)
                xScrollbarTrack.set_alpha(30)
                xScrollbarLength = ((self.scheduleDisplayRect[2]-18)**2)//(int(textNeedArea[0]*30/self.screenSize[0])+self.scheduleDisplayRect[2]-18)
                try:
                    xScrollbarDistance = int((self.scheduleDisplayRect[2]-18-xScrollbarLength)*(-self.timetableScroll[0]/int(textNeedArea[0]*30/self.screenSize[0])))
                except ZeroDivisionError:
                    xScrollbarDistance = 0
                xScrollbar = pygame.Surface((xScrollbarLength,15))
                xScrollbarActiveArea = [self.scheduleDisplayRect[0]+xScrollbarDistance,
                                        self.scheduleDisplayRect[1]+self.scheduleDisplayRect[3]-15,
                                        xScrollbarLength,
                                        15]
                if not mouseBtns[0]:
                    self.scrollbarUnderDrag[0] = False
                    self.scrollbarOndragLastMousepos[0] = -1
                if (xScrollbarActiveArea[0]< mousex <xScrollbarActiveArea[0]+xScrollbarActiveArea[2]) and (xScrollbarActiveArea[1]< mousey <xScrollbarActiveArea[1]+xScrollbarActiveArea[3]) and not self.sidebarLeftsideOndrag:
                    if mouseBtns[0]:
                        self.scrollbarUnderDrag[0] = True
                        xscrollbarAlpha = 100
                        if self.scrollbarOndragLastMousepos[0] == -1:
                            self.scrollbarOndragLastMousepos[0] = mousex
                    else:
                        xscrollbarAlpha = 60
                else:
                    xscrollbarAlpha = 30
                if self.scrollbarUnderDrag[0]:
                    xscrollbarAlpha = 100
                    mouseMoveDistance = mousex - self.scrollbarOndragLastMousepos[0]   # positive while rightwards, negative while leftwards
                    try:
                        self.timetableScroll[0] -= int(textNeedArea[0]*30/self.screenSize[0])//(self.scheduleDisplayRect[2]-18-xScrollbarLength)*mouseMoveDistance
                    except ZeroDivisionError:
                        self.timetableScroll[0] = 0
                self.scrollbarOndragLastMousepos[0] = mousex

                xScrollbar.fill(COLOR7)
                xScrollbar.set_alpha(xscrollbarAlpha)
                if xScrollbarLength < self.scheduleDisplayRect[2]-18:
                    textSurface.blit(xScrollbarTrack,(0,self.scheduleDisplayRect[3]-15))
                    textSurface.blit(xScrollbar,(xScrollbarDistance,self.scheduleDisplayRect[3]-15))

            #endregion

            #region leftsideOnDrag
            leftsideLineX = (int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6)) + int(self.sidebarLeftsideOffset*self.screenSize[0])

            lineHighlightAlpha = 0
            lineActiveArea = (leftsideLineX-4, 5, 8, self.screenSize[1]-10)
            if not mouseBtns[0]:
                self.sidebarLeftsideOndrag = False
                self.sidebarLeftsideOndragLastMouseX = -1
            if (lineActiveArea[0] <= mousex <= lineActiveArea[0]+lineActiveArea[2]) and not(self.scrollbarUnderDrag[0] or self.scrollbarUnderDrag[1]):
                if mouseBtns[0]:
                    self.sidebarLeftsideOndrag = True
                    lineHighlightAlpha = 60
                    if self.sidebarLeftsideOndragLastMouseX == -1:
                        self.sidebarLeftsideOndragLastMouseX = mousex
                else:
                    lineHighlightAlpha = 30
            if self.sidebarLeftsideOndrag:
                lineHighlightAlpha = 60
                mouseMoveDistance = mousex - self.sidebarLeftsideOndragLastMouseX
                self.sidebarLeftsideOffset += (mouseMoveDistance/self.screenSize[0])
            self.sidebarLeftsideOndragLastMouseX = mousex
            lineHighlight = pygame.Surface((6,self.screenSize[1]))
            lineHighlight.fill(COLOR7)
            lineHighlight.set_alpha(lineHighlightAlpha)
            self.master.blit(lineHighlight,(leftsideLineX-3,0))

            if self.sidebarLeftsideOffset < (20-(int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6)))/self.screenSize[0]:
                self.sidebarLeftsideOffset = (20-(int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6)))/self.screenSize[0]
            elif self.sidebarLeftsideOffset > (self.screenSize[0]-40-(int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6)))/self.screenSize[0]:
                self.sidebarLeftsideOffset = (self.screenSize[0]-40-(int(self.screenSize[1]*0.625-6) if self.screenSize[0]/self.screenSize[1]>=1 else int(self.screenSize[0]*0.625-6)))/self.screenSize[0]
            #endregion

            rtn = '0'
            rawSize = 20
            b_radius = 4
            width = 1
            COLOR01 = self.getColor(self.darkMode,x=105)
            COLOR02 = self.getColor(self.darkMode,x=162)
            COLOR03 = self.getColor(self.darkMode,x=229)
            COLOR04 = self.getColor(self.darkMode,x=31)
            COLOR05 = self.getColor(self.darkMode,x=68)
            if self.sidebarDisplayStyle in [0,1]:
                # region zoom2plus for DayList|WeekList's fonts
                rect_btn = (3,totalAreaHeight-38,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3] and self.sidebarZoomChangable[2][0]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,0,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(2,1)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,0,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

                # region zoom2reset for DayList|WeekList's fonts
                rect_btn = (6+rawSize,totalAreaHeight-38,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,16,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(2,0)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,16,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,16,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

                # region zoom2minus for DayList|WeekList's fonts
                rect_btn = (9+2*rawSize,totalAreaHeight-38,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3] and self.sidebarZoomChangable[2][1]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,32,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(2,-1)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,32,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,32,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

            elif self.sidebarDisplayStyle == 2:
                # region zoom1plus for DayColumnar's Y
                rect_btn = (3,3,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3] and self.sidebarZoomChangable[1][0]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,0,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(1,1)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,0,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

                # region zoom1reset for DayColumnar's Y
                rect_btn = (3,6+rawSize,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,16,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(1,0)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,16,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,16,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

                # region zoom1minus for DayColumnar's Y
                rect_btn = (3,9+2*rawSize,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3] and self.sidebarZoomChangable[1][1]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,32,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(1,-1)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,32,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,32,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

            else:   # self.sidebarDisplayStyle == 3
                # region zoom0plus for WeekColumnar's X
                rect_btn = (3,totalAreaHeight-38,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3] and self.sidebarZoomChangable[1][0]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,0,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(0,1)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,0,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

                # region zoom0reset for WeekColumnar's X
                rect_btn = (6+rawSize,totalAreaHeight-38,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,16,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(0,0)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,16,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,16,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

                # region zoom0minus for WeekColumnar's X
                rect_btn = (9+2*rawSize,totalAreaHeight-38,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3] and self.sidebarZoomChangable[0][1]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,32,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(0,-1)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,32,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,32,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

                # region zoom1plus for WeekColumnar's Y
                rect_btn = (totalAreaWidth-38,3,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3] and self.sidebarZoomChangable[1][0]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,0,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(1,1)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,0,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,0,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

                # region zoom1reset for WeekColumnar's Y
                rect_btn = (totalAreaWidth-38,6+rawSize,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,16,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(1,0)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,16,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,16,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

                # region zoom1minus for WeekColumnar's Y
                rect_btn = (totalAreaWidth-38,9+2*rawSize,rawSize,rawSize)
                if rect_btn[0]+self.scheduleDisplayRect[0] <= mousex < rect_btn[0]+self.scheduleDisplayRect[0]+rect_btn[2] and rect_btn[1]+self.scheduleDisplayRect[1] <= mousey < rect_btn[1]+self.scheduleDisplayRect[1]+rect_btn[3] and self.sidebarZoomChangable[1][1]:
                    if mouseBtns[0] or mouseBtns[4]:
                        pygame.draw.rect(textSurface,COLOR05,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR03,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,32,64,COLOR03)
                        textSurface.blit(btnimg,rect_btn)
                        if mouseBtns[4]:
                            rtn = 'rtns.zoomSidebar(1,-1)'
                    else:
                        pygame.draw.rect(textSurface,COLOR04,rect_btn,0,border_radius=b_radius)
                        pygame.draw.rect(textSurface,COLOR02,rect_btn,width*2,border_radius=b_radius)
                        btnimg = self.getButtons(rawSize,32,64,COLOR02)
                        textSurface.blit(btnimg,rect_btn)
                else:
                    pygame.draw.rect(textSurface,COLOR0,rect_btn,0,border_radius=b_radius)
                    pygame.draw.rect(textSurface,COLOR01,rect_btn,width*2,border_radius=b_radius)
                    btnimg = self.getButtons(rawSize,32,64,COLOR01)
                    textSurface.blit(btnimg,rect_btn)
                # endregion

            self.master.blit(textSurface,(totalAreaLeft,totalAreaUp))
            return rtn

    def writeNowSchedule(self,subjectName:str,timeAreaText:str,portValues:List[int]=[0,0,0,0,0,0,0,0,0]):
        # portValue: [<weekday>,<year>,<month>,<date>,<hour>,<minute>,<second>,<countDays>,<countWeeks>]
        w,y,n,d,h,m,s,cd,cw = portValues
        if eval(subjectName) == '':
            return None
        
        COLOR1 = self.getColor(self.darkMode,x=254)
        COLOR2 = self.getColor(self.darkMode,x=155)

        fontSize = min(int(self.screenSize[0]/50),int(self.screenSize[1]/50),int((self.clockCenter[0]-5)/15))
        subjectName = eval(subjectName)
        if self.compressLevel in [0,1]:
            if self.doTimetableSearch:
                font = (self.getPygameFont(self.textFonts[0],fontSize*4),self.getPygameFont(self.textFonts[3],fontSize*2))
                text = (font[0].render(subjectName,True,COLOR1),font[1].render(timeAreaText,True,COLOR1))
                size = (font[0].size(subjectName),font[1].size(timeAreaText))
                self.master.blit(text[0],(self.clockCenter[0]-int(size[0][0]/2),int(self.screenSize[1]*0.75-size[0][1])))
                self.master.blit(text[1],(self.clockCenter[0]-int(size[1][0]/2),int(self.screenSize[1]*0.75)))
            else:
                font = (self.getPygameFont(self.textFonts[0],fontSize*3),self.getPygameFont(self.textFonts[3],fontSize*2))
                text = (font[0].render('未开启跟进计划',True,COLOR1),font[1].render('',True,COLOR1))
                text[0].set_alpha(45)
                size = (font[0].size('未开启跟进计划'),font[1].size(''))
                self.master.blit(text[0],(self.clockCenter[0]-int(size[0][0]/2),int(self.screenSize[1]*0.75-size[0][1]/2)))
        else:
            if self.doTimetableSearch:
                font = (self.getPygameFont(self.textFonts[0],int(fontSize*3.5)),self.getPygameFont(self.textFonts[3],fontSize*3))
                text = (font[0].render(subjectName,True,COLOR1),font[1].render('',True,COLOR1))
                size = (font[0].size(subjectName),font[1].size(''))
                self.master.blit(text[0],(self.clockCenter[0]-int(size[0][0]/2),int(self.screenSize[1]*0.7-size[0][1]/2)))

    def getPeriodLenth(self,rawDigitFr:int,rawDigitsTo:int) -> int:
        '''Accepts two 0~2400 int as rawDigits, and returns the minutes between them.'''
        return (rawDigitsTo//100*60+rawDigitsTo%100)-(rawDigitFr//100*60+rawDigitFr%100)