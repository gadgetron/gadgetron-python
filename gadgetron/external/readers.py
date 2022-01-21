import ctypes
import numpy as np

import ismrmrd

import functools

import numpy

from . import constants

from ..types.serialization import reader, read, isstruct, isgeneric, NDArray, inheritsfrom, isoptional, Vector
from typing import get_args, List, Optional
import dataclasses


@reader(predicate=inheritsfrom(np.number))
def read_numpy_number(source, class_type):
    dtype = np.dtype(class_type)
    return np.frombuffer(source.read(dtype.itemsize), dtype=dtype).item()


@reader(predicate=dataclasses.is_dataclass)
def read_dataclass(source, class_type):
    return class_type(*(read(source, dim.type) for dim in dataclasses.fields(class_type)))


@reader(predicate=isstruct)
def read_struct(source, struct_type):
    return struct_type.unpack(source.read(struct_type.size))[0]


@reader(predicate=inheritsfrom(ctypes.Structure))
def read_cstruct(source, obj_type):
    return obj_type.from_buffer_copy(source.read(ctypes.sizeof(obj_type)))


@reader(predicate=isgeneric(set))
def read_set(source, obj_type):
    return set(read_list(source, obj_type))

@reader(predicate=isgeneric(Vector))
def read_vector(source, obj_type):
    subtype = get_args(obj_type)[0]
    size = read_struct(source, constants.uint64)
    dtype = np.dtype(subtype)

    if dtype == object or not dtype.isbuiltin or subtype == str:
        return np.array([read(source, subtype) for s in range(size)],dtype=object)
    else:
        return np.frombuffer(source.read(size * dtype.itemsize), dtype=dtype)


@reader(predicate=isgeneric(list))
def read_list(source, obj_type):
    subtype = get_args(obj_type)[0]
    size = read_struct(source, constants.uint64)
    dtype = np.dtype(subtype)

    if dtype == object or not dtype.isbuiltin or subtype == str:
        return [read(source, subtype) for s in range(size)]
    else:
        return list(np.frombuffer(source.read(size * dtype.itemsize), dtype=dtype))


@reader(predicate=isgeneric(NDArray))
def read_array(source, obj_type):
    subtype = get_args(obj_type)[0]
    dtype = np.dtype(subtype)
    dimensions = read(source, List[np.uint64])
    elements = np.prod(dimensions)
    if dtype == object or not dtype.isbuiltin:

        return np.reshape(np.asarray([read(source, subtype) for _ in range(elements)], dtype=object), dimensions,
                          order='F')
    else:
        return np.reshape(np.frombuffer(source.read(int(elements) * dtype.itemsize), dtype=dtype), dimensions,
                          order='F')


@reader(predicate=isoptional)
def read_optional(source, obj_type):
    subtype = get_args(obj_type)[0]
    is_present = read_struct(source, constants.bool)
    return read(source, subtype) if is_present else None


@reader(ismrmrd.ImageHeader)
def read_image_header(source):
    header_bytes = source.read(ctypes.sizeof(ismrmrd.ImageHeader))
    return ismrmrd.ImageHeader.from_buffer_copy(header_bytes)


@reader(ismrmrd.AcquisitionHeader)
def read_acquisition_header(source):
    header_bytes = source.read(ctypes.sizeof(ismrmrd.AcquisitionHeader))
    return ismrmrd.AcquisitionHeader.from_buffer_copy(header_bytes)


@reader(ismrmrd.WaveformHeader)
def read_waveform_header(source):
    header_bytes = source.read(ctypes.sizeof(ismrmrd.WaveformHeader))
    return ismrmrd.Waveform.from_buffer_copy(header_bytes)


def read_gadget_message_length(source, type=constants.uint32):
    return read(source, type)


def read_byte_string(source, type=constants.uint32):
    length = read_gadget_message_length(source, type)
    byte_string = source.read(length)
    return byte_string


@reader(ismrmrd.Acquisition)
def read_acquisition(source):
    return ismrmrd.Acquisition.deserialize_from(source.read)


@reader(ismrmrd.Waveform)
def read_waveform(source):
    return ismrmrd.Waveform.deserialize_from(source.read)


@reader(data_type=ismrmrd.Image)
def read_image(source):
    return ismrmrd.Image.deserialize_from(source.read)


@reader(str)
def read_str(source):
    return read_byte_string(source, constants.uint64).rstrip(b'\0').decode('utf-8')
