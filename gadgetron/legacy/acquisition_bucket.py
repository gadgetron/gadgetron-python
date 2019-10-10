import numpy as np
import struct
import ctypes
import logging
from ismrmrd import Acquisition, Waveform
from ..external import decorators
from ..external.readers import read, read_acquisition_header,read_vector, read_waveform_header
from ..external.writers import write_optional, write_array, write_object_array, write_acquisition_header
from ..external.constants import uint64, GadgetMessageIdentifier, GADGET_MESSAGE_BUCKET



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
    def __init__(self, data, ref, datastats, refstats, waveform=None):
        self.data = data
        self.ref = ref
        self.datastats = datastats
        self.refstats = refstats
        self.waveform = waveform


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
    count = read(source,uint64)
    print(count)
    return [AcquisitionBucketStats(*[{s for s in read_vector(source,np.uint16)} for i in range(9)]) for k in range(count)]


def read_waveforms(source, sizes):
    headers = [ read_waveform_header(source) for i in range(sizes.count)]
    data_arrays = [read_data_as_array(source,np.uint32,(header.channels,header.number_of_samples)) for header in headers]
    return [Waveform(head,data) for (head,data) in zip(headers,data_arrays)]


def read_data_as_array(source, data_type, shape):
    dtype = np.dtype(data_type)
    bytesize = np.prod(shape) * dtype.itemsize
    print('Bytesize',bytesize,dtype.itemsize,shape)
    return np.reshape(np.frombuffer(source.read(bytesize), dtype), shape)


def read_acquisitions(source, sizes):
    print("Reading ", sizes.count, "headers")
    headers = [read_acquisition_header(source) for i in range(sizes.count)]
    trajectories = [read_data_as_array(source, np.float32, (
        head.number_of_samples, head.trajectory_dimensions)) if head.trajectory_dimensions > 0 else None for head in
                    headers]

    tmp = [head.active_channels for head in headers]

    acqs = [read_data_as_array(source, np.complex64, (head.active_channels, head.number_of_samples)) for head in
            headers]
    return [Acquisition(header,data,trajectory) for header,data,trajectory in zip(headers,acqs,trajectories)]


@decorators.reader(slot=GADGET_MESSAGE_BUCKET)
def read_acquisition_bucket(source):
    meta = bucket_meta.from_buffer_copy(source.read(ctypes.sizeof(bucket_meta)))
    data = read_acquisitions(source,meta.data)
    stats = read_bucketstats(source)
    ref = read_acquisitions(source,meta.reference)
    refstats = read_bucketstats(source)
    waveforms = read_waveforms(source,meta.waveforms)

    return AcquisitionBucket(data,ref,stats,refstats,waveforms)


