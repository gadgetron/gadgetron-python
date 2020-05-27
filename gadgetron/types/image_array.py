import numpy as np

from ..external import readers
from ..external import writers
from ..external import constants


class ImageArray:
    def __init__(self, data=None, headers=None, meta=None, waveform=None, acq_headers=None):
        self.data = data
        self.headers = headers
        self.meta = meta
        self.waveform = waveform
        self.acq_headers = acq_headers



def read_meta_container(source):
    return readers.read_byte_string(source, constants.uint64).decode('ascii')


def read_meta_container_vector(source):
    size = readers.read(source, constants.uint64)
    return [read_meta_container(source) for _ in range(size)]


def read_waveforms(source):
    size = readers.read(source, constants.uint64)
    return [readers.read_waveform(source) for _ in range(size)]


def read_image_array(source):
    return ImageArray(
        data=readers.read_array(source, np.complex64),
        headers=readers.read_object_array(source, readers.read_image_header),
        meta=read_meta_container_vector(source),
        waveform=readers.read_optional(source, read_waveforms),
        acq_headers=readers.read_optional(
            source, readers.read_object_array, readers.read_acquisition_header)
    )


def write_meta_container(destination, container):
    writers.write_byte_string(
        destination, container.encode('ascii'), constants.uint64)


def write_meta_container_vector(destination, containers):
    destination.write(constants.uint64.pack(len(containers)))
    for container in containers:
        write_meta_container(destination, container)


def write_waveforms(destination, waveforms):
    destination.write(constants.uint64.pack(len(waveforms)))
    for waveform in waveforms:
        writers.write_waveform(destination, waveform)


def write_image_array(destination, image_array):
    destination.write(constants.GadgetMessageIdentifier.pack(
        constants.GADGET_MESSAGE_IMAGE_ARRAY))
    writers.write_array(destination, image_array.data, np.complex64)
    writers.write_object_array(
        destination, image_array.headers, writers.write_image_header)
    write_meta_container_vector(destination, image_array.meta)
    writers.write_optional(destination, image_array.waveform, write_waveforms)
    writers.write_optional(destination, image_array.acq_headers,
                           writers.write_object_array, writers.write_acquisition_header)
