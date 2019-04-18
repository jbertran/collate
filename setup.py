from setuptools import setup

setup(
    name='Collate',
    version='0.1',
    description='Minimalist file collation utility leveraging the CLI',
    author='jbertran',
    author_email='j.debalanda@gmail.com',
    url='https://github.com/jbertran/collate',
    packages=['collate'],
    entry_points={
        'console_scripts': ['collate=collate.collate:parse_cli']
    }
)
