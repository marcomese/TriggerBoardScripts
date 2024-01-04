# -*- coding: utf-8 -*-
"""
Created on Mon Jul  5 09:59:31 2021

@author: Wizard
"""

import os
import re
import numpy as np
from io import StringIO
import analysisFunctions as af
from multiprocessing import Process
import plotterLib as pltr
import citSupportLib as csl
from collections import defaultdict

analysisPromptDict = {'1'  : ('plotType',"Tipologia di grafico",af.retVal),
                      '2'  : ('limits',"Limiti degli assi",af.limits),
                      '3'  : ('bins',"Larghezza bins",af.nBins),
                      '4'  : ('cgc',"Citiroc, guadagno, canale",af.cgc),
                      '5'  : ('pdst',"Piedistalli",af.pdst),
                      '6'  : ('calib',"Curve di calibrazione",af.calibs),
                      '7'  : ('fit',"Parametri del fit",af.fit),
                      '8'  : ('markersize',"Markersize",af.marksize),
                      '9'  : ('errorbars',"Barre di errore",af.errorbars),
                      '10' : ('txtpos',"Posiione casella di testo",af.txtpos)}

# def main():
mainDir = os.getcwd()

dirName = af.promptDir("Selezionare la directory da analizzare: ")

os.chdir(dirName)

dataDirs = af.promptDir(f"Contenuto della directory {dirName}:", False)

regexIn = input("Applica regex per filtrare "
                "le acquisizioni (invio per selezionarle tutte): ")

regex = None
if regexIn != '':
    regex = re.compile(regexIn)

anParams = af.analysisPrompt(analysisPromptDict,
                             "Scegliere:",
                             "Es.: 1:ebd 2:100bx,100-300by,dx 3:200"
                             " 4:cit0,all,ch00,ch01,ch11-ch13")

pdstDict = None
# if 'pdst' in anParams.keys():
#     if anParams['pdst'] == 'default':
#         pdstDict = af.getPedestalsDict(f"{mainDir}\\defaultPedestals.dat")
#     else:
#         pdstDict = af.getPedestalsDict(f"{anParams['pdst']}")

dataValues = {}
meanValues = {}
relValues = {}
dataOverPdst = {}
meansPer = defaultdict(dict)
for d in dataDirs:
    startDir = os.getcwd()

    if regex != None and regex.search(d) is None:
        continue

    print(f"Analizzo {d}")

    os.chdir(d)

    i = 0
    for f in os.scandir():
        if f.name[:5] == "table":
            tableFileName = f.name

            parsedData,header = af.fileParse(tableFileName)

            keyName = tableFileName.split('--')[0].split('table-')[1]

            dataValues[keyName] = csl.makeCITDict(parsedData[:-2].T, rec=True)
            
            nEvents = dataValues[keyName]['nEvt']
            
            if pdstDict is None:
                meanValues[keyName] = csl.makeCITDict(parsedData[-2],
                                                      stdDev=parsedData[-1],
                                                      nevtMeans=nEvents)
            else:
                meanValues[keyName] = csl.getMeansOverPdst(dataValues[keyName],
                                                           pdstDict,
                                                           nEvents)

            if 'paramsToPlot' in anParams.keys():
                for k in anParams['paramsToPlot']:
                    pltr.meansPerParams(i,k,header,
                                        meanValues[keyName],meansPer[k])

            # if pdstDict is not None:
            #     relValues[keyName] = af.removePedestals(meanValues[keyName],pdstDict)

            i += 1

    os.chdir(startDir)

analysStr = f"analisi-{csl.timeDataStr}"

os.mkdir(analysStr)
os.chdir(analysStr)

plotTypeOK = 'plotType' in anParams.keys()
calibPlotOK = False
otherPlotsOK = False
if plotTypeOK:
    calibPlotOK = 'c' in anParams['plotType']

    otherPlotsOK = ('e' in anParams['plotType'] or
                    'b' in anParams['plotType'] or
                    'd' in anParams['plotType'])

processes = []    
if otherPlotsOK:
    for f,d in dataValues.items():
        print(f"Realizzo i grafici per {f}")

        sDir = os.getcwd()
        os.mkdir(f)
        os.chdir(f)

        anParams.update({'directory':os.getcwd()})
        
        values = meanValues[f] #if pdstDict is None else relValues[f]
    
        # plotter = Process(target = pltr.plotData,
        #                   name = f"{f}",
        #                   args = (f"plot-{f}",d,values),
        #                   kwargs = anParams)
        # plotter.start()
        # processes.append(plotter)
        
        pltr.plotData(f"plot-{f}",d,values,**anParams)
        
        os.chdir(sDir)

if calibPlotOK:
    print("Realizzo le curve di calibrazione")
    
    if not os.path.exists("calibCurves"):
        os.mkdir("calibCurves")
    
    anParams.update({'plotType':'c'})
    anParams.update({'directory':"calibCurves"})
    anParams.update({'calibparams':meansPer})
    
    pltr.plotData(f"{dirName}-",
                  None,None,
                  **anParams)

os.chdir(startDir)
os.chdir(mainDir)

# for p in processes:
#     print(f"Attendo la fine del processo {p.name}")
#     p.join()

# if __name__ == '__main__':
#     try:
#         main()
#     except OSError as e:
#         print(e)
#     finally:
#         input("Premere un tasto per continuare...")