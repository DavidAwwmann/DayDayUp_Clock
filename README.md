# DayDayUp_Clock_v1.3
跟进计划表的时钟

本程序系 DavidAwwmann 本人编写，仅在 GitHub 上由本人账号上传。未经许可请勿商用

代码均使用 `Python(v3.7.4)` 编写，导入了第三方库`pygame(v2.1.0)`和`zhdate`，运行源码需预先安装

## 使用指南

### 1. 下载与配置  

**所有正式版的 exe 文件均可在`Release`处下载。**  

下载`codes`文件夹中的代码，文件除`DDU_Clock.ico`、`timetableUpgrader.ico`和`timetableEditor.ico`无需使用外，其余须与该项目文件结构一致；运行`main.py`，即打开时钟主程序。  
也可直接使用`executables`文件夹中打包好的exe文件，将包含`buttons.png`和`icon.png`的`GUI`文件夹置于exe同目录下。  
  
首次运行后，程序会在其同目录下生成一个`timetable3.txt`文件，其中记录了程序运行的参数，包含三行文本：  
**第一行** 为时间计划表，格式为：`[周一计划,周二计划,…,周日计划]`，其中`<周X计划> = [[<时段1起点>,<时段1终点>,'计划1名称'],[<时段2起点>,<时段2终点>,'计划2名称'],…]； <时段起/终点> = 100\*小时+分钟`，当天留空(即`计划名称 = ''`)的计划会被忽略。  
  
**第二行** 为程序的设置参数，采用`Python`字典类型格式，分别控制程序打开时的默认设置，除了与之前版本相同的暗色模式(`darkMode: bool = True`)、简略模式级别(`compressLevel: int = 0`)、窗口大小(`screenSize: tuple[int, int] = (600, 600)`)、是否跟进计划(`doTimetableSearch: bool = True`)的参数、字体文件路径(`textFonts`)外，1.3版本新添加了以下设置参数：   

- `colorfuncs: list[list[str]]`：内含两个列表，分别记录时钟在暗/亮色模式下前景色的RGB表达式；
- `doBackgroundImgDisplay: list[bool]`：记录暗/亮色模式下背景图片是否显示；
- `backgroundImgPaths: list[str]`：记录暗/亮色模式下背景图片的文件路径，可以为PNG或JPG等格式，若无法正常读取则自动将对应的`doBackgroundImgDisplay`当作`False`处理；
- `backgroundAlpha: int = 60`：记录背景图片的不透明度。
- `language: Literal['Chinese中文', 'English英文']`：记录程序内文字语言
- `timeOffset: list[int, int, int, int, int]`：用于时钟时间微调，单位分别为日、时、分、秒、毫秒，正值为延后，负值为提前；
- `sidebarDisplayStyle: int = 0`：记录计划单样式，从0到3分别为：“当天列表”、“本周列表”、“当天柱状”、“本周柱状”；
- `columnarGapMergeThreshold: int = 2401`：记录计划单在“当天柱状”样式下缩略显示计划间隙的最小时间跨度(小时*100+分钟)，取2401即为“永不缩略”。请注意：在图形化编辑器中，该选项单位为“分钟”，此时“永不缩略”为1441；
- `retrenchMode: bool`：是否开启节能模式。节能模式开启时，程序会强制限制自身刷新率和事件响应频率降低至5次每秒(前台)或1次每秒(后台)。这将导致本程序窗口出现明显卡顿，而同时使其cpu占用率降低至原本的20%(前台)或8%(后台)以下；
- `maxTps: int = 60`：程序最大刷新率，可为5~100间的整数。

另外，`textFonts`参数自该版本起支持使用由pygame读取的系统字体。以上参数中大部分仅影响运行程序时的初始设置，可以在程序内手动调整。

**第三行** 为固定字符：`# Timetable version: 3`，用以标识版本。  

DayDayUp_Clock正式版 1.3 的参数文件格式相比于 1.2 版本，在“计划表”部分未作格式修改，但增添了若干设置参数。若想对之前版本的参数文件进行一键升级，可将`timetableUpgrader_2_to_3.exe`置于任意位置运行，并在弹出的“打开”对话框中选择待升级的 版本2时间表文件，运行后弹出“另存为”窗口，在指定目录下生成一个 版本3时间表文件。  

