

import sys
import glob
import os
import pandas as pd
import numpy as np
import zlib
#from PIL import Image
#import matplotlib.pyplot as plt

def readDat( fname, Header=None ):
    ndir, nfile  = os.path.split( fname )
    ndir=ndir+'/'
    try:
        with open(fname, mode='rb') as binary_file:
            data = binary_file.read() 
    except IOError as error:              
        print(('oops! File '+nfile+' can not be read.'))     
    if b'[Parameter]' in data:
        STMAFMVersion = 1
    elif b'[Paramet32]' in data:
        STMAFMVersion = 2
    elif b'[Paramco32]' in data:
        STMAFMVersion = 3
    else:
    # If none of these is found, stop and signal file error.
        print ('Createc DAT file version does not match')

    # Read out all header information until the max header byte of 16384 bytes.
    header_size=16384
    header_binary =data[0:header_size]

    idx = header_binary.index(b'DSP-COMPDATE')
    header_binary = header_binary[:idx] + b'\r' + header_binary[idx:];
    header_binary=header_binary.splitlines()
    ind = [i for i, s in enumerate(header_binary) if b'DSP-COMPDATE' in s][0]; header_binary[ind]


    d = []
    for i in range(1,ind):
        #try:
            tmp=header_binary[i].split(b'=');
            d.append((tmp[0],tmp[1]))
        #except:
        #    pass
    SplittedLine=pd.DataFrame(d, columns=('parameter', 'value'))


    if Header is None:
        Header = {}
    
    Header['ScanPixels_X'] = int(SplittedLine.loc[SplittedLine['parameter'] == b'Num.X / Num.X'].value.item())
    Header['ScanPixels_Y'] = int(SplittedLine.loc[SplittedLine['parameter'] == b'Num.Y / Num.Y'].value.item())
    Header['GainX'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'GainX / GainX'].value.item())
    Header['GainY'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'GainY / GainY'].value.item())
    Header['GainZ'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'GainZ / GainZ'].value.item())
    Header['GainPreamplifier'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Gainpreamp / GainPre 10^'].value.item())
    Header['ChannelCount'] = int(SplittedLine.loc[SplittedLine['parameter'] == b'Channels / Channels'].value.item())
    Header['DACToZConversionFactor'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Dacto[A]z'].value.item())
    Header['DACToXYConversionFactor'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Dacto[A]xy'].value.item())
    Header['ScanRange_X'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Length x[A]'].value.item())
    Header['ScanRange_Y'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Length y[A]'].value.item())
    Header['ScanOffset_X'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Scanrotoffx / OffsetX'].value.item())
    Header['ScanOffset_Y'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Scanrotoffy / OffsetY'].value.item())
    Header['Bias'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Biasvolt[mV]'].value.item())
    Header['Current'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Current[A]'].value.item())
    Header['ACQ_Time'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Sec/Image:'].value.item())
    Header['ScanAngle'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Rotation / Rotation'].value.item())
    Header['ZControllerSetpoint'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'FBLogIset'].value.item())
    Header['ZControllerIntegralGain'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'FBIntegral'].value.item())
    Header['ZControllerProportionalGain'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'FBProp'].value.item())
    Header['PiezoX'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Xpiezoconst'].value.item())
    Header['LengthX'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Length x[A]'].value.item())
    Header['LengthY'] = float(SplittedLine.loc[SplittedLine['parameter'] == b'Length y[A]'].value.item())    

    #print " int(SplittedLine.loc[SplittedLine['parameter'] ", int(SplittedLine.loc[SplittedLine['parameter'] == b'Num.X / Num.X'].value.item())
    '''
    keyws = [ b'Num.X / Num.X', b'Num.Y / Num.Y', b'GainX / GainX', b'GainY / GainY', b'GainZ / GainZ', b'Gainpreamp / GainPre 10^', b'Channels / Channels'
        b'Dacto[A]z', b'Dacto[A]xy', b'Length x[A]', b'Length y[A]', b'Scanrotoffx / OffsetX', b'Scanrotoffy / OffsetY', b'Biasvolt[mV]', b'Current[A]', b'Sec/Image:'
         b'Rotation / Rotation', b'FBLogIset', b'FBIntegral', b'FBProp', b'Xpiezoconst'
     ]
    for keyw in keyws:
        try:
            print "keyw", keyw
            val = SplittedLine.loc[SplittedLine['parameter'] ==  keyw ].value.item()
            Header[ keyw.decode('ascii') ] = val
        except:
            print "keyw WRONG:", keyw
            pass
    '''

    if STMAFMVersion == 1:
        BytePerPixel = 2
        # Header + 2 unused "NULL"-Bytes
        data_start=header_size+2
    elif STMAFMVersion == 2:
        BytePerPixel = 4
        # Header + 4 unused "NULL"-Bytes
        data_start=header_size+4
    elif STMAFMVersion == 3:
        BytePerPixel = 4
        data_start=header_size
        # No Seek of additional bytes, since they are compressed:
    image_data=data[data_start:]
    x = zlib.decompress(image_data)
    y = np.frombuffer(x, dtype=np.float32 ).transpose()
    y=y[1:]
    y=y[:-4*Header['ScanPixels_X']+1];
    #because some files have corrupted length we continue it with zeros to obtain coorect reshape to 2D	
    y_round_size=int(np.ceil(float(len(y))/float(Header['ScanPixels_X']))*Header['ScanPixels_X'])
    y_round=np.zeros(y_round_size);
    y_round[:len(y)]=y
    mat_image=y_round.reshape(-1,Header['ScanPixels_X']);
    y_size=Header['ScanPixels_Y']
    pic1=mat_image[:y_size,:]
    pic2=mat_image[y_size:2*y_size,:]
    pic3=mat_image[2*y_size:3*y_size,:]
    pic4=mat_image[3*y_size:,:] 
    return (pic1,pic2,pic3,pic4) 
'''
    output_dir=ndir+'npy_png/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_npy=nfile[:-3]+'npy'
    file_png=nfile[:-3]+'png'
    np.save(output_dir+file_npy, pic2)
    print(output_dir+file_npy)
    plt.imshow(pic2)
    plt.colorbar()
    plt.savefig(output_dir+file_png)
    plt.close()
    '''


