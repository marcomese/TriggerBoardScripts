# -*- coding: utf-8 -*-

import serialeLib as sl
import serial
import sys
import time
from regNameRegs import regNameRegs as regs
import alimLib as alm
from collections import defaultdict
import pulseGenLib as pgen

########################### PARAMETRI #########################################

alimAddr = 'USB0::0x0957::0x0F07::MY53004295::0::INSTR'

trigCit = "cit1"
cit = "cit0"

ch = "02"

dacVal = 225

holdDelay = 32

trgMsk = 0

outINV = False

peakDetectorON = True

impFrequency = 20

inCalibHG = False
inCalibLG = False

useProbe = False
probeReg = "OUTPAHG_CIT1_ADDR"
probeVal = "08000000"

sleepTime = 1

dacPedestalCIT0 = "17E617AB"
dacPedestalCIT1 = "132718A3"

#dacPedestalCIT0 = "19901945"
#dacPedestalCIT1 = "19571930"

#dacPedestalCIT0 = "147A1999"
#dacPedestalCIT1 = "1EB723D6"

pwrLogFileName = "acqTB2"

comConf = {
        'comPort' : 'COM5',
        'baudRate' : '115200',
        'acqTime' : '30'
        }

pwrSide = "cold"

###############################################################################

if pwrSide == "cold":
    import spwLibCold as sw
else:
    import spwLib as sw

impAddr = 'TCPIP0::jemeusot3awg3k::inst0::INSTR'

confParameters = {
        "cit" : cit,
        "ch" : ch,
        "dacVal" : dacVal,
        "holdDelay" : holdDelay,
        "trgMsk" : trgMsk,
        "peakDetector" : peakDetectorON,
        "inCalibHG" : inCalibHG,
        "inCalibLG" : inCalibLG,
        "dacPedestalCIT0" : dacPedestalCIT0,
        "dacPedestalCIT1" : dacPedestalCIT1
        }

timeLog = defaultdict(float)

try:

    spwSer = serial.Serial(port = 'COM8',
                        baudrate = 115200,
                        timeout = 10,
                        parity = serial.PARITY_NONE,
                        stopbits = serial.STOPBITS_TWO)

    alim = alm.triggerBoardAlim(alimAddr)
    
    timeLog["startLogTime"] = time.perf_counter()
    
#    alim.dataLogStart(pwrLogFileName)
    
    time.sleep(2)

    alim.powerOnSide(pwrSide)
    
    timeLog["pwrOnFPGATime"] = time.perf_counter()

    if pwrSide == "hot":
        print("Con la modifica sulla sezione di alimentazione, i citiroc del lato HOT partono"
              " accesi quindi li spengo prima")
        sw.powerOffCITs(spwSer)
    
    time.sleep(5)

    print("Accendo il CITIROC0")
    sw.powerOnCIT(spwSer,"cit0")

    timeLog["pwrOnCIT0Time"] = time.perf_counter()
    
    time.sleep(1)
    
    print("Accendo il CITIROC1")
    sw.powerOnCIT(spwSer,"all")

    timeLog["pwrOnCIT1Time"] = time.perf_counter()

    time.sleep(5)

    timeLog["startDefConfigTime"] = time.perf_counter()

    print(f"Imposto i piedistalli ai valori {dacPedestalCIT0} e {dacPedestalCIT1}")
    sw.changePedestal(spwSer, dacPedestalCIT0, "cit0")
    sw.changePedestal(spwSer, dacPedestalCIT1, "cit1")

    #imposto ad un valore sicuro le soglie dei due citiroc
    print("Imposto le soglie a 500 per sicurezza")
    sw.changeConfigVal(spwSer,"dac_code_1",500,"all")
    sw.changeConfigVal(spwSer,"dac_code_2",500,"all")
    
    print(f"Imposto il peak detector nello stato {peakDetectorON}")

    sw.peakDetector(spwSer,'hg',peakDetectorON,"all")
    sw.peakDetector(spwSer,'lg',peakDetectorON,"all")

    print(f"Imposto il delay dell'hold a {holdDelay}")

    sw.changeConfigVal(spwSer,"HOLDDELAY_CONST",holdDelay,cit)

    sw.changeConfigVal(spwSer, "TCONST_HG_SHAPER", 0, "all")
    sw.changeConfigVal(spwSer, "TCONST_LG_SHAPER", 0, "all")

    print("Seleziono il trigger esterno")
    sw.changeConfigVal(spwSer,"SEL_TRIG_EXT_PSC",1,"all")
    
    print("Azzero i guadagni di tutti i canali per il tutti i CITIROC")
    for ich in range(0,32):
        sw.changeConfigVal(spwSer,f"preamp_config{ich:02d}",0,"all")

    sw.changeConfigVal(spwSer,"FAST_SHAPER_LG",int(inCalibLG),cit)

