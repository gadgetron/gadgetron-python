from setuptools import setup

setup(
    name='gadgetron',
    version='1.0.0',
    packages=[
        'gadgetron',
        'gadgetron.util',
        'gadgetron.legacy',
        'gadgetron.external'
    ],
    package_dir={
        'gadgetron': 'src'
    },
    url='',
    license='',
    author='Kristoffer Langeland Knudsen',
    author_email='kristofferlknudsen@gradientsoftware.net',
    description='',
    install_requires=[
        'numpy>=1.15.1',
        'ismrmrd>=1.6.1'
    ]
)
