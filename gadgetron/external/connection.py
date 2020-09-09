
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
    """ Represents a connection to an ISMRMRD client.
    """

    class SocketWrapper:

        def __init__(self, socket):
            self.socket = socket
            self.socket.settimeout(None)

        def read(self, nbytes):
            bytes = self.socket.recv(nbytes, socket.MSG_WAITALL)
            while len(bytes) < nbytes:
                bytes += self.read(nbytes - len(bytes))
            return bytes

        def write(self, byte_array):
            self.socket.sendall(byte_array)

        def close(self):
            end = constants.GadgetMessageIdentifier.pack(constants.GADGET_MESSAGE_CLOSE)
            self.socket.send(end)
            self.socket.close()

    class Struct:
        def __init__(self, **fields):
            self.__dict__.update(fields)

    def __init__(self, socket):
        self.socket = Connection.SocketWrapper(socket)

        self.readers = Connection._default_readers()
        self.writers = Connection._default_writers()

        self.raw_bytes = Connection.Struct(config=None, header=None)
        self.config, self.raw_bytes.config = self._read_config()
        self.header, self.raw_bytes.header = self._read_header()

        self.filters = []

    def __next__(self):
        return self.next()

    def __enter__(self):
        return self

    def __exit__(self, *exception_info):
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

    def add_reader(self, mid, reader, *args, **kwargs):
        """ Add a reader to the connection's readers.

        :param mid: The ISMRMRD Message ID for which the reader is called.
        :param reader: Reader function to be called when `mid` is encountered on the connection.
        :param args: Additional arguments. These are forwarded to the reader when it's called.
        :param kwargs: Additional keyword-arguments. These are forwarded to the reader when it's called.

        Add (or overwrite) a reader to the connection's reader-set. Readers are used to deserialize
        binary ISMRMRD data into usable items.
        """
        self.readers[mid] = lambda readable: reader(readable, *args, **kwargs)

    def add_writer(self, accepts, writer, *args, **kwargs):
        """ Add a writer to the connection's writers.

        :param accepts: Predicate used to determine if a writer accepts an item.
        :param writer: Writer function to be called when `accepts` predicate returned truthy value.
        :param args: Additional arguments. These are forwarded to the writer when it's called.
        :param kwargs: Additional keyword-arguments. These are forwarded to the writer when it's called.

        Add a writer to the connection's writer-set. Writers are used to serialize items into appropriate
        ISMRMRD binary data.
        """
        self.writers.insert(0, (accepts, lambda writable: writer(writable, *args, **kwargs)))

    def filter(self, predicate):
        """ Filters the items that come through the Connection.

        :param predicate: Predicate used when filtering items.

        Filters the items returned by `next`, such that only items for which `predicate(item)`
        returns a truthy value is returned. Items not satisfying the predicate will be silently
        sent back to the client.

        Accepts types as well as function predicates. Supplying a type is shorthand for `isinstance`
        based filtering, such that
            `connection.filter(type)` is equivalent to
            `connection.filter(lambda item: isinstance(item, type))`
        """
        if isinstance(predicate, type):
            return self.filters.append(lambda o: isinstance(o, predicate))
        self.filters.append(predicate)

    def send(self, item):
        """ Send an item to the client.

        :param item: Item to be sent.
        :raises: :class:`TypeError`: If no appropriate writer is found.

        Calling send will offer the item to the connection's current writer-set. If
        an appropriate writer is found, the item is serialized, and sent to the client.
        """
        for predicate, writer in self.writers:
            if predicate(item):
                return writer(self.socket, item)
        raise TypeError(f"No appropriate writer found for item of type '{type(item)}'")

    def next(self):
        """ Retrieves the next item available on a connection.

        :return: The next message from the connection (along with the corresponding MessageID).
        :raises: :class:`StopIteration`: If no more items are available.
        :raises: :class:`TypeError`: If no appropriate reader is found.

        When `next` is called, the next ISMRMRD message id is read from the connection.
        This message id is used to select an appropriate reader, which in in turn reads
        the next item from the connection. The item is returned to the caller.

        If the connection is filtered, only items satisfying the supplied predicate is
        returned. Any items not satisfying the predicate is silently returned to the
        client.
        """
        mid, item = self._read_item()

        while not all(pred(item) for pred in self.filters):
            self.send(item)
            mid, item = self._read_item()

        return mid, item

    def _read_item(self):
        message_identifier = self._read_message_identifier()

        def unknown_message_identifier(*_):
            logging.error(f"Received message (id: {message_identifier}) with no registered readers.")
            raise StopIteration()

        reader = self.readers.get(message_identifier, unknown_message_identifier)
        return message_identifier, reader(self.socket)

    def _read_message_identifier(self):
        return read(self.socket, constants.GadgetMessageIdentifier)

    def _read_config(self):
        message_identifier = self._read_message_identifier()
        assert(message_identifier == constants.GADGET_MESSAGE_CONFIG)
        config_bytes = read_byte_string(self.socket)
        return xml.fromstring(config_bytes), config_bytes

    def _read_header(self):
        message_identifier = self._read_message_identifier()
        assert(message_identifier == constants.GADGET_MESSAGE_HEADER)
        header_bytes = read_byte_string(self.socket)
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

