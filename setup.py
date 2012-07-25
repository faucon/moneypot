import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'sqlalchemy',
    'zope.sqlalchemy',
    'fa.bootstrap',
    'pyramid_mailer',
    'zope.testbrowser',
    'webtest',
    'beautifulsoup4',
    ]

test_requires = [
        'zope.testbrowser',
        'webtest'
        ]

if sys.version_info[:3] < (2, 5, 0):
    requires.append('pysqlite')

setup(name='moneypot',
      version='0.0',
      description='moneypot',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      test_suite="moneypot",
      entry_points="""\
      [paste.app_factory]
      main = moneypot:main
      """,
      paster_plugins=['pyramid'],
      )
