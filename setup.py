from setuptools import find_packages, setup


setup(
    name="pysim",
    version="0.9.0",
    author="Andrey Larionov",
    author_email="larioandr@gmail.com",
    platforms=["any"],
    license="MIT",
    url="https://github.com/larioandr/thesis-rfidsim",
    packages=["pysim"],
    entry_points='''
        [console_scripts]
        sim=pysim.main:cli
    ''',
)
