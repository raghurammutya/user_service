from setuptools import setup, find_packages

setup(
    name="shared_architecture",  # Replace with your package name
    version="0.1.0",  # Increment version appropriately
    description="A shared library for backend services, including models, utilities, and configurations",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Raghuram Mutya",
    author_email="raghu.mutya@gmail.com",
    url="https://pypi.org/project/shared-models-stocksblitz/",  # Replace with your repository URL
    packages=find_packages(exclude=["tests", "examples"]),  # Dynamically discover submodules
    install_requires=[
        "SQLAlchemy>=1.4",
        "psycopg2>=2.9",
        "redis>=4.0",
        "pika>=1.3",
        "requests>=2.25",
        "pytest>=7.0",
        "pydantic>=1.10",
        "circuitbreaker>=1.3",
        "zoneinfo>=0.2.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    include_package_data=True
)