import ctypes

import ismrmrd
import numpy as np

from . import constants
from ..types.serialization import writer, NDArray, isstruct, isgeneric, write, inheritsfrom, isoptional, Vector
from typing import Optional, List, get_args
import dataclasses


@writer(predicate=inheritsfrom(np.number))
def write_numpy_number(source, number, num_type):
    source.write(num_type(number).tobytes())


@writer(predicate=dataclasses.is_dataclass)
def write_dataclass(source, dataclass_obj, class_type):
    for dim in dataclasses.fields(class_type):
        write(source, getattr(dataclass_obj, dim.name), dim.type)


@writer(predicate=isstruct)
def write_struct(destination, value, struct_type):
    destination.write(struct_type.pack(value))


@writer(predicate=inheritsfrom(ctypes.Structure))
def write_cstruct(destination, value, obj_type):
    destination.write(value)


@writer(predicate=isoptional)
def write_optional(destination, optional, obj_type):
    subtype = get_args(obj_type)[0]
    if optional is None:
        destination.write(constants.bool.pack(False))
    else:
        destination.write(constants.bool.pack(True))
        write(destination, optional, subtype)


@writer(predicate=isgeneric(set))
def write_set(destination, values, obj_type):
    subtype = get_args(obj_type)[0]
    destination.write(constants.uint64.pack(len(values)))
    for val in values:
        write(destination, val, subtype)


@writer(predicate=isgeneric(Vector))
def write_vector(destination, values, obj_type):
    subtype = get_args(obj_type)[0]
    destination.write(constants.uint64.pack(len(values)))
    __writer_array_content(destination,values,subtype)

@writer(predicate=isgeneric(list))
def write_list(destination, values, obj_type):
    subtype = get_args(obj_type)[0]
    destination.write(constants.uint64.pack(len(values)))
    for val in values:
        write(destination, val, subtype)


def __writer_array_content(destination, array, data_type):
    dtype = np.dtype(data_type)
    if dtype == object or not dtype.isbuiltin:
        for item in np.nditer(array, ('refs_ok', 'zerosize_ok'), order='F'):
            item = item.item()  # Get rid of the numpy 0-dimensional array.
            write(destination, item, data_type)
    else:
        array_view = np.array(array, dtype=dtype, copy=False)
        destination.write(array_view.tobytes(order='F'))


@writer(predicate=isgeneric(NDArray))
def write_array(destination, array, array_type):
    write_list(destination, array.shape, List[np.uint64])
    subtype = get_args(array_type)[0]
    __writer_array_content(destination,array,subtype)


@writer(ismrmrd.AcquisitionHeader)
def write_acquisition_header(destination, header):
    destination.write(header)


@writer(ismrmrd.ImageHeader)
def write_image_header(destination, header):
    destination.write(header)


def write_byte_string(destination, byte_string, type=constants.uint32):
    destination.write(type.pack(len(byte_string)))
    destination.write(byte_string)


@writer(ismrmrd.Acquisition)
def write_acquisition(destination, acquisition):
    acquisition.serialize_into(destination.write)


@writer(ismrmrd.Waveform)
def write_waveform(destination, waveform):
    waveform.serialize_into(destination.write)


@writer(ismrmrd.Image)
def write_image(destination, image):
    image.serialize_into(destination.write)

@writer(str)
def write_str(destination, string : str ):
    write_byte_string(destination, string.encode("utf-8"), type=constants.uint64)