import setuptools

setuptools.setup(
  name="podracer",
  version="0.9.0",
  author="Seam",
  author_email="hello@getseam.com",
  description="Tool to run repacked containers",
  url="https://github.com/hello-seam/podracer",
  packages=['podracer'],
  python_requires='>=3.8',
  license='AGPL-3.0-or-later',
  entry_points = {
    'console_scripts': [
      'podracer-export=podracer.export:main',
      'podracer-manifests=podracer.manifests:main',
      'podracer-run=podracer.run:main',
      'podracer-repack=podracer.repack:main',
    ]
  }
)
