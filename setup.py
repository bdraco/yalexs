from setuptools import find_packages, setup

setup(
    name="yalexs",
    version="1.10.0",
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    url="https://github.com/bdraco/yalexs",
    license="MIT",
    author="bdraco",
    author_email="nick@koston.org",
    description="Python API for Yale Access (formerly August) Smart Lock and Doorbell",
    packages=find_packages(include=["yalexs", "yalexs.backports", "yalexs.*"]),
    install_requires=[
        "ciso8601>=2.1.3",
        "pyjwt",
        "requests",
        "vol",
        "python-dateutil",
        "aiohttp",
        "aiofiles",
        "pubnub>=7.1.0",
        "typing_extensions>=4.5.0"
    ],
)
