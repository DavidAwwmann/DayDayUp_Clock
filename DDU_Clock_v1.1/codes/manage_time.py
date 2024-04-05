import pygame
from datetime import datetime
from zhdate import ZhDate

pygame.init()
TIMEREVENT = pygame.USEREVENT + 1

class Time_manager():
    def __init__(self,master):
        self.master = master
        self.today = datetime.today()
        self.tickRate = 30

    def tick(self):
        self.today = datetime.today()
        seconds = self.today.second + self.today.microsecond*0.000001
        minutes = self.today.minute + seconds/60.0
        hours = self.today.hour + minutes/60.0
        self.timeStr = f'{self.today.hour:02}:{self.today.minute:02}:{self.today.second:02}'
        rtn = self.clockHandAngles(seconds,minutes,hours)
        pygame.time.set_timer(TIMEREVENT,int(1000/self.tickRate))
        return rtn

    def date(self):
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        year = self.today.year
        month = self.today.month
        day = self.today.day
        weekday = weekdays[self.today.weekday()]
        self.dateStr = f'{year}年{month}月{day}日 {weekday}'

    def lunar(self):
        lmonths = ['','正','二','三','四','五','六','七','八','九','十','冬','腊']
        ldays = ['','初一','初二','初三','初四','初五','初六','初七','初八','初九','初十',
                   '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十',
                   '廿一','廿二','廿三','廿四','廿五','廿六','廿七','廿八','廿九','三十']
        lyear = ZhDate.from_datetime(self.today).chinese()[-8:-5]
        lmonth = lmonths[ZhDate.from_datetime(self.today).lunar_month]
        lday = ldays[ZhDate.from_datetime(self.today).lunar_day]
        self.lunarStr = f'{lyear}{lmonth}月{lday}'

    def clockHandAngles(self,s,m,h):
        s_ang = -s*6+180
        m_ang = -m*6+180
        h_ang = -h*30+180
        return f'rtns.deliverClockHandAngles({s_ang},{m_ang},{h_ang})'
    
    def updateDigitalTexts(self):
        self.date()
        self.lunar()
        return [self.dateStr,self.timeStr,self.lunarStr]