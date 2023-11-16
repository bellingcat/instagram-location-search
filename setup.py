import setuptools
from instagram_locations.version import __version__
with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()


setuptools.setup(
    name="instagram-location-search",
    version=__version__,
    author="Bellingcat",
    author_email="tech@bellingcat.com",
    packages=["instagram_locations"],
    description="Finds Instagram location IDs near a specified latitude and longitude.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.bellingcat.com",
    license="MIT License",
    install_requires=["requests", "numpy", "pandas", "selenium", "webdriver-manager"],
    classifiers=[
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python :: 3'
        ],
    entry_points={
        "console_scripts": [
            "instagram-location-search=instagram_locations.instagram_locations:main",
        ]
    },
)
