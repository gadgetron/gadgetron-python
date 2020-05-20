
import numpy
import struct
import ctypes

from gadgetron.external.readers import read, read_optional, read_array, read_object_array, read_acquisition_header
from gadgetron.external.writers import write_optional, write_array, write_object_array, write_acquisition_header
from gadgetron.external.constants import uint64, GadgetMessageIdentifier, GADGET_MESSAGE_RECON_DATA

uint16 = struct.Struct('<H')


class SamplingLimit(ctypes.Structure):
    _fields_ = [
        ('min', ctypes.c_uint16),
        ('center', ctypes.c_uint16),
        ('max', ctypes.c_uint16)
    ]

    def __iter__(self):
        return iter([self.min, self.center, self.max])


class SamplingDescription(ctypes.Structure):
    _fields_ = [
        ('encoded_FOV', ctypes.c_float * 3),
        ('recon_FOV', ctypes.c_float * 3),
        ('encoded_matrix', ctypes.c_uint16 * 3),
        ('recon_matrix', ctypes.c_uint16 * 3),
        ('sampling_limits', SamplingLimit * 3)
    ]


class ReconBuffer:
    def __init__(self, data, trajectory, density, headers, sampling_description):
        self.data = data
        self.trajectory = trajectory
        self.density = density
        self.headers = headers
        self.sampling = sampling_description


class ReconBit:
    def __init__(self, buffer, reference=None):
        self.data = buffer
        self.ref = reference


class ReconData:
    def __init__(self, bits):
        self.bits = bits

    def __getitem__(self, item):
        return self.bits[item]

    def __iter__(self):
        return iter(self.bits)


def read_sampling_description(source):
    return SamplingDescription.from_buffer_copy(source.read(ctypes.sizeof(SamplingDescription)))


def read_recon_buffer(source):

    data = read_array(source, numpy.complex64)
    trajectory = read_optional(source, read_array, numpy.float32)
    density = read_optional(source, read_array, numpy.float32)
    headers = read_object_array(source, read_acquisition_header)
    sampling_description = read_sampling_description(source)

    return ReconBuffer(data, trajectory, density, headers, sampling_description)


def read_recon_bit(source):
    buffer = read_recon_buffer(source)
    reference = read_optional(source, read_recon_buffer)
    return ReconBit(buffer, reference)


def read_recon_bits(source):
    size = read(source, uint64)
    return [read_recon_bit(source) for _ in range(size)]


def read_recon_data(source):
    return ReconData(read_recon_bits(source))


def write_sampling_description(destination, description):
    destination.write(description)


def write_recon_buffer(destination, buffer):
    write_array(destination, buffer.data, numpy.complex64)
    write_optional(destination, buffer.trajectory, write_array,numpy.float32)
    write_optional(destination, buffer.density, write_array,numpy.float32)
    write_object_array(destination, buffer.headers, write_acquisition_header)
    write_sampling_description(destination, buffer.sampling)


def write_recon_bit(destination, bit):
    write_recon_buffer(destination, bit.data)
    write_optional(destination, bit.ref, write_recon_buffer)


def write_recon_data(destination, recon_data):
    destination.write(GadgetMessageIdentifier.pack(GADGET_MESSAGE_RECON_DATA))
    destination.write(uint64.pack(len(recon_data.bits)))
    for bit in recon_data.bits:
        write_recon_bit(destination, bit)
