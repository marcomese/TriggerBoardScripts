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
import oscLib as ol
from regNameRegs import regNameRegs as tbRegs
import alimLib as alim

def main(channel):
    ########################### PARAMETRI #########################################
    
    alimAddr = 'USB0::0x0957::0x0F07::MY53004295::0::INSTR'
    oscAddr = 'TCPIP0::jemeusohd06k.na.infn.it::inst0::INSTR'
    impAddr = 'TCPIP0::jemeusot3awg3k.na.infn.it::inst0::INSTR'
    
    dpcuEmulatorAddr = '172.16.1.2'
    
    acqCit = ["cit0"]#,"cit1"]
    acqCh = [channel]#["ch00"]#f"ch{d:02d}" for d in range(32)]#,"ch01","ch02","ch03","ch06","ch07","ch08"]#,"ch01","ch02"]

    citConf = {
        'ch00': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch01': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch02': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch03': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch04': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch05': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch06': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch07': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch08': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch09': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch10': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch11': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch12': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch13': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch14': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch15': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch16': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch17': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch18': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch19': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch20': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch21': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch22': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch23': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch24': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch25': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch26': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch27': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch28': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch29': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch30': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
        'ch31': {'hg': 20.0, 'lg': 2.0, 'inCalib': None, 'enabled': True},
    }
    
    dacVal = 210
    
    impFrequency = 20
    
    sleepTime = 1
    acqTime = 600
    
    # dacPedestalCIT0 = "32C83000"
    # dacPedestalCIT1 = "30003000"
    
    dacPedestalCIT0 = "317E31C6" # pedestals for SN05
    dacPedestalCIT1 = "31003100"
    
    shapingT = 50
    
    calibCurvesDir = "calibCurves"
    
    doublePulseCh2 = False
    
    pulseTrigCh = 1
    pulseAcqCh = 2

    trigAmpl = 3000e-3
    trigWidth = 30e-9
    
    usePulseGen = True
    
    triggerMask = "0400 0000"
    genericTriggerMask = "0000 0000"
    
    cit0PMTMask = "FFFF FFFF"
    cit1PMTMask = "FFFF FFFF"
    
    pulseType = "square"
    
    expDecayFreq = 3e6
    
    dataFrom = "debug"
    
    powerDataLog = False
    pwrDataLogFileName = "pwrTest061023"
    
    prescalerFactors = {0 : 1,
                        1 : 1,
                        2 : 1,
                        3 : 1}
    
    ###############################################################################
    
    triggerMask = triggerMask.replace(' ','')
    genericTriggerMask = genericTriggerMask.replace(' ','')
    
    useGenericTriggerMask = genericTriggerMask != "00000000"
    
    cit0PMTMask = cit0PMTMask.replace(' ','')
    cit1PMTMask = cit1PMTMask.replace(' ','')
    
    timeFile = open("pwrTiming.dat",'w')
    
    osc = None#ol.oscilloscope(oscAddr)
    
    if osc is None:
        print("Errore: impossibile collegarsi all'oscilloscopio!")
    
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
    
    aT = input(f"Inserire il numero di eventi da acquisire (default {acqTime}): ")
    if aT != '':
        acqTime = float(aT)
    
    tbAlim = alim.triggerBoardAlim(alimAddr)
    
    if powerDataLog is True:
        tbAlim.dataLogStart(pwrDataLogFileName,time=90,channel=2)
    
    start = time.perf_counter()
    
    time.sleep(1)
    
    tbAlim.powerOnChannel(2)
    
    stop = time.perf_counter()
    
    timeFile.write(f"power on = {stop-start}\n")
    
    tb = tbl.triggerBoard(alimAddr,dpcuEmulatorAddr)
    
    if usePulseGen:
        print("Collegamento all'impulsatore...")
        impSer = pgen.pulseGenerator(impAddr)
    
    if not powerDataLog:
        tbCurr = tb.power.getCurr()[0].split(',')
        print(f"Corrente assorbita: \n\tDPCU = {tbCurr[0]}A\n\tTRG = {tbCurr[1]}A")
    
    tb.powerOnCIT("cit0")
    
    stop = time.perf_counter()
    
    timeFile.write(f"cit0 On = {stop-start}\n")
    
    time.sleep(1)
    
    tb.powerOnCIT("cit1")
    
    stop = time.perf_counter()
    
    timeFile.write(f"all cit On = {stop-start}\n")
    
    time.sleep(1)
    
    tb.initialize()
    
    print("inizializzo i dac in ingresso...")
    
    tb.slowCtrl.changeConfigVal("DAC_REF", 0)
    tb.slowCtrl.changeConfigVal("EN_TEMP", 0)
    
    print("inizializzo i piedistalli...")
    
    tb.pedestals = {'cit0': {'hg': dacPedestalCIT0[:4],
                             'lg': dacPedestalCIT0[4:]},
                    'cit1': {'hg': dacPedestalCIT1[:4],
                             'lg': dacPedestalCIT1[4:]}}
    
    print("inizializzo le soglie a 500")
    
    tb.thresholds = {'charge' : 500,
                     'time'   : 500}
    
    
    print("imposto holdDelay a 32")
    
    tb.holdDelay = 32
    
    print("Imposto Tshaper a 0")
    
    tb.tConstShaper = {'hg' : shapingT,
                       'lg' : shapingT}
    
    print("imposto il fast shaper su HG")
    
    tb.gains = citConf
    
    tb.fastShaperOn = 'hg'

    tb.configure()
    
    stop = time.perf_counter()
    
    timeFile.write(f"configured1 = {stop-start}\n")

    print("Imposto le PMT mask")
    tb.pmtMask = {'cit0' : cit0PMTMask,
                  'cit1' : cit1PMTMask}

    print(f"imposto la maschera di trigger {triggerMask}")
    
    tb.triggerMask = triggerMask
    if useGenericTriggerMask is True:
        print(f"imposto la generic trigger mask {genericTriggerMask}")
        tb.genericTriggerMask = genericTriggerMask
    
    tb.configure()
    
    stop = time.perf_counter()
    
    timeFile.write(f"configured2 = {stop-start}\n")
    
    pros = 's'
    if not powerDataLog:
        tbCurr = tb.power.getCurr()[0].split(',')
        tbCurrStr = f"Corrente assorbita: \n\tDPCU = {tbCurr[0]}A\n\tTRG = {tbCurr[1]}A\n"
        pros = input(f"{tbCurrStr}, proseguire? (S/n) ") or 's'
    else:
        tbCurrStr = "Data Logger in funzione..."
    
    if pros == 's':
    
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
    
        params = sl.paramsPrompt("Inserire parametri da variare durante l'acquisizione (o i singoli parametri nel caso di una sola acquisizione)"
                              " SEPARATI DA VIRGOLA.\nSe non viene specificata l'unità di misura si assume che il parametro sia in mV."
                              "ES.\nvariare ampiezza impulsi con durata di 30ns ->30mV,40mV,50mV,30ns oppure variare guadagni ->10g,100g,1000g\n"
                              "\nSe si usa l'ingresso in_calib bisogna impostare i guadagni nel seguente modo:\n"
                              "\t<num>tg per impostare a num il valore del guadagno di HG\n"
                              "\t<num>cg per importare a num il valore del guadagno di LG\n"
                              "ES.\n"
                              "30,30ns,10tg,1cg\n>")
    
        fileNames, paramStrings, paramList = sl.genFileNameList(prefixName,
                                                                params['mv'],
                                                                params['ns'],
                                                                params['g'],
                                                                params['b'],
                                                                params['d'],
                                                                params['a'],
                                                                params['p'])
    
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
        tb.thresholds = {'time'   : dacVal,
                         'charge' : dacVal}

        for k,v in prescalerFactors.items():
            tb.slowCtrl.selectPrescaler(k,v)

        tb.configure()
    
        stop = time.perf_counter()
        
        timeFile.write(f"configured3 = {stop-start}\n")
    
        print("Soglie configurate")
        time.sleep(1)
    
        if usePulseGen:
            meansPerV = defaultdict(list)
            meansPerT = defaultdict(list)
        meansPerHG = defaultdict(list)
        meansPerLG = defaultdict(list)
        meansPerShap = defaultdict(list)
        for i,f in enumerate(fileNames):
            
            if usePulseGen:
                print("Applico l'impulso...")
                
                couplePhase = True
                phase = [0, 0]
                if paramList['p'].count(None) != len(paramList['p']):
                    couplePhase = False

                    ph = paramList['p'][i][0]

                    phaseIdx = 0 if ph > 0 else 1
                    
                    phase[phaseIdx] = abs(ph)
                    
                
                if pulseType == "square":
                    impSer.configurePulse(pulseAcqCh,paramList['mv'][i][0]*1e-3,0,
                                          paramList['ns'][i][0]*1e-9,2e-9,2e-9,
                                          impFrequency,phase=phase)
                else:
                    impSer.configureExpDecay(pulseAcqCh, paramList['mv'][i][0]*1e-3, expDecayFreq, impFrequency)
    
                vocm = 0.5 if doublePulseCh2 is False else 0
        
                if pulseType == "square":
                    impSer.configurePulse(pulseTrigCh,trigAmpl,0,trigWidth,2e-9,2e-9,impFrequency,
                                          double=doublePulseCh2,vocm=vocm,phase=phase)
                    
                    if couplePhase is True:
                        impSer.coupleToChannel1("phase")
                    
                else:
                    impSer.configurePulse(pulseTrigCh,trigAmpl,0,trigWidth,2e-9,2e-9,impFrequency,
                                          double=doublePulseCh2,vocm=vocm,
                                          burst=True)
        
                impSer.turnOnChannel("all")
        
                impSer.startPulseGenerator()

                stop = time.perf_counter()
    
                timeFile.write(f"startPulse{i} = {stop-start}\n")

            for ach in acqCh:
                pInCalib = None

                if 'hg' in paramList.keys() and paramList['hg'][i] is not None:
                    hgConf = paramList['hg'][i][0][0]
                    
                    if pInCalib is None:
                        pInCalib = 'hg' if paramList['hg'][i][0][1] == 't' else None
                else:
                    hgConf = citConf[ach]['hg']
                    pInCalib = citConf[ach]['inCalib']
                    paramList['hg'][i] = [[hgConf,'h']]

                if 'lg' in paramList.keys() and paramList['lg'][i] is not None:
                    lgConf = paramList['lg'][i][0][0]
                    
                    if pInCalib is None:
                        pInCalib = 'lg' if paramList['lg'][i][0][1] == 'c' else None
                else:
                    lgConf = citConf[ach]['lg']
                    pInCalib = citConf[ach]['inCalib']
                    paramList['lg'][i] = [[lgConf,'l']]

                print(f"Imposto preamp_config{acqCh} HG={hgConf}"
                      f" LG={lgConf}")
                tb.gains = {ach:{'hg':hgConf,
                                 'lg':lgConf,
                                 'inCalib':pInCalib}}
    
            # shapStr = ''
            # if 'a' in paramList.keys() and paramList['a'][0] is not None:
            #     shapTConst = int(paramList['a'][i][0])
            #     shapStr = f"s={paramList['a'][i][0]}"
            #     tb.tConstShaper = {'cit0' : {'hg' : shapTConst,
            #                                  'lg' : shapTConst},
            #                        'cit1' : {'hg' : shapTConst,
            #                                  'lg' : shapTConst}}
            # else:
            #     tb.tConstShaper = {'cit0' : {'hg' : 3,
            #                                  'lg' : 5},
            #                        'cit1' : {'hg' : 3,
            #                                  'lg' : 5}}
    
            print("Configuro i CITIROC")
            tb.configure()
            
            stop = time.perf_counter()
    
            timeFile.write(f"configured4 = {stop-start}\n")
            
            pmVStr = f"v={paramList['mv'][i][0]} " if usePulseGen else ''
            pnsStr = f"t={paramList['ns'][i][0]} " if usePulseGen else ''
            hgStr = f"hg={paramList['hg'][i][0][0]} " if paramList['hg'][i] is not None else ''
            lgStr = f"lg={paramList['lg'][i][0][0]} " if paramList['lg'][i] is not None else ''
            shapStr = f"shapT={shapingT}ns"
            
            header = (f"{pmVStr}"
                      f"{pnsStr}"
                      f"{hgStr}"
                      f"{lgStr}"
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
    
                time.sleep(sleepTime)   # aspetta prima di avviare l'acquisizione per essere
                                        # sicuri che l'impulsatore finisca di impostare l'output
    
                if osc is not None:
                    osc.trgNormal()
                    osc.clearSweeps()
                    osc.clearMeasurements()
                    osc.setMeasure(1, 1, 'max')
    
                print("Reset dei registri")
                tb.slowCtrl.flushRegisters()
    
                print("Abilito l'acquisizione")
                tb.startAcq()
    
                # print("Avvio l'acquisizione della DPCU")
                # tb.slowCtrl.startDPCURun()
                
                stop = time.perf_counter()
    
                timeFile.write(f"startAcq = {stop-start}\n")
                
    
                tb.saveData(acqTime,f"{f}-t{timeDataStr}",
                            fileHeader=header)
    
                print("Fermo l'acquisizione DPCU")
                tb.slowCtrl.stopDPCURun()
                
                print("Fermo l'acquisizione TB")
                tb.stopAcq()

                print("Acquisizione arrestata!")

                stop = time.perf_counter()
    
                timeFile.write(f"stopAcq = {stop-start}\n")
    
                print("Sincronizzo i registri...")
    
                tb.syncTBRegisters("TBRegisters")
    
                if osc is not None:
                    osc.trgStop()
    
                citDict = tb.lastResults
                meansDict = tb.lastMeans
                
                # af.acquirePedestals(anParams,defPedestalsFile,meansDict)
    
                anParams.update({'directory':os.getcwd()})
    
                print("avvio processo plotter")
    
                plotter = Process(target = pltr.plotData,
                                  name = f"{f}",
                                  args = (f"plot-{f}",citDict,meansDict),
                                  kwargs = anParams)
                plotter.start()
                processes.append(plotter)
                
                print("processo avviato")
                
                if usePulseGen:
                    pltr.meansPerParams(i,'mv',paramList,meansDict,meansPerV,header=False)
                    pltr.meansPerParams(i,'ns',paramList,meansDict,meansPerT,header=False)
                pltr.meansPerParams(i,'hg',paramList,meansDict,meansPerHG,header=False)
                pltr.meansPerParams(i,'lg',paramList,meansDict,meansPerLG,header=False)
                if 'a' in paramList.keys() and paramList['a'][0] is not None:
                    pltr.meansPerParams(i,'a',paramList,meansDict,meansPerShap,header=False)
    
                os.chdir(fDir)
                
            if osc is not None:
                with open("oscRes.dat",'w') as oscFile:
                    print(f"V = {osc.getMeasure(1,'mean')}\n"
                          f"stdV = {osc.getMeasure(1, 'sdev')}\n"
                          f"num = {osc.getMeasure(1, 'num')}\n")
                    oscFile.write(f"{osc.getMeasure(1,'mean')},{osc.getMeasure(1,'sdev')},{osc.getMeasure(1, 'num')}\n")
    
            # tb.syncTBRegisters(f+"postACQ",citBinaryValues=True)
            
            if usePulseGen:
                impSer.turnOffChannel("ch1")
    
        if usePulseGen:
            impSer.turnOffChannel("ch2")
    
        if usePulseGen:
            impSer.stopPulseGenerator()

        stop = time.perf_counter()

        timeFile.write(f"stopPulse = {stop-start}\n")

        # if dataFrom == "slowCtrl" and usePulseGen:
        #     tim.cancel()
    
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
    
        time.sleep(1)
    
        print("Spengo la scheda")
        tb.powerOff(2)

        stop = time.perf_counter()

        timeFile.write(f"powerOffTB = {stop-start}\n")

        if powerDataLog is True:
            print("Attendo la fine del log degli assorbimenti...")
            time.sleep(30)
            tb.power.exportLoggedData(pwrDataLogFileName)
            print("Aspetto che il file venga esportato in csv...")
            time.sleep(90)
            tb.power.getLoggedData(pwrDataLogFileName)
    
        tb.close()
        
        if osc is not None:
            osc.close()
        
        for p in processes:
            print(f"Attendo la fine del processo {p.name}")
            p.join()
        
        os.chdir(startDir)
    
        time.sleep(2)
    
        timeFile.close()

if __name__ == '__main__':
    try:
        channels = ["ch00","ch01","ch02"]
        
        for c in channels:
            main(c)
    except Exception as e:
        print(f"Errore: {e}")
        sys.exit(e)