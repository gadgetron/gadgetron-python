
import socket
import logging

import xml.etree.ElementTree as xml

import ismrmrd

from . import constants

from .readers import read, read_byte_string, read_acquisition, read_waveform, read_image
from .writers import write_acquisition, write_waveform, write_image

from ..types.image_array import ImageArray, read_image_array, write_image_array
from ..types.recon_data import ReconData, read_recon_data, write_recon_data
from ..types.acquisition_bucket import read_acquisition_bucket


class Connection:
    """ Connection class representing a remote connection via the Gadgetron protocol

    """

    class Raw:
        def __init__(self, **fields):
            self.__dict__.update(fields)

    def __init__(self, socket):
        self.socket = socket

        self.readers = Connection._default_readers()
        self.writers = Connection._default_writers()

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
                _, item = next(self)
                yield item
            except StopIteration:
                return

    def iter_with_mids(self):
        while True:
            try:
                yield next(self)
            except StopIteration:
                return

    def add_reader(self, slot, reader, *args, **kwargs):
        self.readers[slot] = lambda readable: reader(readable, *args, **kwargs)

    def add_writer(self, accepts, writer, *args, **kwargs):
        self.writers.insert(0, (accepts, lambda writable: writer(writable, *args, **kwargs)))

    def filter(self, predicate):
        """
         Filters the messages that come through the connection
        :param predicate: Function returning false if the message should be removed
        """
        if isinstance(predicate, type):
            return self.filters.append(lambda o: isinstance(o, predicate))
        self.filters.append(predicate)

    def send(self, item):
        """
        Sends a message via the connection
        :param item: Message to be sent. Must have corresponding writer
        """
        for predicate, writer in self.writers:
            if predicate(item):
                return writer(self, item)
        raise TypeError(f"No appropriate writer found for item of type '{type(item)}'")

    def next(self):
        """
        :return: The next message from the connection
        """
        mid, item = self._read_item()

        while not all(pred(item) for pred in self.filters):
            self.send(item)
            mid, item = self._read_item()

        return mid, item

    def read(self, nbytes):
        """
        Reads raw bytes from the connection
        :param nbytes: Number of bytes to read
        :return: An array of nbytes bytes
        """
        bytes = self.socket.recv(nbytes, socket.MSG_WAITALL)
        while len(bytes) < nbytes:
            bytes += self.read(nbytes-len(bytes))
        return bytes

    def write(self, byte_array):
        """
        Writes an array of bytes to the connection
        :param byte_array: Bytes to be written
        :return:
        """
        self.socket.sendall(byte_array)

    def _read_item(self):
        message_identifier = self._read_message_identifier()

        def unknown_message_identifier(*_):
            logging.error(f"Received message (id: {message_identifier}) with no registered readers.")
            raise StopIteration()

        reader = self.readers.get(message_identifier, unknown_message_identifier)
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
    def _default_readers():
        return {
            constants.GADGET_MESSAGE_CLOSE: Connection.stop_iteration,
            constants.GADGET_MESSAGE_ISMRMRD_ACQUISITION: read_acquisition,
            constants.GADGET_MESSAGE_ISMRMRD_WAVEFORM: read_waveform,
            constants.GADGET_MESSAGE_ISMRMRD_IMAGE: read_image,
            constants.GADGET_MESSAGE_IMAGE_ARRAY: read_image_array,
            constants.GADGET_MESSAGE_RECON_DATA: read_recon_data,
            constants.GADGET_MESSAGE_BUCKET: read_acquisition_bucket
        }

    @ staticmethod
    def _default_writers():
        return [
            (lambda item: isinstance(item, ismrmrd.Acquisition), write_acquisition),
            (lambda item: isinstance(item, ismrmrd.Waveform), write_waveform),
            (lambda item: isinstance(item, ismrmrd.Image), write_image),
            (lambda item: isinstance(item, ImageArray), write_image_array),
            (lambda item: isinstance(item, ReconData), write_recon_data)
        ]

    @ staticmethod
    def stop_iteration(_):
        logging.debug("Connection closed normally.")
        raise StopIteration()

