from setuptools import setup

import gadgetron

setup(
    name='gadgetron',
    version=gadgetron.__version__,
    packages=[
        'gadgetron',
        'gadgetron.util',
        'gadgetron.external',
        'gadgetron.examples',
        'gadgetron.legacy'
    ],
    url='',
    license='MIT',
    author='Kristoffer Langeland Knudsen',
    author_email='kristofferlknudsen@gradientsoftware.net',
    description='',
    install_requires=[
        'numpy>=1.15.1',
        'ismrmrd>=1.6.2',
        'pyFFTW>=0.11',
        'multimethod'
    ]
)
