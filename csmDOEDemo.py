# csmDOEDemo.py
# 2013 01 25
''' demonstrate Design of Expt of LCOE  using OpenMDAO

   Sweeps over a 10x10 grid of rotorDiameter and maxTipSpeed
   Saves output at each point in 'doePts.txt'
   Plots 3-d wireframe diagram of LCOE vs. rDiam and mTS

    Author: G. Scott, NREL, Jan 2013
'''

import sys, os, fileinput
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree, Slot
from openmdao.lib.drivers.api import DOEdriver
from openmdao.lib.doegenerators.api import FullFactorial, Uniform
from openmdao.lib.casehandlers.api import ListCaseRecorder

from lcoe_csm_assembly import lcoe_csm_assembly

global doplot, rpopt
doplot = True
#doplot = False
rpopt = False # if True, optimize with ratedPower rather than maxTipSpeed

try:
    import matplotlib.cm as cm
    import matplotlib.mlab as mlab
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
except:
    doplot = False
    sys.stderr.write("Couldn't find matplotlib - no plots will be generated\n")
    
#-----------------------------------------

class csmDOE(Assembly):
    """Design of Expt for csm LCOE"""
    global doplot, rpopt

    def configure(self):

        # Create Optimizer instance
        self.add('driver',DOEdriver())
        
        self.nfact = 10
        self.rdMin = 110.0
        self.rdMax = 145.0
        self.tsMin =  75.0
        self.tsMax = 100.0
        self.rpMin = 4500.0
        self.rpMax = 5400.0
        
        #There are a number of different kinds of DOE available in openmdao.lib.doegenerators
        self.driver.DOEgenerator = FullFactorial(self.nfact) # Full Factorial DOE with X levels for each variable
        #self.driver.DOEgenerator = Uniform(50) # random uniform sample of points - can't plot results with wireframe

        # Create LCOE instances
        self.add('lcoe', lcoe_csm_assembly())

        # Driver process definition
        self.driver.workflow.add('lcoe')

        self.driver.iprint = 0
        #self.driver.iprint = 1

        # Design Variables
        self.driver.add_parameter('lcoe.rotorDiameter', low=self.rdMin, high=self.rdMax)
        if rpopt:
            self.driver.add_parameter('lcoe.ratedPower',   low=self.rpMin, high=self.rpMax)
        else:
            self.driver.add_parameter('lcoe.maxTipSpeed',  low=self.tsMin, high=self.tsMax)
        
        self.driver.case_outputs = ['lcoe.lcoe', 'lcoe.turbineCost', 'lcoe.BOScost', 
                                    'lcoe.OnMcost', 'lcoe.aep', 'lcoe.ratedPower',
                                    'lcoe.maxTipSpeed']
        
        #Simple recorder which stores the cases in memory.
        self.driver.recorders = [ListCaseRecorder(),]
        
#-----------------------------------------

def main():
    
    global doplot, rpopt
    for i in range(1,len(sys.argv)):
        if sys.argv[i].startswith('-rp'):
        	  rpopt = True
    
    doe_problem = csmDOE()

    import time
    tt = time.time()

    doe_problem.run()

    print "Elapsed time: {:.2f} seconds".format(time.time()-tt)
    
    # show results of each case
    
    lcoeVals = []
    diamVals = []
    tipsVals = []
    rpwrVals = []

    X = np.zeros((doe_problem.nfact, doe_problem.nfact)) 
    Y = np.zeros((doe_problem.nfact, doe_problem.nfact)) 
    Z = np.zeros((doe_problem.nfact, doe_problem.nfact)) 
    
    ofname = 'doePts.txt'
    ofh = open(ofname,'w')
    ofh.write('LCOE    Diam    TipSp  TurbCost     BOSCost    OnMCost    AEP\n')
    nIter = 0
    for c in doe_problem.driver.recorders[0].get_iterator():
        print 'LCOE {:7.5f} at diameter {:6.2f} m TS {:6.2f} mps'.format( 
            c['lcoe.lcoe'], c['lcoe.rotorDiameter'], c['lcoe.maxTipSpeed']),
        print ' T {:9.1f} B {:9.1f} O {:9.1f} A {:9.1f}'.format(
            c['lcoe.turbineCost'], c['lcoe.BOScost'], c['lcoe.OnMcost'],
            c['lcoe.aep']),
        print
        ofh.write('{:7.5f} {:6.2f} {:6.2f} {:9.1f} {:9.1f} {:9.1f} {:9.1f}\n'.format(
            c['lcoe.lcoe'], c['lcoe.rotorDiameter'], c['lcoe.maxTipSpeed'],
            c['lcoe.turbineCost'], c['lcoe.BOScost'], c['lcoe.OnMcost'],
            c['lcoe.aep']))
        
        lcoeVals.append(c['lcoe.lcoe'])
        diamVals.append(c['lcoe.rotorDiameter'])
        tipsVals.append(c['lcoe.maxTipSpeed'])
        rpwrVals.append(c['lcoe.ratedPower'])
        
        ix = nIter / doe_problem.nfact
        iy = nIter % doe_problem.nfact
        X[ix][iy] = c['lcoe.rotorDiameter']
        if rpopt:
        	  Y[ix][iy] = c['lcoe.ratedPower']
        else:
            Y[ix][iy] = c['lcoe.maxTipSpeed']
        Z[ix][iy] = c['lcoe.lcoe']
        nIter += 1
        
    ofh.close()
    sys.stderr.write("Wrote output to '{:}'\n".format(ofname))
    
    if doplot:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        
        if rpopt:
            ax.scatter(diamVals,rpwrVals, zs=lcoeVals) # 3-d sample points
        else:
            ax.scatter(diamVals,tipsVals, zs=lcoeVals) # 3-d sample points
        
        ax.plot(diamVals,tipsVals, zs=lcoeVals[-1]) # 2-d projection
        
        plt.title("DOE Sample Points")
        ax.set_xlabel('Diameter')
        ax.set_ylabel('Tip Speed')
        if rpopt:
            ax.set_ylabel('Rated Power')
        ax.set_zlabel('LCOE')
        ax.set_zlim3d(0.98*min(lcoeVals), 1.02*max(lcoeVals))
      
        ax.plot_wireframe(X,Y,Z)  # wireframe 'surface' defined by sample points
        
        # projections of curves with constant X|Y|Z onto proper plane
        
        cset = ax.contour(X, Y, Z, zdir='z', offset=0.96*min(lcoeVals), cmap=cm.coolwarm)
        cset = ax.contour(X, Y, Z, zdir='x', offset=doe_problem.rdMin-5.0, cmap=cm.coolwarm)
        if rpopt:
            cset = ax.contour(X, Y, Z, zdir='y', offset=doe_problem.rpMin-50.0, cmap=cm.coolwarm)
        else:
            cset = ax.contour(X, Y, Z, zdir='y', offset=doe_problem.tsMax+5.0, cmap=cm.coolwarm)
        
        
        #ax.plot(X, Y, zs=0, zdir='z', label='zs=0, zdir=z')
        	  
        ax.set_xlim(doe_problem.rdMin-5.0, doe_problem.rdMax)
        if rpopt:
            ax.set_ylim(doe_problem.rpMin-50.0, doe_problem.rpMax)
        else:
        	  ax.set_ylim(doe_problem.tsMin, doe_problem.tsMax+5.0)
        ax.set_zlim(0.96*min(lcoeVals), 1.02*max(lcoeVals))

        plt.tight_layout()
        plt.savefig('DOEpts.png')
        sys.stderr.write('Saved plot file DOEpts.png\n')
        plt.show()
    
if __name__=="__main__":

    main()
