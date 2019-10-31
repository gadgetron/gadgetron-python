
import logging

import numpy as np

from .shared import Slice


def create_slice_from_bucket(iterable, header):

    matrix_size = header.encoding[0].encodedSpace.matrixSize

    def assemble_slice(bucket):

        acqs = bucket.data

        logging.debug(f"Assembling buffer from bucket containing {len(acqs)} acquisitions.")

        buffer = np.zeros(
            (acqs[0].data.shape[0],
             acqs[0].data.shape[1],
             matrix_size.y,
             matrix_size.z),
            dtype=np.complex64
        )

        for acq in acqs:
            buffer[:, :, acq.idx.kspace_encode_step_1, acq.idx.kspace_encode_step_2] = acq.data

        return Slice(data=buffer, reference=acqs[-1])

    yield from map(assemble_slice, iterable)

