# Copyright 2014 Rackspace, Andrew Melton
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


import setuptools


setuptools.setup(
    name="IDMapShift",
    version="0.0.2",
    packages=['idmapshift'],
    author="Andrew Melton",
    author_email="andrew.melton@rackspace.com",
    description="Tool to properly chown filesystems for "
                 "use with user namespaces.",
    license="Apache",
    keywords="user namespaces idmap containers",
    url="https://github.com/ramielrowe/idmapshift",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux"
    ],
    install_requires=[
        'argparse'
    ],
    entry_points={
        "console_scripts": [
            "idmapshift = idmapshift.main:main"
        ]
    }
)
