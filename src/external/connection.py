
import socket
import logging
import xml.etree.ElementTree as xml

import ismrmrd

from . import constants

from .readers import read, read_byte_string, read_acquisition, read_waveform, read_image
from .writers import write_acquisition, write_waveform, write_image


def close(_):
    logging.debug("Connection closed normally.")
    raise StopIteration()


_readers = {
    constants.GADGET_MESSAGE_CLOSE: close,
    constants.GADGET_MESSAGE_ISMRMRD_ACQUISITION: read_acquisition,
    constants.GADGET_MESSAGE_ISMRMRD_WAVEFORM: read_waveform,
    constants.GADGET_MESSAGE_ISMRMRD_IMAGE: read_image
}

_writers = [
    (lambda item: isinstance(item, ismrmrd.Acquisition), write_acquisition),
    (lambda item: isinstance(item, ismrmrd.Waveform), write_waveform),
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

        self.raw = Connection.Raw(config=None, header=None)
        self.config, self.raw.config = self._read_config()
        self.header, self.raw.header = self._read_header()

        self.filters = []

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
            try:
                yield next(self)
            except StopIteration:
                return

    def send(self, item):
        for predicate, writer in _writers:
            if predicate(item):
                return writer(self, item)
        raise TypeError(f"No appropriate writer found for item of type '{type(item)}'")

    def next(self):
        mid, item = self._read_item()

        while not all(pred(item) for pred in self.filters):
            self.send(item)
            mid, item = self._read_item()

        return mid, item

    def read(self, nbytes):
        bytes = self.socket.recv(nbytes, socket.MSG_WAITALL)
        return bytes if len(bytes) is nbytes else bytes + self.read(nbytes - len(bytes))

    def write(self, byte_array):
        self.socket.sendall(byte_array)

    def _read_item(self):
        message_identifier = self._read_message_identifier()

        def unknown_message_identifier(*_):
            logging.error(f"Received message (id: {message_identifier}) with no registered readers.")
            Connection.stop_iteration()

        reader = _readers.get(message_identifier, unknown_message_identifier)
        return message_identifier, reader(self)

    def _read_message_identifier(self):
        return read(self, constants.GadgetMessageIdentifier)

    def _read_config(self):
        message_identifier = self._read_message_identifier()
        assert(message_identifier == constants.GADGET_MESSAGE_CONFIG)
        config_bytes = read_byte_string(self)
        return xml.fromstring(config_bytes), config_bytes

    def _read_header(self):
        message_identifier = self._read_message_identifier()
        assert(message_identifier == constants.GADGET_MESSAGE_HEADER)
        header_bytes = read_byte_string(self)
        return ismrmrd.xsd.CreateFromDocument(header_bytes), header_bytes

    @ staticmethod
    def stop_iteration():
        raise StopIteration()

