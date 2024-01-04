# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 16:17:19 2019

@author: Marco
"""

import pyvisa as visa
import re

numericPattern = "([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)*)"
numericRegex = re.compile(numericPattern)

class oscilloscope(object):
    def __init__(self,visaAddr,nChannels=4,timeout=10000,rst=False):
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
        
        self.measurements = {}

    def performance(self,perf):
        if self.device is not None:
            self.device.write(fr"""vbs 'app.preferences.performance "{perf}"'""")
        else:
            raise IOError("Device non connesso!")

    def displayChannel(self,ch):
        if self.device is not None:
            self.device.write(fr"vbs 'app.acquisition.C{ch}.view = true'")
        else:
            raise IOError("Device non connesso!")

    def hideChannel(self,ch):
        if self.device is not None:
            self.device.write(fr"vbs 'app.acquisition.C{ch}.view = false'")
        else:
            raise IOError("Device non connesso!")

    def scale(self,ch,scale,grain=False):
        if self.device is not None:
            self.device.write(fr"vbs 'app.acquisition.C{ch}.VerScaleVariable = {grain}'")
            self.device.write(fr"vbs 'app.acquisition.C{ch}.VerScale = {scale}'")
        else:
            raise IOError("Device non connesso!")

    def getScale(self,ch):
        if self.device is not None:
            ans = self.device.query(fr"vbs? 'return=app.acquisition.C{ch}.VerScale'")
            resObj = numericRegex.search(ans)
            if resObj is not None:
                resValue = float(resObj.group())
            else:
                resValue = None
            
            return resValue
        else:
            raise IOError("Device non connesso!")

    def offset(self,ch,offset,divControl=False):
        if self.device is not None:
            if divControl is False:
                self.device.write(fr"""vbs 'app.preferences.offsetcontrol = "volts"'""")
            else:
                self.device.write(fr"""vbs 'app.preferences.offsetcontrol = "div"'""")

            self.device.write(fr"vbs 'app.acquisition.C{ch}.VerOffset = {offset}'")
        else:
            raise IOError("Device non connesso!")
    
    def timeBase(self,tbase):
        if self.device is not None:
            self.device.write(fr"vbs 'app.acquisition.horizontal.horscale = {tbase}'")
        else:
            raise IOError("Device non connesso!")
    
    def getTimeBase(self):
        if self.device is not None:
            ans = self.device.query(fr"vbs? 'return=app.acquisition.horizontal.horscale'")
            resObj = numericRegex.search(ans)
            if resObj is not None:
                resValue = float(resObj.group())
            else:
                resValue = None
            
            return resValue
        else:
            raise IOError("Device non connesso!")

    def tOffset(self,offset,divControl=False):
        if self.device is not None:
            if divControl is False:
                self.device.write(fr"""vbs 'app.preferences.horoffsetcontrol = "time"'""")
            else:
                self.device.write(fr"""vbs 'app.preferences.horoffsetcontrol = "div"'""")

            self.device.write(fr"vbs 'app.acquisition.horizontal.horoffset = {offset}'")
        else:
            raise IOError("Device non connesso!")
    
    def triggerOn(self,ch):
        if self.device is not None:
            self.device.write(fr"""vbs 'app.acquisition.trigger.edge.source = "C{ch}"'""")
        else:
            raise IOError("Device non connesso!")
    
    def triggerLevel(self,level):
        if self.device is not None:
            self.device.write(fr"vbs 'app.acquisition.trigger.edge.level = {level}'")
        else:
            raise IOError("Device non connesso!")

    def clearMeasurements(self):
        if self.device is not None:
            self.device.write(fr"vbs 'app.measure.clearall'")
            self.measurements = {}
        else:
            raise IOError("Device non connesso!")

    def clearSweeps(self):
        if self.device is not None:
            self.device.write(fr"vbs 'app.measure.clearsweeps'")
        else:
            raise IOError("Device non connesso!")

    def setMeasure(self,ch,pN,measName):
        if self.device is not None:
            self.device.write(fr"vbs 'app.measure.showmeasure = true'")
            self.device.write(fr"vbs 'app.measure.statson = true'")
            self.device.write(fr"""vbs 'app.measure.p{pN}.paramengine = "{measName}"'""")
            self.device.write(fr"""vbs 'app.measure.p{pN}.source1 = "C{ch}"'""")
            self.device.write(fr"vbs 'app.measure.p{pN}.view = true'")
            self.measurements.update({f"P{pN}":{'name':measName}})
        else:
            raise IOError("Device non connesso!")

    def delMeasure(self,pN):
        if self.device is not None:
            self.device.write(fr"""vbs 'app.measure.p{pN}.paramengine="null"'""")
            self.device.write(fr"vbs 'app.measure.p{pN}.view = false")
            del(self.measurements[f"P{pN}"])
        else:
            raise IOError("Device non connesso!")

    def getMeasure(self,pN,param):
        if self.device is not None:
            ans = self.device.query(fr"vbs? 'return=app.measure.p{pN}.{param}.result.value'")
            resObj = numericRegex.search(ans)
            if resObj is not None:
                resValue = float(resObj.group())
            else:
                resValue = None
            
            self.measurements[f"P{pN}"].update({param:resValue})

            return resValue
        else:
            raise IOError("Device non connesso!")

    def trgStop(self):
        if self.device is not None:
            self.device.write(r"""vbs 'app.acquisition.triggermode = "stop"'""")
        else:
            raise IOError("Device non connesso!")

    def trgNormal(self):
        if self.device is not None:
            self.device.write(r"""vbs 'app.acquisition.triggermode = "normal"'""")
        else:
            raise IOError("Device non connesso!")

    def trgAuto(self):
        if self.device is not None:
            self.device.write(r"""vbs 'app.acquisition.triggermode = "auto"'""")
        else:
            raise IOError("Device non connesso!")

    def close(self):
        try:
            self.device.close()
        except visa.errors.VisaIOError as e:
            print(f"Errore nella chiusura dell'interfaccia VISA!\n\t{e}")
