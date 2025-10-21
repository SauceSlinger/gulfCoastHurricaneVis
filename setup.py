from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gulf-coast-hurricane-vis",
    version="2.0.0",
    author="SauceSlinger",
    author_email="",
    description="A comprehensive native GUI application for visualizing Gulf Coast hurricane data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SauceSlinger/gulfCoastHurricaneVis",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-timeout>=2.1.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hurricane-dashboard=launch_tabbed:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["storms.csv", "database/*.sql"],
    },
    keywords=[
        "hurricane", 
        "visualization", 
        "dashboard", 
        "matplotlib", 
        "customtkinter",
        "weather",
        "gulf-coast",
        "storm-tracking"
    ],
    project_urls={
        "Bug Reports": "https://github.com/SauceSlinger/gulfCoastHurricaneVis/issues",
        "Source": "https://github.com/SauceSlinger/gulfCoastHurricaneVis",
        "Documentation": "https://github.com/SauceSlinger/gulfCoastHurricaneVis/tree/main/docs",
    },
)