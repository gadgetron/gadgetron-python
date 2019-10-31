
import logging
import ismrmrd
import collections

import numpy as np

from gadgetron.util.cfft import cifftn

Slice = collections.namedtuple('Slice', ['data', 'reference'])


def reconstruct_images(iterable):
    # Reconstruction is an inverse fft.

    for slice in iterable:
        yield Slice(data=cifftn(slice.data, axes=[1, 2, 3]), reference=slice.reference)


def combine_channels(iterable):
    # Slice data contains complex images, one for each channel. We combine these into a single image
    # through a sum of squares along the channels (axis 0).

    for slice in iterable:
        yield Slice(data=np.sqrt(np.sum(np.square(np.abs(slice.data)), axis=0)), reference=slice.reference)


def create_ismrmrd_images(iterable):
    # Slice data contains the finished image. We wrap it in an ISMRMRD data structure, so the connection
    # can send it back to Gadgetron. We provide a reference acquisition to properly initialize the
    # image header with delicious metadata; feel the good karma!

    for slice in iterable:
        yield ismrmrd.image.Image.from_array(slice.data, acquisition=slice.reference)


def send_images_to_client(iterable, connection):
    for image in iterable:
        logging.debug("Sending image back to client.")
        connection.send(image)

