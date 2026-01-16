import sys

if __name__ == "__main__":
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"Environment: {sys.executable}")
    if python_version >= (3, 12) and python_version < (3, 13):
        print("✅ Python version compatible.")
    else:
        print("❌ Python version must >= 3.12 and < 3.13")
        exit()
