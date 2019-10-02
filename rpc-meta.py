import sys
import gdal
import numpy as np


print('arg:', sys.argv)


def save_meta(rpc_in, tif_in, fname_out):
    def check_key(key0, key, meta):
        key = key0
        if key in meta:
            meta[key] = meta[key] + ' ' + str(float(val.split('\n')[0].split()[0]))
        else:
            meta[key] = str(float(val.split('\n')[0].split()[0]))
        return meta

    meta = {}
    with open(rpc_in) as f:
        for line in f:
            (key, val) = line.split(':')
            if 'LINE_NUM_COEFF' in key:
                meta = check_key('LINE_NUM_COEFF', key, meta)
            elif 'LINE_DEN_COEFF' in key:
                meta = check_key('LINE_DEN_COEFF', key, meta)
            elif 'SAMP_NUM_COEFF' in key:
                meta = check_key('SAMP_NUM_COEFF', key, meta)
            elif 'SAMP_DEN_COEFF' in key:
                meta = check_key('SAMP_DEN_COEFF', key, meta)
            else:
                meta[key] = val.split('\n')[0]  # .split()[0]

    gds = gdal.Open(tif_in)

    gds.SetMetadata(meta, 'RPC')

    meta_orig = gds.GetMetadata()

    xs1 = gds.RasterXSize
    ys1 = gds.RasterYSize
    if gds.RasterCount > 1:
        b1 = gds.GetRasterBand(2)
    elif gds.RasterCount == 1:
        b1 = gds.GetRasterBand(1)
    else:
        print 'wrong input'
        return -1
    img1 = b1.ReadAsArray()

    img1 = np.rot90(img1, k=3)

    drv = gdal.GetDriverByName('GTiff')
    gds_out = drv.Create(fname_out, ys1, xs1, 1, gdal.GDT_UInt16)

    gds_out.GetRasterBand(1).WriteArray(img1)
    gds_out.SetMetadata(meta_orig)
    gds_out.SetMetadata(meta, 'RPC')

    del gds_out
    del gds

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--c2_tif', help='raw c-2 tif file')
parser.add_argument('--c2_rpc', help='earth-i rpc')
parser.add_argument('--c2_out', help='output rpc file')
args = parser.parse_args()

print args.c2_tif
print args.c2_rpc
print args.c2_out

rpc_in = '/Users/max/satellite/carbonite-2/Delivery_20190409/VX02000379_MD Folder/VX02000379_001_01_L1A.rpc'
tif_in = '/Volumes/lacie_data/satellite/carbonite-2/VX02000379/orig/001/VX02000379_001_01_L1A_Stretched.tif'
f_out = '/Volumes/lacie_data/satellite/carbonite-2/VX02000379/meta/VX02000379_001_01_L1A_meta.tif'

# save_meta(rpc_in,
#           tif_in,
#           fname_out = f_out)

save_meta(rpc_in = args.c2_tif,
          tif_in = args.c2_rpc,
          fname_out = args.c2_out)