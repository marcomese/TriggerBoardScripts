# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 17:45:24 2023

@author: limadou
"""

import re
import os
import numpy as np
import matplotlib.pyplot as plt
import analysisFunctions as af

colors = 'bgrcmy'
markers = '.v^x+D'

numPtrn = "([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)*)"
dataFPtrn = (f"data-cit(0|1)-(hg|lg)-ch{numPtrn}-perV{numPtrn}ns"
                f"{numPtrn}hg{numPtrn}lg.dat")
dataFRegex = re.compile(dataFPtrn)

fileKeys = ("file","cit","gain","ch","pulseT","hg","lg","shapingT")

tSPtrn = f"Registro\s*\t*TCONST_(HG|LG)_SHAPER\s*\t*=\s*\t*{numPtrn}"
tSRegex = re.compile(tSPtrn)

homeDir = os.getcwd()

compare = 'shapingT'

c = ''
fileArr = []
while True:
    files = dict.fromkeys(fileKeys)

    c = af.promptDir("Selezionare directory contenente il file di dati\n"
                     " da aggiungere al plot ('exit' per continuare): ")

    if c == 'exit':
        break

    dataRootDir = homeDir+"\\"+c.split(homeDir)[1].split('\\')[1]

    filesInRootDir = os.listdir(dataRootDir)
    
    for f in filesInRootDir:
        fPath = dataRootDir+"\\"+f

        if os.path.isdir(fPath):
            flist = os.listdir(fPath)
            
            for rf in flist:
                if rf[:11] == 'REGSnapshot':
                    snapFile = fPath+"\\"+rf
    
    with open(snapFile,"r") as sf:
        for lines in sf.readlines():
            tSFind = tSRegex.match(lines)
            
            if tSFind is not None:
                break

    files['shapingT'] = tSFind.group(2)

    filesInDir = os.listdir(c)

    for f in filesInDir:
        fm = dataFRegex.match(f)

        if fm is not None:
            break

    for i,k in enumerate(fileKeys[:-1]):
        files[k] = fm.group(i)

    files['file'] = f"{c}\\{files['file']}"

    fileArr.append(files)

for i,f in enumerate(fileArr):
    data = np.genfromtxt(f['file'],
                         delimiter=',',
                         names=True)

    c = colors[i%len(colors)]
    m = markers[i%len(markers)]

    xlimit = 6 if f['gain'] == 'lg' else 2

    plt.xlim((0,xlimit))

    plt.plot(data['v'],data['adc'],
             f'{c}{m}',
             label=(f"cit{f['cit']} HG={f['hg']} LG={f['lg']} T={f['pulseT']}"
                    f" shaping={f['shapingT']}ns"))
    plt.legend(loc='best')

fig = plt.gcf()

plt.show()

plotName = input("Inserire il nome con cui salvare il plot: ")

plotName = dataRootDir+"\\"+plotName

fig.savefig(plotName, bbox_inches='tight')

print(f"File salvato in {plotName}")
