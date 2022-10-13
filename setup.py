from setuptools import find_packages, setup


setup(
    name="pysim",
    version="0.9.0",
    author="Andrey Larionov, Abramian Vilmen",
    author_email="abramian.vl@phystech.edu",
    platforms=["any"],
    license="MIT",
    url="https://github.com/VilmenAbramian/RFID_sim",
    packages=["pysim"],
    entry_points='''
        [console_scripts]
        sim=pysim.main:cli
    ''',
)