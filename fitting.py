#!/usr/bin/python
import sys
import numpy as np
import os
import __main__ as main
from optparse import OptionParser
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import minimize,basinhopping

from pyProbeParticle import basUtils
import pyProbeParticle.GridUtils as GU
import pyProbeParticle  as PPU
import pyProbeParticle.HighLevel as PPH


iteration=0

def pm2a(val):
    """
    Function which converts picometers in angstroms"
    """
    res=float(val)/100
    return res

def pN2ev_o_a(val):
    """
    Function which converts forces from piconewtons to ev/A
    """
    res=float(val)*6.241506363094e-4
    return res

def getFzlist(BIGarray,MIN,MAX,points):
    """
    Function makes an interpolation of a function stored in the BIGarray and finds its values in the "points"
    BIGarray - a 3d array containing a grid of function values
    MIN,MAX  - 1d array containing the minimum and maximum values of x,y,z
    """
    x=np.linspace(MIN[0],MAX[0],int(BIGarray.shape[2]))
    y=np.linspace(MIN[1],MAX[1],int(BIGarray.shape[1]))
    z=np.linspace(MIN[2],MAX[2],int(BIGarray.shape[0]))
    result=[]
    interp = RegularGridInterpolator((z, y, x), BIGarray)
#    print BIGarray.shape
    for p in points :
        if (p >= MIN).all() and (p <= MAX).all():
            result.append(interp([p[2],p[1],p[0]])[0])
#    print "TEST", interp([MAX[2], current_pos[1],current_pos[0]])
#    print "TEST", interp([8.0, current_pos[1],current_pos[0]])
    return np.array(result)

FFparams=None
if os.path.isfile( 'atomtypes.ini' ):
	print(">> LOADING LOCAL atomtypes.ini")  
	FFparams=PPU.loadSpecies( 'atomtypes.ini' ) 
        print(FFparams)
        elem_dict={}
        for i,ff in enumerate(FFparams):
            elem_dict[ff[3]] = i
else:
    raise ValueError('Please provide the file "atomtypes.ini"')

print(" >> OVEWRITING SETTINGS by params.ini  ")
PPU.loadParams( 'params.ini',FFparams=FFparams )
scan_min=PPU.params['scanMin']
scan_max=PPU.params['scanMax']
atoms,nDim,lvec=basUtils.loadGeometry("p_eq.xyz", params=PPU.params)
# The function automatically load the geometry from the file of any
# supported format. The desigion about the file format is based on the
# filename extension
PPU.params['gridN'] = nDim
PPU.params['gridA'] = lvec[1]
PPU.params['gridB'] = lvec[2]
PPU.params['gridC'] = lvec[3]
V, lvec_bak, nDim_bak, head = GU.loadCUBE("hartree.cube")
FFel=PPH.computeElFF(V,lvec_bak,nDim_bak,'s',sigma=PPU.params['sigma'])
loaded_forces=np.loadtxt("frc_tip.txt",
                         converters={0:pm2a,1:pm2a,2:pm2a},
                         skiprows=2, usecols=(0,1,2,5))
loaded_o_pos=np.loadtxt("co_pos.txt", skiprows=2, usecols=(6,7,8))
points=loaded_forces[:,:3]
iZs,Rs,Qs=PPH.parseAtoms(atoms, autogeom = False, PBC = PPU.params['PBC'], FFparams=FFparams )
from collections import OrderedDict
fit_dict=OrderedDict()
def update_atoms(atms=None):
#    print "UPDATING ATOMS"
#    print atms
    x=[]
    constr=[]
    min_range=0.8
    max_range=1.2
    for atm in atms:
        i=elem_dict[atm[0]]
        val1,val2=float(atm[1]),float(atm[2])
        FFparams[i][0]=val1
        x.append(val1)
#        constr.append((val1*min_range,val1*max_range ) )
        constr.append((1.0,3.0) )
        FFparams[i][1]=float(atm[2])
        x.append(val2)
        constr.append((1e-6,0.1 ) )
    #print "UPDATING : " ,x
    return x,constr

