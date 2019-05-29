

class Module:

    @ classmethod
    def __init_subclass__(cls, **kwargs):
        print(f"Initializing hooks for Module class: {cls.__name__}")

        



