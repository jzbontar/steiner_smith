import numpy as np
import scipy.signal
import scipy.ndimage.morphology

def ipol_nearest(src, trg, data):
    tree = scipy.spatial.cKDTree(src)
    dists, ix = tree.query(trg, k=1)
    return data[ix]

def compute_spinchange(data):
    spin = np.zeros_like(data)
    for i in range(data.shape[0]):
        signs = np.sign(np.trunc(np.diff(data[i]) / 2))
        nnz = np.flatnonzero(signs)
        spin[i,nnz[1:]] = np.diff(signs[nnz]) != 0
    kernel = np.ones((11, 21))
    spin = scipy.signal.fftconvolve(spin, kernel, 'same')
    possible = np.ones_like(spin)
    possible[:,[0,-1]] = 0
    possible = scipy.signal.fftconvolve(possible, kernel, 'same')
    return spin / possible

def steiner_smith(radar, refl_thresh=5, spin_thresh_a=8, spin_thresh_b=40, spin_thresh_c=15, grad_thresh=20):
    data0 = radar[0].get_field(0, 'reflectivity')
    x0, y0, _ = radar[0].get_gate_x_y_z(0)
    data2 = radar[2].get_field(0, 'reflectivity')
    x2, y2, _ = radar[2].get_gate_x_y_z(0)
    src = np.column_stack((x2.ravel(), y2.ravel()))
    trg = np.column_stack((x0.ravel(), y0.ravel()))
    data2 = ipol_nearest(src, trg, data2.ravel()).reshape(data0.shape)

    spin_thresh = (spin_thresh_a - (data0.filled(0) - spin_thresh_b) / spin_thresh_c) * 0.01
    zpixel = data0.filled(0) >= refl_thresh
    echotop = data2.filled(0) >= refl_thresh
    echotop = scipy.ndimage.morphology.binary_dilation(echotop)
    spinchange = compute_spinchange(data0.filled(0)) >= spin_thresh
    vertgrad = np.abs(data0 - data2).filled(0) > grad_thresh

    r1 = ~zpixel
    r2 =  zpixel & ~echotop
    r3 =  zpixel &  echotop & ~spinchange
    r4 =  zpixel &  echotop &  spinchange & ~vertgrad
    r5 =  zpixel &  echotop &  spinchange &  vertgrad
    return r1 | r2 | r5

if __name__ == '__main__':
    import os

    import pylab as plt
    import pyart
    import cv2

    def togrid(polar, x, y, gridsize=1024, lim=460):
        src = np.column_stack((x.ravel(), y.ravel()))
        grid = np.linspace(-lim * 1000, lim * 1000, gridsize)
        mgrid = np.meshgrid(grid, grid[::-1])
        trg = np.column_stack((mgrid[0].ravel(), mgrid[1].ravel()))
        grid = ipol_nearest(src, trg, polar.ravel())
        return grid.reshape(gridsize, gridsize)

    def dump_ref_cmap(fname, data, vmin=-32., vmax=94.5, cmap='pyart_NWSRef'):
        cmap = plt.get_cmap(cmap)
        data = (data - vmin) / (vmax - vmin)
        data_bgr = cmap(data)[:,:,2::-1] * 255
        data_bgr[data.mask] = 0
        cv2.imwrite(fname, data_bgr)

    for fname in sorted(os.listdir('data')):
        print fname

        try:
            # hack to avoid data interpolating by pyart
            radar = [pyart.io.read(os.path.join('data', fname), scans=[i]) for i in range(3)]
        except ValueError:
            print "Can't read radar file. Please update PyART."
            continue

        ref = radar[0].get_field(0, 'reflectivity')
        x, y, _ = radar[0].get_gate_x_y_z(0)
        grid = togrid(ref, x, y, gridsize=256, lim=250)
        dump_ref_cmap('img/{}_orig.png'.format(fname), grid)

        clutter = steiner_smith(radar)
        ref = np.ma.masked_where(clutter, ref)
        grid = togrid(ref, x, y, gridsize=256, lim=250)
        dump_ref_cmap('img/{}_qc.png'.format(fname), grid)
