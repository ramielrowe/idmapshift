import setuptools


setuptools.setup(
    name="IDMapShift",
    version="0.0.1",
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
