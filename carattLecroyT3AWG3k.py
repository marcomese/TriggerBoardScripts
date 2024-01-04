# -*- coding: utf-8 -*-

import pulseGenLib as pgen
import oscLib as oscl
from time import sleep

oscAddr = 'TCPIP0::jemeusohd06k.na.infn.it::inst0::INSTR'
impAddr = 'TCPIP0::jemeusot3awg3k.na.infn.it::inst0::INSTR'

impTrgOnCH = 1
impAcqOnCH = (1-impTrgOnCH)+2

try:
    print("Connessione all'impulsatore...")
    imp = pgen.pulseGenerator(impAddr)
    
    print("Connessione all'oscilloscopio...")
    osc = oscl.oscilloscope(oscAddr)
    
    acqTime = float(input("Inserire la durata dell'acquisizione in secondi: "))
    
    outFileName = input("Inserire il nome del file da generare: ")
    outFile = open(f"{outFileName}.dat","w")

    imp.promptParameters("ch1")
    imp.promptParameters("ch2")
    
    osc.hideChannel(3)
    osc.hideChannel(4)
    
    osc.performance("analysis")
    
    print("Configuro il trigger dell'oscilloscopio (canale CH2)")
    osc.triggerOn(2)
    vImpTrgCH = float(imp.paramsProduct[impTrgOnCH][0][0])
    osc.triggerLevel(vImpTrgCH/4)
    osc.offset(2,0)

    print("Elimino tutte le misure")
    osc.clearMeasurements()

    print("Configuro le misure per il canale CH1 dell'oscilloscopio")
    osc.setMeasure(1,1,"rise")
    osc.setMeasure(1,2,"fall")
    osc.setMeasure(1,3,"width")
    osc.setMeasure(1,4,"top")
    osc.setMeasure(1,5,"area")
    osc.setMeasure(1,6,"ampl")
    osc.setMeasure(1,7,"max")

    print(f"Configuro il canale di trigger (CH{impTrgOnCH}) dell'impulsatore")
    imp.configurePulse(f"ch{impTrgOnCH}",*imp.paramsProduct[impTrgOnCH][0])
    imp.coupleToChannel1("frequency")
    imp.coupleToChannel1("phase")

    outFile.write("Vimp,trise,Strise,tfall,Stfall,width,"
                  "Swidth,Vtop,SVtop,charge,Scharge,measNum,"
                  "Vampl,SVampl,Vmax,SVmax\n")

    for p in imp.paramsProduct[impAcqOnCH]:
        print("Configuro la scala verticale del canale CH1 dell'oscilloscopio")
        divisions = float(p[0])/4
        osc.scale(1,divisions,grain=True)
        
        oscVDiv = osc.getScale(1)
        
        osc.offset(1,-2*oscVDiv)


        print("Configuro la scala orizzontale dell'oscilloscopio")
        tDivisions = float(p[2])/5
        osc.timeBase(tDivisions)
        
        oscTDiv = osc.getTimeBase()
        
        osc.tOffset(-3.5*oscTDiv)

        print(f"Configuro il canale CH{impAcqOnCH} dell'impulsatore:\n"
              f"\tV = {p[0]}V, T = {p[2]}s")
        imp.configurePulse(f"ch{impAcqOnCH}",*p)
        sleep(1)
        imp.turnOnChannel(1)
        imp.turnOnChannel(2)
        sleep(1)
        imp.startPulseGenerator()
        sleep(1)
        
        osc.clearSweeps()
        
        sleep(acqTime)
        
        for i in range(len(osc.measurements)):
            osc.getMeasure(i+1,"mean")
            osc.getMeasure(i+1,"sdev")
            osc.getMeasure(i+1,"num")
        
        riseRes = osc.measurements['P1']
        fallRes = osc.measurements['P2']
        widthRes = osc.measurements['P3']
        topRes = osc.measurements['P4']
        areaRes = osc.measurements['P5']
        amplRes = osc.measurements['P6']
        maxRes = osc.measurements['P7']
        
        outFile.write(f"{p[0]},"
                      f"{riseRes['mean']:.3e},{riseRes['sdev']:.3e},"
                      f"{fallRes['mean']:.3e},{fallRes['sdev']:.3e},"
                      f"{widthRes['mean']:.3e},{widthRes['sdev']:.3e},"
                      f"{topRes['mean']:.3e},{topRes['sdev']:.3e},"
                      f"{areaRes['mean']/50:.3e},{areaRes['sdev']/50:.3e},"
                      f"{areaRes['num']:.3e},"
                      f"{amplRes['mean']:.3e},{amplRes['sdev']:.3f},"
                      f"{maxRes['mean']:.3e},{maxRes['sdev']:.3e}\n")

        imp.turnOffChannel(1)
        imp.turnOffChannel(2)

    outFile.close()

except IOError as e:
    print(f"Errore: {e}")
except ValueError as e:
    print(f"Errore: {e}")
finally:
    print("Disconnessione dei dispositivi...")
    osc.close()
    osc = None
    imp.close()
    imp = None
    outFile.close()