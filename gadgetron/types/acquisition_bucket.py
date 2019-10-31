
import ctypes
import logging

import numpy as np

from ismrmrd import Acquisition, Waveform

from ..external.constants import uint64
from gadgetron.external.readers import read, read_acquisition_header, read_vector, read_waveform_header
from gadgetron.external.writers import write_optional, write_array, write_object_array, write_acquisition_header


class AcquisitionBucketStats:

    def __init__(self, kspace_encode_step_1={}, kspace_encode_step_2={}, slice={}, phase={}, contrast={}, repetition={},
                 set={}, segment={}, average={}):
        self.kspace_encode_step_1 = kspace_encode_step_1
        self.kspace_encode_step_2 = kspace_encode_step_2
        self.contrast = contrast
        self.slice = slice
        self.phase = phase
        self.repetition = repetition
        self.segment = segment
        self.average = average
        self.set = set


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


def read_bucketstats(source):
    count = read(source, uint64)
    return [AcquisitionBucketStats(*[{s for s in read_vector(source, np.uint16)}
                                     for _ in range(9)])
            for _ in range(count)]


def read_waveforms(source, sizes):
    headers = [read_waveform_header(source) for _ in range(sizes.count)]
    data_arrays = [read_data_as_array(source, np.uint32, (header.channels, header.number_of_samples))
                   for header in headers]
    return [Waveform(head, data) for head, data in zip(headers, data_arrays)]


def read_data_as_array(source, data_type, shape):
    dtype = np.dtype(data_type)
    bytesize = np.prod(shape) * dtype.itemsize
    return np.reshape(np.frombuffer(source.read(bytesize), dtype), shape)


def read_acquisitions(source, sizes):
    headers = [read_acquisition_header(source) for _ in range(sizes.count)]

    trajectories = [read_data_as_array(source, np.float32, (head.number_of_samples, head.trajectory_dimensions))
                    if head.trajectory_dimensions > 0 else None
                    for head in headers]

    acqs = [read_data_as_array(source, np.complex64, (head.active_channels, head.number_of_samples))
            for head in headers]

    return [Acquisition(header, data, trajectory) for header, data, trajectory in zip(headers, acqs, trajectories)]


def read_acquisition_bucket(source):
    meta = bucket_meta.from_buffer_copy(source.read(ctypes.sizeof(bucket_meta)))

    return AcquisitionBucket(
        read_acquisitions(source, meta.data),
        read_bucketstats(source),
        read_acquisitions(source, meta.reference),
        read_bucketstats(source),
        read_waveforms(source, meta.waveforms)
    )


