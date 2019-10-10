import struct

GADGET_MESSAGE_INT_ID_MIN                             =    0
GADGET_MESSAGE_FILENAME                               =    1
GADGET_MESSAGE_CONFIG                                 =    2
GADGET_MESSAGE_HEADER                                 =    3
GADGET_MESSAGE_CLOSE                                  =    4
GADGET_MESSAGE_TEXT                                   =    5
GADGET_MESSAGE_QUERY                                  =    6
GADGET_MESSAGE_RESPONSE                               =    7
GADGET_MESSAGE_ERROR                                  =    8
GADGET_MESSAGE_INT_ID_MAX                             =  999
GADGET_MESSAGE_EXT_ID_MIN                             = 1000
GADGET_MESSAGE_ISMRMRD_ACQUISITION                    = 1008
GADGET_MESSAGE_ISMRMRD_IMAGE_CPLX_FLOAT               = 1009
GADGET_MESSAGE_ISMRMRD_IMAGE_REAL_FLOAT               = 1010
GADGET_MESSAGE_ISMRMRD_IMAGE_REAL_USHORT              = 1011
GADGET_MESSAGE_DICOM                                  = 1012
GADGET_MESSAGE_ISMRMRD_IMAGE                          = 1022
GADGET_MESSAGE_RECON_DATA                             = 1023
GADGET_MESSAGE_IMAGE_ARRAY                            = 1024
GADGET_MESSAGE_ISMRMRD_WAVEFORM                       = 1026
GADGET_MESSAGE_BUCKET                                 = 1050
GADGET_MESSAGE_EXT_ID_MAX                             = 4096

GadgetMessageIdentifier = struct.Struct('<H')

bool = struct.Struct('<?')
uint32 = struct.Struct('<I')
uint64 = struct.Struct('<Q')
uint16 = struct.Struct('<H')
