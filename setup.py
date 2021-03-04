import pathlib

from setuptools import find_packages
from setuptools import setup

readme_path = pathlib.Path("./README.md")
requirements_path = pathlib.Path("./requirements.txt")

setup_args = dict(
    name="release_helpers",
    description="Release helpers for Python and/or npm packages.",
    long_description=readme_path.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    version="0.1.0",
    packages=find_packages("."),
    include_package_data=True,
    author="Jupyter Development Team",
    author_email="jupyter@googlegroups.com",
    url="http://jupyter.org",
    license="BSD",
    platforms="Linux, Mac OS X, Windows",
    keywords=["ipython", "jupyter"],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=requirements_path.read_text(encoding="utf-8").splitlines(),
    extras_require={"test": ["coverage", "pytest", "pytest-cov"]},
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "release-helpers = release_helpers.__main__:main",
        ]
    },
)

if __name__ == "__main__":
    setup(**setup_args)
