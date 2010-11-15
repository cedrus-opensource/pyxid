import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name = "pyxid",
    version = "0.1b1",
    packages = find_packages(),
    install_requires = ["pyserial>=2.5"],
    author = "Grant Limberg",
    author_email = "glimberg@cedrus.com",
    maintainer = "Cedrus Corporation",
    maintainer_email = "opensource@cedrus.com",
    description = "Pure python library for communicating with Cedrus XID devices.",
    long_description = open('README.txt').read(),
    license = "BSD",
    keywords = "cedrus xid XID",
    url = "http://www.github.com/cedrus-opensource/pyxid/",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: System :: Hardware",
        ]
    )
