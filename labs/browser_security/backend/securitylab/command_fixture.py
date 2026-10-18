"""Fixed child program: parse arguments and print JSON; never run another program."""
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--flag", action="store_true")
    parser.add_argument("names", nargs="*")
    arguments = parser.parse_args()
    print(json.dumps({
        "argv": sys.argv[1:],
        "names": arguments.names,
        "flag": arguments.flag,
        "marker": "ARGUMENT_FLAG_MARKER" if arguments.flag else None,
    }))


if __name__ == "__main__":
    main()
