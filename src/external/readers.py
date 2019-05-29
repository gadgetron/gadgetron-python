
import logging
import ismrmrd

import binascii

import gadgetron.external.constants as constants


def read_gadget_message_length(source):
    length_bytes = source.read(constants.SIZEOF_GADGET_MESSAGE_LENGTH)
    return constants.GadgetMessageLength.unpack(length_bytes)[0]


def read_byte_string(source):
    length = read_gadget_message_length(source)
    byte_string = source.read(length)
    return byte_string


def read_acquisition(source):
    return ismrmrd.Acquisition.deserialize_from(source.read)


def read_waveform(source):
    return ismrmrd.Waveform.deserialize_from(source.read)


def read_image(source):
    return ismrmrd.Image.deserialize_from(source.read)
