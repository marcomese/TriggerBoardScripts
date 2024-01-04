# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 14:17:50 2021

@author: Wizard
"""

import re
import plotterLib as pltr
import os
from os.path import isfile
import numpy as np
import citSupportLib as csl

analysisPromptPattern = "(\d)\s*:\s*([\w,-:\\\\]+)"
apRegex = re.compile(analysisPromptPattern)

rangePattern = f"{pltr.numericPattern}-?{pltr.numericPattern}?"

limitPattern = f"{rangePattern}([ebdc][xy])"
limitRegex = re.compile(limitPattern)

calibLimitPattern = f"{rangePattern}([vthlsq][xy])"
calibLimitRegex = re.compile(calibLimitPattern)

cgcPattern = "(cit[01]|all)\s*,\s*(hg|lg|all)\s*,?\s*(.*)?"
cgcRegex = re.compile(cgcPattern)

singleChannelPattern = "ch(\d\d?)"
schRegex = re.compile(singleChannelPattern)

multChannelPattern = "ch(\d\d?)-ch(\d\d?)"
mchRegex = re.compile(multChannelPattern)

dataPattern = "\d+\s*"
dataRegex = re.compile(dataPattern)

calibPattern = "([vthlsqg]+)\s*,\s*([vthlsq])(adc)?\s*,\s*(.*)"
calibRegex = re.compile(calibPattern)

fitPattern = f"(\d)?([lpgnmrs])(?:{rangePattern})?(?:,|\/?([\d,.e+-]*)\/?)(n)?"
fitRegex = re.compile(fitPattern)

headerPattern = f"(v|t|hg|lg|s)\s*=\s*{pltr.numericPattern}\s*"
headerRegex = re.compile(headerPattern)

fileNameHeaderPattern = f"(?:{pltr.numericPattern}(mv|ns|hg|lg)-?|(ssh)(\d)-?)"
fNameHeadRegex = re.compile(fileNameHeaderPattern)

markSizePattern = f"{pltr.numericPattern}"
markSizeRegex = re.compile(markSizePattern)

errBarsPattern = "(none|sem|stddev)"
errBarsRegex = re.compile(errBarsPattern)

txtPosPattern = f"{pltr.numericPattern}\s*,\s*{pltr.numericPattern}"
txtPosRegex = re.compile(txtPosPattern)

def promptDir(prompt,select=True):
    startDir = os.getcwd()

    selOK = False
    while selOK is False:
        dirName = ''
        dirNames = []
    
        path = os.getcwd()
        
        directories = {str(i):[d.name,f"{path}\{d.name}"] for i,d in enumerate(dd for dd in os.scandir()
                       if dd.is_dir() is True)}
        
        if directories != {}:
            dirNames = np.asarray([*directories.values()])[:,0]
        
        print(prompt)
        
        for i,d in directories.items():
            print(f"{i}) {d[0]}")
    
        if select is False:
            return dirNames
    
        dirName = input("> ")
        
        if dirName == "exit":
            return dirName

        if dirName == "..":
            os.chdir(dirName)
            selOK = False
        elif dirName[0] == '*':
            dirName = dirName[1:]
            if dirName in dirNames:
                os.chdir(dirName)
            elif dirName in directories.keys():
                os.chdir(directories[dirName][1])
            else:
                raise OSError(f"Errore! {dirName} non è una directory!")
            selOK = False
        elif dirName == "\n":
            selOK = False
        else:
            selOK = True

    if (dirName not in dirNames and
        dirName not in directories.keys()):
        raise OSError(f"Errore! {dirName} non è una directory!")

    if dirName.isnumeric():
        dirName = directories[dirName][1]
    
    os.chdir(startDir)
    
    return f"{dirName}"

def fileParse(fileName):
    unitConv = {'mv':'v',
                'ns':'t',
                'hg':'h',
                'lg':'l',
                's':'s'}

    dataValues = []
    headerVals = {}
    
    skipHeader=3
    
    with open(fileName) as f:
        if (h0 := headerRegex.findall(f.readline())) != []:
            for hh in h0:
                headerVals[hh[0]] = float(hh[1])
        elif (h0 := fNameHeadRegex.findall(fileName)) != []:
            for hh in h0:
                if hh[1] != '':
                    headerVals[unitConv[hh[1]]] = float(hh[0])
                elif h0[2] != '':
                    headerVals[unitConv[hh[2]]] = float(hh[3])

            skipHeader = 2

        f.seek(0)
        for i,line in enumerate(f):
            evt = None
            if i > skipHeader:
                evt = dataRegex.findall(line)

            if evt is not None:
                data = [float(d) for d in evt]

                if len(data) > 0:
                    dataValues.append(data)

    return np.asarray(dataValues),headerVals

def analysisPrompt(anPromptDict,promptTxt='',exampleTxt=''):
    promptList = '\n'.join([f"\t{k}) {v[1]}" for k,v in anPromptDict.items()])
    
    if exampleTxt != '':
        exampleTxt += '\n'

    anPrompt = input(f"{promptTxt}\n{promptList}\n{exampleTxt}> ")
    
    params = apRegex.findall(anPrompt)
    
    if params is None:
        return

    params = {p[0]:p[1] for p in params}

    retDict = {}
    
    for k in anPromptDict.keys():
        if k in params.keys():
            aFunc = anPromptDict[k]
            
            aFRet = aFunc[-1](params[k])
            
            if type(aFRet) is not dict:
                retDict[aFunc[0]] = aFRet
            else:
                retDict.update(**aFRet)

    return retDict

def retVal(val):
    return val

def nBins(val):
    return float(val)

def limits(pStr,calib=False):
    retDict = {}

    pNoSpace = pStr.replace(' ','')
    pArr = pNoSpace.split(',')
    
    regx = limitRegex if calib is False else calibLimitRegex
    autoT = pltr.autoTypes if calib is False else pltr.calibAutoTypes

    autoLimStr = ('calib'*int(calib))+'autolim'

    for p in pArr:
        limitMatch = regx.match(p)

        if limitMatch is not None:
            grpLim = limitMatch.groups()
            if grpLim[1] is None:
                retDict.update({f'{grpLim[2]}lim':[0,float(grpLim[0])]})
            else:
                retDict.update({f'{grpLim[2]}lim':[float(grpLim[0]),float(grpLim[1])]})
        elif p in autoT:
            if autoLimStr not in retDict.keys():
                retDict.update({autoLimStr:p})
            else:
                retDict.update({autoLimStr:f"{retDict[autoLimStr]}{p}"})
        else:
            for a in autoT:
                if a in p:
                    if autoLimStr not in retDict.keys():
                        retDict.update({autoLimStr:a})
                    else:
                        retDict.update({autoLimStr:f"{retDict[autoLimStr]}{a}"})

    return retDict

def cgc(pStr,pedestals=False):
    cit = None
    gain = None
    channels = None

    pdstStr = "Pdst"

    chToAppend = set()

    pNoSpace = pStr.replace(' ','')
    
    cgcMatch = cgcRegex.match(pNoSpace)
    
    if cgcMatch is None:
        return

    cgcGroups = cgcMatch.groups()

    if cgcGroups is not None:
        cit = cgcGroups[0]
        gain = cgcGroups[1]
 
        if cgcGroups[2] == '':
            channels = {f"ch{n:02d}" for n in range(32)}

        if (sch := schRegex.findall(cgcGroups[2])) != []:
            channels = {f"ch{int(n):02d}" for n in sch}

        if (mch := mchRegex.findall(cgcGroups[2])) is not None:
            for m in mch:
                chToAppend.update({f"ch{n:02d}" 
                                  for n in range(int(m[0]),int(m[1])+1)})
    
    channels = list(channels.union(chToAppend))
    channels.sort()

    return {'cits'+pdstStr*int(pedestals):cit,
            'gains'+pdstStr*int(pedestals):gain,
            'channels'+pdstStr*int(pedestals):channels}

def pdst(pStr):
    acqPdst = cgc(pStr,True)

    if acqPdst is not None:
        return acqPdst
    elif pStr == "default":
        return pStr
    elif isfile(pStr):
        return pStr

    return None

def calibs(pStr):
    calibMatch = calibRegex.match(pStr)
    retDict = {}
    
    if calibMatch is not None:
        calibGroups = calibMatch.groups()
        calibParams = calibGroups[0]
        indipVar = calibGroups[1]
        adcOnX = calibGroups[2]
        limitsStr = calibGroups[3]
        
        limitsCalib = limits(limitsStr,True)
        
        adcIndip = (adcOnX == 'adc')
        
        retDict.update({'paramsToPlot':calibParams,
                        'indipVar':indipVar,
                        'invAxes':adcIndip})
        retDict.update(limitsCalib)

    return retDict

def fit(pStr):
    fitGroups = fitRegex.findall(pStr.replace(' ',''))
    
    retGroups = []
    for f in fitGroups:
        p = None
        if (numsInGuess := pltr.numericRegex.findall(f[-2])) != []:
            p = [float(pp) for pp in numsInGuess]

        retGroups.append((f[1],
                          *[float(n) if n != '' else None for n in [f[0],*f[2:-2]]],
                          p,
                          f[-1]))
    
    return retGroups

def marksize(pStr):
    marksGroups = markSizeRegex.findall(pStr.replace(' ',''))
    
    if marksGroups != []:
        return float(marksGroups[0])
    else:
        return 3.0

def errorbars(pStr):
    errBGroups = errBarsRegex.findall(pStr.replace(' ',''))
    
    if errBGroups != []:
        return errBGroups[0]
    else:
        return 'sem'

def txtpos(pStr):
    txtPosGroups = txtPosRegex.findall(pStr.replace(' ',''))
    
    if txtPosGroups != []:
        return (float(txtPosGroups[0][0]),
                float(txtPosGroups[0][1]))
    else:
        return 0.5,0.5

def getPedestalsDict(pdstFile):
    if isfile(pdstFile) is False:
        raise OSError(f"Errore! {pdstFile} non è un file!")

    with open(pdstFile) as pf:
        pdst = [int(p) for p in dataRegex.findall(pf.readline())]
        stdDev = [int(p) for p in dataRegex.findall(pf.readline())]
    
    return csl.makeCITDict(pdst,stdDev)

def removePedestals(meansDict,pdstDict):
    retDict = {'cit0':{f"ch{n:02d}":{'hg':{'mean':None,'stddev':None},
                                     'lg':{'mean':None,'stddev':None}} 
                       for n in range(32)},
               'cit1':{f"ch{n:02d}":{'hg':{'mean':None,'stddev':None},
                                     'lg':{'mean':None,'stddev':None} }
                       for n in range(32)},
               'nEvt':0}

    for c,cit in meansDict.items():
        for ch,gain in cit.items():
            for g,val in gain.items():
                retDict[c][ch][g]['mean'] = val['mean']-pdstDict[c][ch][g]['mean']
                retDict[c][ch][g]['stddev'] = np.sqrt(val['stddev']**2+
                                                      pdstDict[c][ch][g]['stddev']**2)
    
    retDict['nEvt'] = meansDict['nEvt']

    return retDict

def acquirePedestals(analysisParams,defPdstFile,newPedestals):
    ak = analysisParams.keys()
    citPdstOK = 'citsPdst' in ak
    gainPdstOK = 'gainsPdst' in ak

    if citPdstOK and gainPdstOK:
        retDict = getPedestalsDict(defPdstFile)

        citirocs = csl.argToList(analysisParams['citsPdst'],["cit0","cit1"])
        gains = csl.argToList(analysisParams['gainsPdst'],["hg","lg"])
        channels = csl.argToList(analysisParams['channelsPdst'],list(csl.chToNum.keys()))

        for c in citirocs:
            for g in gains:
                for ch in channels:
                    retDict[c][ch][g]['mean'] = newPedestals[c][ch][g]['mean']
                    retDict[c][ch][g]['stddev'] = newPedestals[c][ch][g]['stddev']

        with open(defPdstFile,'w') as f:
            cit0hgVals = [retDict['cit0'][f"ch{n:02d}"]['hg']['mean'] for n in range(32)]
            cit0lgVals = [retDict['cit0'][f"ch{n:02d}"]['lg']['mean'] for n in range(32)]
            cit1hgVals = [retDict['cit1'][f"ch{n:02d}"]['hg']['mean'] for n in range(32)]
            cit1lgVals = [retDict['cit1'][f"ch{n:02d}"]['lg']['mean'] for n in range(32)]

            cit0hgStd = [retDict['cit0'][f"ch{n:02d}"]['hg']['stddev'] for n in range(32)]
            cit0lgStd = [retDict['cit0'][f"ch{n:02d}"]['lg']['stddev'] for n in range(32)]
            cit1hgStd = [retDict['cit1'][f"ch{n:02d}"]['hg']['stddev'] for n in range(32)]
            cit1lgStd = [retDict['cit1'][f"ch{n:02d}"]['lg']['stddev'] for n in range(32)]

            values = [*cit0hgVals,*cit0lgVals,*cit1hgVals,*cit1lgVals]
            stddevs = [*cit0hgStd,*cit0lgStd,*cit1hgStd,*cit1lgStd]

            f.write(csl.fileChWrite(values))
            f.write(csl.fileChWrite(stddevs))
