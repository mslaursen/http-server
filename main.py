import argparse


parser = argparse.ArgumentParser(description="test")

parser.add_argument("-d", "--directory", help="Help directory")

args = parser.parse_args()


print(args.directory)
