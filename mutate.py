#! /usr/bin/env python


import argparse
import logging
import os
import random
import subprocess
import sys


def main():
  parser = argparse.ArgumentParser(description='Dumb mutation fuzzer')
  parser.add_argument('--num-iterations', type=int,
      default=1000, metavar='NUM',
      help=('Specify the number of files to generate'
            'Default: %(default)s'))
  parser.add_argument('--append-every', type=int,
      default=100, metavar='NUM',
      help=('Specify how often to append random data. '
            'Default: %(default)s'))
  parser.add_argument('--append-length', type=int,
      default=10, metavar='NUM',
      help=('Specify how many bytes of random data to append. '
            'Default: %(default)s'))
  parser.add_argument('--seed', type=int, metavar='NUM',
      help='Specify the random number seed')
  parser.add_argument('--flip-probability', type=float,
      default=0.20, metavar='FLOAT',
      help=('Specify the probability to flip a given byte '
            'Default: %(default)s'))

  parser.add_argument('template',
      help='Specify the file to use as a template for mutations.')
  parser.add_argument('program',
      help=('Specify the program to run. Program should be a format string '
            'where {} is replaced with the input file'))

  args = parser.parse_args()

  # Check to make sure flip probability is between 0 and 1
  if args.flip_probability <= 0 or args.flip_probability >= 1:
    logging.critical('Flip probability should be between 0 and 1')
    sys.exit(1)

  # Set the random seed according to argument
  if args.seed is not None:
    random.seed(args.seed)

  # Read the template file
  template = None
  with open(args.template, 'rb') as fin:
    template = bytearray(fin.read())

  # Directory where interesting mutations will be saved
  if os.path.exists('interesting'):
    logging.critical('Old interesting directory still exists')
    sys.exit(1)

  os.mkdir('interesting')

  # Figure out what the extension of the original file is
  ext = os.path.splitext(args.template)[1]

  # Start generating mutations
  for i in xrange(args.num_iterations):
    fname = 'mutation-{:04d}{}'.format(i, ext)

    # Append new bytes to template
    if i % args.append_every == 0:
      template += bytearray([
        random.getrandbits(8) for _ in xrange(args.append_length)
      ])

    # Write out mutated template
    with open(fname, 'wb') as out:
      for byte in template:
        if random.random() <= args.flip_probability:
          out.write(chr(random.getrandbits(8)))
        else:
          out.write(chr(byte))

    # Run the program, look for core dumps
    retval = subprocess.call(args.program.format(fname), shell=True)

    # Log if the program did not exit cleanly
    if retval != 0:
      logging.debug('Got non-zero exit code for mutation #%d', i)

    # Check for core dump
    if os.path.exists('core'):
      logging.info('Caused program to core dump on mutation #%d', i)
      os.rename(fname, 'interesting/' + fname)
      os.rename('core', 'interesting/core-{:4d}')
    else:
      os.remove(fname)


if __name__ == '__main__':
  main()