`timetableEditor.exe`由`manage_edit.py`打包而成。运行该程序并选择打开电脑中任意一个**格式正确的`.txt`或`.json`文件**即可进行图形化编辑。

***注意：如果在该文件中需用到中文字符，须将文件编码格式设置为`GBK`或`ANSI`，否则会导致乱码或崩溃！***  

### 2. 程序内操作

双击运行程序，在默认设置参数下，程序将打开一个600*600像素的暗色窗口，右侧为计划单(无计划即为空)，左侧上方为一时钟，时钟下方为目前计划名称及其有效时段(若目前时间不符合计划单中任一时段则不显示)。三色的指针分别贴时钟表盘边缘移动，表盘中央为三行显示文本，由上至下分别为当前日期(`XXXX年X月XX日 周X`)、当前时间(`XX:XX:XX`)、当前农历日期(`XX年X月XX`)，其中农历日期在英文模式下显示为文字化的公历日期。

窗口右下角有四个按钮，从右至左分别为`简略模式`、`暗色模式`、`是否跟进计划`与`重新读取数据`，鼠标悬停于对应按钮上方会显示文本提示。  
`简略模式`共三挡(`0`, `1`, `2`)，其中`0`挡显示全部数据；`1`挡隐藏计划栏并将剩余部分居中，同时`是否跟进计划`和`重新读取数据`两个按钮也会被隐藏；`2`挡则将时钟表盘占满窗口，同时隐藏目前计划的有效时段，并将目前计划名称显示于表盘内三行文本之下(若目前无计划则不显示)。  
`暗色模式`能够切换窗口的颜色主题。  
`是否跟进计划`控制程序是否搜索当前时间在计划单中的计划，若关闭则不会在计划单中用颜色明暗区分“已完成”和“未完成”的计划，并不再将当前计划显示于时钟表盘下方(`简略模式`为`0`挡或`1`挡时)或内部(`简略模式`为`2`挡时)。  
`重新读取数据`会在按下时重新读取`timetable.txt`中的所有数据并刷新显示设置(包括窗口大小)。
在该版本中，在窗口右上角新增四个按钮，从右至左分别为`语言`、`背景图片开关`、`计划单样式`与`节能模式`。在暗/亮色模式中，`背景图片开关`彼此独立工作。

另外，双击`重新读取数据`可以选择一个`.txt`或`.json`文件作为时间表重新读取；双击`背景图片开关`可以重新选择背景图片。**请注意：由于`tkinter.filedialogue`对线程的严苛要求，在文件选择窗口弹出期间主程序窗口将不会刷新。**

鼠标悬停于侧边计划单上并滚动鼠标滚轮，或拖动滚动条，可使计划单滚动显示。

窗口可以自由调整大小，其上的所有元素都会自动适应。若要最小化、最大化或关闭窗口，请使用标题栏右上角的对应选项。

>**在本版本中**，运行`manage_edit.py`或`timetableEditor.exe`可以对 **任意符合`timetable3.txt`或`timetable3.json`格式的文本文件** 进行图形化编辑，功能包括：
>- 对计划的增添、修改、删除；
>- 对以上三个操作的撤销、重做；
>- 修改设置选项；
>- 对计划表进行保存编辑、取消编辑，以及将`.txt`和`.json`互相导出。  
>
>在进行计划的增添或修改时，计划名称的输入可选择“普通模式”或“高级模式”，后者支持一个*在 Python 中可被 `eval()` 的字符串型表达式*，并提供了以下可供引用的变量：  
>- `w`：当前为星期几，周一为`0`，周日为`6`；
>- `y`：当前年份，整数；
>- `n`：当前月份，`1`~`12`的整数；
>- `d`：当前日期，`1`~`31`的整数；
>- `h`：当前小时数，`0`~`23`的整数；
>- `m`：当前分钟数，`0`~`59`的整数；
>- `s`：当前秒数，`0`~`59`的整数；
>- `cd`：以本年1月1日为`0`，累计至当前的天数，`0~364`(平年)或`0~365`(闰年)的整数；
>- `cw`：以本年1月1日所在星期为`0`，累计至当前的星期，`0`~`52`的整数。
>
>例如，使用`"'A' if n==5 else ''"`可以使计划 A 仅在五月显示，而`"'even' if cw%2==0 else 'odd'"`是一个简单的单双周判断。
>
>**注：由于Windows文件夹权限问题，在修改设置项中浏览字体文件夹`C:/Windows/Fonts/`时可能失败。该版本中，pygame读取的系统字体可由下拉选项的方式备选。**

