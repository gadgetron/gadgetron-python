
import time
import logging

import ismrmrd
import gadgetron
import itertools
import multimethod

import numpy as np


def prepare_buffers(input, header):

    def buffer_from_bucket(bucket):
        matrix_size = header.encoding[0].encodedSpace.matrixSize
        acquisitions = bucket.data

        logging.debug(f"Assembling buffer from bucket containing {len(acquisitions)} acquisitions.")

        channels, samples = acquisitions[0].data.shape
        buffer = np.zeros(
            (channels, matrix_size.z, matrix_size.y, samples),
            dtype=np.complex64
        )

        for acq in acquisitions:
            buffer[:, acq.idx.kspace_encode_step_2, acq.idx.kspace_encode_step_1, :] = acq.data

        return buffer, acquisitions[0]

    def buffer_from_buffer(buffer):
        return buffer.data.reshape(buffer.data.shape[:4]).transpose(), buffer.headers.item(0)

    @multimethod.multimethod
    def prepare_buffers(bucket: gadgetron.types.AcquisitionBucket):
        yield buffer_from_bucket(bucket)

    @multimethod.multimethod
    def prepare_buffers(recon_data: gadgetron.types.ReconData):
        yield from (buffer_from_buffer(bit.data) for bit in recon_data)

    for item in input:
        yield from prepare_buffers(item)


def reconstruct_images(buffers, header):

    indices = itertools.count(start=1)
    field_of_view = header.encoding[0].reconSpace.fieldOfView_mm

    def reconstruct_buffer(data):
        return gadgetron.util.cifftn(data, axes=[1, 2, 3])

    def combine_channels(data):
        return np.sqrt(np.sum(np.square(np.abs(data)), axis=0))

    def create_ismrmrd_image(data, reference):
        return ismrmrd.image.Image.from_array(
            data,
            acquisition=reference,
            image_index=next(indices),
            image_type=ismrmrd.IMTYPE_MAGNITUDE,
            field_of_view=(field_of_view.x, field_of_view.y, field_of_view.z),
            transpose=False
        )

    def build_image(buffer, reference):

        buffer = reconstruct_buffer(buffer)
        buffer = combine_channels(buffer)

        return create_ismrmrd_image(buffer, reference)

    for buffer, reference in buffers:
        yield build_image(buffer, reference)


def recon_buffers(connection):
    logging.info("Python reconstruction running - reconstructing images from acquisition buffers.")

    input = iter(connection)
    buffers = prepare_buffers(input, connection.header)
    images = reconstruct_images(buffers, connection.header)

    start = time.time()

    for image in images:
        connection.send(image)

    logging.info(f"Python reconstruction done. Duration: {(time.time() - start):.2f} s")


#######################################################################################################################
# This allows the file to be run directly as a server

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    gadgetron.external.listen(9100, recon_buffers)
