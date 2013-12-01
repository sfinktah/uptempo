#!/opt/local/bin/python2.7
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("echo", help="thing to echo")
args = parser.parse_args()
print args.echo
