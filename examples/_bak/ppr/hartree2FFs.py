#!/usr/bin/python
import sys
import numpy as np
import basUtils
import elements
import GridUtils     as GU
import ProbeParticle as PP
from libFFTfin import *
from optparse import OptionParser


parser = OptionParser()
parser.add_option( "-i", "--input", action="store", type="string", help="format of input file", default='vasp.locpot.xsf')
(options, args) = parser.parse_args()

num = len(sys.argv)
if (num < 2):
    sys.exit("Number of arguments = "+str(num-1)+". This script should have at least one argument. I am terminating...")
finput = sys.argv[num-1]

# --- initialization ---

sigma  = 1.0 # [ Angstroem ] 

print('--- Data Loading ---')

# TODO with time implement reading a hartree potential generated by different software
if(options.input == 'vasp.locpot.xsf'):
    V, lvec, nDim, head = GU.loadXSF(finput)
elif(options.input == 'aims.cube'):
    V, lvec, nDim, head = GU.loadCUBE(finput)


print('--- Preprocessing ---')

sampleSize = getSampleDimensions(lvec)
dims = (nDim[2], nDim[1], nDim[0])

xsize, dx = getSize('x', dims, sampleSize)
ysize, dy = getSize('y', dims, sampleSize)
zsize, dz = getSize('z', dims, sampleSize)

dd = (dx, dy, dz)

X, Y, Z = getMGrid(dims, dd)

print('--- Get Probe Density ---')

rho = getProbeDensity(sampleSize, X, Y, Z, sigma, dd, {'dz2':1.0})

print('--- Get Forces ---')
Fx, Fy, Fz = getForces( V, rho, sampleSize, dims, dd, X, Y, Z)
print('Fx.max(), Fx.min() = ', Fx.max(), Fx.min())


PP.params['gridA'] = lvec[ 1,:  ].copy()
PP.params['gridB'] = lvec[ 2,:  ].copy()
PP.params['gridC'] = lvec[ 3,:  ].copy()
PP.params['gridN'] = nDim.copy()

print("--- Compute Lennard-Jones Force-filed ---")
atoms     = basUtils.loadAtoms('input.xyz')
if os.path.isfile( 'atomtypes.ini' ):
    print(">> LOADING LOCAL atomtypes.ini")  
    FFparams=PPU.loadSpecies( 'atomtypes.ini' ) 
else:
    FFparams = PPU.loadSpecies( cpp_utils.PACKAGE_PATH+'/defaults/atomtypes.ini' )

iZs,Rs,Qs = PP.parseAtoms(atoms, autogeom = False, PBC = True,
                          FFparams=FFparams)
FFLJ      = PP.computeLJ( Rs, iZs, FFLJ=None, FFparams=FFparams)

print("--- Saving ---")

GU.saveXSF('FFel_x.xsf', Fx, lvec, head)
GU.saveXSF('FFel_y.xsf' , Fy, lvec, head)
GU.saveXSF('FFel_z.xsf' , Fz, lvec, head)

GU.saveVecFieldXsf( 'FFLJ', FFLJ, lvec, head)