def set_fit_dict(opt=None):
    i=0
    x=[]
    constr=[]
    for key,value in opt.items():
            if opt[key] is None:
                continue
            if key is "atom":
                if key not in fit_dict:
                    fit_dict['atom']=[]
                print(opt[key])
                x_tmp,constr_tmp=update_atoms(value)
                x+=x_tmp
                constr+=constr_tmp
                for val in value:
                    fit_dict['atom'].append(list(val))
            elif (key is "ChargeCuDown"):
                constr.append((-1,1))
                fit_dict[key]=opt[key]
                x.append(opt[key])
            elif (key is "ChargeCuUp"):
                constr.append((-1,1))
                fit_dict[key]=opt[key]
                x.append(opt[key])
            elif (key is "Ccharge"):
                constr.append((-1,1))
                fit_dict[key]=opt[key]
                x.append(opt[key])
            elif (key is "Ocharge"):
                constr.append((-1,1))
                fit_dict[key]=opt[key]
                x.append(opt[key])
            elif (key is "sigma"):
                constr.append((0.001,3))
                fit_dict[key]=opt[key]
                x.append(opt[key])
            elif (key is "Cklat"):
                constr.append( (0.001,5) )
                fit_dict[key]=opt[key]
                x.append(opt[key])
            elif (key is "Oklat"):
                constr.append( (0.001,5) )
                fit_dict[key]=opt[key]
                x.append(opt[key])
            elif (key is "krad"):
                constr.append( (0.01,100) )
                fit_dict[key]=opt[key]
                x.append(opt[key])
            else:
                continue
            i+=1
    return np.array(x),constr
def update_fit_dict(x=[]):
    i=0
    for key,value in fit_dict.items():
        if key is "atom":
            for atm in value:
#                print atm
                atm[1]=x[i]
                atm[2]=x[i+1]
                i+=2
        else:
            fit_dict[key]=x[i]
            i+=1


def comp_msd(x=[]):
    """ Function computes the Mean Square Deviation of DFT forces (provided in the file frc_tip.ini)
    and forces computed with the ProbeParticle approach"
    """
    global iteration
    iteration+=1
    update_fit_dict(x) # updating the array with the optimized values
    PPU.apply_options(fit_dict) # setting up all the options according to their
                                # current values
    try:
        fit_dict['atom']
        update_atoms(atms=fit_dict['atom'])
        print("Atom section is defined")
    except:
        print("Atom section is not defined")

    print(FFparams)
    FFLJC,VLJC,FFLJO,VLJO=PPH.computeLJFF(iZs,Rs,FFparams)
    #GU.save_vec_field( 'FFLJC', FFLJC, lvec)
    #GU.save_vec_field( 'FFLJO', FFLJO, lvec)
#    sys.exit()
    FFboltz=None
    fzs,PPCpos,PPOpos,lvecScan=PPH.perform_relaxation(lvec,FFLJC,FFLJO,FFel,FFTip=FFel[:,:,:,2].copy())

    print("Copying PP positions")
    posXC=PPCpos[:,:,:,0].copy()
    posYC=PPCpos[:,:,:,1].copy()
    posZC=PPCpos[:,:,:,2].copy()
    posXO=PPOpos[:,:,:,0].copy()
    posYO=PPOpos[:,:,:,1].copy()
    posZO=PPOpos[:,:,:,2].copy()
    xTips, yTips, zTips, garbage = PPU.prepareScanGrids()
    minimum=[min(xTips), min(yTips), min(zTips)]
    maximum=[max(xTips), max(yTips), max(zTips)]
