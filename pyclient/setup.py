# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
'''
Python package setup (used by Dockerfile).
'''

from setuptools import setup, find_packages

setup(
    name='cookiejar-cli',
    version='1.0',
    description='Sawtooth Cookie Jar Example',
    author='Dan Anderson',
    url='https://github.com/danintel/sawtooth-cookiejar',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'colorlog',
        'protobuf',
        'sawtooth-sdk',
        'sawtooth-signing',
        'PyYAML',
    ],
    data_files=[],
    entry_points={
        'console_scripts': [
            'cookiejar = cookiejar_cli:main',
        ]
    })

