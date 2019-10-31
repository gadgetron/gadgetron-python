
import logging
import ismrmrd
import numpy as np

from gadgetron.util.cfft import cfftn, cifftn

from .shared import Slice


def noise_adjustment(iterable, header):
    # The dataset might include noise measurements (mine does). We'll consume noise measurements, use them
    # to prepare a noise adjustment matrix, and never pass them down the chain. They contain no image data,
    # and will not be missed. We'll also perform noise adjustment on following acquisitions, when we have a
    # noise matrix available.

    noise_matrix = None
    noise_dwell_time = 1.0

    try:
        noise_bandwidth = header.encoding[0].acquisitionSystemInformation.relativeNoiseBandwidth
    except:
        noise_bandwidth = 0.793

    def scaling_factor(acq):
        return np.sqrt(2 * acq.sample_time_us * noise_bandwidth / noise_dwell_time)

    def calculate_whitening_transformation(noise):
        noise = np.asmatrix(noise)
        covariance = (1.0 / (noise.shape[1] - 1)) * (noise * noise.H)
        return np.linalg.inv(np.linalg.cholesky(covariance))

    def apply_whitening_transformation(acq):
        return np.asarray(scaling_factor(acq) * noise_matrix * np.asmatrix(acq.data))

    def noise_adjust(acq):
        if noise_matrix is not None:
            acq.data[:] = apply_whitening_transformation(acq)
        return acq

    for acquisition in iterable:
        if acquisition.is_flag_set(ismrmrd.ACQ_IS_NOISE_MEASUREMENT):
            noise_matrix = calculate_whitening_transformation(acquisition.data)
            noise_dwell_time = acquisition.sample_time_us
        else:
            yield noise_adjust(acquisition)


def remove_oversampling(iterable, header):
    # The dataset I'm working with was originally taken on a Siemens scanner. It features 2x oversampling
    # along the first image dimension. We're going to have a look at the header. If our encoded space
    # doesn't match the recon space, we're going to crop the acquisition.

    encoding_space = header.encoding[0].encodedSpace.matrixSize
    recon_space = header.encoding[0].reconSpace.matrixSize

    if encoding_space.x == recon_space.x:
        yield from iterable

    x0 = (encoding_space.x - recon_space.x) // 2
    x1 = (encoding_space.x - recon_space.x) // 2 + recon_space.x

    def crop_acquisition(acquisition):
        x_space = cifftn(acquisition.data, axes=[1])
        x_space = x_space[:, x0:x1]
        acquisition.resize(number_of_samples=x_space.shape[1], active_channels=x_space.shape[0])
        acquisition.center_sample = recon_space.x // 2
        acquisition.data[:] = cfftn(x_space, axes=[1])

        return acquisition

    for acq in iterable:
        yield crop_acquisition(acq)


def create_slice_from_acquisitions(iterable, header):
    # To form images, we need a full slice of data. We accumulate acquisitions until we reach the
    # end of a slice. The acquisitions are then combined in a single buffer, which is passed
    # on. We also pass on a reference acquisition header. We use it later to initialize image metadata.

    acquisitions = []
    matrix_size = header.encoding[0].encodedSpace.matrixSize

    def assemble_slice_data(acqs):
        logging.debug(f"Assembling buffer from {len(acqs)} acquisitions.")

        buffer = np.zeros(
            (acqs[0].data.shape[0],
             acqs[0].data.shape[1],
             matrix_size.y,
             matrix_size.z),
            dtype=np.complex64
        )

        for acq in acqs:
            buffer[:, :, acq.idx.kspace_encode_step_1, acq.idx.kspace_encode_step_2] = acq.data

        return buffer

    for acquisition in iterable:
        acquisitions.append(acquisition)
        if acquisition.is_flag_set(ismrmrd.ACQ_LAST_IN_SLICE):
            yield Slice(reference=acquisition, data=assemble_slice_data(acquisitions))
            acquisitions = []
