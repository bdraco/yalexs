from distutils.core import setup

setup(
    name="yalexs",
    version="1.0.1",
    packages=["yalexs"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    url="https://github.com/bdraco/yalexs",
    license="MIT",
    author="bdraco",
    author_email="nick@koston.org",
    description="Python API for Yale Access (formerly August) Smart Lock and Doorbell",
    install_requires=[
        "requests",
        "vol",
        "python-dateutil",
        "aiohttp",
        "aiofiles",
        "pubnub",
    ],
)
