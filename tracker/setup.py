from setuptools  import setup, find_packages

setup(name='tormenta-tracker',
      version='0.1',
      packages=find_packages(),
      author='Jorge Niedbalski R. <jnr@pyrosome.org>',
      include_package_data=True,
      namespace_package=['tormenta'],
      license='BSD')