#    print minimum
#    print maximum
#    print "x shape", posX.shape
#    print "TYT"
    print("Getting interpolated values")
    Fzlist=getFzlist(BIGarray=fzs, MIN=scan_min, MAX=scan_max, points=points)
    XlistC=getFzlist(BIGarray=posXC, MIN=minimum, MAX=maximum, points=points)
    YlistC=getFzlist(BIGarray=posYC, MIN=minimum, MAX=maximum, points=points)
    ZlistC=getFzlist(BIGarray=posZC, MIN=minimum, MAX=maximum, points=points)
    XlistO=getFzlist(BIGarray=posXO, MIN=minimum, MAX=maximum, points=points)
    YlistO=getFzlist(BIGarray=posYO, MIN=minimum, MAX=maximum, points=points)
    ZlistO=getFzlist(BIGarray=posZO, MIN=minimum, MAX=maximum, points=points)
    """
    pr=0
    for i,x in enumerate( xTips):
        for j,y in enumerate( yTips):
            for k,z in enumerate( zTips):
                print x, y , z, Xlist[pr], Ylist[pr], Zlist[pr], points[pr], loaded_o_pos[pr,0] , loaded_o_pos[pr,1], loaded_o_pos[pr,2]
                pr+=1
    sys.exit()
    """
    print("Computing msd")
    Fzlist=getFzlist(BIGarray=fzs, MIN=scan_min, MAX=scan_max, points=points)
    dev_arr=np.abs(loaded_forces[:,3]-Fzlist*1.60217733e3)
    max_dev=np.max(dev_arr)
    msd=np.sum(dev_arr**4) /len(Fzlist)
    print("Printing fz pp")
    with open("fz_pp.dat", 'w') as f:
        for i,elem in enumerate(points):
            f.write("{} {} {}".format(elem[0]*100,elem[1]*100,elem[2]*100))
            f.write(" {} \n".format(Fzlist[i]*1.60217733e3))

    dev_O_x=np.sum((XlistO-loaded_o_pos[:,0])**2)/len(Fzlist)*10000
    dev_O_y=np.sum((YlistO-loaded_o_pos[:,1])**2)/len(Fzlist)*10000
    dev_O_z=np.sum((ZlistO-loaded_o_pos[:,2])**2)/len(Fzlist)*10000

    print("Printing tip's trajectory")
    with open("trajectory.xyz", 'w') as f:
        for i,elem in enumerate(points):
            f.write("3\n\n")
            f.write("Cu {} {} {}\n".format(elem[0],elem[1],elem[2]))
            f.write("C {} {} {}\n".format(XlistC[i],YlistC[i],ZlistC[i]))
            f.write("O {} {} {}\n".format(XlistO[i],YlistO[i],ZlistO[i]))

    print("Deviation: xpos, ypos, zpos, Fz: ", dev_O_x, dev_O_y, dev_O_z, msd)
    with open ("iteration.txt", "a") as myfile:
        myfile.write( "iteration {}: {} max dev: {} sigma^2: {} x-disp: {} y-disp: {} z-dizp: {} total: {}"
        "\n".format(iteration, x, max_dev, msd, dev_O_x, dev_O_y, dev_O_z, msd+dev_O_x+dev_O_y+dev_O_z))
    return msd + dev_O_z+dev_O_y+dev_O_x

if __name__=="__main__":
    parser = OptionParser()
    parser.add_option( "--Ccharge", action="store", type="float", help="fit "
    "Carbon charge ", default=None)
    parser.add_option( "--Ocharge", action="store", type="float", help="fit "
    "Oxygen charge ", default=None)
    parser.add_option( "--ChargeCuUp", action="store", type="float", help="fit "
    "Cu Up charge", default=None)
    parser.add_option( "--ChargeCuDown", action="store", type="float", help="fit "
    "Cu Up charge", default=None)
    parser.add_option( "-s","--sigma", action="store", type="float", help="Fit "
    "the gaussian width of the charge distribution", default=None)
    parser.add_option( "--Cklat", action="store", type="float", help="Fit "
    "the lateral stiffness of the Carbon atom", default=None)
    parser.add_option( "--Oklat", action="store", type="float", help="Fit "
    "the lateral stiffness of the Oxygen atom", default=None)
    parser.add_option( "--Ckrad", action="store", type="float", help="Fit "
    "the radial stiffness of the Carbon atom", default=None)
    parser.add_option( "--Okrad", action="store", type="float", help="Fit "
    "the radial stiffness of the Oxygen atom", default=None)
    parser.add_option( "-a","--atom", action="append", type="string",help="Fit "
    "the LJ parameters of the given atom", default=None, nargs=3)
    parser.add_option( "--nobounds", action="store_true",
    help="Skipf the first optimization step with bounds", default=False)

    (options, args) = parser.parse_args()
    opt_dict = vars(options)
    PPU.apply_options(opt_dict) # setting up all the options according to their
    x_new,bounds=set_fit_dict(opt=opt_dict)
    print("params", x_new)
    print("bounds", bounds)
#    print "fit_dict", fit_dict
    it=0
    if opt_dict['nobounds'] is not True:
        while   it == 0 or np.max(np.abs((x-x_new)/x)) > 0.10:
            x=x_new.copy()
            print("Starting bounded optimization")
            result=minimize(comp_msd,x,bounds=bounds)
            x_new=result.x.copy()
            it+=1
    print("Bounded optimization is finished")
    it=0
    while   it == 0 or np.max(np.abs((x-x_new)/x)) > 0.001:
        print("Starting non-bounded optimization")
        x=x_new.copy()
        result=minimize(comp_msd,x,method='Nelder-Mead')
        x_new=result.x.copy()
        it+=1
    print("Non-bounded optimization is finished")

