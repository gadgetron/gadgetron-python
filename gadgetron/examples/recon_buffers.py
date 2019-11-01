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
        (number_of_samples, matrix_size.y, matrix_size.z, number_of_channels, 1),
        dtype=np.complex64
    )

    for acq in acqs:
        buffer[:, acq.idx.kspace_encode_step_1, acq.idx.kspace_encode_step_2, :, 0] = acq.data.T

    return buffer, bucket.data[0].getHead()


def reconstruct_image(kspace_data):
    return gadgetron.util.cifftn(kspace_data, axes=[0, 1, 2])


def combine_channels(image):
    return np.sqrt(np.sum(np.abs(image) ** 2, axis=3))


def split_image_array(image_data):
    image_5d_view = image_data.reshape(*image_data.shape[:4], -1)
    return [image_5d_view[..., i] for i in range(image_5d_view.shape[4])]


def create_ismrmrd_image(image_data, reference_acquisition_header):
    return ismrmrd.image.Image.from_array(image_data, acquisition=reference_acquisition_header)


def reconstruct_buffer(kspace_data, reference_header):
    print(kspace_data.shape)
    image_data = reconstruct_image(kspace_data)
    image_data = combine_channels(image_data)
    image_data_list = split_image_array(image_data)
    images = [create_ismrmrd_image(img, reference_header) for img in image_data_list]
    return images

def flatten(lists):
    return sum(lists,[])

@multimethod
def reconstruct(buffers: gadgetron.types.ReconData, header):
    return flatten([[image for image in reconstruct_buffer(buffer.data.data, buffer.data.headers.flat[0])] for buffer in
            buffers])


@multimethod
def reconstruct(bucket: gadgetron.types.AcquisitionBucket, header):
    kspace_data, acq_header = buffer_from_bucket(bucket, header)
    return reconstruct_buffer(kspace_data, acq_header)


def send_images(connection, images):
    for img in images:
        print(img.getHead())
        connection.send(img)


def recon_buffers(connection):
    logging.info("Python reconstruction running - reconstructing images from acquisition buffers.")

    start = time.time()


    for data in connection:
        images = reconstruct(data, connection.header)
        send_images(connection, images)

    logging.info(f"Python reconstruction done. Duration: {(time.time() - start):.2f} s")


#######################################################################################################################
# This allows the file to be run directly as a server


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    gadgetron.external.listen(9100, recon_buffers)
