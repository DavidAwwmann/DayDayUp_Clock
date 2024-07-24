import tkinter as tk
import tkinter.messagebox as tkmsg
import tkinter.filedialog as tkfile
from manage_edit import isFileOpenable
from typing import Tuple

root = tk.Tk()
root.withdraw()

class Tk_Manager():
    def __init__(self):
        ...

    def separate_dir_and_filename(self,path:str) -> Tuple[int]:
        '''Accepts a string path, which can be relative or absolute, and may include '/' or  '\\' as folder structures.\n
        Returns a tuple of (dir, filename).'''
        if '/' in path:
            dir = '/'.join(path.split('/')[:-1])
            filename = path.split('/')[-1]
        elif '\\' in path:
            dir = '/'.join(path.split('\\')[:-1])
            filename = path.split('\\')[-1]
        else:
            dir = './'
            filename = path
        return (dir,filename)

    def reopenTimetable(self,currentPath:str,language):
        currentDir, currentFile = self.separate_dir_and_filename(currentPath)
        if language == 'Chinese':
            title = '打开时间表文件 (<.txt>或<.json>)'
        else:
            title = 'Open a timetable file (<.txt> or <.json>)'
        newPath = tkfile.askopenfilename(defaultextension='.txt',title=title,initialdir=currentDir,initialfile=currentFile)
        if newPath == '':
            return '*cancel'
        elif isFileOpenable(newPath,True,allowJson=True):
            return newPath
        else:
            return '*failed'
        
    def reopenBackgroundImg(self,currentPath:str,language):
        currentDir, currentFile = self.separate_dir_and_filename(currentPath)
        if language == 'Chinese':
            title = '选择图片文件'
        else:
            title = 'Choose an image file'
        newPath = tkfile.askopenfilename(defaultextension='.png',title=title,initialdir=currentDir,initialfile=currentFile)
        if newPath == '':
            return '*cancel'
        else:
            return newPath