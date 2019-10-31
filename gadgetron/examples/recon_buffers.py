import logging
import numpy as np
import gadgetron
import ismrmrd
import time
from multimethod import multimethod


def buffer_from_bucket(bucket, header):
    matrix_size = header.encoding[0].encodedSpace.matrixSize
    acqs = bucket.data

    logging.debug(f"Assembling buffer from bucket containing {len(acqs)} acquisitions.")

    number_of_channels = acqs[0].data.shape[0]
    number_of_samples = acqs[0].data.shape[1]
    buffer = np.zeros(
        (number_of_samples, matrix_size.y, matrix_size.z, number_of_channels),
        dtype=np.complex64
    )

    for acq in acqs:
        buffer[:, acq.idx.kspace_encode_step_1, acq.idx.kspace_encode_step_2,:] = acq.data.T

    return buffer

def reconstruct_image(kspace_data):
    return gadgetron.util.cifftn(kspace_data, axes=[0, 1, 2])


def combine_channels(image):
    return np.sqrt(np.sum(np.abs(image) ** 2), 3)


def split_image_array(image_data):
    shape = image_data.shape
    image_5d_view = image_data.reshape(*shape[:4], -1)
    return np.split(image_5d_view, 1, axis=4)


def create_ismrmrd_image(image_data, reference_acquisition_header):
    return ismrmrd.image.Image.from_array(image_data, acquisition=reference_acquisition_header)

def reconstruct_buffer(kspace_data,reference_header):
    image_data = reconstruct_image(kspace_data)
    image_data = combine_channels(image_data)
    image_data_list = split_image_array(image_data)
    images = [create_ismrmrd_image(img, reference_header) for img in image_data_list]
    return images

@multimethod
def reconstruct(buffer : gadgetron.types.ReconData):
    return

@multimethod
def reconstruct(bucket : gadgetron.types.AcquisitionBucket):


def send_images(connection, images):
    for img in images:
        connection.send(img)


def recon_buffers(connection):
    logging.info("Python reconstruction running - reconstructing images from acquisition buffers.")

    start = time.time()

    for data in connection:
        images = reconstruct(data)
        send_images(connection, images)

    logging.info(f"Python reconstruction done. Duration: {(time.time() - start):.2f} s")
