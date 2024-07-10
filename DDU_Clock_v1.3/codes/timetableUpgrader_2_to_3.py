from tkinter.messagebox import showinfo,showerror,askyesno
import tkinter as tk
import tkinter.filedialog as tkfile
from manage_tk import Tk_Manager
from sys import exit

root = tk.Tk()
root.withdraw()
ttkk = Tk_Manager()

try:
    old_filepath = tkfile.askopenfilename(defaultextension='.txt',title='打开<版本2>时间表文件',initialdir='./',initialfile='timetable2.txt')
    if old_filepath == '':
        exit()
    file0 = open(old_filepath,'r')
    lines0 = file0.readlines()
    file0.close()
except FileNotFoundError:
    showerror('错误',f'找不到文件：{old_filepath}')
    exit()
try:
    if lines0[2] != '# Timetable version: 2':
        raise IndexError
except IndexError:
    showerror('错误','原文件格式异常!\n应打开<版本2>的时间表文件')
    exit()



try:
    new_filepath = tkfile.asksaveasfilename(defaultextension='.txt',title='另存<版本3>时间表文件',initialdir='./',initialfile='timetable3.txt')
    if new_filepath == '':
        exit()
    file1 = open(new_filepath,'w')
    lines1 = ['','','# Timetable version: 3']

    scheds = eval(lines0[0])
    lines1[0] = f'{scheds}'

    newSettings:dict = eval(lines0[1])
    newSettings['colorfuncs'] = [['(47/51)*x+20','(15/17)*x+20','(38/51)*x+20'],['(-41/51)*x+225','(-41/51)*x+225','(-41/51)*x+225']]
    newSettings['doBackgroundImgDisplay'] = [False,False]
    newSettings['backgroundImgPaths'] = ['','']
    newSettings['backgroundAlpha'] = 60
    newSettings['language'] = 'Chinese中文'
    newSettings['timeOffset'] = (0,0,0,0,0)
    newSettings['sidebarDisplayStyle'] = 0
    newSettings['columnarGapMergeThreshold'] = 2401
    newSettings['retrenchMode'] = False
    newSettings['maxTps'] = 60
    lines1[1] = f'{newSettings}'

    lines1Text = '\n'.join(lines1)

    file1.write(lines1Text)
    showinfo('提示',f'成功将 {ttkk.separate_dir_and_filename(old_filepath)[1]} 升级为 {ttkk.separate_dir_and_filename(new_filepath)[1]} ！')
except Exception as e:
    showerror('错误',f'升级失败!\n{e}')
finally:
    try:
        file1.close()
    except NameError:
        pass
