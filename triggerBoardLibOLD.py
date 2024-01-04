# -*- coding: utf-8 -*-

import serial as srl
import alimLib as alm
import time
import spwLib as sw
import numpy as np
import os
import matplotlib.pyplot as plt
########## da rimuovere #############
import spwLibCold as swc
#####################################
from regNameRegs import regNameRegs as tbRegs
from valNameRegs import valNameRegs as citRegs
import citSupportLib as csl

class triggerBoard(object):
    def __init__(self,alimAddr,slowCtrlConfig,debugConfig):
        try:
            self.slowCtrl = srl.Serial(port = slowCtrlConfig['port'],
                                       baudrate = slowCtrlConfig['baudrate'],
                                       timeout = slowCtrlConfig['timeout'],
                                       parity = slowCtrlConfig['parity'],
                                       stopbits = slowCtrlConfig['stopbits'])

            self.debug = srl.Serial(port = debugConfig['port'],
                                    baudrate = debugConfig['baudrate'],
                                    timeout = debugConfig['timeout'],
                                    parity = debugConfig['parity'],
                                    stopbits = debugConfig['stopbits'])

            self.power = alm.triggerBoardAlim(alimAddr) # aggiungere gestione eccezioni

        except srl.SerialException as e:
            print(f"Non è stato possibile collegarsi alla Trigger Board:\n\t{e}")
            self.slowCtrl = None
            self.debug = None

        else:
            self.activeSide = None
            self._pedestals = {}
            self._thresholds = {}
            self._usePeakDetector = {}
            self._holdDelay = {}
            self._tConstShaper = {}
            self._triggerMask = None
            self._pmtMask = {}
            self._fastShaperOn = {}
            self._gains = {}
            self._citBinary = False

            self.tbRegisters = {}
            self.citRegisters = {}
            
            self.lastResults = {}
            self.lastMeans = {}

    def _checkSlowCtrl(f):
        def wrapper(self,*args,**kwargs):
            if self.slowCtrl is not None:
                fRes = f(self,*args,**kwargs)
            else:
                raise ValueError("Errore! Slow Control non inizializzato!")
            return fRes
        return wrapper

    @property
    def pedestals(self):
        return self._pedestals

    @property
    def thresholds(self):
        return self._thresholds

    @property
    def usePeakDetector(self):
        return self._usePeakDetector

    @property
    def holdDelay(self):
        return self._holdDelay
    
    @property
    def tConstShaper(self):
        return self._tConstShaper
    
    @property
    def triggerMask(self):
        return self._triggerMask
    
    @property
    def pmtMask(self):
        return self._pmtMask
    
    @property
    def fastShaperOn(self):
        return self._fastShaperOn

    @property
    def gains(self):
        return self._gains

    @pedestals.setter
    @_checkSlowCtrl
    def pedestals(self,p):
        self._pedestals.update(p)

        for cit,param in self._pedestals.items():
            pedestalVal = f"{param['hg']}{param['lg']}"
            ########## da rimuovere #############
            if self.activeSide == "cold":
                swc.changePedestal(self.slowCtrl,pedestalVal,cit)
            else:
            #####################################
                sw.changePedestal(self.slowCtrl,pedestalVal,cit)

    @thresholds.setter
    @_checkSlowCtrl
    def thresholds(self,t):
        self._thresholds.update(t)

        for cit,param in self._thresholds.items():
            for typ,val in param.items():
                ########## da rimuovere #############
                if self.activeSide == "cold":
                    swc.changeConfigVal(self.slowCtrl,csl.typDACToReg[typ],val,cit)
                else:
                #####################################
                    sw.changeConfigVal(self.slowCtrl,csl.typDACToReg[typ],val,cit)

    @usePeakDetector.setter
    @_checkSlowCtrl
    def usePeakDetector(self,u):
        self._usePeakDetector.update(u)

        for cit,param in self._usePeakDetector.items():
            for gain,val in param.items():
                ########## da rimuovere #############
                if self.activeSide == "cold":
                    swc.peakDetector(self.slowCtrl,gain,val,cit)
                else:
                #####################################
                    sw.peakDetector(self.slowCtrl,gain,val,cit)

    @holdDelay.setter
    @_checkSlowCtrl
    def holdDelay(self,h):
        self._holdDelay.update(h)

        for cit,param in self._holdDelay.items():
            ########## da rimuovere #############
            if self.activeSide == "cold":
                swc.changeConfigVal(self.slowCtrl,"HOLDDELAY_CONST",param,cit)
            else:
            #####################################
                sw.changeConfigVal(self.slowCtrl,"HOLDDELAY_CONST",param,cit)

    @tConstShaper.setter
    @_checkSlowCtrl
    def tConstShaper(self,tc):
        self._tConstShaper.update(tc)

        for cit,param in self._tConstShaper.items():
            for gain,val in param.items():
                ########## da rimuovere #############
                if self.activeSide == "cold":
                    swc.changeConfigVal(self.slowCtrl,f"TCONST_{gain.upper()}_SHAPER",val,cit)
                else:
                #####################################
                    sw.changeConfigVal(self.slowCtrl,f"TCONST_{gain.upper()}_SHAPER",val,cit)

    @triggerMask.setter
    @_checkSlowCtrl
    def triggerMask(self,tm):
        ########## da rimuovere #############
        if self.activeSide == "cold":
            swc.selectTriggerMask(self.slowCtrl,tm,feedback=True)
            swc.applyTriggerMask(self.slowCtrl,feedback=True)
        else:
        #####################################
            sw.selectTriggerMask(self.slowCtrl,tm,feedback=True)
            sw.applyTriggerMask(self.slowCtrl,feedback=True)

        self._triggerMask = tm

    @pmtMask.setter
    @_checkSlowCtrl
    def pmtMask(self,pm):
        self._pmtMask.update(pm)

        for cit,param in self._pmtMask.items():
            ########## da rimuovere #############
            if self.activeSide == "cold":
                swc.writeReg(self.slowCtrl,tbRegs[f"PMT_{csl.citToReg[cit]}_MASK_ADDR"],param,feedback=True)
                swc.readDataThread(self.slowCtrl, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                                          ### spacewire altrimenti resta nella fifo
                swc.applyPMTMask(self.slowCtrl,feedback=True)
            else:
            #####################################
                sw.writeReg(self.slowCtrl,tbRegs[f"PMT_{csl.citToReg[cit]}_MASK_ADDR"],param,feedback=True)
                sw.readDataThread(self.slowCtrl, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                                         ### spacewire altrimenti resta nella fifo
                sw.applyPMTMask(self.slowCtrl,feedback=True)

    @fastShaperOn.setter
    @_checkSlowCtrl
    def fastShaperOn(self,g):
        self._fastShaperOn.update(g)

        for cit,param in self._fastShaperOn.items():
            ########## da rimuovere #############
            if self.activeSide == "cold":
                swc.changeConfigVal(self.slowCtrl,"FAST_SHAPER_LG",csl.hglgToVal[param],cit)
            else:
            #####################################
                sw.changeConfigVal(self.slowCtrl,"FAST_SHAPER_LG",csl.hglgToVal[param],cit)

    @gains.setter
    @_checkSlowCtrl
    def gains(self,gs):
        for cit,param in gs.items():
            for ch,gains in param.items():
                for gk,gv in gains.items():
                    self._gains[cit][ch][gk] = gv

                regGain = csl.getGainStr(self._gains[cit][ch]['hg'],
                                         self._gains[cit][ch]['lg'],
                                         self._gains[cit][ch]['inCalib'],
                                         self._gains[cit][ch]['enabled'])

                ########## da rimuovere #############
                if self.activeSide == "cold":
                    swc.changeConfigVal(self.slowCtrl,
                                        f"PREAMP_CONFIG{csl.chToNum[ch]}",
                                        int(regGain,2),cit)
                else:
                #####################################
                    sw.changeConfigVal(self.slowCtrl,
                                       f"PREAMP_CONFIG{csl.chToNum[ch]}",
                                       int(regGain,2),cit)

    def _updateParamsFromRegs(self,tbRegistr,citRegistr):
        self._pedestals = {'cit0' : {'hg' : tbRegistr['REF_DAC_1'][1][2:6],
                                     'lg' : tbRegistr['REF_DAC_1'][1][6:10]},
                           'cit1' : {'hg' : tbRegistr['REF_DAC_2'][1][2:6],
                                     'lg' : tbRegistr['REF_DAC_2'][1][6:10]}}

        self._thresholds = {'cit0' : {'charge' : citRegistr['cit0']['DAC_CODE_1'],
                                      'time'   : citRegistr['cit0']['DAC_CODE_2']},
                            'cit1' : {'charge' : citRegistr['cit1']['DAC_CODE_1'],
                                      'time'   : citRegistr['cit1']['DAC_CODE_2']}}

        self._usePeakDetector = {'cit0' : {'hg' : bool(citRegistr['cit0']['EN_HG_PDET']),
                                           'lg' : bool(citRegistr['cit0']['EN_LG_PDET'])},
                                 'cit1' : {'hg' : bool(citRegistr['cit1']['EN_HG_PDET']),
                                           'lg' : bool(citRegistr['cit1']['EN_LG_PDET'])}}

        self._holdDelay = {'cit0' : citRegistr['cit0']['HOLDDELAY_CONST'],
                           'cit1' : citRegistr['cit1']['HOLDDELAY_CONST']}

        self._tConstShaper = {'cit0' : {'hg' : citRegistr['cit0']['TCONST_HG_SHAPER'],
                                        'lg' : citRegistr['cit0']['TCONST_LG_SHAPER']},
                              'cit1' : {'hg' : citRegistr['cit1']['TCONST_HG_SHAPER'],
                                        'lg' : citRegistr['cit1']['TCONST_LG_SHAPER']}}
        
        self._triggerMask = int(tbRegistr['TRIGGER_MASK'][1],16)

        self._pmtMask = {'cit0' : tbRegistr['PMT_1_MASK'][1][2:],
                         'cit1' : tbRegistr['PMT_2_MASK'][1][2:]}
        
        self._fastShaperOn = {'cit0' : csl.invHGLGToVal[citRegistr['cit0']['FAST_SHAPER_LG']],
                              'cit1' : csl.invHGLGToVal[citRegistr['cit1']['FAST_SHAPER_LG']]}
        
        self._gains = {'cit0' : {f"ch{i:02d}" : {'hg'      : citRegistr['cit0'][f"PREAMP_CONFIG{i:02d}"]['hg'],
                                                 'lg'      : citRegistr['cit0'][f"PREAMP_CONFIG{i:02d}"]['lg'],
                                                 'inCalib' : citRegistr['cit0'][f"PREAMP_CONFIG{i:02d}"]['inCalib'],
                                                 'enabled' : citRegistr['cit0'][f"PREAMP_CONFIG{i:02d}"]['enabled']}
                                 for i in range(32)},
                       'cit1' : {f"ch{i:02d}" : {'hg'      : citRegistr['cit0'][f"PREAMP_CONFIG{i:02d}"]['hg'],
                                                 'lg'      : citRegistr['cit0'][f"PREAMP_CONFIG{i:02d}"]['lg'],
                                                 'inCalib' : citRegistr['cit0'][f"PREAMP_CONFIG{i:02d}"]['inCalib'],
                                                 'enabled' : citRegistr['cit0'][f"PREAMP_CONFIG{i:02d}"]['enabled']}
                                 for i in range(32)}}

    @_checkSlowCtrl
    def syncTBRegisters(self,outFileName=None,citBinaryValues=False,updateParameters=True):
        ########## da rimuovere #############
        if self.activeSide == "cold":
            self.tbRegisters = swc.regSnapshot(self.slowCtrl)
        else:
        #####################################
            self.tbRegisters = sw.regSnapshot(self.slowCtrl)

        cRB = csl.getCITConfiguration(self.tbRegisters)
        cR = csl.citConfToValues(cRB)

        self.citRegisters = cRB if citBinaryValues is True else cR
        self._citBinary = citBinaryValues

        if outFileName is not None:
            with open(f"REGSnapshot-{outFileName}-{csl.timeDataStr}.snap","w") as regFile:
                for reg,conf in self.tbRegisters.items():
                    addr = conf[0]
                    val = conf[1]
                    regFile.write(f"Registro {reg.ljust(20,' ')} (0x{addr}) = {val}\n")

                for cit,citConf in self.citRegisters.items():
                    gainConfigStr = []
                    regFile.write(f"------------------------------- {cit.upper()} -------------------------------\n")
                    for reg,val in citConf.items():
                        if reg[:-2] != 'PREAMP_CONFIG':
                            regFile.write(f"Registro {cit.upper()} "
                                          f"{reg.rjust(25,' ')} = {val}\n")
                        else:
                            if citBinaryValues is False:
                                gainConfigStr.append(f"Registro {cit.upper()} "
                                                     f"{reg.rjust(25,' ')} = HG : "
                                                     +f"{val['hg']}".ljust(8,' ')
                                                     +" LG : "+
                                                     f"{val['lg']}".ljust(8,' ')
                                                     +" CALIB : "+
                                                     f"{val['inCalib']}".ljust(4,' ')
                                                     +f" ENABLED : {val['enabled']}\n")
                            else:
                                gainConfigStr.append(f"Registro {cit.upper()} "
                                                     f"{reg.rjust(25,' ')} = HG : "
                                                     +f"{val[:6]}".ljust(6,' ')
                                                     +" LG : "+
                                                     f"{val[6:12]}".ljust(6,' ')
                                                     +" CALIB : "+
                                                     f"{csl.invInCalibHGLG[val[12:14]]}".ljust(4,' ')
                                                     +f" ENABLED : {bool(val[14])}\n")
                    
                    for gainStr in gainConfigStr[::-1]: # i registri dei CITIROC vanno dal canale 31 a 0 quindi li inverto
                        regFile.write(gainStr)

                    regFile.write("--------------------------------------------------------------------\n")

        if updateParameters is True:
            self._updateParamsFromRegs(self.tbRegisters,cR)


    @_checkSlowCtrl
    def readRegister(self,reg,cit=None):
        retVal = None
        reg = reg.upper()
        
        if f"{reg}_ADDR" in tbRegs.keys():
            ########## da rimuovere #############
            if self.activeSide == "cold":
                addr,val = swc.readRegVal(self.slowCtrl,reg)
            else:
            #####################################
                addr,val = sw.readRegVal(self.slowCtrl,reg)
            
            self.tbRegisters[reg] = [addr,val]
            
            retVal = self.tbRegisters[reg]

        elif reg in citRegs.keys():
            if cit is not None:
                ########## da rimuovere #############
                if self.activeSide == "cold":
                    val = swc.readConfigVal(self.slowCtrl,reg,cit)[0]
                else:
                #####################################
                    val = sw.readConfigVal(self.slowCtrl,reg,cit)[0]
                
                if self._citBinary is False:
                    self.citRegisters[cit][reg] = csl.citBinaryToVal(reg,val)
                else:
                    self.citRegisters[cit][reg] = val
                
                retVal = self.citRegisters[cit][reg]

            else:
                ########## da rimuovere #############
                if self.activeSide == "cold":
                    vals = swc.readConfigVal(self.slowCtrl,reg,'all')
                else:
                #####################################
                    vals = sw.readConfigVal(self.slowCtrl,reg,'all')

                if self._citBinary is False:
                    self.citRegisters['cit0'][reg] = csl.citBinaryToVal(reg,vals[0])
                    self.citRegisters['cit1'][reg] = csl.citBinaryToVal(reg,vals[1])
                else:
                    self.citRegisters['cit0'][reg] = vals[0]
                    self.citRegisters['cit1'][reg] = vals[1]
                
                retVal = {'cit0' : self.citRegisters['cit0'][reg],
                          'cit1' : self.citRegisters['cit1'][reg]}
            
        else:
            raise ValueError(f"Registro '{reg}' non esistente!")
        
        cR = (csl.citConfToValues(self.citRegisters) if self._citBinary is True 
              else self.citRegisters)
        self._updateParamsFromRegs(self.tbRegisters,cR)
        
        return retVal

    @_checkSlowCtrl
    def setGain(self,cit,ch,gainLine,gain,inCalib=None,enabled=True):
        self._gains[cit][ch][gainLine] = gain
        self._gains[cit][ch]['inCalib'] = inCalib
        self._gains[cit][ch]['enabled'] = enabled
        
        regGain = csl.getGainStr(self._gains[cit][ch]['hg'],
                                 self._gains[cit][ch]['lg'],
                                 self._gains[cit][ch]['inCalib'],
                                 self._gains[cit][ch]['enabled'])

        ########## da rimuovere #############
        if self.activeSide == "cold":
                swc.changeConfigVal(self.slowCtrl,
                                    f"PREAMP_CONFIG{csl.chToNum[ch]}",
                                    int(regGain,2),cit)
        else:
        #####################################
                sw.changeConfigVal(self.slowCtrl,
                                   f"PREAMP_CONFIG{csl.chToNum[ch]}",
                                   int(regGain,2),cit)

    def powerOn(self,side="hot",pause=1):
        if self.activeSide is None:
            self.power.powerOnSide(side)
            ########## da rimuovere #############
            if side == "hot":
                sw.powerOffCITs(self.slowCtrl)
            #####################################
        elif self.activeSide == "hot" or self.activeSide == "cold":
            self.power.powerOffSide(self.activeSide)
            time.sleep(pause)
            self.power.powerOnSide(side)
        else:
            raise ValueError("Errore! Possibili valori per 'side': hot|cold.")

        self.activeSide = side

    def powerOff(self):
        self.power.powerOffSide(self.activeSide)
        self.activeSide = None

    def powerOnCIT(self,citiroc):
        if citiroc == "cit0" or citiroc == "cit1" or citiroc == "all":
            ########## da rimuovere #############
            if self.activeSide == "cold":
                swc.powerOnCIT(self.slowCtrl,citiroc)
            else:
            #####################################
                sw.powerOnCIT(self.slowCtrl,citiroc)
        else:
            raise ValueError("Errore! Possibili valori per 'citiroc':"
                             " cit0|cit1|all")

    @_checkSlowCtrl
    def configure(self,citiroc="all"):
        ########## da rimuovere #############
        if self.activeSide == "cold":
            swc.applyConfiguration(self.slowCtrl,citiroc)
        else:
        #####################################
            sw.applyConfiguration(self.slowCtrl,citiroc)

    @_checkSlowCtrl
    def probeOn(self,probeName,cit,ch,gainLine):
        probeReg,probeVal = csl.getProbeRegVal(cit,gainLine,ch,probeName)

        ########## da rimuovere #############
        if self.activeSide == "cold":
            swc.changeProbeRegVal(self.slowCtrl,probeReg,probeVal)
        else:
        #####################################
            sw.changeProbeRegVal(self.slowCtrl,probeReg,probeVal)

    @_checkSlowCtrl
    def probeOff(self,probeName,cit,ch,gainLine):
        probeReg,probeVal = csl.getProbeRegVal(cit,gainLine,ch,probeName)

        ########## da rimuovere #############
        if self.activeSide == "cold":
            swc.changeProbeRegVal(self.slowCtrl,probeReg,"00000000")
        else:
        #####################################
            sw.changeProbeRegVal(self.slowCtrl,probeReg,"00000000")

    def initialize(self):
        # print("Applico la configurazione di default ai CITIROC")
        # self.configure()
        print("Sincronizzo i registri...")
        self.syncTBRegisters(updateParameters=True)

    @_checkSlowCtrl
    def startAcq(self):
        ########## da rimuovere #############
        if self.activeSide == "cold":
            swc.startACQ(self.slowCtrl)
        else:
        #####################################
            sw.startACQ(self.slowCtrl)

    @_checkSlowCtrl
    def stopAcq(self):
        ########## da rimuovere #############
        if self.activeSide == "cold":
            swc.stopACQ(self.slowCtrl)
        else:
        #####################################
            sw.stopACQ(self.slowCtrl)

    def close(self):
        try:
            self.debug.close()
            self.slowCtrl.close()
            self.power.close()
        except srl.SerialException as e:
            print("Non è stato possibile disconntettersi"
                  f" dalla Trigger Boar:\n\t{e}")

    def saveData(self,acqTime,fileName,fileHeader=None,dataFrom='debug',
                 adcOnly=False,plainTextData=True,oldFormat=False):
        serData = b''
        
        try:
            # if fileHeader is not None: #forse è meglio non mettere l'header nel file raw
            #     fileOutput.write(f"{fileHeader}\n".encode('utf-8'))
            
            print("Inizio acquisizione... Premere CTRL-C per uscire...\n")
            
            elapsedTime = 0

            t1 = time.perf_counter()

            if dataFrom == 'debug':
                fileOutput = open(f"raw-{fileName}.dat","wb")

                print("Eliminazione dati residui nella fifo...")
                while self.debug.in_waiting > 0:
                    self.debug.read(self.debug.in_waiting)
                self.debug.reset_input_buffer()
                self.debug.reset_output_buffer()
            
                while elapsedTime <= acqTime:
                    if self.debug.in_waiting > 0:
                        serData = self.debug.read(self.debug.in_waiting)
                        fileOutput.write(serData)
            
                    elapsedTime = time.perf_counter() - t1
            
                print(f"Acquisizione finita, sono passati {elapsedTime:.3f} secondi")
                
            elif dataFrom == 'slowCtrl':
                fileOutput = open(f"raw-{fileName}.dat","w")

                print("Acquisizione dati da SpaceWire...")
                pckPresMask = 0b1 << 14
                
                print("Invio comando di inzio lettura")
                swc.writeReg(self.slowCtrl,tbRegs["CMD_REG_ADDR"],"00008030",feedback=True)
                swc.readDataThread(self.slowCtrl, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                                          ### spacewire altrimenti resta nella fifo
                                                                                          
                dataFromSpw = []
                print("Inizio acquisizione...")
                packetPresent = 1
                while packetPresent:
                    statusAddr,statusReg = self.readRegister("STATUS_REG")
                    
                    packetPresent = (int(statusReg,16) & pckPresMask) >> 14

                    for i in range(73): # un pacchetto è costituito da 4x576=2304 bit ovvero 72x4 byte (dallo spw hai 4 byte alla volta)
                        dataAddr, dataWord = self.readRegister("ACQDATA")
                        
                        dataFromSpw.append(dataWord)
            
                for d in dataFromSpw:
                    fileOutput.write(f"{d.split('x')[1]}\n")
            
            fileOutput.close()
            
            packets = csl.getPacketsFromRawFile(f"raw-{fileName}.dat",dataFrom)
            adcVals, dataVals = csl.getADCsFromPackets(packets,dataFrom,
                                                       adcOnly)
            citDict = csl.makeCITDict(adcVals)

            nEvt = len(packets)

            if plainTextData is True:
                with open(f"counters-{fileName}.dat","w") as cntFileOut:
                    # cntFileOut.write("trgCounters,trgFlagCIT0,trgFlagCIT1,"
                    #                  "trgMaskRate")
                    for i,d in enumerate(dataVals):
                        cntFileOut.write(f"------ t{i} ------\n")
                        trgCountBin = int.from_bytes(d['trgCount'],'big')
                        trgFlag0 = int.from_bytes(d['trgFlagCIT0'],'big')
                        trgFlag1 = int.from_bytes(d['trgFlagCIT1'],'big')
                        trgMskRate0 = int.from_bytes(d['trgMaskRate0'],'big')
                        trgMskRate1 = int.from_bytes(d['trgMaskRate1'],'big')
                        trgMskRate2 = int.from_bytes(d['trgMaskRate2'],'big')
                        trgMskRate3 = int.from_bytes(d['trgMaskRate3'],'big')
                        trgMskRate4 = int.from_bytes(d['trgMaskRate4'],'big')
                        trgMskRate5 = int.from_bytes(d['trgMaskRate5'],'big')
                        trgMskRate6 = int.from_bytes(d['trgMaskRate6'],'big')
                        trgMskRate7 = int.from_bytes(d['trgMaskRate7'],'big')
                        trgMskRate8 = int.from_bytes(d['trgMaskRate8'],'big')

                        cntFileOut.write(f"\tcount = {trgCountBin}\n"
                                         f"\tflagCIT0 = {trgFlag0:032b}\n"
                                         f"\tflagCIT1 = {trgFlag1:032b}\n"
                                         f"\tmask0Rate = {trgMskRate0}\n"
                                         f"\tmask1Rate = {trgMskRate1}\n"
                                         f"\tmask2Rate = {trgMskRate2}\n"
                                         f"\tmask3Rate = {trgMskRate3}\n"
                                         f"\tmask4Rate = {trgMskRate4}\n"
                                         f"\tmask5Rate = {trgMskRate5}\n"
                                         f"\tmask6Rate = {trgMskRate6}\n"
                                         f"\tmask7Rate = {trgMskRate7}\n"
                                         f"\tmask8Rate = {trgMskRate8}\n")
                        
                        cntFileOut.write(f"------------------\n")

                with open(f"table-{fileName}.dat","w") as dataFileOut:
    
                    if fileHeader is not None:
                        dataFileOut.write(f";;; {fileHeader} ;;;\n")

                    if oldFormat is True:    
                        for c,chs in citDict.items(): #è possibile eliminare questi for
                            for ch,gs in chs.items():
                                for g,val in gs.items():
                                    dataFileOut.write(f";;; CITIROC{csl.CIT[c.upper()]}"
                                                      f" {g.upper()} {ch.upper()} ;;;\n")
                                    for v in val:
                                        dataFileOut.write(f"{int(v)} ")
                                    dataFileOut.write("\n")
                    else:
                        c = f"{'CIT0'.center(448)} {'CIT1'.center(448)} "
                        g = f"{'HG'.center(223)} {'LG'.center(223)} "*2
                        ch = ' '.join([f'CH{i:02d}'.ljust(6,' ')
                                       for i in range(32)])
                        dataFileOut.write(f"{c}\n{g}\n{ch} {ch} {ch} {ch} \n")
                        
                        for i in range(nEvt):
                            dataFileOut.write(csl.fileChWrite(adcVals[:,i]))

                        mvals = np.mean(adcVals, axis=1)
                        stdvals = np.std(adcVals, axis=1)

                        dataFileOut.write("\nMEAN VALUES:\n")
                        dataFileOut.write(csl.fileChWrite(mvals))

                        dataFileOut.write("\nSTD DEVs:\n")
                        dataFileOut.write(csl.fileChWrite(stdvals))

            self.lastResults = citDict
            
            self.lastMeans = {'cit0':{f'ch{i:02d}':{'hg':{'mean':mvals[i],
                                                          'stddev':stdvals[i]},
                                                    'lg':{'mean':mvals[i+32],
                                                          'stddev':stdvals[i+32]}}
                                      for i in range(32)},
                              'cit1':{f'ch{i:02d}':{'hg':{'mean':mvals[i+64],
                                                          'stddev':stdvals[i+64]},
                                                    'lg':{'mean':mvals[i+96],
                                                          'stddev':stdvals[i+96]}}
                                      for i in range(32)}}

            print("Eliminazione dati residui nella fifo...")
            while self.debug.in_waiting > 0:
                self.debug.read(self.debug.in_waiting)
            self.debug.reset_input_buffer()
            self.debug.reset_output_buffer()

        except KeyboardInterrupt:
            self.debug.reset_input_buffer()
            self.debug.reset_output_buffer()
            fileOutput.close()
            print("Acquisizione arrestata!")
