import ismrmrd
import numpy as np
import struct
import ctypes

from gadgetron.external.constants import uint64, GadgetMessageIdentifier, GADGET_MESSAGE_RECON_DATA
from gadgetron.types.serialization import NDArray
import dataclasses
from typing import Optional, List


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


@dataclasses.dataclass
class ReconBuffer:
    data: NDArray[np.complex64]
    trajectory: Optional[NDArray[np.float32]]
    density : Optional[NDArray[np.float32]]
    headers : NDArray[ismrmrd.AcquisitionHeader]
    sampling_description : SamplingDescription


@dataclasses.dataclass
class ReconBit:
    data : ReconBuffer
    ref : Optional[ReconBuffer]

@dataclasses.dataclass
class ReconData:
    bits: List[ReconBit]

    def __getitem__(self, item):
        return self.bits[item]

    def __iter__(self):
        return iter(self.bits)