### 3. 可能的故障及解决方案

若程序完全无法启动，且提示无权限访问文件等错误，可能系杀毒软件查杀所致。某安全卫士经常将该程序误报为木马，**请自行甄别**，如需恢复请打开杀毒软件将程序添加信任。  

若程序能够启动但无法实现功能，或能实现功能但功能异常，可能为时间表文件或`GUI`文件夹内容出现错误。请再次检查`timetable3.txt`的编码格式是否已设置为`GBK`或`ANSI`，其中的内容格式是否正确，以及`GUI`文件夹是否已包含`buttons.png`和`icon.png`且与主程序文件处于同一目录下。  

由于此程序仅在 Windows10 x64 系统上开发和测试，故操作系统的版本差异也可能引发故障。如果遇到无法解决的故障或程序自身BUG，请在GitHub留言或向`2439886732@qq.com`发送邮件反馈。本人学业繁忙，可能无法做到一一回复，还请谅解！

## 更新内容记录

### Pre - 1.0 (原 15Clock v1.0) (源码未收录)
- 基于 Python Turtle 的时钟，具备时钟表盘及数字显示的日期与时间
- 能够从外部文件`timetable.txt`读取时间表，并根据时间跟进并显示计划
- 时钟表盘两侧能够显示从`timetable.txt`中读取的标语

### Pre - 2.0 (原 15Clock v2.0) (源码未收录)
- 基于 python Pygame 重写了15Clock，其外部读取文件`timetable.txt`兼容上一版本
- 包含 Pre - 1.0 版本中除标语显示外的所有功能
- 添加了暗色模式、简略模式、是否跟进计划、重新读取数据的按钮及其功能
- 添加了侧边的计划单区域，调整了原有元素的位置
- 现在窗口中的元素能够自动适应窗口大小

### 正式版 1.0 (原 15Clock v2.1)
- 紧急修复了程序窗口关闭后后台进程不退出的BUG
- 现在`timetable.txt`中当天计划名称留空(即`''`)的计划会被忽略
- 更改程序名称为 DayDayUp_Clock，简称 DDU_Clock

### 正式版 1.1
- 修复了以下bug：
    - 滚动侧边计划表时滚动范围未作限制
    - 农历日期显示不正确
    - 计划表为空时可能引发报错
    - 侧边计划表中用颜色标注“当前计划”时出现错位
    - 部分文字在极端的窗口尺寸下显示不正确
- 为解决程序所用部分字体文件缺失导致无法使用的问题，现在程序使用的5种字体都可以在`timetable.txt`中进行更改
- 彻底移除了“标语”功能
- 大幅度更改了`timetable.txt`中的格式，并更名为`timetable1.txt`，可以在同一目录下运行`timetableUpgrader_0_to_1.exe`对 v1.0 中的文件进行升级
- 对窗口外观进行了优化  

### 正式版 1.2
- 修复了以下bug：
    - 时钟程序在窗口尺寸过小时崩溃
    - 时钟程序右下角按钮的悬浮文本图层不正确
- 实现了时间表的图形化编辑
- 再次更改了`timetable1.txt`中的格式，并更名为`timetable2.txt`，可以在同一目录下运行`timetableUpgrader_1_to_2.exe`对 v1.1 中的文件进行升级
- 对窗口外观进行了再次优化  
  
### 正式版 1.3
- 修复了 图形化编辑器中执行“保存文件”操作后再对时间表进行的改动不会在主界面中显示 的Bug
- 增添了以下功能：
    - 自定义前景色
    - 自定义背景图片
    - 程序的中英双语模式
    - 时钟时间的微调
    - 计划单的三种新样式
    - 节能模式
    - 时间表文件.txt与.json的转化
    - 双击对应按钮以选择时间表文件和背景图片文件的功能
    - 计划单左侧的区域隔断现在可以被左右拖动
- 取消了计划单的单击滚动区域，改为滚动条方式
- 相比`timetable2.txt`添加了更多设置参数，并更名为`timetable3.txt`，可以运行`timetableUpgrader_1_to_2.exe`对 v1.2 中的文件进行升级
- 运行时间表升级程序将弹出“打开”对话框和“另存为”对话框
- 对窗口外观进行了最终优化

---
好好学习 · 天天向上  
David Awwmann
