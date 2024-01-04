# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 14:15:39 2021

@author: marco
"""

# -*- coding: utf-8 -*-

import serialeLib as sl
import sys
import time
import pulseGenLib as pgen
import triggerBoardLib as tbl
from citSupportLib import timeDataStr
import os
from multiprocessing import Process
from threading import Timer
import plotterLib as pltr
from collections import defaultdict
import analysisFunctions as af
#####debug
import spwLibCold as swc
#####

def main():
    ########################### PARAMETRI #########################################
    
    alimAddr = 'USB0::0x0957::0x0F07::MY53004295::0::INSTR'
    oscAddr = 'TCPIP0::jemeusohd06k.na.infn.it::inst0::INSTR'
    impAddr = 'TCPIP0::jemeusot3awg3k.na.infn.it::inst0::INSTR'
    
    spwConf = {'port': 'COM5',
               'baudrate': 115200,
               'timeout': 10,
               'parity': 'N',
               'stopbits': 2}
    
    debConf = {'port': 'COM6',
               'baudrate': 115200,
               'timeout': 10,
               'parity': 'N',
               'stopbits': 1}
    
    dacVal = 240
    
    startPedestalDAC = "1000"
    
    impFrequency = 20
    
    sleepTime = 1
    acqTime = 30
    
    pwrSide = "cold"
    
    pulseTrigCh = 2
    
    trigAmpl = 1200e-3
    trigWidth = 30e-9
    
    
    dataFrom ="debug"
    
    ###############################################################################

    analysisPromptDict = {'1' : ('plotType',"Tipologia di grafico",af.retVal),
                          '2' : ('limits',"Limiti degli assi",af.limits),
                          '3' : ('bins',"Larghezza bins",af.nBins),
                          '4' : ('cgc',"Citiroc, guadagno, canale",af.cgc),
                          '5' : ('pdst',"Rimozione piedistalli",af.pdst),
                          '6' : ('calib',"Parametri delle curve di calibrazione",af.calibs),
                          '7' : ('fit',"Parametri del fit",af.fit)}    

    anParamsDefault = {'plotType' : 'ebd',
                       'autolim'  : 'bydxdy',
                       'bins'     : 1,
                       'cits'     : acqCit,
                       'gains'    : 'all',
                       'channels' : [acqCh]}
    
    startDir = os.getcwd()

    defPedestalsFile = f"{startDir}\\defaultPedestals.dat"

    aT = input("Inserire il tempo di acquisizione (default 30s): ")
    if aT != '':
        acqTime = float(aT)

    tb = tbl.triggerBoard(alimAddr,spwConf,debConf)
    
    if usePulseGen:
        impSer = pgen.pulseGenerator(impAddr)

    tb.powerOn(pwrSide)
    time.sleep(1)
    
    tbCurr = float(tb.power.getCurr()[0][1:-1])*1e3
    print(f"Corrente assorbita: {tbCurr:.1f}mA")

    tb.powerOnCIT("cit0")
    time.sleep(1)
    tb.powerOnCIT("all")
    time.sleep(5)

    tb.initialize()

    print("inizializzo i piedistalli...")

    tb.pedestals = {'cit0': {'hg': startPedestalDAC,
                             'lg': startPedestalDAC},
                    'cit1': {'hg': startPedestalDAC,
                             'lg': startPedestalDAC}}

    print("inizializzo le soglie a 500")

    tb.thresholds = {'cit0' : {'charge' : 500,
                               'time'   : 500},
                     'cit1' : {'charge' : 500,
                               'time'   : 500}}

    print("abilito il peak detector")

    tb.peakDetector = {'cit0' : {'hg' : True,
                                 'lg' : True},
                       'cit1' : {'hg' : True,
                                 'lg' : True}}

    print("imposto holdDelay a 32")

    tb.holdDelay = {'cit0' : 32,
                    'cit1' : 32}
    
    print("Imposto Tshaper a 0")
    
    tb.tConstShaper = {'cit0' : {'hg' : 0,
                                 'lg' : 0},
                       'cit1' : {'hg' : 0,
                                 'lg' : 0}} 
    
    print("imposto il trigger esterno")
    
    swc.changeConfigVal(tb.slowCtrl,"SEL_TRIG_EXT_PSC",1,"all")
    swc.changeConfigVal(tb.slowCtrl,"EN_VAL_EVT",1,"all")

    print("azzero i guadagni")

    tb.gains = {'cit0' : {f"ch{i:02d}" : {'hg'      : 9.524,
                                          'lg'      : 0.952,
                                          'inCalib' : None,
                                          'enabled' : True}
                          for i in range(32)},
                'cit1' : {f"ch{i:02d}" : {'hg'      : 9.524,
                                          'lg'      : 0.952,
                                          'inCalib' : None,
                                          'enabled' : True}
                          for i in range(32)}}

    print("imposto il fast shaper su HG")

    tb.fastShaperOn = {'cit0' : 'hg',
                       'cit1' : 'hg'}

    tb.configure()

    enableExtTrg = 1 << 10  # (00000400 abilita il trigger esterno)

    trgMask = int('00000000',16) | enableExtTrg

    tb.triggerMask = f"{trgMask:08x}"
    
    tb.pmtMask = {'cit0' : "FFFFFFFF",
                  'cit1' : "FFFFFFFF"}

    tb.configure()

    tbCurr = float(tb.power.getCurr()[0][1:-1])*1e3

    pros = input(f"Corrente assorbita: {tbCurr:.1f}mA, proseguire? (S/n) ")
    if pros != 'n':

        dirNameOk = False
        while dirNameOk is False:
            prefixName = input("Inserire il nome della cartella "
                           "in cui salvare i file: ")
        
            for d in os.scandir():
                if d.name == prefixName and d.is_dir():
                    prefixName = input(f"La cartella '{d.name}' esiste già"
                                    " scegliere un altro nome: ")
                else:
                    dirNameOk = True
        
        os.mkdir(prefixName)
        os.chdir(prefixName)
    
        anParams = af.analysisPrompt(analysisPromptDict,
                                     "Scegliere i parametri per l'analisi"
                                     " preliminare dei dati (invio per usare"
                                     " i parametri di default):",
                                     "ES.\n1:ebd 2:100bx,100-300by,dx 3:200"
                                     " 4:cit0,all,ch00,ch01,ch11-ch13")
        
        if anParams == {}:
            anParams = anParamsDefault

        pdstDict = None
        if 'pdst' in anParams.keys():
            if anParams['pdst'] == 'default':
                pdstDict = af.getPedestalsDict(defPedestalsFile)
            else:
                pdstDict = af.getPedestalsDict(f"{anParams['pdst']}")

        print(f"Imposto le soglie al valore {dacVal}")
        tb.thresholds = {'cit0' : {'time'   : dacVal,
                                   'charge' : dacVal},
                         'cit1' : {'time'   : dacVal,
                                   'charge' : dacVal}}

        tb.configure()

        print("Soglie configurate")
        time.sleep(5)

        print("Abilito l'acquisizione")
        tb.startAcq()

        meansPerV = defaultdict(list)
        meansPerT = defaultdict(list)
        meansPerHG = defaultdict(list)
        meansPerLG = defaultdict(list)
        meansPerShap = defaultdict(list)

        print("Applico l'impulso...")
                
        impSer.configurePulse(pulseTrigCh,trigAmpl,0,trigWidth,2e-9,2e-9,impFrequency)
        
        impSer.turnOnChannel(pulseTrigCh)

        impSer.startPulseGenerator()
    
        print(f"Imposto preamp_config{acqCh} HG={paramList['hg'][i][0][0]}"
              f" LG={paramList['lg'][i][0][0]}")
        tb.gains = {acqCit:{acqCh:{'hg':paramList['hg'][i][0][0],
                                   'lg':paramList['lg'][i][0][0]}}}
    
        tb.configure()
            
        header = (f"{pmVStr} "
                  f"{pnsStr} "
                  f"hg={paramList['hg'][i][0][0]} "
                  f"lg={paramList['lg'][i][0][0]} "
                  f"{shapStr}")
            
            processes = []
            if prefixName != "test":
                fDir = os.getcwd()
                os.mkdir(f)
                os.chdir(f)

                if (dataFrom == "slowCtrl") and usePulseGen:
                    print("Avvio il timer")
                    tim = Timer(acqTime,
                                impSer.stopPulseGenerator)
                    tim.start()

                print("Eliminazione dati residui nella fifo...")
                while tb.debug.in_waiting > 0:
                    tb.debug.read(tb.debug.in_waiting)
                    tb.debug.reset_input_buffer()
                    tb.debug.reset_output_buffer()
                time.sleep(sleepTime)   # aspetta prima di avviare l'acquisizione per essere
                                        # sicuri che l'impulsatore finisca di impostare l'output

                tb.saveData(acqTime,f"{f}-t{timeDataStr}",fileHeader=header,dataFrom=dataFrom)

                print("Eliminazione dati residui nella fifo...")
                while tb.debug.in_waiting > 0:
                    tb.debug.read(tb.debug.in_waiting)
                    tb.debug.reset_input_buffer()
                    tb.debug.reset_output_buffer()

                citDict = tb.lastResults
                meansDict = tb.lastMeans
                
                af.acquirePedestals(anParams,defPedestalsFile,meansDict)

                anParams.update({'directory':os.getcwd()})

                plotter = Process(target = pltr.plotData,
                                  name = f"{f}",
                                  args = (f"plot-{f}",citDict,meansDict),
                                  kwargs = anParams)
                plotter.start()
                processes.append(plotter)
                
                if usePulseGen:
                    pltr.meansPerParams(i,'mv',paramList,meansDict,meansPerV,header=False)
                    pltr.meansPerParams(i,'ns',paramList,meansDict,meansPerT,header=False)
                pltr.meansPerParams(i,'hg',paramList,meansDict,meansPerHG,header=False)
                pltr.meansPerParams(i,'lg',paramList,meansDict,meansPerLG,header=False)
                if 'a' in paramList.keys() and paramList['a'][0] is not None:
                    pltr.meansPerParams(i,'a',paramList,meansDict,meansPerShap,header=False)

                os.chdir(fDir)

            tb.syncTBRegisters(f+"postACQ",citBinaryValues=True)
            
            if usePulseGen:
                impSer.turnOffChannel("ch1")
    
        if usePulseGen:
            impSer.turnOffChannel("ch2")

        if usePulseGen:
            impSer.stopPulseGenerator()
        
        if dataFrom == "slowCtrl" and usePulseGen:
            tim.cancel()

        if usePulseGen:
            impSer.close()
            calibParPulse = {'v':meansPerV,
                             't':meansPerT,
                             'h':meansPerHG,
                             'l':meansPerLG,
                             's':meansPerShap}
        else:
            calibParPulse = {'h':meansPerHG,
                             'l':meansPerLG,
                             's':meansPerShap}            

        if calibCurvesDir is not None:
            print("Realizzo le curve di calibrazione")
            if not os.path.exists(calibCurvesDir):
                os.mkdir(calibCurvesDir)
            pltr.plotData(f"{prefixName}-",
                          citDict,None,"c",
                          acqCit,"all",acqCh,
                          directory=calibCurvesDir,
                          calibparams=calibParPulse,
                          indipVar="t")

        print("Fermo l'acquisizione")
        tb.stopAcq()

        time.sleep(2)
    
        print("Spengo la scheda")
        tb.powerOff()

        tb.close()
        
        for p in processes:
            print(f"Attendo la fine del processo {p.name}")
            p.join()
        
        os.chdir(startDir)

        time.sleep(2)



if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Errore: {e}")
        if usePulseGen:
            impSer.close()
        tb.close()
        os.chdir(startDir)
        sys.exit(e)