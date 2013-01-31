# csmSensDemo.py
# 2013 01 24
''' demonstrate sensitivity of LCOE to different parameters using OpenMDAO

    Author: G. Scott, NREL, Jan 2013
'''

import sys, os, fileinput
from lcoe_csm_assembly import lcoe_csm_assembly

global doplot
doplot = True
try:
    import matplotlib.cm as cm
    import matplotlib.mlab as mlab
    import matplotlib.pyplot as plt
except:
    doplot = False
    sys.stderr.write("Couldn't find matplotlib - no plots will be generated\n")
    
#-----------------------------------------

def lcoePlot(x,y,xname,subplt=111, lcoe=None):
    
    global doplot
    if not doplot:
        return
        
    if subplt==111:
        fig = plt.figure()
    plt.subplot(subplt)
    
    plt.plot(x,y)
    plt.plot(x,y,'b+')
    
    if lcoe is not None:
        ymin = 0.90*lcoe
        ymax = 1.10*lcoe
        plt.ylim(ymin,ymax)
    
    plt.ylabel('LCOE')
    plt.xlabel(xname)
    plt.title('LCOE vs. {:}'.format(xname))
    plt.grid()
    
    if subplt==111:
        plt.show()

#-----------------------------------------

def main():
    
    global doplot
    
    lcoe = lcoe_csm_assembly()
    
    lcoe.advancedBlade = True
    
    lcoe.execute()
    
    #lcoe.printResults()
    lcoe.printShortHeader()
    lcoe.printShortResults()
    
    lcoe.advancedBlade = False
    
    lcoe.execute()
    
    #lcoe.printResults()
    lcoe.printShortResults()
    
    #--------------  Sensitivity analysis  --------------
    
    import numpy as np
    
    # keep default values so we can reset
    
    hhDefault = lcoe.hubHeight
    tsDefault = lcoe.maxTipSpeed
    rdDefault = lcoe.rotorDiameter
    rpDefault = lcoe.ratedPower
    lcoe_start = lcoe.lcoe
    
    # sweep over hubht (hubHeight = 90.0)
    
    x = []
    y = []
    for hubht in np.arange(70.0,121.0,10.0):
        lcoe.hubHeight = hubht
        lcoe.execute()
        print '{:4.0f}m '.format(hubht),
        lcoe.printShortResults()
        x.append(hubht)
        y.append(lcoe.lcoe)
    lcoe.hubHeight = hhDefault
    lcoePlot(x,y,'HubHeight (m)', 221, lcoe_start)
    
    # sweep over rotor diameter (rotorDiameter=126.0)
    
    x = []
    y = []
    for rotorDiameter in np.arange(112.0,141.0,2.0):
        lcoe.rotorDiameter = rotorDiameter
        lcoe.execute()
        print '{:4.0f}m '.format(rotorDiameter),
        lcoe.printShortResults()
        x.append(rotorDiameter)
        y.append(lcoe.lcoe)
    lcoe.rotorDiameter = rdDefault
    lcoePlot(x,y,'Rotor Diameter (m)', 222, lcoe_start)
    
    # sweep over tip speed (maxTipSpeed = 80.0)
    
    x = []
    y = []
    for maxTipSpeed in np.arange(70.0,101.0,2.0):
        lcoe.maxTipSpeed = maxTipSpeed
        lcoe.execute()
        print '{:4.0f}mps '.format(maxTipSpeed),
        lcoe.printShortResults()
        x.append(maxTipSpeed)
        y.append(lcoe.lcoe)
    lcoe.maxTipSpeed = tsDefault
    lcoePlot(x,y,'Max Tip Speed (m/s)', 223, lcoe_start)
    
    # sweep over rated power (ratedPower = 5000.0)
    
    x = []
    y = []
    for ratedPower in np.arange(4500.0,5501.0,100.0):
        lcoe.ratedPower = ratedPower
        lcoe.execute()
        print '{:4.0f}kW '.format(ratedPower),
        lcoe.printShortResults()
        x.append(ratedPower)
        y.append(lcoe.lcoe)
    lcoe.ratedPower = rpDefault
    lcoePlot(x,y,'Rated Power (kW)', 224, lcoe_start)
    
    if doplot:
        plt.tight_layout()
        plt.savefig('csmdemo.png')
        plt.show()
    
if __name__=="__main__":

    main()
