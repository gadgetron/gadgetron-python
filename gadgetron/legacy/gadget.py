
import numpy
import ismrmrd
import logging

from ..external import constants
from ..external import handlers


def _transform_to_legacy_acquisition(acquisition):
    return acquisition.getHead(), numpy.transpose(acquisition.data)


def _transform_from_legacy_acquisition(items):
    header, data = items
    header.number_of_samples, header.active_channels = data.shape
    acquisition = ismrmrd.Acquisition(header)
    acquisition.data[:] = numpy.transpose(data)
    return acquisition


def _transform_to_legacy_waveform(waveform):
    return waveform,


def _transform_to_legacy_image(image):
    return image.getHead(), numpy.transpose(image.data), image.attribute_string


def _transform_from_legacy_image(items):
    items = list(items) + [""]
    header, data, meta = items[:3]
    header.attribute_string_len = len(meta)
    image = ismrmrd.Image(header, meta)
    image.data[:] = numpy.reshape(numpy.transpose(data), image.data.shape)
    return image


def _parse_params(xml):
    return {p.get('name'): p.get('value') for p in xml.iter('property')}


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
        self.params = None
        self.hooks = {
            constants.GADGET_MESSAGE_ISMRMRD_WAVEFORM:
                self._process_waveform if hasattr(self, 'process_waveform') else self._ignore_waveform
        }

    def handle(self, connection):
        self.connection = connection
        self.params = _parse_params(connection.config)
        self.process_config(connection.raw_bytes.header)

        def invoke_process(process, args):
            if not args:
                raise ValueError()
            try:
                process(*args)
            except TypeError:
                invoke_process(process, args[:-1])

        for mid, item in connection.iter_with_mids():
            if mid in self.hooks:
                self.hooks.get(mid)(item)
            else:
                transformation = Gadget._reader_transformations.get(mid, lambda x: [x])
                args = transformation(item)
                try:
                    invoke_process(self.process, args)
                except ValueError:
                    raise TypeError(f"Failed to invoke self.process; arguments do not match. Had arguments: "
                                    f"{[type(a) for a in args]}")

    def process_config(self, config):
        pass

    def process(self, *args):
        pass

    def wait(self):
        pass

    def put_next(self, *args):
        transformation = next((trans for pred, trans in Gadget._writer_transformation if pred(args)), lambda x: x[0])
        self.connection.send(transformation(args))

    def _ignore_waveform(self, waveform):
        self.connection.send(waveform)

    def _process_waveform(self, waveform):
        self.process_waveform(waveform)
    

    def set_parameter(self, name, value):
        self.params[name] = value

    def get_parameter(self, name):
        return self.params.get(name, None)
