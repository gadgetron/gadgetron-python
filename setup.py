from setuptools import setup


version = {}
with open("gadgetron/version.py") as fp:
    exec(fp.read(), version)
# later on we use: version['__version__']
setup(
    name='gadgetron',
    version=version['version'],
    packages=[
        'gadgetron',
        'gadgetron.util',
        'gadgetron.external',
        'gadgetron.examples',
        'gadgetron.legacy',
        'gadgetron.types'
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
        'multimethod >= 1.0'
    ]
)
