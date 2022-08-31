from setuptools import setup


version = {}
with open("gadgetron/version.py") as fp:
    exec(fp.read(), version)
# later on we use: version['__version__']

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

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
    description='Python interface for Gadgetron',
    long_description = long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'numpy>=1.22',
        'ismrmrd>=1.12.5',
        'pyFFTW>=0.11',
        'multimethod>=1.0'
    ]
)
