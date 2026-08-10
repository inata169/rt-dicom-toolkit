"""
RT DICOM Toolkit インストーラ設定
"""

from setuptools import setup, find_packages

setup(
    name="rt_dicom_toolkit",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pydicom>=2.4.4,<3.1",
        "numpy>=1.26.4,<3",
        "matplotlib>=3.10.3,<4",
        "pandas>=2.3.1,<3",
        "customtkinter>=5.2.2,<6",
    ],
    entry_points={
        'console_scripts': [
            'rt-anonymizer=rt_dicom_toolkit.cli:run_anonymizer_cli',
            'rt-validator=rt_dicom_toolkit.cli:run_validator_cli',
        ],
        'gui_scripts': [
            'rt-anonymizer-gui=rt_dicom_toolkit.gui.anonymizer_gui:run_anonymizer_gui',
            'rt-validator-gui=rt_dicom_toolkit.gui.validator_gui:run_validator_gui',
        ],
    },
    author="Medical Physics Team",
    author_email="example@example.com",
    description="放射線治療用DICOM匿名化・検証ツールキット",
    keywords="dicom, anonymization, radiation therapy, medical physics",
    python_requires=">=3.10",
)
