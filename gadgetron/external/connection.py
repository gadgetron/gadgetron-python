import logging
from socket import MSG_WAITALL

import xml.etree.ElementTree as xml

import ismrmrd

from . import constants

from .readers import read, read_byte_string
from .writers import write, write_byte_string

from ..types.image_array import ImageArray
from ..types.recon_data import ReconData
from ..types.acquisition_bucket import AcquisitionBucket

from ..types.serialization import message_reader, message_writer
from ..types import serialization


class Connection:
    """ Represents a connection to an ISMRMRD client.
    """

    class SocketWrapper:

        def __init__(self, socket):
            self.socket = socket
            self.socket.settimeout(None)

        def read(self, nbytes):
            bytedata = self.socket.recv(nbytes, MSG_WAITALL)
            while len(bytedata) < nbytes:
                bytedata += self.socket.recv(nbytes - len(bytedata), MSG_WAITALL)
            return bytedata

        def write(self, byte_array):
            self.socket.sendall(byte_array)

        def close(self):
            self.socket.close()

    class Struct:
        def __init__(self, **fields):
            self.__dict__.update(fields)

    @staticmethod
    def initiate_connection(socket, config, header):

        connection = Connection(socket,config,header)
        connection._write_config(config)
        connection._write_header(header)

        return connection

    def __init__(self, socket, config=None, header=None):
        self.socket = Connection.SocketWrapper(socket)

        self.readers = Connection._default_readers()
        self.writers = Connection._default_writers()

        self.config = config if config is not None else self._read_config()
        self.header = header if header is not None else self._read_header()

        self.filters = []
        self.__closed = False

    def __next__(self):
        return self.next()

    def __enter__(self):
        return self

    def __exit__(self, *exception_info):
        self.close()
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

        aparam accepts: Predicate used to determine if a writer accepts an item.
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

    def close(self):
        if not self.__closed:
            end = constants.GadgetMessageIdentifier.pack(constants.GADGET_MESSAGE_CLOSE)
            self.socket.write(end)
            self.__closed = True

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
        assert (message_identifier == constants.GADGET_MESSAGE_CONFIG)
        config_bytes = read_byte_string(self.socket)

        try:
            parsed_config = xml.fromstring(config_bytes)
        except xml.ParseError as e:
            logging.warning(f"Config parsing failed with error message {e}")
            parsed_config = None

        return parsed_config

    def _write_config(self, config):
        serialization.write(self.socket, constants.GADGET_MESSAGE_CONFIG, constants.GadgetMessageIdentifier)
        write_byte_string(self.socket, xml.tostring(config, encoding='utf-8', method='xml'))

    def _read_header(self):
        message_identifier = self._read_message_identifier()
        assert (message_identifier == constants.GADGET_MESSAGE_HEADER)
        header_bytes = read_byte_string(self.socket)
        return ismrmrd.xsd.CreateFromDocument(header_bytes)

    def _write_header(self, header: ismrmrd.xsd.ismrmrdHeader):
        serialization.write(self.socket, constants.GADGET_MESSAGE_HEADER, constants.GadgetMessageIdentifier)
        write_byte_string(self.socket, ismrmrd.xsd.ToXML(header).encode('utf-8'))

    @staticmethod
    def _default_readers():
        return {
            constants.GADGET_MESSAGE_CLOSE: Connection.stop_iteration,
            constants.GADGET_MESSAGE_ISMRMRD_ACQUISITION: message_reader(ismrmrd.Acquisition),
            constants.GADGET_MESSAGE_ISMRMRD_WAVEFORM: message_reader(ismrmrd.Waveform),
            constants.GADGET_MESSAGE_ISMRMRD_IMAGE: message_reader(ismrmrd.Image),
            constants.GADGET_MESSAGE_IMAGE_ARRAY: message_reader(ImageArray),
            constants.GADGET_MESSAGE_RECON_DATA: message_reader(ReconData),
            constants.GADGET_MESSAGE_BUCKET: message_reader(AcquisitionBucket)
        }

    @staticmethod
    def _default_writers():
        def create_writer(message_id, obj_type):
            return lambda item: isinstance(item, obj_type), message_writer(message_id, obj_type)

        return [
            create_writer(constants.GADGET_MESSAGE_ISMRMRD_ACQUISITION, ismrmrd.Acquisition),
            create_writer(constants.GADGET_MESSAGE_ISMRMRD_WAVEFORM, ismrmrd.Waveform),
            create_writer(constants.GADGET_MESSAGE_ISMRMRD_IMAGE, ismrmrd.Image),
            create_writer(constants.GADGET_MESSAGE_IMAGE_ARRAY, ImageArray),
            create_writer(constants.GADGET_MESSAGE_RECON_DATA, ReconData)
        ]

    @staticmethod
    def stop_iteration(_):
        logging.debug("Connection closed normally.")
        raise StopIteration()
