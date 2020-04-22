# todo steps
# 1. get list of cardnames from txt file
# 2. get card info from ygopro api https://db.ygoprodeck.com/api/v7/cardinfo.php?name=
# 3. parse info needed and add to decklist in memory
# 4. create a bitmap based on decklist
# 5. upload bitmap
# 6. create TTS json file in %USER%/Documents/my games/Table Top Simulator/Saves/Saved Objects

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import subprocess

__author__ = "Jake Riesser"
__license__ = """/*
 * ----------------------------------------------------------------------------
 * "THE BEER-WARE LICENSE" (Revision 42):
 * <Jake.Riesser@Gmail.com> wrote this file.  As long as you retain this notice you
 * can do whatever you want with this stuff. If we meet some day, and you think
 * this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp
 * ----------------------------------------------------------------------------
 */"""
__version__ = "0.0.1"
__maintainer__ = "Jake.Riesser@Gmail.com"
__email__ = "Jake.Riesser@Gmail.com"
__status__ = "Development"

parser = argparse.ArgumentParser(
    description='A console tool for generating a Tabletop Simulator (TTS) Deck from a text file')

# Positional Arguments
parser.add_argument('list',
                    help="path to the text file containing the desired decklist. Each line in the " +
                        "file must be in the form of: 'N Cardname', where 'N' is the number of copies " +
                        "of the card to include",
                    nargs='?',
                    const=0)

# Optional Arguments
# parser.add_argument("-f", "--foo",
#                     help="specify foo",
#                     action='store_true')
# parser.add_argument("-b", "--bar",
#                     help="specify bar",
#                     metavar='BAR',
#                     nargs=1)

args = parser.parse_args()


def main():
    pass

if __name__ == '__main__':
    main()