#!/usr/bin/python
import sys
import numpy as np
import os
import __main__ as main


import pyProbeParticle                as PPU     
from   pyProbeParticle            import basUtils
from   pyProbeParticle            import elements   
import pyProbeParticle.GridUtils      as GU
import pyProbeParticle.HighLevel      as PPH
import pyProbeParticle.cpp_utils      as cpp_utils


if __name__=="__main__":
    HELP_MSG="""Use this program in the following way:
    """+os.path.basename(main.__file__) +""" -i <filename> [ --sigma <value> ]
    Supported file fromats are:
       * cube
       * xsf """
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option( "-i", "--input", action="store", type="string", help="format of input file")
    parser.add_option( "-m", "--Omultipole", action="store", type="string", help="Oxygen (and Carbone)"
                      "model (multipole)", default=None)
    parser.add_option( "-t", "--tip", action="store", type="string", help="tip (metal)"
                      "model (multipole)", default=None)
    parser.add_option( "-E", "--energy", action="store_true",  help="pbc False", default=False)
    parser.add_option("--noPBC", action="store_false",  help="pbc False",
    dest="PBC", default=None)
    parser.add_option( "-w", "--sigma", action="store", type="float",
                      help="gaussian width for convolution in Electrostatics (for C and O) "
                      "[Angstroem]", default=None)
    parser.add_option( "--tipsigma"   , action="store", type="float",
                      help="gaussian width for convolution in Electrostatics (for metallic tip base)"
                      "[Angstroem]", default=None)
    parser.add_option("-f","--data_format" , action="store" , type="string",
                      help="Specify the output format of the vector and scalar "
                      "field. Supported formats are: xsf,npy", default="xsf")
    (options, args) = parser.parse_args()
    print(options)
    opt_dict = vars(options)
    
    if options.input==None:
        sys.exit("ERROR!!! Please, specify the input file with the '-i' option \n\n"+HELP_MSG)
    print(" >> OVEWRITING SETTINGS by params.ini  ")

    if os.path.isfile( 'atomtypes.ini' ):
        print(">> LOADING LOCAL atomtypes.ini")  
        FFparams=PPU.loadSpecies( 'atomtypes.ini' ) 
    else:
        FFparams = PPU.loadSpecies( cpp_utils.PACKAGE_PATH+'/defaults/atomtypes.ini' )

    PPU.loadParams( 'params.ini', FFparams=FFparams)
    PPU.apply_options(opt_dict); #print("DEBUG: PPU.params['tip']", PPU.params['tip']); exit()
    iZs,Rs,Qs=None,None,None
    V=None
    if(options.input.lower().endswith(".xsf") ):
        print(" loading Hartree potential from disk ")
        print("Use loadXSF")
        V, lvec, nDim, head = GU.loadXSF(options.input)
    elif(options.input.lower().endswith(".cube") ):
        print(" loading Hartree potential from disk ")
        print("Use loadCUBE")
        V, lvec, nDim, head = GU.loadCUBE(options.input)
    elif(options.input.lower().endswith(".xyz") ):
        atoms,nDim,lvec=basUtils.loadGeometry(options.input, params=PPU.params)
        iZs,Rs,Qs=PPH.parseAtoms(atoms, autogeom = False, PBC =PPU.params['PBC'],
                                 FFparams=FFparams )
    else:
        sys.exit("ERROR!!! Unknown format of the input file\n\n"+HELP_MSG)
    
    FFel=PPH.computeElFF(V,lvec,nDim,PPU.params['Omultipole'],sigma=PPU.params['sigma'], Fmax=10.0,computeVpot=options.energy,Vmax=10)
    print(" saving electrostatic forcefield ")
    GU.save_vec_field('FFel',FFel,lvec,data_format=options.data_format)
    if (PPU.params['tip'] == None) or (PPU.params['tip'] == 'None') or (PPU.params['tip'] == "None"):
        print("No FFelTip calculated - but linking is still necessary")
        nameend = ".xsf" if options.data_format == "xsf" else ".npy"; print("tip parameters are the same as for oxygen")
        os.symlink("FFel_x"+nameend, "FFelTip_x"+nameend); os.symlink("FFel_y"+nameend, "FFelTip_y"+nameend); os.symlink("FFel_z"+nameend, "FFelTip_z"+nameend);
        if nameend==".npy":
            os.symlink("FFel_vec"+nameend, "FFelTip_vec"+nameend)

    else:
        if (PPU.params['tip']==PPU.params['Omultipole'])and(PPU.params['tipsigma']==PPU.params['sigma']):
            print("FFelTip params are the same as O, we are just linking")
            nameend = ".xsf" if options.data_format == "xsf" else ".npy"; print("tip parameters are the same as for oxygen")
            os.symlink("FFel_x"+nameend, "FFelTip_x"+nameend); os.symlink("FFel_y"+nameend, "FFelTip_y"+nameend); os.symlink("FFel_z"+nameend, "FFelTip_z"+nameend);
            if nameend==".npy":
                os.symlink("FFel_vec"+nameend, "FFelTip_vec"+nameend)
        else:
            print(" saving tip electrostatic forcefield ")
            FFelTip=PPH.computeElFF(V,lvec,nDim,PPU.params['tip'],sigma=PPU.params['tipsigma'],Fmax=10.0,computeVpot=options.energy,Vmax=10)
            GU.save_vec_field('FFelTip',FFelTip,lvec,data_format=options.data_format)
   
    if options.energy :
        GU.save_scal_field( 'Vel', V, lvec, data_format=options.data_format)
    del FFel,V;
    print("Done ")
