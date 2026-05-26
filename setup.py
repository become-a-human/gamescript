from setuptools import setup, find_packages

setup(
    name="gamescript",
    version="0.1.0",
    description="GameScript — DSL для геймдева, компилируется в C++",
    author="become-a-human",
    packages=find_packages(),
    python_requires=">=3.9",
    license="WTFPL",
    entry_points={
        'console_scripts': [
            'gamescript=gamescript.compiler:compile_file',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
