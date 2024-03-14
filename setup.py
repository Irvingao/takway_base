# setup.py

from setuptools import setup, find_packages

setup(
    name='takway',
    version='1.0',
    packages=find_packages(),  # 自动发现包和子包
    url='https://github.com/Irvingao/takway_base',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
