# -*- coding: utf-8 -*-

import analisiLib as al
import numpy as np
import os
import sys
import re

startDir = os.getcwd()

fileSelected = al.selectFilePrompt()

floatPattern = "\d+(?:.\d+)?"

gainsPattern = f"CIT(\d)CH(\d\d)-({floatPattern})(HG)-({floatPattern})(LG),?"

gainsRegex = re.compile(gainsPattern)

try:
    if al.EXIT_FROM_PROMPT not in fileSelected:
        
        citiroc,gain,channel = al.plotPrompt()
        
        for f in fileSelected:
            
            resDirName = al.resDirHead+f[:f.find(al.fNameHead)]
            
            numEvt,startWord,stopWord,startPos,stopPos,paramString = al.getDataFromLog(f)
            
            gainsUsed = gainsRegex.findall(paramString)
            
            cit0hgDict = {g[1] : float(g[2]) for g in gainsUsed if g[0] == '0'}
            cit0lgDict = {g[1] : float(g[4]) for g in gainsUsed if g[0] == '0'}
            cit1hgDict = {g[1] : float(g[2]) for g in gainsUsed if g[0] == '1'}
            cit1lgDict = {g[1] : float(g[4]) for g in gainsUsed if g[0] == '1'}
            
            gainsDict = {
                    "CIT0" : {"HG" : cit0hgDict, "LG" : cit0lgDict},
                    "CIT1" : {"HG" : cit1hgDict, "LG" : cit1lgDict}
                    }
            
            DACSBinaryVal, countersBinaryVal = al.getDACSVal(f, numEvt,
                                                             startWord,
                                                             stopWord,
                                                             startPos,
                                                             stopPos)
            
            CIT = np.chararray(shape = (2,2,32,numEvt), itemsize = 12)
            intCIT = np.ndarray(shape = (2,2,32,numEvt), dtype = int)
            avgCIT = np.ndarray(shape = (2,2,32), dtype = float)
            avgErrCIT = np.ndarray(shape = (2,2,32), dtype = float)
            
            print("\nAttendere... Lettura valori per {}...".format(f))
            
            for k,D in enumerate(DACSBinaryVal):
                sys.stdout.write("\rLettura evento "+str(k))
                sys.stdout.flush()

                al.spanCIT(al.makeCITArray,
                           nEVT = k,
                           Data = D,
                           outCIT = CIT,
                           outIntCIT = intCIT)

            al.spanCIT(al.saveDataFile,fileSel = f,\
                       stDir = startDir, resDir = resDirName, intCIT = intCIT)

            histParams = {
#                    'histUnits' : 'pe',
##                    'xlim' : (0,2500),
##                    'ylim' : (0,2000),
#                    'xpass' : 500,
#                    'ypass' : 500,
#                    'binsWidth' : 1,
#                    'gaussFIT' : False,
#                    'fitRange' : (0,2500),
#                    'color' : 'red',
#                    'multiGaussFit' : False,
##                    'ylog' : True
                    
#                     'histUnits' : 'pc',
#                     'xlim' : (0,80),
#                     'ylim' : (0,5000),
#                     'xpass' : 5,
#                     'ypass' : 500,
#                     'binsWidth' : 1,
#                     'gaussFIT' : False,
#                     'fitRange' : (0,400),
#                     'color' : 'red',
#                     'multiGaussFit' : False,
# #                    'ylog' : True

#                    'xlim' : (0,4000),
#                    'xlim' : (0,200),
#                    'ylim' : (0,100),
#                    'xpass' : 500,
#                    'ypass' : 5,
                    'binsWidth' : 5,
                    'gaussFIT' : True,
                    'fitRange' : (0,4100),
                    'color' : 'red',
                    'multiGaussFit' : False,
                    'xlog' : False,
                    'ylog' : False
                    }

            al.savePlot(startDir,resDirName,CIT,citiroc,
                        gain,channel,numEvt,gainsDict,
                        evtPass=10)#,
#                        histParams=histParams)
#                        gaussFitGuess = [100,50,10])
#                        multiGaussFitGuess = [200,200,10,
#                                              200,280,10,
#                                              100,320,10])

            al.spanCIT(al.saveMeansFile,
                       fileSel = f,
                       stDir = startDir, resDir = resDirName,
                       parStr = paramString, intCIT = intCIT, outAvg = avgCIT,
                       outAvgErr = avgErrCIT, numEvt = numEvt)
        
except Exception as e:
    os.chdir(startDir)
    sys.exit(e)
except IOError as e:
    os.chdir(startDir)
    sys.exit("Errore nella creazione dei file {}!".format(e))
except FileNotFoundError as e:
    sys.exit("File {} non trovato!".format(e))
