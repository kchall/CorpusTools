import argparse
import os
import sys
import csv

# default to importing from CorpusTools repo
base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0,base)

from corpustools.corpus.io import load_binary
from corpustools.funcload.functional_load import *
from corpustools.contextmanagers import *
from corpustools.corpus.classes.lexicon import EnvironmentFilter

#### Script-specific functions

def check_bool(string):
    if string == 'False':
        return False
    else:
        return True

def main():

    #### Parse command-line arguments
    parser = argparse.ArgumentParser(description = \
             'Phonological CorpusTools: functional load CL interface')
    parser.add_argument('corpus_file_name', help='Name of corpus file')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-p', '--pairs_file_name_or_segment', help='Name of file with segment pairs (or target segment if relative_fl is True)')
    group.add_argument('-l', '--all_pairwise_fls', action='store_true', help="Calculate FL for all pairs of segments")
    parser.add_argument('-c', '--context_type', type=str, default='Canonical', help="How to deal with variable pronunciations. Options are 'Canonical', 'MostFrequent', 'SeparatedTokens', or 'Weighted'. See documentation for details.")
    parser.add_argument('-a', '--algorithm', default='minpair', help='Algorithm to use for calculating functional load: "minpair" for minimal pair count or "deltah" for change in entropy. Defaults to minpair.')
    parser.add_argument('-f', '--frequency_cutoff', type=float, default=0, help='Minimum frequency of words to consider as possible minimal pairs or contributing to lexicon entropy.')
    parser.add_argument('-r', '--relative_count', type=check_bool, default=True, help='For minimal pair FL: whether or not to divide the number of minimal pairs by the number of possible minimal pairs (words with either segment in the proper environment). Defaults to True; pass -r False to set as False.')
    parser.add_argument('-d', '--distinguish_homophones', action='store_true', help="For minimal pair FL: if False, then you'll count sock~shock (sock=clothing) and sock~shock (sock=punch) as just one minimal pair; but if True, you'll overcount alternative spellings of the same word, e.g. axel~actual and axle~actual. False is the value used by Wedel et al.")
    parser.add_argument('-t', '--type_or_token', default='token', help='For change in entropy FL: specifies whether entropy is based on type or token frequency.')
    parser.add_argument('-e', '--relative_fl', action='store_true', help="If True, calculate the relative FL of a single segment by averaging across the functional loads of it and all other segments.")
    parser.add_argument('-s', '--sequence_type', default='transcription', help="The attribute of Words to calculate FL over. Normally this will be the transcription, but it can also be the spelling or a user-specified tier.")
    parser.add_argument('-q', '--environment_lhs', default=None, help="Left hand side of environment filter. Format: positions separated by commas, groups by slashes, e.g. m/n,i matches mi or ni.")
    parser.add_argument('-w', '--environment_rhs', default=None, help="Right hand side of environment filter. Format: positions separated by commas, groups by slashes, e.g. m/n,i matches mi or ni.")
    parser.add_argument('-x', '--separate_pairs', action='store_true', help="If present, calculate FL for each pair in the pairs file separately.")
    parser.add_argument('-o', '--outfile', help='Name of output file')

    args = parser.parse_args()

    ####

    corpus = load_binary(args.corpus_file_name)
    if args.context_type == 'Canonical':
        corpus = CanonicalVariantContext(corpus, args.sequence_type, args.type_or_token, frequency_threshold=args.frequency_cutoff)
    elif args.context_type == 'MostFrequent':
        corpus = MostFrequentVariantContext(corpus, args.sequence_type, args.type_or_token, frequency_threshold=args.frequency_cutoff)
    elif args.context_type == 'SeparatedTokens':
        corpus = SeparatedTokensVariantContext(corpus, args.sequence_type, args.type_or_token, frequency_threshold=args.frequency_cutoff)
    elif args.context_type == 'Weighted':
        corpus = WeightedVariantContext(corpus, args.sequence_type, args.type_or_token, frequency_threshold=args.frequency_cutoff)

    if not args.environment_lhs and not args.environment_rhs:
        environment_filter = None
    else:
        if args.environment_lhs:
            split_lhs = [tuple(pos.split('/')) for pos in args.environment_lhs.split(',')]
        else:
            split_lhs = None
        if args.environment_rhs:
            split_rhs = [tuple(pos.split('/')) for pos in args.environment_rhs.split(',')]
        else:
            split_rhs = None
        environment_filter = EnvironmentFilter([], split_lhs, split_rhs)

    if args.all_pairwise_fls:
        result = all_pairwise_fls(corpus, relative_fl=args.relative_fl, algorithm=args.algorithm, relative_count=args.relative_count,
                     distinguish_homophones=args.distinguish_homophones, environment_filter=environment_filter)

    else:
        if args.relative_fl != True:
            try:
                with open(args.pairs_file_name_or_segment) as segpairs_or_segment_file:
                    segpairs_or_segment = [line for line in csv.reader(segpairs_or_segment_file, delimiter='\t') if len(line) > 0]
            except FileNotFoundError:
                raise FileNotFoundError("Did not find the segment pairs file even though 'relative_fl' is set to false. If calculating the relative FL of a single segement, please set 'relative_fl' to True. Otherwise, specify correct filename.")
        else:
            segpairs_or_segment = args.pairs_file_name_or_segment

        if args.algorithm == 'minpair':
            if args.relative_fl:
                result = relative_minpair_fl(corpus, segpairs_or_segment, relative_count=bool(args.relative_count), distinguish_homophones=args.distinguish_homophones, environment_filter=environment_filter)
            else:
                if args.separate_pairs:
                    result = []
                    for pair in segpairs_or_segment:
                        result.append(minpair_fl(corpus, [pair], relative_count=bool(args.relative_count), distinguish_homophones=args.distinguish_homophones, environment_filter=environment_filter))
                else:
                    result = minpair_fl(corpus, segpairs_or_segment, relative_count=bool(args.relative_count), distinguish_homophones=args.distinguish_homophones, environment_filter=environment_filter)
        elif args.algorithm == 'deltah':
            if args.relative_fl:
                result = relative_deltah_fl(corpus, segpairs_or_segment, environment_filter=environment_filter)
            else:
                if args.separate_pairs:
                    result = []
                    for pair in segpairs_or_segment:
                        result.append(deltah_fl(corpus, [pair], environment_filter=environment_filter))
                else:
                    result = deltah_fl(corpus, segpairs_or_segment, environment_filter=environment_filter)
        else:
            raise Exception('-a / --algorithm must be set to either \'minpair\' or \'deltah\'.')

    if args.outfile:
        with open(args.outfile, 'w') as outfile:
            if type(result) != list:
                outstr = 'result\t' + '\t'.join([a for a in vars(args)]) + '\n' + str(result) + '\t' + '\t'.join([str(getattr(args, a)) for a in vars(args)])
                outfile.write(outstr)
            else:
                outstr = 'result\tsegment(s)\t' + '\t'.join([a for a in vars(args)]) + '\n'
                for element in result:
                    outstr += str(element[1]) + '\t' + str(element[0]) + '\t' + '\t'.join([str(getattr(args,a)) for a in vars(args)]) + '\n'
                outfile.write(outstr)

    else:
        print('No output file name provided.')
        print('The functional load of the given inputs is {}.'.format(str(result)))


if __name__ == '__main__':
    main()
