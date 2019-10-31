
import logging
import numpy as np

from .shared import Slice


def create_slice_from_buffer(iterable, header):

    def slice_from_recon_buffer(buffer):
        logging.debug(f"Assembling buffer from recon buffer.")

        data = np.moveaxis(buffer.data, 3, 0)

        # Recon Data buffers have pretty high dimensionality. I'll just squeeze them out, as dealing with correctly
        # depends strongly on context.
        data = np.reshape(data, data.shape[0:4])

        return Slice(
            data=data,
            reference=buffer.headers[-1].item()
        )

    def slice_from_recon_data(recon_data):
        return slice_from_recon_buffer(recon_data[0].data)

    yield from map(slice_from_recon_data, iterable)
