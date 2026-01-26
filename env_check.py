import subprocess
import sys




def check_docker():
    




def check_uv():
    result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=5)
    print(result)


if __name__ == "__main__":
    check_uv()

    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"Environment: {sys.executable}")
    if python_version >= (3, 12) and python_version < (3, 13):
        print("✅ Python version compatible.")
    else:
        print("❌ Python version must >= 3.12 and < 3.13")
        exit()
