from gadgetron.types.serialization import NDArray
from gadgetron.types import serialization
from gadgetron.types.recon_data import SamplingDescription
from gadgetron.types.image_array import ImageArray

import ismrmrd
import numpy as np
import dataclasses

from typing import List, Optional

from io import BytesIO


@dataclasses.dataclass
class SimpleTestClass:
    data: NDArray[np.float32]
    mdata: NDArray[np.float64]
    headers: List[ismrmrd.AcquisitionHeader]


def roundtrip_serialization(obj, obj_type):
    buffer = BytesIO()
    serialization.write(buffer, obj, obj_type)
    buffer.seek(0)
    return serialization.read(buffer, obj_type)


def test_dataclass():
    a = SimpleTestClass(np.zeros((2, 2), dtype=np.float32), np.ones((1, 1, 3), dtype=np.float64), [])
    b = roundtrip_serialization(a, SimpleTestClass)

    assert np.equal(a.data, b.data, casting='no').all()
    assert np.equal(a.mdata, b.mdata, casting='no').all()
    assert a.headers == b.headers


def test_acquisition():
    data = np.array(np.random.normal(0, 10, size=(12, 128)), dtype=np.complex64)
    traj = np.array(np.random.normal(0, 10, size=(128, 2)), dtype=np.float32)

    a = ismrmrd.Acquisition.from_array(data, traj)

    b = roundtrip_serialization(a, ismrmrd.Acquisition)
    assert a == b


def test_optional():
    a = np.array(np.random.random((1, 2, 3)), dtype=np.complex128)

    b = roundtrip_serialization(a, Optional[NDArray[np.complex128]])

    assert np.equal(a, b, casting='no').all()


def test_sampling_description():
    a = SamplingDescription()
    b = roundtrip_serialization(a, SamplingDescription)

    for field in a._fields_:
        assert (np.array(getattr(a, field[0])) == np.array(getattr(b, field[0]))).all()


def test_image_array():
    a = ImageArray()
    a.acq_headers = np.array([ismrmrd.AcquisitionHeader() for k in range(20)], dtype=object)

    b = roundtrip_serialization(a, ImageArray)

    assert np.equal(a.data, b.data, casting='no').all()
    assert np.equal(a.headers, b.headers, casting='no').all()
    assert a.meta == b.meta
