import sys

def ensure_importable():
    try:
        import gadgetron      
    except ModuleNotFoundError or ImportError as ee:
        print('This dummy test script can only run if gadgetron is importable : {0}'.format(ee.msg), file=sys.stderr)
        exit(1)

ensure_importable()