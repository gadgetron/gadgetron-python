

from . import util
from . import version
from . import external
from . import examples
from . import types

__version__ = version.version

# To maintain compatibility with the old Gadgetron interface, we need names/types to be available
# in the 'gadgetron' package. These are aliased here:
from .legacy import Gadget

from .types.image_array import ImageArray as IsmrmrdImageArray
from .types.recon_data import ReconData as IsmrmrdReconData
from .types.recon_data import ReconBit as IsmrmrdReconBit
from .types.recon_data import ReconBuffer as IsmrmrdDataBuffered
from .types.recon_data import SamplingDescription, SamplingLimit


__all__ = [
    util,
    legacy,
    external,
    examples,
    Gadget,
    IsmrmrdImageArray,
    IsmrmrdReconData,
    IsmrmrdReconBit,
    IsmrmrdDataBuffered,
    SamplingDescription,
    SamplingLimit
]
