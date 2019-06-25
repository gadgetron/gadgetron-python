

import numpy.fft as fft


def cfftn(data, axes):
    return fft.ifftshift(fft.fftn(fft.fftshift(data, axes=axes)))


def cifftn(data, axes):
    return fft.fftshift(fft.ifftn(fft.ifftshift(data, axes), axes=axes))
