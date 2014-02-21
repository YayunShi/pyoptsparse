from __future__ import print_function
#!/usr/bin/env python
import time, sys
from pyoptsparse import Optimization
import os, argparse
import numpy
import sys
import pdb
# import cProfile

parser = argparse.ArgumentParser()
parser.add_argument("--sens",help="sensitivity mode",type=str, default='FD')
parser.add_argument("--constrained",help="constrained or not",type=int,default=0)
parser.add_argument("--testHist",help="test history",type=str,default="no")
parser.add_argument("--groups",help="use groups",type=int, default=0)
parser.add_argument("--sensMode",help="gradient mode",type=str, default='')
parser.add_argument("--opt",help="optimizer",type=str, default='SNOPT')
parser.add_argument('--pythonProf',help="profile in Python",type=int,default=0)
args = parser.parse_args()
sens = args.sens
constrained = args.constrained
testHist = args.testHist
groups = args.groups
sensMode = args.sensMode
pythonProf = args.pythonProf
if args.opt.lower() == 'ipopt':
    from pyoptsparse import IPOPT as OPT
    optOptions={'max_iter':150,
                'tol': 1e-6,
                'derivative_test':'first-order',
                'derivative_test_print_all':'yes',
                'derivative_test_tol':1e-4,
                'output_file':'testoutIPOPT.out'}
elif args.opt.lower() == 'snopt':
    from pyoptsparse import SNOPT as OPT
    optOptions = {}
elif args.opt.lower() == 'slsqp':
    from pyoptsparse import SLSQP as OPT
    optOptions = {}
elif args.opt.lower() == 'conmin':
    from pyoptsparse import CONMIN as OPT
    optOptions = {}
elif args.opt.lower() == 'fsqp':
    from pyoptsparse import FSQP as OPT
    optOptions = {}
elif args.opt.lower() == 'nlpql':
    from pyoptsparse import NLPQL as OPT
    optOptions = {}
elif args.opt.lower() == 'nlpy_auglag':
    from pyoptsparse import NLPY_AUGLAG as OPT
    optOptions = {}

def objfunc(xx):
    x = xx['x'] # Extract array

    fobj = 100*(x[1]-x[0]**2)**2+(1-x[0])**2

    fcon = {}
    fcon['con'] = 0.1-(x[0]-1)**3 - (x[1]-1)

    fail = False

    return fobj, fcon, fail

def sensfunc(xx, fobj, fcon):
    x = xx['x'] # Extract array

    gobj = {}
    gobj['x'] = [2*100*(x[1]-x[0]**2)*(-2*x[0]) - 2*(1-x[0]),
                     2*100*(x[1]-x[0]**2)]
    gcon = {}
    gcon['con'] = {'x':[-3*(x[0]-1)**2, -1]}
    fail = False

    return gobj, gcon, fail


# Matrix-free algorithm return functions
def objgrad(xx):
    x = xx['x']
    # x = xx

    gobj = numpy.array([2*100*(x[1]-x[0]**2)*(-2*x[0]) - 2*(1-x[0]),
                    2*100*(x[1]-x[0]**2)])
    fail = False

    return gobj, fail


def jprod(xx,p,sparse_only):
    x = xx['x']
    # x = xx

    if constrained:
        q = numpy.zeros(1)
        gcon = numpy.array([-3*(x[0]-1)**2, -1])
        q = numpy.dot(gcon,p)
    else:
        q = numpy.zeros(0)
    fail = False

    return q, fail


def jtprod(xx,q,sparse_only):
    x = xx['x']
    # x = xx

    p = numpy.zeros(len(x))
    if constrained:
        gcon = numpy.array([-3*(x[0]-1)**2, -1])
        p = q*gcon
    fail = False

    return p, fail


if sens == 'none':
    sens = None
if sens == 'user':
    sens = sensfunc
if sens == 'matrix-free':
    sens = [objgrad,jprod,jtprod]

# Instantiate Optimization Problem
optProb = Optimization('Rosenbrock function', objfunc)
optProb.addVarGroup('x', 2, 'c', value=[3,-3], lower=-5.12, upper=5.12,
                    scale=[1.0, 1.0])
optProb.finalizeDesignVariables()
if constrained:
    optProb.addCon('con',upper=0, scale=1.0)
optProb.addObj('f')

# Create optimizer
opt = OPT(options=optOptions)
if testHist == 'no':
    # Just run a normal run
    sol = opt(optProb, sens=sens, sensMode=sensMode)
    print(sol.fStar)
else:
    # First call just does 10 iterations
    if args.opt.lower() == 'snopt':
        opt.setOption('Major iterations limit',10)
        solSnopt1 = opt(optProb, sens=sens, sensMode='pgc', storeHistory='opt_hist')

        # Now we are allowed to do 50
        opt.setOption('Major iterations limit',50)
        if testHist == 'hot':
            solSnopt2 = opt(optProb, sens=sens, sensMode=sensMode,
                              hotStart='opt_hist', storeHistory='opt_hist')
        else:
            solSnopt2 = opt(optProb, sens=sens, sensMode=sensMode,
                              coldStart='opt_hist', storeHistory='opt_hist')

        print(solSnopt2.fStar)

    else:
        # Quick test that history prints ok
        # if pythonProf:
        #     cProfile.run('sol = opt(optProb, sens=sens, sensMode=sensMode, storeHistory=\'opt_hist.bin\')',args.opt.lower()+'_profile.profile')
        # else:
        sol = opt(optProb, sens=sens, sensMode=sensMode, storeHistory='opt_hist.bin')