
import numpy
import ismrmrd

import gadgetron.external.constants as constants

from ..external import handlers


def _transform_to_legacy_acquisition(acquisition):
    return acquisition.getHead(), numpy.transpose(acquisition.data)


def _transform_from_legacy_acquisition(items):
    header, data = items
    header.number_of_samples, header.active_channels = data.shape
    acquisition = ismrmrd.Acquisition(header)
    acquisition.data[:] = numpy.transpose(data)
    return acquisition


def _transform_to_legacy_image(image):
    return image.getHead(), numpy.transpose(image.data)


def _transform_from_legacy_image(items):
    header, data = items
    image = ismrmrd.Image(header)
    image.data[:] = numpy.reshape(numpy.transpose(data), image.data.shape)
    return image


class Gadget:

    _reader_transformations = {
        constants.GADGET_MESSAGE_ISMRMRD_ACQUISITION: _transform_to_legacy_acquisition,
        constants.GADGET_MESSAGE_ISMRMRD_IMAGE: _transform_to_legacy_image
    }

    _writer_transformation = [
        (lambda args: isinstance(args[0], ismrmrd.AcquisitionHeader), _transform_from_legacy_acquisition),
        (lambda args: isinstance(args[0], ismrmrd.ImageHeader), _transform_from_legacy_image)
    ]

    @ classmethod
    def __init_subclass__(cls, **kwargs):
        handlers.register_handler(lambda conn: cls().handle(conn))

    def __init__(self, *args, **kwargs):
        self.connection = None

    def handle(self, connection):
        self.connection = connection

        self.process_config(connection.raw.header)

        def iterate_with_mids(conn):
            while True:
                try:
                    yield conn.next()
                except StopIteration:
                    return

        for message_identifier, item in iterate_with_mids(connection):
            transformation = Gadget._reader_transformations.get(message_identifier)
            self.process(*transformation(item))

    def process_config(self, config):
        pass

    def process(self, *args):
        pass

    def wait(self):
        pass

    def put_next(self, *args):

        def unknown_output(items):
            raise TypeError(f"No registered transformation accepted types: {[type(item) for item in items]}")

        transformation = next((trans for pred, trans in Gadget._writer_transformation if pred(args)), unknown_output)
        self.connection.send(transformation(args))