#    sw.changeConfigVal(spwSer,"TESTB_OTAQ",0,"all")

    print("Applico la configurazione scelta")
    sw.applyConfiguration(spwSer,"all")

    print("Applico la configurazione scelta")
    sw.applyConfiguration(spwSer,"all")

    print("Applico la configurazione scelta")
    sw.applyConfiguration(spwSer,"all")


    if useProbe is True:
        sw.changeProbeRegVal(spwSer,probeReg,probeVal)

    print("Seleziono la maschera di trigger T")
    sw.selectTriggerMask(spwSer,trgMsk,feedback=True)
    print("Applico la maschera di trigger")
    sw.applyTriggerMask(spwSer,feedback=True)

    print("Applico PMT MASK")
    sw.writeReg(spwSer,regs["PMT_1_MASK_ADDR"],"FFFFFFFF",feedback=True)

    print("Applico PMT MASK")
    sw.writeReg(spwSer,regs["PMT_2_MASK_ADDR"],"FFFFFFFF",feedback=True)
    
    sw.applyPMTMask(spwSer,feedback=True)

    timeLog["endDefConfigTime"] = time.perf_counter()

    ser = sl.connectToSerial(comConf)

    prefixName = input("Inserire prefisso al nome del file da generare: ")

    params = sl.paramsPrompt("Inserire parametri da variare durante l'acquisizione (o i singoli parametri nel caso di una sola acquisizione)"
                          " SEPARATI DA VIRGOLA.\nSe non viene specificata l'unità di misura si assume che il parametro sia in mV."
                          "ES.\nvariare ampiezza impulsi con durata di 30ns ->30mV,40mV,50mV,30ns oppure variare guadagni ->10g,100g,1000g\n"
                          "\nSe si usa l'ingresso in_calib bisogna impostare i guadagni nel seguente modo:\n"
                          "\t<num>tg per impostare a num il valore del guadagno di HG\n"
                          "\t<num>cg per importare a num il valore del guadagno di LG\n"
                          "ES.\n"
                          "30,30ns,10tg,1cg\n>")
    
    timeLog["endInputTime"] = time.perf_counter()
    
    fileNames, paramStrings, paramList = sl.genFileNameList(prefixName,
                                                            params['mv'],
                                                            params['ns'],
                                                            params['g'],
                                                            params['b'],
                                                            params['d'])

    impSer = pgen.pulseGenerator(impAddr)

    gains = sl.setGainParam(fileNames,paramList,
                            CtestHG = inCalibHG,CtestLG = inCalibLG)

    #imposto al minimo le soglie dei due citiroc
    print("Inizializzo le soglie")
    sw.changeConfigVal(spwSer,"dac_code_1",dacVal,"all")
    sw.changeConfigVal(spwSer,"dac_code_2",dacVal,"all")

    lgGainBits = sl.getGainBits(0,sl.InCALIBGainToGainBits,
                             sl.InCALIBValidGains)
    hgGainBits = sl.getGainBits(0,sl.InCALIBGainToGainBits,
                             sl.InCALIBValidGains)

    registerGain = f"{hgGainBits}{lgGainBits}100"

    #imposto il citiroc 0 per generare il trigger.
    print("Imposto il citiroc 1 per generare il trigger.")
    sw.changeConfigVal(spwSer,"preamp_config00",int(registerGain,2),trigCit)

    sw.applyConfiguration(spwSer,"all")

    print("Faccio partire l'acquisizione")
    sw.startACQ(spwSer)

    timeLog["startAcqTime"] = time.perf_counter()
    
    for i,f in enumerate(fileNames):

        impSer.configurePulse(1,paramList['mv'][i][0]*1e-3,0,
                              paramList['ns'][i][0]*1e-9,2e-9,2e-9,20)

        impSer.configurePulse(2,300e-3,0,30e-9,2e-9,2e-9,20)
        impSer.coupleToChannel1("frequency")
        impSer.coupleToChannel1("phase")

        impSer.turnOnChannel("all")
        impSer.turnOnChannel("ch1")
        
        impSer.startPulseGenerator()

        if len(gains) > 0:
            print(f"Imposto preamp_config{ch}={int(gains[i],2)}")
            sw.changeConfigVal(spwSer,f"preamp_config{ch}",
                               int(gains[i],2),cit)
#            for ich in range(0,32):
#                sw.changeConfigVal(spwSer,f"preamp_config{ich:02d}",
#                                   int(gains[i],2),
#                                   cit)

        sw.applyConfiguration(spwSer,cit,feedback=True)

        sl.dummyRead(ser) # fa una lettura di tutto ciò che c'è
                          # nella seriale per svuotare il buffer

        time.sleep(sleepTime)   # aspetta prima di avviare l'acquisizione per essere
                                # sicuri che l'impulsatore finisca di impostare l'output
        if prefixName != "test":
            sl.saveDataFromSerial(ser,comConf,f"{f}-",
                                  paramStrings[i]+f"dacVal={dacVal}",
                                  confParameters)
        
        sw.regSnapshot(spwSer,f+"postACQ_")
                
        impSer.turnOffChannel("ch1")

    impSer.turnOffChannel("ch2")

    impSer.stopPulseGenerator()

    sl.disconnectFromSerial(ser)
    
    impSer.close()
    
    print("Fermo l'acquisizione")
    sw.stopACQ(spwSer)
    
    timeLog["endAcqTime"] = time.perf_counter()

    time.sleep(2)

    print("Spengo i CITIROC")
    sw.powerOffCITs(spwSer)

    timeLog["citsOffTime"] = time.perf_counter()

    spwSer.close()

    time.sleep(2)

#    alim.exportLoggedData(pwrLogFileName)
#    time.sleep(60)
    alim.powerOffSide(pwrSide)
    timeLog["allOffTime"] = time.perf_counter()

    with open(f"timeLog-{prefixName}.log","w") as timeFile:
        for k,v in timeLog.items():
            t = v-timeLog["startLogTime"]
            timeFile.write(f"{k}={t:.3f}\n")
        

except Exception as e:
    print(f"Errore: {e}")
    sl.disconnectFromSerial(ser)
    impSer.close()
    spwSer.close()
    sys.exit(e)
