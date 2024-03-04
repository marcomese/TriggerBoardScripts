# -*- coding: utf-8 -*-

import re
import os
import numpy as np
import matplotlib.pyplot as plt
import analysisFunctions as af
import seaborn as sns

colors = 'bgrcmy'
markers = '.v^x+D'

numPtrn = "([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)*)"
dataFPtrn = (f"data-cit(0|1)-(hg|lg)-ch{numPtrn}-per[TV]{numPtrn}(?:ns|mv)"
                f"{numPtrn}hg{numPtrn}lg.dat")
dataFRegex = re.compile(dataFPtrn)

funcFName = "fitReport.dat"

funcParPtrn = f"(c\d):\s*{numPtrn}\s*\+/-\s*{numPtrn}"
funcParRegex = re.compile(funcParPtrn)

tSPtrn = f"Registro\s*\t*TCONST_(HG|LG)_SHAPER\s*\t*=\s*\t*{numPtrn}"
tSRegex = re.compile(tSPtrn)

gainPtrn = r"\\([hl]g)\\"
gainRegex = re.compile(gainPtrn)

homeDir = os.getcwd()

gainDict = {'hg' : 'High Gain',
            'lg' : 'Low Gain'}

c = ''
fileArr = []
dataFilePath = None
while True:
    dataFilePath = c

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

    shapingT = tSFind.group(2)

    filesInDir = os.listdir(c)

dataF = None
fitF = None
for f in filesInDir:
    if funcFName in f and fitF is None:
        fitF = dataFilePath+"\\"+f

    if (fm := dataFRegex.match(f)) is not None and dataF is None:
        dataF = dataFilePath+"\\"+fm.group(0)

gain = gainRegex.findall(dataF)[0]

fitPar = {}
with open(fitF) as fitFile:
    fitRep = fitFile.readlines()
    
    par = funcParRegex.findall(''.join(fitRep))
    
    for p in par:
        fitPar.update({p[0]: (float(p[1]),float(p[2]))})

fitFunc = lambda x: fitPar['c0'][0]+(fitPar['c1'][0]*x)

data = np.genfromtxt(dataF,
                     delimiter=',',
                     names=True)

residuals = abs(fitFunc(data['t'])-data['adc'])/data['adc']

resDict = {t:r for t,r in zip(data['t'],residuals) if r <= 0.5}

for k,v in resDict.items():
    if k > 30 and v > 0.055:
        break
    
    impT = k
    res = v

print(impT,res)

plt.title(f"Shaping time = {shapingT}ns, {gainDict[gain]}")

plt.axvline(impT, 0, 1)
plt.grid(which='both')
plt.minorticks_on()

plt.xlabel(r"$T \quad (ns)$")
plt.ylabel(r"$\frac{|y_{pred}-y|}{y}$")

plt.ylim((0,0.2))
plt.xlim((10,80))

plt.plot(resDict.keys(),resDict.values(),'r.')
plt.savefig(f"shapT{shapingT}{gain}.png", bbox_inches="tight", dpi=300)
