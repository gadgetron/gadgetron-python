
import numpy as np

from ..external import constants


def write_optional(destination, optional, continuation, *args, **kwargs):
    if optional is None:
        destination.write(constants.bool.pack(False))
    else:
        destination.write(constants.bool.pack(True))
        continuation(destination, optional, *args, **kwargs)


def write_vector(destination, values, type=constants.uint64):
    destination.write(constants.uint64.pack(len(values)))
    for val in values:
        destination.write(type.pack(val))


def write_array(destination, array, dtype):
    write_vector(destination, array.shape)
    array_view = np.array(array,dtype=dtype,copy=False)
    destination.write(array_view.tobytes(order='F'))


def write_object_array(destination, array, writer, *args, **kwargs):
    write_vector(destination, array.shape)
    for item in np.nditer(array, ('refs_ok', 'zerosize_ok'), order='F'):
        item = item.item()  # Get rid of the numpy 0-dimensional array.
        writer(destination, item, *args, **kwargs)


def write_acquisition_header(destination, header):
    destination.write(header)


def write_image_header(destination, header):
    destination.write(header)


def write_byte_string(destination, byte_string, type=constants.uint32):
    destination.write(type.pack(len(byte_string)))
    destination.write(byte_string)


def write_acquisition(destination, acquisition):
    message_id_bytes = constants.GadgetMessageIdentifier.pack(constants.GADGET_MESSAGE_ISMRMRD_ACQUISITION)
    destination.write(message_id_bytes)
    acquisition.serialize_into(destination.write)


def write_waveform(destination, waveform):
    message_id_bytes = constants.GadgetMessageIdentifier.pack(constants.GADGET_MESSAGE_ISMRMRD_WAVEFORM)
    destination.write(message_id_bytes)
    waveform.serialize_into(destination.write)


def write_image(destination, image):
    message_id_bytes = constants.GadgetMessageIdentifier.pack(constants.GADGET_MESSAGE_ISMRMRD_IMAGE)
    destination.write(message_id_bytes)
    image.serialize_into(destination.write)
