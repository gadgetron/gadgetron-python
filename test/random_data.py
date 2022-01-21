
import ismrmrd

import numpy as np
import numpy.random



def random_32bit_float():
    return numpy.random.rand(1).astype(np.float32)

def random_int(dtype,size=None):
    dinfo = np.iinfo(dtype)
    return numpy.random.randint(dinfo.min, dinfo.max,dtype=dtype,size=size)

def random_tuple(size, random_fn):
    return tuple([random_fn() for _ in range(0, size)])


def create_random_acquisition_properties():
    return {
        'flags': np.random.randint(0, 1 << 64,dtype=np.uint64),
        'measurement_uid': np.random.randint(0, 1 << 32,dtype=np.uint32),
        'scan_counter': np.random.randint(0, 1 << 32,dtype=np.uint32 ),
        'acquisition_time_stamp': random_int(np.uint32),
        'physiology_time_stamp': random_tuple(3, lambda: random_int(np.uint32)),
        'available_channels': random_int(np.uint16),
        'channel_mask': random_tuple(16, lambda: np.random.randint(0, 1 << 64,dtype=np.uint64)),
        'discard_pre': random_int(np.uint16),
        'discard_post': random_int(np.uint16),
        'center_sample': random_int(np.uint16),
        'encoding_space_ref': random_int(np.uint16),
        'sample_time_us': random_32bit_float(),
        'position': random_tuple(3, random_32bit_float),
        'read_dir': random_tuple(3, random_32bit_float),
        'phase_dir': random_tuple(3, random_32bit_float),
        'slice_dir': random_tuple(3, random_32bit_float),
        'patient_table_position': random_tuple(3, random_32bit_float),
        'idx': ismrmrd.EncodingCounters(),
        'user_int': random_tuple(8, lambda: random_int(np.int32)),
        'user_float': random_tuple(8, random_32bit_float)
    }


def create_random_image_properties():
    return {
        'flags': random_int(np.uint64),
        'measurement_uid': random_int(np.uint32),
        'field_of_view': random_tuple(3, random_32bit_float),
        'position': random_tuple(3, random_32bit_float),
        'read_dir': random_tuple(3, random_32bit_float),
        'phase_dir': random_tuple(3, random_32bit_float),
        'slice_dir': random_tuple(3, random_32bit_float),
        'patient_table_position': random_tuple(3, random_32bit_float),
        'average': random_int(np.uint16),
        'slice': random_int(np.uint16),
        'contrast': random_int(np.uint16),
        'phase': random_int(np.uint16),
        'repetition': random_int(np.uint16),
        'set': random_int(np.uint16),
        'acquisition_time_stamp': random_int(np.uint32),
        'physiology_time_stamp': random_tuple(3, lambda: random_int(np.uint32)),
        'image_index': random_int(np.uint16),
        'image_series_index': random_int(np.uint16),
        'user_int': random_tuple(8, lambda: random_int(np.int32)),
        'user_float': random_tuple(8, random_32bit_float),
    }


def create_random_waveform_properties():
    return {
        'flags': random_int(np.uint64),
        'measurement_uid': random_int(np.uint32),
        'waveform_id': random_int(np.uint16),
        'scan_counter': random_int(np.uint32),
        'time_stamp': random_int(np.uint32),
        'sample_time_us': random_32bit_float()
    }


def create_random_array(shape, dtype):
    array = numpy.random.random_sample(shape)
    return array.astype(dtype)


def create_random_data(shape=(32, 256)):
    array = numpy.random.random_sample(shape) + 1j * numpy.random.random_sample(shape)
    return array.astype(np.complex64)


def create_random_trajectory(shape=(256, 2)):
    return create_random_array(shape, dtype=np.float32)


def create_random_waveform_data(shape=(32, 256)):
    data = numpy.np.random.randint(0, 1 << 32, size=shape)
    return data.astype(np.uint32)


def create_random_acquisition():
    data = create_random_data((32, 256))
    traj = create_random_trajectory((256, 2))
    header = create_random_acquisition_properties()

    return ismrmrd.Acquisition.from_array(data, traj, **header)


def create_random_image():

    data = create_random_array((256, 256), dtype=np.float32)
    header = create_random_image_properties()

    image = ismrmrd.Image.from_array(data, **header)
    image.meta = {f"Random_{i}" : random_int(np.int64) for i in range(10)}

    return image

def create_random_image_header():
    return ismrmrd.ImageHeader(**create_random_image_properties())

def create_random_acquisition_header():
    return ismrmrd.AcquisitionHeader(**create_random_acquisition_properties())


def create_random_waveform():

    data = random_int(np.uint32, size=(4, 256))
    header = create_random_waveform_properties()

    return ismrmrd.Waveform.from_array(data, **header)
