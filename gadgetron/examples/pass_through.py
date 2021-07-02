
import time
import logging


def pass_through(connection):

    logging.info("Python pass-through gadget running - forwarding input.")

    start = time.time()

    for item in connection:
        connection.send(item)

    logging.info(f"Python forwarding done. Duration: {(time.time() - start):.2f} s")
