
import numpy

from ..external import decorators

from ..external.constants import uint64, GadgetMessageIdentifier, GADGET_MESSAGE_ISMRMRD_IMAGE_ARRAY
from ..external.readers import read, read_optional, read_array, read_object_array, read_byte_string, read_image_header, read_acquisition_header, read_waveform
from ..external.writers import write_optional, write_array, write_object_array, write_byte_string, write_image_header, write_acquisition_header, write_waveform


class ImageArray:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def read_meta_container(source):
    return read_byte_string(source, uint64).decode('utf-8')


def read_meta_container_vector(source):
    size = read(source, uint64)
    return [read_meta_container(source) for _ in range(size)]


def read_waveforms(source):
    size = read(source, uint64)
    return [read_waveform(source) for _ in range(size)]


@ decorators.reader(slot=GADGET_MESSAGE_ISMRMRD_IMAGE_ARRAY)
def read_image_array(source):
    return ImageArray(
        data=read_array(source, numpy.complex64),
        headers=read_object_array(source, read_image_header),
        meta=read_meta_container_vector(source),
        waveform=read_optional(source, read_waveforms),
        acq_headers=read_optional(source, read_object_array, read_acquisition_header)
    )


def write_meta_container(destination, container):
    write_byte_string(destination, container.encode('utf-8'), uint64)


def write_meta_container_vector(destination, containers):
    destination.write(uint64.pack(len(containers)))
    for container in containers:
        write_meta_container(destination, container)


def write_waveforms(destination, waveforms):
    destination.write(uint64.pack(len(waveforms)))
    for waveform in waveforms:
        write_waveform(destination, waveform)


@ decorators.writer(predicate=lambda item: isinstance(item, ImageArray))
def write_image_array(destination, image_array):
    destination.write(GadgetMessageIdentifier.pack(GADGET_MESSAGE_ISMRMRD_IMAGE_ARRAY))
    write_array(destination, image_array.data)
    write_object_array(destination, image_array.header, write_image_header)
    write_meta_container_vector(destination, image_array.meta)
    write_optional(destination, image_array.waveform, write_waveforms)
    write_optional(destination, image_array.acq_headers, write_object_array, write_acquisition_header)

