
import ismrmrd

import gadgetron.external.constants as constants


def write_image(destination, image):
    message_id_bytes = constants.GadgetMessageIdentifier.pack(constants.GADGET_MESSAGE_ISMRMRD_IMAGE)
    destination.write(message_id_bytes)
    image.serialize_into(destination.write)
