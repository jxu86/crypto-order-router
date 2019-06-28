# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name='crypto_order_router',
    description='crypto exchange order router',
    version='0.0.2',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    test_suite="tests",
    zip_safe=False)
