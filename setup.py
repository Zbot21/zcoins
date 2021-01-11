from setuptools import setup, find_packages

VERSION_NUMBER = '0.0.1'

setup(
  name='zcoins',
  version=VERSION_NUMBER,
  packages=find_packages(),
  url='https://github.com/Zbot21/zcoins',
  download_url='https://github.com/Zbot21/zcoins/archive/v{}.tar.gz'.format(VERSION_NUMBER),
  license='MIT',
  author='chris',
  author_email='chris@zbots.org',
  description='A generic crypto-market API.',
  install_requires=['zcoinbase',
                    'python-binance']
)
