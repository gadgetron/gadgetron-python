
import socket
import logging
import xml.etree.ElementTree as xml

import ismrmrd

import gadgetron.external.constants as constants

from .readers import read_byte_string, read_acquisition, read_waveform, read_image
from .writers import write_image


def not_implemented(_):
    raise NotImplemented()


def close(_):
    pass


_readers = {
    constants.GADGET_MESSAGE_CLOSE: close,
    constants.GADGET_MESSAGE_ISMRMRD_ACQUISITION: read_acquisition,
    constants.GADGET_MESSAGE_ISMRMRD_WAVEFORM: read_waveform,
    constants.GADGET_MESSAGE_ISMRMRD_IMAGE: read_image,
    constants.GADGET_MESSAGE_ISMRMRD_IMAGE_ARRAY: not_implemented,
    constants.GADGET_MESSAGE_ISMRMRD_BUFFER: not_implemented
}

_writers = [
    (lambda item: isinstance(item, ismrmrd.Image), write_image)
]


def register_reader(*, slot, reader):
    global _readers
    _readers[slot] = reader


def register_writer(*, predicate, writer):
    global _writers
    _writers.append((predicate, writer))


class Connection:
    """
    Consider writing some excellent documentation here.
    """

    class Raw:
        def __init__(self, **fields):
            self.__dict__.update(fields)

    def __init__(self, socket):
        self.socket = socket

        self.transformations = {constants.GADGET_MESSAGE_CLOSE: Connection.stop_iteration}
        self.raw = Connection.Raw(config=None, header=None)
        self.config, self.raw.config = self.read_config()
        self.header, self.raw.header = self.read_header()

    def __next__(self):
        return self.next()

    def __enter__(self):
        return self

    def __exit__(self, *exception_info):
        end = constants.GadgetMessageIdentifier.pack(constants.GADGET_MESSAGE_CLOSE)
        self.socket.send(end)
        self.socket.close()

    def __iter__(self):
        while True:
            yield next(self)

    def send(self, item):
        for predicate, writer in _writers:
            if predicate(item):
                return writer(self, item)
        raise TypeError(f"No appropriate writer found for item of type '{type(item)}'")

    def next(self):
        message_identifier = self.read_message_identifier()
        transformation = self.transformations.get(message_identifier, lambda x: x)
        reader = _readers.get(message_identifier, lambda *args: Connection.unknown_message_identifier(message_identifier))
        return transformation(reader(self))

    def read(self, nbytes):
        return self.socket.recv(nbytes, socket.MSG_WAITALL)

    def write(self, byte_array):
        self.socket.sendall(byte_array)

    def read_message_identifier(self):
        identifier_bytes = self.read(constants.SIZEOF_GADGET_MESSAGE_IDENTIFIER)
        identifier = constants.GadgetMessageIdentifier.unpack(identifier_bytes)[0]
        logging.debug(f"Read message identifier: {identifier}")
        return identifier

    def read_config(self):
        message_identifier = self.read_message_identifier()
        assert(message_identifier == constants.GADGET_MESSAGE_CONFIG)
        config_bytes = read_byte_string(self)
        return xml.fromstring(config_bytes), config_bytes

    def read_header(self):
        message_identifier = self.read_message_identifier()
        assert(message_identifier == constants.GADGET_MESSAGE_HEADER)
        header_bytes = read_byte_string(self)
        return ismrmrd.xsd.CreateFromDocument(header_bytes), header_bytes

    @ staticmethod
    def stop_iteration():
        logging.debug("Reached end of input.")
        raise StopIteration()

    @ staticmethod
    def unknown_message_identifier(message_identifier):
        logging.error(f"Received message (id: {message_identifier}) with no registered readers.")
        Connection.stop_iteration()
