"""
RPC -> tif
gdal_merge
"""

import sys
import gdal
import numpy as np
import subprocess as sp
import argparse
import os


print('arg:', sys.argv)


def check_key(key0, key, val, meta):
    """

    :param key0:
    :param key:
    :param meta:
    :return:
    """
    key = key0
    if key in meta:
        meta[key] = meta[key] + ' ' + str(float(val.split('\n')[0].split()[0]))
    else:
        meta[key] = str(float(val.split('\n')[0].split()[0]))
    return meta


def save_rpc(rpc_in, tif_in, fname_out):
    """

    :param rpc_in:
    :param tif_in:
    :param fname_out:
    :return:
    """

    meta = {}
    with open(rpc_in) as f:
        for line in f:
                (key, val) = line.split(':')
                if 'LINE_NUM_COEFF' in key:
                    meta = check_key('LINE_NUM_COEFF', key, val, meta)
                elif 'LINE_DEN_COEFF' in key:
                    meta = check_key('LINE_DEN_COEFF', key, val, meta)
                elif 'SAMP_NUM_COEFF' in key:
                    meta = check_key('SAMP_NUM_COEFF', key, val, meta)
                elif 'SAMP_DEN_COEFF' in key:
                    meta = check_key('SAMP_DEN_COEFF', key, val, meta)
                else:
                    meta[key] = val.split('\n')[0]  # .split()[0]

    gds = gdal.Open(tif_in)

    # proj = gds.GetProjection()
    # geo = gds.GetGeoTransform()

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


def save_lst_rpc(rpc_in, tif_in, f_dir_out):
    """

    :param rpc_in:
    :param tif_in:
    :param f_dir_out:
    :return:
    """

    f = open(tif_in)
    tif_lst = f.read().split("\n")
    nl = len(tif_lst)
    if tif_lst[-1] == "":
        nl = nl - 1
    f.close()

    f = open(rpc_in)
    rpc_lst = f.read().split("\n")
    f.close()

    tif_out_lst_rpc = []
    tif_out_lst_rect = []

    for i in range(nl):
        fname_out_rpc = f_dir_out + tif_lst[i].split("/")[-1].split(".")[0] + "_rpc.tif"
        save_rpc(rpc_lst[i], tif_lst[i], fname_out_rpc)
        tif_out_lst_rpc.append(fname_out_rpc)
        fname_out_rect = fname_out_rpc.split(".")[0] + "_rect.tif"
        rectify(fname_out_rpc, fname_out_rect)
        tif_out_lst_rect.append(fname_out_rect)

    return tif_out_lst_rect, tif_out_lst_rpc


def rectify(fname_in, fname_out_rect):
    """
    Write geo-information (roughly rectify image) based on the given RPC model.

    :param string fname_in: Input name
    :return: Output rectified image
    """
    if os.path.isfile(fname_out_rect):
        sp.check_output("rm " + fname_out_rect, shell=True)
    # cmd_warp = "gdalwarp -t_srs EPSG:4326 -rpc " + f_dir_out + "/" + fname_out + " " + fname_out_rect
    cmd_warp = "gdalwarp -rpc " + fname_in + " " + fname_out_rect
    cmd_out = sp.check_output(cmd_warp, shell=True)
    print('Rectification:')
    print(cmd_warp)
    print(cmd_out)


def merge(tif_in_lst, tif_lst_rpc, f_dir_out):
    """

    :param tif_in_lst:
    :return:
    """

    nl = len(tif_in_lst)
    merge_str = ""
    for i in range(nl):
        merge_str = merge_str + " " + tif_in_lst[i]
    merge_out = f_dir_out + "merge_tmp.tif"
    if os.path.isfile(merge_out):
        sp.check_output("rm " + merge_out, shell=True)
    cmd_merge = "gdal_merge.py -separate " + merge_str + " -o " + merge_out + " -of GTiff "
    com_out = sp.check_output(cmd_merge, shell=True)
    print('gdal_merge:')
    print(cmd_merge)
    print(com_out)

    for i in range(1, nl+1):
        f_out_trans = f_dir_out + tif_in_lst[i-1].split("/")[-1].split(".")[0] + "_stacked.tif"
        if os.path.isfile(f_out_trans):
            sp.check_output("rm " + f_out_trans, shell=True)
        cmd_str = "gdal_translate -b %d " % i + f_dir_out + "merge_tmp.tif " + f_out_trans
        sp.check_output(cmd_str, shell=True)
        print('gdal_translate:')
        print(cmd_str)
        print(com_out)

        # Set RPCs to metadata
        # gds_rpc = gdal.Open(tif_lst_rpc[i-1], gdal.gdalconst.GA_ReadOnly)
        # gds_rect = gdal.Open(f_out_trans, gdal.gdalconst.GA_Update)
        # rpc_meta = gds_rpc.GetMetadata('RPC')
        # gds_rect.SetMetadata(rpc_meta, 'RPC')
        del gds_rpc
        del gds_rect


if __name__ == "__main__":
    """
    Main function. Parse arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--c2_tif', help='list of raw c-2 tif files')
    parser.add_argument('--c2_rpc', help='list of RPCs')
    parser.add_argument('--c2_out', help='output directory')
    args = parser.parse_args()

    print args.c2_tif
    print args.c2_rpc
    print args.c2_out

    # rpc_in = 'input_rpc.txt'
    # tif_in = 'input_tif.txt'
    # dir_out = 'output/'

    # tif_in_lst, tif_lst_rpc = save_lst_rpc(rpc_in, tif_in, f_dir_out=dir_out)
    # merge(tif_in_lst, tif_lst_rpc, dir_out)

    tif_in_lst, tif_lst_rpc = save_lst_rpc(rpc_in=args.c2_rpc, tif_in=args.c2_tif, f_dir_out=args.c2_out)
    merge(tif_in_lst, tif_lst_rpc, args.c2_out)