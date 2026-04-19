from setuptools import setup, find_packages

setup(
    name="polymarket-btc-bot",
    version="1.0.0",
    description="Polymarket BTC Up/Down 5-Minute Automation Bot",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "py-clob-client>=0.24.0",
        "yfinance>=0.2.28",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "colorama>=0.4.6",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "polymarket-bot=src.bot:main",
        ],
    },
)
