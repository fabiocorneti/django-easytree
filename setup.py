from setuptools import setup, find_packages
import os

version = '0.4.3'

setup(name='django-easytree',
      version=version,
      description="Another attempt at modified preordered tree traversal for Django.",
      long_description="", 
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='python django tree mptt',
      author='Oyvind Saltvik',
      author_email='oyvind.saltvik@gmail.com',
      url='http://bitbucket.org/fivethreeo/django-easytree',
      license='',
      packages=find_packages(exclude=['ez_setup','easytree_example']),
      namespace_packages=[],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
