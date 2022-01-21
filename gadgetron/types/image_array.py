import ismrmrd
import numpy as np

from ..external import readers, constants
from ..external import writers
import dataclasses
from ..types.serialization import NDArray, Vector
from typing import List, Optional


@dataclasses.dataclass
class ImageArray:
    data: NDArray[np.complex64] = np.zeros(0,dtype=np.complex64)
    headers: NDArray[ismrmrd.ImageHeader] = np.array([],dtype=object)
    meta: List[str] = dataclasses.field(default_factory=list)
    waveform: Optional[Vector[ismrmrd.Waveform]] = None
    acq_headers: Optional[Vector[ismrmrd.AcquisitionHeader]] = None

