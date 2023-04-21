#!/usr/bin/env python3

import sys
import os
import argparse
import glob
import egglib
import pandas as pd

print("the version of egglib is: " + str(egglib.__version__))

# This script reads in a fasta alignment or a directory of alignments and calculates piN and piS. 
# Alignments must be in frame coding sequence. 
# This script requires egglib installed with the Bio++ libraries.
# Edited by MAT 3/7/2023


class FullPaths(argparse.Action):
    """Expand user- and relative-paths"""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest,
            os.path.abspath(os.path.expanduser(values)))

def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]

def is_dir(dirname):
    """Checks if a path is a directory"""
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname

def is_file(filename):
    """Checks if a file exists"""
    if not os.path.isfile(filename):
        msg = "{0} is not a file".format(filename)
        raise argparse.ArgumentTypeError(msg)
    else:
        return filename

def get_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Calculate diversity and selection statistic")
    input_files = parser.add_mutually_exclusive_group(required=True)
    input_files.add_argument('-a', '--alignment', help = 'Alignment to calculate statistics',
        type=is_file)
    input_files.add_argument('-d', '--directory', help = 'Directory of alignments',
        type=is_dir)
    return parser.parse_args()


def calc_stats(alignment):
    statDict = {}
    cs = egglib.stats.ComputeStats(multi_hits=True)
    cs.add_stats('Pi','lseff', 'nseff')
    a = egglib.io.from_fasta(alignment,egglib.alphabets.DNA)
    a_codons = egglib.tools.to_codons(a)
    a_div = egglib.stats.CodingDiversity(a_codons, multiple_alleles=True, multiple_hits=True, max_missing= .2)
    statsall = cs.process_align(a, max_missing= .2)
    statsS = cs.process_sites(a_div.sites_S)
    statsNS = cs.process_sites(a_div.sites_NS)

    try:
        statDict['pi'] = float(statsall['Pi'])/statsall['lseff']
        statDict['nseff'] = statsall['nseff']
    ##sometimes Pi = None because there isn't enough information because the alignment or codon alignment didn't pass the max_missing threshhold.
    ##This is when a gene has really bad alignment. Stats aren't able to be calculated, so we just get "None."
    except TypeError:
        statDict['nseff'] = statsall['nseff']
        statDict['pi'] = None
    try:
        statDict['piN'] = float(statsNS['Pi'])/a_div.num_sites_NS
    ##Here, if pi is 0, piN = 0 (because piN is calculated as pi/#N_sites). But if pi is nonne, piN = None.
    except TypeError:
        statDict['piN'] = 0
    try:
        statDict['piS'] = float(statsS['Pi'])/a_div.num_sites_S
    except TypeError:
        statDict['piS'] = 0
    ##making sure that 0/0 = 0 and 0/1= 0 and 0/None = None, in terms of piNpiS.
    try: 
        statDict['piNpiS'] = statDict['piN']/statDict['piS']
    except ZeroDivisionError:
        if statDict['piN'] == 0:
            statDict['piNpiS'] = 0
        else:
            statDict['piNpiS'] = None
    return statDict

def write_outfile(alignDict):
    outfile = open('selectionStats_piNpiS.txt', 'w')
    outfile.write('Alignment\tPi\tPiN\tPiS\tPiNPiS\tnseff\n')
    for key,value in alignDict.items():
        outfile.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (key, value['pi'],value['piN'],\
                value['piS'],value['piNpiS'],value['nseff']))
    outfile.close()

args = get_arguments()

alignDict = {}

# Check if alignment or directory was given and calculate stats accordingly
if args.alignment is None:
    for align in glob.glob(args.directory + '*.fasta'):
        alignName = os.path.splitext(align)[0].replace(args.directory, "")
        alignDict[alignName] = calc_stats(align)
else:
    alignName = os.path.splitext(args.alignment)[0]
    alignDict[alignName] = calc_stats(args.alignment)

write_outfile(alignDict)


##Add here the averaging script that will be important

