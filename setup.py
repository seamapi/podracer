import setuptools

setuptools.setup(
  name="podracer",
  version="0.0.1",
  author="Seam",
  author_email="hello@getseam.com",
  description="Tool to run repacked containers",
  url="https://github.com/hello-seam/podracer",
  packages=setuptools.find_packages(),
  python_requires='>=3.8',
  license='AGPL-3.0-or-later',
  entry_points = {
    'console_scripts': [ 'podracer-run=podracer.run:main' ]
  }
)
