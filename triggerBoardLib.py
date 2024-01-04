# -*- coding: utf-8 -*-

import serial as srl
import alimLib as alm
from time import perf_counter
import numpy as np
import dpcuEmulatorLib as dpcuel
from regNameRegs import regNameRegs as tbRegs
from valNameRegs import valNameRegs as citRegs
import citSupportLib as csl


class triggerBoard(object):
    def __init__(self,alimAddr,dpcuEmAddr):
        try:
            self.slowCtrl = dpcuel.dpcuEmulator(dpcuEmAddr)

            self.power = alm.triggerBoardAlim(alimAddr) # aggiungere gestione eccezioni

        finally:
            self.feedback = True
            self.activeSide = None
            self._pedestals = {}
            self._thresholds = {}
            self._usePeakDetector = {}
            self._holdDelay = None
            self._tConstShaper = {}
            self._triggerMask = None
            self._genericTriggerMask = None
            self._pmtMask = {}
            self._fastShaperOn = None
            self._gains = {}
            self._citBinary = False

            self.tbRegisters = {}
            self.citRegisters = {}
            
            self.lastResults = {}
            self.lastMeans = {}

    def _checkSlowCtrl(f):
        def wrapper(self,*args,**kwargs):
            if self.slowCtrl.ssh is not None:
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
    def genericTriggerMask(self):
        return self._genericTriggerMask
    
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
            pVal = f"{param['hg']}{param['lg']}"
            self.slowCtrl.changePedestal(pVal,cit,feedback=self.feedback)

    @thresholds.setter
    @_checkSlowCtrl
    def thresholds(self,t):
        self._thresholds.update(t)

        for typ,val in self._thresholds.items():
            self.slowCtrl.changeConfigVal(csl.typDACToReg[typ],val,feedback=self.feedback)

    @usePeakDetector.setter
    @_checkSlowCtrl
    def usePeakDetector(self,u):
        self._usePeakDetector.update(u)

        for gain,val in self._usePeakDetector.items():
           self.slowCtrl.peakDetector(gain,val,feedback=self.feedback)

    @holdDelay.setter
    @_checkSlowCtrl
    def holdDelay(self,h):
        self._holdDelay = h

        self.slowCtrl.changeConfigVal("HOLDDELAY_CONST",h,feedback=self.feedback)

    @tConstShaper.setter
    @_checkSlowCtrl
    def tConstShaper(self,tc):
        self._tConstShaper.update(tc)

        for gain,val in self._tConstShaper.items():
            self.slowCtrl.changeConfigVal(f"TCONST_{gain.upper()}_SHAPER",
                                          csl.tConstShaperToID[val],feedback=self.feedback)

    @triggerMask.setter
    @_checkSlowCtrl
    def triggerMask(self,tm):
        self.slowCtrl.selectTriggerMask(tm,feedback=self.feedback)
        self.slowCtrl.applyTriggerMask(feedback=self.feedback)

        self._triggerMask = tm

    @genericTriggerMask.setter
    @_checkSlowCtrl
    def genericTriggerMask(self,gtm):
        if gtm is not None:
            self.slowCtrl.selectGenericTriggerMask(gtm,feedback=self.feedback)
            self.slowCtrl.applyTriggerMask(feedback=self.feedback)

            self._genericTriggerMask = gtm

    @pmtMask.setter
    @_checkSlowCtrl
    def pmtMask(self,pm):
        self._pmtMask.update(pm)

        for cit,param in self._pmtMask.items():
            self.slowCtrl.selectPMTMask(param,csl.citToReg[cit])
            self.slowCtrl.applyPMTMask(feedback=self.feedback)

    @fastShaperOn.setter
    @_checkSlowCtrl
    def fastShaperOn(self,g):
        self._fastShaperOn = g

        self.slowCtrl.changeConfigVal("FAST_SHAPER_LG",csl.hglgToVal[g],feedback=self.feedback)

    @gains.setter
    @_checkSlowCtrl
    def gains(self,gs):
        for ch,gains in gs.items():
            for gk,gv in gains.items():
                self._gains[ch][gk] = gv

            regGain = csl.getGainStr(self._gains[ch]['hg'],
                                     self._gains[ch]['lg'],
                                     self._gains[ch]['inCalib'],
                                     self._gains[ch]['enabled'])

            self.slowCtrl.changeConfigVal(f"PREAMP_CONFIG{csl.chToNum[ch]}",
                                          int(regGain,2),feedback=self.feedback)

    def _updateParamsFromRegs(self,tbRegistr,citRegistr):
        self._pedestals = {'cit0' : {'hg' : tbRegistr['REF_DAC_1'][1][2:6],
                                     'lg' : tbRegistr['REF_DAC_1'][1][6:10]},
                           'cit1' : {'hg' : tbRegistr['REF_DAC_2'][1][2:6],
                                     'lg' : tbRegistr['REF_DAC_2'][1][6:10]}}

        self._thresholds = {'charge' : citRegistr['DAC_CODE_1'],
                            'time'   : citRegistr['DAC_CODE_2']}

        self._usePeakDetector = {'hg' : bool(citRegistr['EN_HG_PDET']),
                                 'lg' : bool(citRegistr['EN_LG_PDET'])}

        self._holdDelay = citRegistr['HOLDDELAY_CONST']

        self._tConstShaper = {'hg' : citRegistr['TCONST_HG_SHAPER'],
                              'lg' : citRegistr['TCONST_LG_SHAPER']}
        
        self._triggerMask = int(tbRegistr['TRIGGER_MASK'][1],16)

        self._pmtMask = {'cit0' : tbRegistr['PMT_1_MASK'][1][2:],
                         'cit1' : tbRegistr['PMT_2_MASK'][1][2:]}
        
        self._fastShaperOn = csl.invHGLGToVal[citRegistr['FAST_SHAPER_LG']]
        
        self._gains = {f"ch{i:02d}" : {'hg'      : citRegistr[f"PREAMP_CONFIG{i:02d}"]['hg'],
                                       'lg'      : citRegistr[f"PREAMP_CONFIG{i:02d}"]['lg'],
                                       'inCalib' : citRegistr[f"PREAMP_CONFIG{i:02d}"]['inCalib'],
                                       'enabled' : citRegistr[f"PREAMP_CONFIG{i:02d}"]['enabled']}
                                 for i in range(32)}

    @_checkSlowCtrl
    def syncTBRegisters(self,outFileName=None,citBinaryValues=False,updateParameters=True):
        self.tbRegisters = self.slowCtrl.regSnapshot()

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
                
                regFile.write("--------------------------------------------------------------------\n")

                gainConfigStr = []
                for reg,val in self.citRegisters.items():
                    if reg[:-2] != 'PREAMP_CONFIG':
                        regFile.write(f"Registro {reg.rjust(25,' ')} = {val}\n")
                    else:
                        if citBinaryValues is False:
                            gainConfigStr.append(f"Registro "
                                                 f"{reg.rjust(25,' ')} = HG : "
                                                 +f"{val['hg']}".ljust(8,' ')
                                                 +" LG : "+
                                                 f"{val['lg']}".ljust(8,' ')
                                                 +" CALIB : "+
                                                 f"{val['inCalib']}".ljust(4,' ')
                                                 +f" ENABLED : {val['enabled']}\n")
                        else:
                            gainConfigStr.append(f"Registro "
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
    def readRegister(self,reg):
        retVal = None
        reg = reg.upper()
        
        if f"{reg}_ADDR" in tbRegs.keys():
            addr,val = self.slowCtrl.readRegVal(reg)
            
            self.tbRegisters[reg] = [addr,val]
            
            retVal = self.tbRegisters[reg]

        elif reg in citRegs.keys():
            val = self.slowCtrl.readConfigVal(reg)[0]
            
            if self._citBinary is False:
                self.citRegisters[reg] = csl.citBinaryToVal(reg,val)
            else:
                self.citRegisters[reg] = val
            
            retVal = self.citRegisters[reg]

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

        self.slowCtrl.changeConfigVal(f"PREAMP_CONFIG{csl.chToNum[ch]}",
                                      int(regGain,2),feedback=self.feedback)

    def powerOn(self,channel,pause=1):
        if self.activeSide is None:
            self.power.powerOnChannel(channel)
            self.activeSide = channel

        # elif self.activeSide == "hot" or self.activeSide == "cold":
        #     self.power.powerOffSide(self.activeSide)
        #     sleep(pause)
        #     self.power.powerOnSide(side)
        else:
            raise ValueError(f"Errore! Canale già attivo: {self.activeSide}.")

    def powerOff(self,channel):
        # self.power.powerOffSide(self.activeSide)
        self.power.powerOffChannel(channel)
        self.activeSide = None

    def powerOnCIT(self,citiroc):
        if citiroc == "cit0" or citiroc == "cit1" or citiroc == "all":
            self.slowCtrl.powerOnCIT(citiroc,feedback=self.feedback)
        else:
            raise ValueError("Errore! Possibili valori per 'citiroc':"
                             " cit0|cit1|all")

    @_checkSlowCtrl
    def configure(self,citiroc="all"):
        self.slowCtrl.applyConfiguration(citiroc,feedback=self.feedback)

    def initialize(self):
        print("Applico la configurazione di default ai CITIROC")
        self.configure()
        print("Sincronizzo i registri...")
        self.syncTBRegisters()

    @_checkSlowCtrl
    def startAcq(self):
        self.slowCtrl.startACQ()

    @_checkSlowCtrl
    def stopAcq(self):
        self.slowCtrl.stopACQ()

    def close(self):
        try:
            self.slowCtrl.close()
            self.power.close()
        except srl.SerialException as e:
            print("Non è stato possibile disconntettersi"
                  f" dalla Trigger Boar:\n\t{e}")

    def saveData(self,evtNum,fileName,fileHeader=None,
                 oldFormat=False):

        try:
            print("Inizio acquisizione... Premere CTRL-C per uscire...\n")
            
            elapsedTime = 0

            t1 = perf_counter()

            remoteFileName = f"raw-{fileName}"
            localFileName = f"./{remoteFileName}.dat"

            self.slowCtrl.saveDataStart(remoteFileName,evtNum)

            elapsedTime = perf_counter() - t1

            print(f"Fine acquisizione, download del file {remoteFileName}...")
            
            self.slowCtrl.getDataFile(remoteFileName, localFileName)

            print(f"Acquisizione finita, sono passati {elapsedTime:.3f} secondi")

            packets = csl.getPacketsFromRawFile(localFileName)
            data,auxData = csl.getADCsFromPackets(packets)
            citDict = csl.makeCITDict(data,auxData)

            nEvt = len(auxData)

            with open(f"./counters-{fileName}.dat","w") as cntFileOut:
                for i,p in enumerate(auxData):
                    cntFileOut.write(f"------ t{i} ------\n")
                    trgCount     = p['trgCount']
                    ppsCount     = f"{p['ppsCount']}"
                    trgID        = f"{p['trgID']}"
                    lostTrgCount = p['lostTrgCount']
                    aliveTime    = p['aliveTime']
                    deadTime     = p['deadTime']
                    trgFlacCIT0  = f"{p['trgFlagCIT0']}"
                    trgFlacCIT1  = f"{p['trgFlagCIT1']}"
                    turrFlag     = f"{p['turrFlag']}"
                    turr0Cnt     = p['turr0Cnt']
                    turr1Cnt     = p['turr1Cnt']
                    turr2Cnt     = p['turr2Cnt']
                    turr3Cnt     = p['turr3Cnt']
                    turr4Cnt     = p['turr4Cnt']

                    cntFileOut.write(f"\trgCount = {trgCount}\n"
                                     f"\tppsCount = {ppsCount}\n"
                                     f"\ttrgID = {trgID}\n"
                                     f"\tlostTrgCount = {lostTrgCount}\n"
                                     f"\taliveTime = {aliveTime}\n"
                                     f"\tdeadTime = {deadTime}\n"
                                     f"\trgFlacCIT0 = {trgFlacCIT0}\n"
                                     f"\ttrgFlacCIT1 = {trgFlacCIT1}\n"
                                     f"\tturrFlag = {turrFlag}\n"
                                     f"\tturr0Cnt = {turr0Cnt}\n"
                                     f"\tturr1Cnt = {turr1Cnt}\n"
                                     f"\tturr2Cnt = {turr2Cnt}\n"
                                     f"\tturr3Cnt = {turr3Cnt}\n"
                                     f"\tturr4Cnt = {turr4Cnt}\n")

                    cntFileOut.write("------------------\n")

            with open(f"./table-{fileName}.dat","w") as dataFileOut:

                if fileHeader is not None:
                    dataFileOut.write(f";;; {fileHeader} ;;;\n")

                c = f"{'CIT0'.center(448)} {'CIT1'.center(448)} "
                g = f"{'HG'.center(223)} {'LG'.center(223)} "*2
                ch = ' '.join([f'CH{i:02d}'.ljust(6,' ')
                               for i in range(32)])
                dataFileOut.write(f"{c}\n{g}\n{ch} {ch} {ch} {ch} \n")

                cit0hgVals = np.zeros((nEvt,0))
                cit0lgVals = np.zeros((nEvt,0))
                cit1hgVals = np.zeros((nEvt,0))
                cit1lgVals = np.zeros((nEvt,0))
                for ch in range(32):
                    cit0hgVals = np.column_stack((cit0hgVals,citDict['cit0'][f"ch{ch:02d}"]['hg']))
                    cit0lgVals = np.column_stack((cit0lgVals,citDict['cit0'][f"ch{ch:02d}"]['lg']))
                    cit1hgVals = np.column_stack((cit1hgVals,citDict['cit1'][f"ch{ch:02d}"]['hg']))
                    cit1lgVals = np.column_stack((cit1lgVals,citDict['cit1'][f"ch{ch:02d}"]['lg']))

                adcArray = np.column_stack((cit0hgVals,cit0lgVals,
                                           cit1hgVals,cit1lgVals))

                for a in adcArray:
                    dataFileOut.write(csl.fileChWrite(a))

                mvals = np.mean(adcArray, axis=0)
                stdvals = np.std(adcArray, axis=0)

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

        except KeyboardInterrupt:
            print("Acquisizione arrestata!")
