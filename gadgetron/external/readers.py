import ctypes
import ismrmrd

import functools

import numpy

from . import constants


def read(source, type):
    return type.unpack(source.read(type.size))[0]


def read_optional(source, continuation, *args, **kwargs):
    is_present = read(source, constants.bool)
    return continuation(source, *args, **kwargs) if is_present else None


def read_vector(source, numpy_type=numpy.uint64):
    size = read(source, constants.uint64)
    dtype = numpy.dtype(numpy_type)
    return numpy.frombuffer(source.read(size * dtype.itemsize), dtype=dtype)


def read_array(source, numpy_type=numpy.uint64):
    dtype = numpy.dtype(numpy_type)
    dimensions = read_vector(source)
    elements = int(functools.reduce(lambda a, b: a * b, dimensions))
    return numpy.reshape(numpy.frombuffer(source.read(elements * dtype.itemsize), dtype=dtype), dimensions, order='F')


def read_object_array(source, read_object):
    dimensions = read_vector(source)
    elements = int(functools.reduce(lambda a, b: a * b, dimensions))
    return numpy.reshape(numpy.asarray([read_object(source) for _ in range(elements)], dtype=object), dimensions,
                         order='F')


def read_image_header(source):
    header_bytes = source.read(ctypes.sizeof(ismrmrd.ImageHeader))
    return ismrmrd.ImageHeader.from_buffer_copy(header_bytes)


def read_acquisition_header(source):
    header_bytes = source.read(ctypes.sizeof(ismrmrd.AcquisitionHeader))
    return ismrmrd.AcquisitionHeader.from_buffer_copy(header_bytes)


def read_waveform_header(source):
    header_bytes = source.read(ctypes.sizeof(ismrmrd.WaveformHeader))
    return ismrmrd.Waveform.from_buffer_copy(header_bytes)


def read_gadget_message_length(source, type=constants.uint32):
    return read(source, type)


def read_byte_string(source, type=constants.uint32):
    length = read_gadget_message_length(source, type)
    byte_string = source.read(length)
    return byte_string


def read_acquisition(source):
    return ismrmrd.Acquisition.deserialize_from(source.read)


def read_waveform(source):
    return ismrmrd.Waveform.deserialize_from(source.read)


def read_image(source):
    return ismrmrd.Image.deserialize_from(source.read)
