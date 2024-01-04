# -*- coding: utf-8 -*-

import os
import matplotlib.pyplot as plt
import numpy as np
from lmfit.models import StepModel,PolynomialModel
import re

numericPattern = "([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)*)"
meanPattern = f"\s*center:\s*{numericPattern}\s*"
fwhmPattern = f"\s*fwhm:\s*{numericPattern}\s*"
sigmaPattern = f"\s*sigma:\s*{numericPattern}\s*"
dirNamePattern = f"ph(-)?{numericPattern}ns"

numericRegex = re.compile(numericPattern)
meanRegex = re.compile(meanPattern)
fwhmRegex = re.compile(fwhmPattern)
sigmaRegex = re.compile(sigmaPattern)
dirNameRegex = re.compile(dirNamePattern)

startDir = os.getcwd()

# os.chdir("D:/TB3/triggerBoardLibs/trToSIG/holdDel127")
os.chdir("D:/TB_FM/triggerBoardLibs/trgSigDelaySec_0")

dataDir = os.getcwd()

pdstRange = (-1,-11)
topRange = (45,74)

dirsVal = {}
for d in os.scandir():
    if d.is_dir() and (regexRes := dirNameRegex.findall(d.name)):
        sign = regexRes[0][0]
        intVal = regexRes[0][1]
        tVal = f"{sign}{intVal}"
        dirsVal.update({d.name:float(tVal)})

tAdcData = []
for d,tVal in dirsVal.items():
    os.chdir(d)

    for f in os.scandir():
        if d in f.name and f.is_dir():
            os.chdir(f.name)
            break
    
    for f in os.scandir():
        if "table" in f.name:
            dataF = f.name
            break
    
    with open(dataF) as dF:
        data = dF.readlines()
    
        means = [float(n) for n in numericRegex.findall(data[-4])]
        errs  = [float(n) for n in numericRegex.findall(data[-1])]
        
        hgMean = means[5]
        hgErr  = errs[5]
    
        tAdcData.append((float(tVal),
                        float(hgMean),
                        np.sqrt(float(hgErr))))

        os.chdir(dataDir)

os.chdir(dataDir)

tAdcData.sort()

tAdcData = np.asarray(tAdcData)

t = tAdcData[:,0]
adc = tAdcData[:,1]
adcErr = tAdcData[:,2]

pdst = np.mean(adc[pdstRange[0]:pdstRange[1]:-1])
top = np.mean(adc[topRange[0]:topRange[1]])

plt.xlabel(r"$T_{sig}-T_{trig}$ (ns)")
plt.ylabel("<ADC>")
plt.grid(which='both')
plt.minorticks_on()

plt.plot(t,adc,'r.')
plt.xlim(-500,400)
plt.ylim((0,500))
plt.errorbar(t, adc, yerr=adcErr, fmt='none')
plt.axhline(y=pdst,color='b',label='pedestal')
plt.axhline(y=top,color='g',label='peak')
plt.axvline(x=0,color='black')

plt.legend(loc='upper left')

plt.savefig("timingTrgToSigSec.png",dpi=600,bbox_inches='tight')

os.chdir(startDir)