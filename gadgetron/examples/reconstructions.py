
import time
import logging
import ismrmrd

from .acquisitions import create_slice_from_acquisitions, noise_adjustment, remove_oversampling
from .buckets import create_slice_from_bucket
from .buffers import create_slice_from_buffer
from .shared import reconstruct_images, combine_channels, create_ismrmrd_images, send_images_to_client


def recon_acquisitions(connection):
    logging.info("Python reconstruction running - reconstructing images from acquisitions.")

    start = time.time()

    # Connections are iterable - iterating them can be done once, and will yield the data sent from Gadgetron.
    # In this example, we use a nested sequence of generators (https://wiki.python.org/moin/Generators) each
    # responsible for part of the reconstruction. In this manner, we construct a succession of generators, each
    # one step closer to the final product. Iterating the final iterator thus produces output-ready images.

    iterable = noise_adjustment(connection, connection.header)
    iterable = remove_oversampling(iterable, connection.header)
    iterable = create_slice_from_acquisitions(iterable, connection.header)
    iterable = reconstruct_images(iterable)
    iterable = combine_channels(iterable)
    iterable = create_ismrmrd_images(iterable)

    # We're only interested in acquisitions in this example, so we filter the connection. Anything filtered out in
    # this way will pass back to Gadgetron unchanged.
    connection.filter(ismrmrd.Acquisition)

    send_images_to_client(iterable, connection)

    logging.info(f"Python reconstruction done. Duration: {(time.time() - start):.2f} s")


def recon_buffers(connection):
    logging.info("Python reconstruction running - reconstructing images from acquisition buffers.")

    start = time.time()

    iterable = create_slice_from_buffer(connection, connection.header)
    iterable = reconstruct_images(iterable)
    iterable = combine_channels(iterable)
    iterable = create_ismrmrd_images(iterable)

    send_images_to_client(iterable, connection)

    logging.info(f"Python reconstruction done. Duration: {(time.time() - start):.2f} s")


def recon_buckets(connection):
    logging.info("Python reconstruction running - reconstructing images from recon data.")

    start = time.time()

    iterable = create_slice_from_bucket(connection, connection.header)
    iterable = reconstruct_images(iterable)
    iterable = combine_channels(iterable)
    iterable = create_ismrmrd_images(iterable)

    send_images_to_client(iterable, connection)

    logging.info(f"Python reconstruction done. Duration: {(time.time() - start):.2f} s")

