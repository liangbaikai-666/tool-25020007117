import argparse
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    a = p.parse_args()
    if a.name.isspace():
        sys.exit(2)
    print(f"Hello, {a.name}!")
