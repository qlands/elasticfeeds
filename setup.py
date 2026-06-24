import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md")) as f:
    README = f.read()
with open(os.path.join(here, "CHANGELOG.rst")) as f:
    CHANGES = f.read()

# Runtime dependencies only. Test/dev tools live in extras_require below so that
# library consumers are not forced to install them.
requires = [
    "elasticsearch>=9.2,<10",
]

tests_require = ["pytest", "pytest-cov", "coverage", "requests"]

setup(
    name="elasticfeeds",
    version="1.2.0",
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
    packages=find_packages(),
    include_package_data=True,
    package_data={"": ["README.md", "LICENSE.txt"]},
    package_dir={"elasticfeeds": "elasticfeeds"},
    zip_safe=False,
    extras_require={
        "testing": tests_require,
        "opensearch": ["opensearch-py>=2,<4"],
        "dev": ["black"],
    },
    install_requires=requires,
)
