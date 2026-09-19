"""Formal-page entrypoint reserved for the post-calibration renderer."""
import argparse


def main():
    argparse.ArgumentParser().parse_known_args()
    raise RuntimeError('Formal page rendering is blocked until C1 calibration passes')


if __name__=='__main__': main()
