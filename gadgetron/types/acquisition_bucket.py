import ctypes

import ismrmrd
import numpy as np

from ismrmrd import Acquisition, Waveform

from gadgetron.external.constants import uint64
from gadgetron.types.serialization import NDArray, read, reader
from typing import Optional, List, Set
from dataclasses import dataclass, field


@dataclass
class AcquisitionBucketStats:
    kspace_encode_step_1: Set[np.uint16] = field(default_factory=set)
    kspace_encode_step_2: Set[np.uint16] = field(default_factory=set)
    contrast: Set[np.uint16] = field(default_factory=set)
    slice: Set[np.uint16] = field(default_factory=set)
    phase: Set[np.uint16] = field(default_factory=set)
    repetition: Set[np.uint16] = field(default_factory=set)
    segment: Set[np.uint16] = field(default_factory=set)
    average: Set[np.uint16] = field(default_factory=set)
    set: Set[np.uint16] = field(default_factory=set)


class AcquisitionBucket:
    def __init__(self, data, datastats, ref, refstats, waveforms):
        self.data = data
        self.datastats = datastats
        self.ref = ref
        self.refstats = refstats
        self.waveforms = waveforms


class bundle_meta(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_uint64),
        ("header_bytes", ctypes.c_uint64),
        ("data_bytes", ctypes.c_uint64),
        ("trajectory_bytes", ctypes.c_uint64)

    ]


class stats_meta(ctypes.Structure):
    _fields_ = [
        ("nbytes", ctypes.c_uint64)
    ]


class waveform_meta(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_uint64),
        ("header_bytes", ctypes.c_uint64),
        ("data_bytes", ctypes.c_uint64)
    ]


class bucket_meta(ctypes.Structure):
    _fields_ = [
        ("data", bundle_meta),
        ("reference", bundle_meta),
        ("data_stats", stats_meta),
        ("reference_stats", stats_meta),
        ("waveforms", waveform_meta)
    ]


def __read_waveforms(source, sizes):
    headers = [read(source, ismrmrd.WaveformHeader) for _ in range(sizes.count)]
    data_arrays = [__read_data_as_array(source, np.uint32, (header.channels, header.number_of_samples))
                   for header in headers]
    return [Waveform(head, data) for head, data in zip(headers, data_arrays)]


def __read_data_as_array(source, data_type, shape):
    dtype = np.dtype(data_type)
    bytesize = np.prod(shape) * dtype.itemsize
    return np.reshape(np.frombuffer(source.read(bytesize), dtype), shape)


def __read_acquisitions(source, sizes):
    headers = [read(source, ismrmrd.AcquisitionHeader) for _ in range(sizes.count)]

    trajectories = [__read_data_as_array(source, np.float32, (head.number_of_samples, head.trajectory_dimensions))
                    if head.trajectory_dimensions > 0 else None
                    for head in headers]

    acqs = [__read_data_as_array(source, np.complex64, (head.active_channels, head.number_of_samples))
            for head in headers]

    return [Acquisition(header, data, trajectory) for header, data, trajectory in zip(headers, acqs, trajectories)]


@reader(AcquisitionBucket)
def read_acquisition_bucket(source):
    meta = bucket_meta.from_buffer_copy(source.read(ctypes.sizeof(bucket_meta)))

    return AcquisitionBucket(
        __read_acquisitions(source, meta.data),
        read(source, List[AcquisitionBucketStats]),
        __read_acquisitions(source, meta.reference),
        read(source, List[AcquisitionBucketStats]),
        __read_waveforms(source, meta.waveforms)
    )
