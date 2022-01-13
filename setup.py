from setuptools import find_packages, setup

setup(
    name="yalexs",
    version="1.1.18",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    url="https://github.com/bdraco/yalexs",
    license="MIT",
    author="bdraco",
    author_email="nick@koston.org",
    description="Python API for Yale Access (formerly August) Smart Lock and Doorbell",
    packages=find_packages(include=["yalexs", "yalexs.*"]),
    install_requires=[
        "requests",
        "vol",
        "python-dateutil",
        "aiohttp",
        "aiofiles",
        "pubnub>=5.5.0",
    ],
)
