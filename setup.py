from setuptools import setup, find_packages

setup(
    name='mosaic',
    version='0.1.0',
    author='Garrett Mathesen',
    author_email='mathesen@u.northwestern.edu',
    description='Moving Object Segmentation under Adverse Imaging Conditions',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'scikit-image',
        'scipy'
    ]
)