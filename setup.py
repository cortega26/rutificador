""" Archivo informativo y de configuración de la librería chile_rut."""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="chile_rut",
    version="1.0.0",
    author="Carlos Ortega González",
    author_email="carlosortega77@gmail.com",
    description="Librería para validar y formatear el RUT utilizado en Chile.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="por definir aun",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
