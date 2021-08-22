import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md")) as f:
    README = f.read()
with open(os.path.join(here, "CHANGELOG.rst")) as f:
    CHANGES = f.read()

requires = [
    "elasticsearch",
    "coverage",
    "pytest",
    "pytest-cov",
    "black",
    "requests",
]

packages = ["elasticfeeds"]

tests_require = ["pytest", "pytest-cov"]

setup(
    name="elasticfeeds",
    version="1.0.0",
    description="ElasticFeeds",
    long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author="Carlos Quiros",
    author_email="cquiros@qlands.com",
    url="",
    keywords="Elasticsearch Feeds",
    packages=packages,
    include_package_data=True,
    package_data={"": ["README.md", "LICENSE.txt"]},
    package_dir={"elasticfeeds": "elasticfeeds"},
    zip_safe=False,
    extras_require={"testing": tests_require},
    install_requires=requires,
)
