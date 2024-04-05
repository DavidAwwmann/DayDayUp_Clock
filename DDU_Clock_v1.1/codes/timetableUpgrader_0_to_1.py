from tkinter.messagebox import showinfo
import tkinter as tk

root = tk.Tk()
root.withdraw()

file0 = open('timetable.txt','r')
lines0 = file0.readlines()
file0.close()
try:
    if lines0[3][:21] == '# Timetable version: ':
        exit()
except IndexError:
    pass

file1 = open('timetable1.txt','w')
lines1 = ['','','# Timetable version: 1']

newScheds = [[],[],[],[],[],[],[]]
for time in eval(lines0[0]):
    for schedIdx in range(2,9):
        sched = time[schedIdx]
        if sched == '':
            continue
        else:
            newScheds[schedIdx-2].append([time[0],time[1],sched])
lines1[0] = f'{newScheds}'

newSettings:dict = eval(lines0[2])
newSettings['textFonts'] = ['C:/Windows/Fonts/stxinwei.ttf','C:/Windows/Fonts/roccb___.ttf','C:/Windows/Fonts/simhei.ttf','C:/Windows/Fonts/rock.ttf','C:/Windows/Fonts/stzhongs.ttf']
lines1[1] = f'{newSettings}'

lines1Text = '\n'.join(lines1)

file1.write(lines1Text)
file1.close()

showinfo('提示','成功将 timetable.txt 升级为 timetable1.txt !')