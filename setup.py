from distutils.core import setup

setup(
    name="yalexs",
    version="1.0.1",
    packages=["yalexs"],
    url="https://github.com/bdraco/yalexs",
    license="MIT",
    author="bdraco",
    author_email="nick@koston.org",
    description="Python API for Yale Access (formerly August) Smart Lock and Doorbell",
    install_requires=["requests", "vol", "python-dateutil", "aiohttp", "aiofiles", "pubnub"],
)
