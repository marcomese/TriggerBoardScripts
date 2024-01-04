# -*- coding: utf-8 -*-

import pyvisa as visa
from collections import defaultdict
import re
from itertools import product

numericPattern = "[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)*"
pulsePattern = fr"(?:(w|a|ah|al|h|r|f)\s*=\s*)?({numericPattern})\s*,?\s*"

pulseRegex = re.compile(pulsePattern)

def getPhase(freq,t):
    if type(freq) == str:
        freq = float(freq)

    dt = (1/freq)/360
    
    n = t/dt
    
    return n

class pulseGenerator(object):
    def __init__(self, visaAddr, channels = 2, timeout = 50000, rst = True):
        rm = visa.ResourceManager()
        
        try:
            self.device = rm.open_resource(visaAddr)
        except visa.errors.VisaIOError as e:
            print(f"Non è stato possibile collegarsi al device:\n\t{e}")
            self.device = None
        else:
            self.device.timeout = timeout
            self.devID = self.device.query("*IDN?")
            if rst is True:
                self.device.write("*RST")

        self.channels = {f"ch{i}":i for i in range(1,channels+1)}
        self.channels["all"] = -1
        self.pulseParams = None
        self.couplingParameters = (
                                    "AMPLITUDE",
                                    "FREQUENCY",
                                    "OFFSET",
                                    "PHASE"
                                    )
        self.coupledChannels = defaultdict(lambda: defaultdict(list))
        self.paramsProduct = {}

    def configurePulse(self,channel,highVampl,lowVoffset,width,leadEdge,trailEdge,freq,
                       highLim = 3, lowLim = -3,
                       lowImpedance=False,amplVShighlow='ampl',vocm=0.5,double=False,
                       delay1=0,delay2=None,burst=False,burstCycles=1,
                       phase=[0,0]):
        if type(channel) is str and channel in self.channels.keys():
            ch = self.channels[channel]
        elif type(channel) is int:
            ch = channel
        else:
            raise ValueError("Canale non valido!")

        if ch == -1:
            raise ValueError("Configurare i canali singolarmente!")

        burstState = {True:"ON",
                      False:"OFF"}

        pulseStr = 'PULSE' if double is False else 'DOUBLEPULSE:PULSE{0}'

        freqCMD = f"SOURCE{ch}:FREQUENCY {freq}"
        funcCMD = f"SOURCE{ch}:FUNCTION {pulseStr.split(':')[0]}"
        trailEdgeCMD = f"SOURCE{ch}:{pulseStr}:TRANSITION:TRAILING {trailEdge}"
        leadEdgeCMD = f"SOURCE{ch}:{pulseStr}:TRANSITION:LEADING {leadEdge}"
        widthCMD = f"SOURCE{ch}:{pulseStr}:WIDTH {width}"
        highLimit = f"SOURCE{ch}:VOLT:LIMIT:HIGH {highLim}"
        lowLimit = f"SOURCE{ch}:VOLT:LIMIT:LOW {lowLim}"
        lowImpedance = f"OUTPUT{ch}:LOW:IMPEDANCE {int(lowImpedance)}"
        lowCMD = f"SOURCE{ch}:VOLT:LOW {lowVoffset}"
        highCMD = f"SOURCE{ch}:VOLT:HIGH {highVampl}"
        amplCMD = f"SOURCE{ch}:VOLT:AMPL {highVampl}"
        offVal = float(lowVoffset)
        offsetCMD = f"SOURCE{ch}:VOLT:OFFSET {offVal}"
        vunitCMD = f"SOURCE{ch}:VOLT:UNIT VPP"
        amplVal = float(highVampl)
        vocmCMD = f"SOURCE{ch}:VOLT:VOCM {vocm*amplVal}"
        burstCyclesCMD = f"SOURCE{ch}:BURST:NCYCLES {burstCycles}"
        burstCMD = f"SOURCE{ch}:BURST:STATE {burstState[burst]}"
        phaseCMD = f"SOURCE{ch}:PHASE {getPhase(freq,phase[ch-1]*1e-9)}DEG"
        
        if double is True:
            doubleAmplCMD = f"SOURCE{ch}:{pulseStr}:AMPL {highVampl}"
            
            if delay2 is None:
                delay2 = 1/(2*freq)

            doubleDelayCMD = [f"SOURCE{ch}:{pulseStr}:DELAY {delay1}",
                              f"SOURCE{ch}:{pulseStr}:DELAY {delay2}"]

        if self.device is not None:
            self.device.write(freqCMD)
            self.device.write(funcCMD)
            self.device.write(phaseCMD)

            if double is False:
                self.device.write(trailEdgeCMD)
                self.device.write(leadEdgeCMD)
                self.device.write(widthCMD)
            else:
                for i in range(1,3):
                    self.device.write(trailEdgeCMD.format(i))
                    self.device.write(leadEdgeCMD.format(i))
                    self.device.write(widthCMD.format(i))
                    self.device.write(doubleAmplCMD.format(i))
                    self.device.write(doubleDelayCMD[i-1].format(i))

            self.device.write(lowImpedance)
            self.device.write(highLimit)
            self.device.write(lowLimit)
            
            if amplVShighlow == 'highlow':
                self.device.write(lowCMD)
                self.device.write(highCMD)
            else:
                self.device.write(vunitCMD)
                self.device.write(amplCMD)
                self.device.write(offsetCMD)
                self.device.write(vocmCMD)

            if burst is True:
                self.device.write(burstCyclesCMD)
                self.device.write(burstCMD)

        else:
            raise IOError("Device non connesso!")

    def configureExpDecay(self,channel,ampl,freq,trigFreq,
                          lowImpedance=False):
        if type(channel) is str and channel in self.channels.keys():
            ch = self.channels[channel]
        elif type(channel) is int:
            ch = channel
        else:
            raise ValueError("Canale non valido!")

        if ch == -1:
            raise ValueError("Configurare i canali singolarmente!")

        pulseStr = 'EDEC'
        freqCMD = f"SOURCE{ch}:FREQUENCY {freq}"
        funcCMD = f"SOURCE{ch}:FUNCTION {pulseStr.split(':')[0]}"
        lowImpedance = f"OUTPUT{ch}:LOW:IMPEDANCE {int(lowImpedance)}"
        amplCMD = f"SOURCE{ch}:VOLT:AMPL {ampl}"
        vunitCMD = f"SOURCE{ch}:VOLT:UNIT VPP"
        trigCMD = "TRIGGER:SOURCE TIMER"
        trigPeriodCMD = f"TRIGGER:TIMER {1/trigFreq}"
        burstCyclesCMD = f"SOURCE{ch}:BURST:NCYCLES 1"
        burstCMD = f"SOURCE{ch}:BURST:STATE ON"
        
        if self.device is not None:
            self.device.write(freqCMD)
            self.device.write(funcCMD)

            self.device.write(lowImpedance)

            self.device.write(vunitCMD)
            self.device.write(amplCMD)
            
            self.device.write(trigCMD)
            self.device.write(trigPeriodCMD)
            
            self.device.write(burstCyclesCMD)
            self.device.write(burstCMD)

        else:
            raise IOError("Device non connesso!")
        
        
    def coupleToChannel1(self,parameter,ratio = 1.0,offset = 0.0,channel = 2):
        if self.device is not None:
            if type(channel) is str and channel in self.channels.keys():
                ch = self.channels[channel]
            elif type(channel) is int:
                ch = channel
            else:
                raise ValueError("Canale non valido!")
            
            cmdStr = ""
            
            if max(self.channels.values()) == 2 and ch == 1:
                ch = 2
            
            par = parameter.upper()
            
            if len(self.coupledChannels) == 0:
                self.device.write(f"SOURCE{ch}:COUPLE:STATE ON")
            
            if par in self.couplingParameters:
                cmdStr = (f"SOURCE{ch}:COUPLE:{par}:STATe ON;:"
                          f"SOURCE{ch}:COUPLE:{par}:RATIO {ratio};:"
                          f"SOURCE{ch}:COUPLE:{par}:OFFSET {offset}")
    
                self.device.write(cmdStr)
                
                self.coupledChannels[ch].update({par:[ratio,offset]})

            else:
                pPoss = ""
                for p in self.couplingParameters:
                    pPoss += f"\t{p}\n"
                raise ValueError("Parametro non valido!\n"
                                 f"Parametri possibili:\n{pPoss}")

        else:
            raise IOError("Device non connesso!")

    def decoupleChannel(self,parameter,channel = 2):
        if self.device is not None:
            if type(channel) is str and channel in self.channels.keys():
                ch = self.channels[channel]
            elif type(channel) is int:
                ch = channel
            else:
                raise ValueError("Canale non valido!")
            
            cmdStr = ""
            
            if max(self.channels.values()) == 2 and ch == 1:
                ch = 2
            
            par = parameter.upper()

            if par in self.couplingParameters:
                cmdStr = (f"SOURCE{ch}:COUPLE:{par}:STATe OFF")
    
                self.device.write(cmdStr)
                
                if ch in self.coupledChannels.keys():
                    self.coupledChannels[ch].pop(par,None)
                
                if len(self.coupledChannels[ch]) == 0:
                    self.device.write(f"SOURCE{ch}:COUPLE:STATe OFF")
                    self.coupledChannels.pop(ch,None)

            else:
                pPoss = ""
                for p in self.couplingParameters:
                    pPoss += f"\t{p}\n"
                raise ValueError("Parametro non valido!\n"
                                 f"Parametri possibili:\n{pPoss}")

        else:
            raise IOError("Device non connesso!")

    def startPulseGenerator(self):
        if self.device is not None:
            self.device.write("AFGControl:START")
        else:
            raise IOError("Device non connesso!")

    def turnOnChannel(self,channel = 1):
        if self.device is not None:
            if type(channel) is str and channel in self.channels.keys():
                ch = self.channels[channel]
            elif type(channel) is int:
                ch = channel
            else:
                raise ValueError("Canale non valido!")
            
            if ch == -1:
                for c in self.channels.values():
                    self.device.write(f"OUTPUT{c} ON")
            else:
                self.device.write(f"OUTPUT{ch} ON")
        else:
            raise IOError("Device non connesso!")
    
    def turnOffChannel(self,channel = 1):
        if self.device is not None:
            if type(channel) is str and channel in self.channels.keys():
                ch = self.channels[channel]
            elif type(channel) is int:
                ch = channel
            else:
                raise ValueError("Canale non valido!")
            
            if ch == -1:
                for c in self.channels.values():
                    self.device.write(f"OUTPUT{c} OFF")
            else:
                self.device.write(f"OUTPUT{ch} OFF")

        else:
            raise IOError("Device non connesso!")
    
    def stopPulseGenerator(self):
        if self.device is not None:
            self.device.write("AFGControl:STOP")
        else:
            raise IOError("Device non connesso!")

    def promptParameters(self,channel = 1):
        if type(channel) is str and channel in self.channels.keys():
            ch = self.channels[channel]
        elif type(channel) is int:
            ch = channel
        else:
            raise ValueError("Canale non valido!")

        pulsePrompt = input("Inserire i parametri da impostare per"
                            f"il canale CH{ch} dell'impulsatore:\n"
                            "Sintassi: <w|h|a|r|f>=<num1>,<num2>,...\n"
                            "w -> durata in ns\n"
                            "h -> frequenza in Hz\n"
                            "a -> ampiezza in mV\n"
                            "r -> rising time in ns\n"
                            "f -> falling time in ns\n\n"
                            ">")
        
        parameters = pulseRegex.findall(pulsePrompt)
        
        paramsDict = defaultdict(list)
        lastKey = ''        
        for p in parameters:
            lastKey = p[0] if p[0] != '' else lastKey
            paramsDict[lastKey].append(p[1])
    
        if paramsDict == {}:
            raise ValueError("Inserire parametri dell'impulsatore!")
        elif 'ah' not in paramsDict.keys() and 'a' not in paramsDict.keys():
            raise ValueError("Inserire almeno un valore per l'ampiezza!")
        elif 'w' not in paramsDict.keys():
            raise ValueError("Inserire almeno un valore per la durata!")
        elif 'h' not in paramsDict.keys():
            raise ValueError("Inserire almeno un valore per la frequenza!")
        else:
            if 'r' not in paramsDict.keys():
                paramsDict['r'] = ['2']
            if 'f' not in paramsDict.keys():
                paramsDict['f'] = ['2']
            if 'al' not in paramsDict.keys():
                paramsDict['al'] = ['0']
            if 'a' in paramsDict.keys():
                paramsDict['ah'] = paramsDict['a']
            
            w = [f"{p}e-9" for p in paramsDict['w']]
            h = [f"{p}" for p in paramsDict['h']]
            ah = [f"{p}e-3" for p in paramsDict['ah']]
            al = [f"{p}e-3" for p in paramsDict['al']]
            r = [f"{p}e-9" for p in paramsDict['r']]
            f = [f"{p}e-9" for p in paramsDict['f']]
            
            self.paramsProduct.update({ch:[p for p in product(ah,al,w,r,f,h)]})
        
        return self.paramsProduct

    def close(self):
        try:
            self.device.close()
        except visa.errors.VisaIOError as e:
            print(f"Errore nella chiusura dell'interfaccia VISA!\n\t{e}")