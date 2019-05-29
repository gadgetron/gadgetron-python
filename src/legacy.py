
import numpy
import logging

import ismrmrd

import gadgetron.external.constants as constants

from .external import handlers


def _transform_acquisition(acquisition):
    return acquisition, numpy.transpose(acquisition.data), numpy.transpose(acquisition.traj)


class Gadget:

    @ classmethod
    def __init_subclass__(cls, **kwargs):
        handlers.register_handler(lambda conn: cls().handle(conn))

    def __init__(self, *args, **kwargs):
        self.connection = None

    def handle(self, connection):
        self.connection = connection
        self.connection.transformations = {
            constants.GADGET_MESSAGE_ISMRMRD_ACQUISITION: _transform_acquisition,
            constants.GADGET_MESSAGE_ISMRMRD_WAVEFORM: lambda x: x,
            constants.GADGET_MESSAGE_ISMRMRD_IMAGE: lambda x: x,
            constants.GADGET_MESSAGE_ISMRMRD_BUFFER: lambda x: x,
            constants.GADGET_MESSAGE_ISMRMRD_IMAGE_ARRAY: lambda x: x
        }

        self.process_config(connection.raw.header)
        for items in connection:
            self.process(*items)

    def process_config(self, config):
        pass

    def process(self, *args):
        pass

    def wait(self):
        pass

    def put_next(self, *items):
        logging.debug(f"Legacy output produced: {[type(item) for item in items]}")
        header, data, _ = items

        logging.info(f"Data shape: {data.shape}")

        image = ismrmrd.Image(header)
        image.data[:] = numpy.transpose(numpy.squeeze(data, axis=3))

        self.connection.send(image)


