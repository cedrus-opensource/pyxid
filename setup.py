from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.txt'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = "pyxid2",
    version = "1.0.5",
    packages = find_packages(),
    install_requires = ["ftd2xx>=1.3.1"],
    author = "Eugene Matsak",
    author_email = "developers@cedrus.com",
    maintainer = "Cedrus Corporation",
    maintainer_email = "developers@cedrus.com",
    description = ("Python library for interfacing with Cedrus XID devices, e.g. StimTracker, RB-x40, c-pod, and Lumina."),
    long_description = long_description,
    long_description_content_type='text/markdown',
    license = "BSD",
    keywords = "cedrus xid XID stimulus response data collection",
    url = "http://www.github.com/cedrus-opensource/pyxid/",
    classifiers = [
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: System :: Hardware",
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        ]
    )
