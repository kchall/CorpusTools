from math import log2
from collections import defaultdict
from corpustools.corpus.classes.lexicon import Inventory

#for testing purposes
import pickle

#load .corpus file
with open("lemurian.corpus", 'rb') as file:
    corpus = pickle.load(file)


def context(index, word, algorithm="all"):
    """Get the context for a given segment, specified by its index, according to one of
    the algorithms "all", "triphone", or "biphone", as discussed in Cohen Priva (2015).
    The default selection is "all".
    
    Parameters
    ----------
    index: int 
        Segment index
    word: Word 
        Word object from which the context will be obtained
    algorithm: str 
        The method used to define context, options include "all", "triphone", and "biphone"
    
    Returns
    -------
    tuple (segment, ...)
        Tuple of context segments according to the method selected    
    """
    if 0<index<len(word.transcription):
        if algorithm=="all":
            return tuple(word.transcription[0:index])
        elif algorithm=="triphone":
            if index<2:
                return tuple(word.transcription[0:index])
            else:
                return tuple(word.transcription[index-2:index])
        elif algorithm=="biphone":
            if index<1:
                return tuple(word.transcription[0:index])
            else:
                return tuple(word.transcription[index-1:index])
    elif index==0:
        return tuple()
    else:
        return tuple()


def segment_in_context_frequencies(segment, corpus_context, algorithm="all"):
    """Given a segment and algorithm for determining context (defaults to "all"), gets the
     frequencies of a segment occurring in the context
    
    Parameters
    ----------
    segment: str
    corpus_context: CorpusContext
        Context manager for a corpus
    algorithm: string
        The method used to define context, options include "all", "triphone", and "biphone"

   Returns
    ----------
    dict {tuple : int,...}
        Dictionary with tuple of context segments as key, and integer of frequency as value
    """
    contexts = defaultdict(int)
    for word in corpus_context:
        i = 0
        for seg in word.transcription:
            i += 1
            if seg == segment:
                contexts[context(i, word, algorithm)] += word.frequency
    return contexts


def context_frequencies(contexts, corpus_context):
    """Given a dictionary (or list/iterable) of contexts and a corpus, gets frequencies for the
     contexts regardless of the following segment.
    
    Parameters
    ----------
    contexts: dict (or other iterable)
        Dictionary or other iterable of tuples containing contexts
    corpus_context: CorpusContext
        Context manager for a corpus
    
    Returns
    ----------
    dict {tuple : int,...}
        Dictionary with tuple of context segments as key, and integer of frequency as value
    """
    context_frs = defaultdict(int)
    for c in contexts:
        for word in corpus_context:
            if tuple(word.transcription[0:len(c)]) == c:
                context_frs[c] += word.frequency
    return context_frs


def conditional_probability(segment_frs, context_frs):
    """
    Parameters
    ----------
    segment_frs: dict 
        with {segment : segment|context frequency,...}
    context_frs: dict 
        with {segment : context|segment frequency,...}
    
    Returns
    ----------
    dict {tuple:float,...}
        Dictionary with tuple of context segments as key, and float of conditional probability
         of the given segment occurring in that context
    """
    conditional_probs=defaultdict(float)
    for c in segment_frs:
        conditional_probs[c]= segment_frs[c]/context_frs[c]
    return conditional_probs


def get_informativity(corpus_context, segment, algorithm="all",precision=3):
    """
    
    Parameters
    ----------
    corpus_context: CorpusContext
        Context manager for a corpus
    segment: str 
        specifying the segment to get informativity of
    algorithm: 
        
    precision: int 
        to specify rounding
    
    Returns
    ----------
    dict {}
        with summary of parameters and float informativity
    """
    s_frs= segment_in_context_frequencies(segment,corpus_context,algorithm)
    c_frs= context_frequencies(s_frs, corpus_context)
    c_prs= conditional_probability(s_frs, c_frs)
    informativity=round(-(sum([(s_frs[c])*log2(c_prs[c]) for c in c_prs]))/sum([(s_frs[s]) for s in s_frs]),precision)
    summary={
        "Corpus": corpus_context.name,
        "Segment": segment,
        "Context": algorithm,
        "Precision": precision,
        "Informativity": informativity
    }
    return summary


def all_informativity(corpus_context,algorithm="all",precision=3):
    """
    :param corpus_context:
    :param algorithm: currently only "all"
    :param precision: int defaults to 3
    :return:
    """
    all_informativities = defaultdict(dict)
    for segment in corpus_context.inventory:
        all_informativities[str(segment)]=get_informativity(corpus_context,segment)
    return all_informativities



#testing
# test_word=corpus.random_word()
# i=len(test_word.transcription)-1
# print("segment:", test_word.transcription[i])
# print("all:", context(i, test_word))
# print("triphone:", context(i, test_word, algorithm="triphone"))
# print("biphone:", context(i, test_word, algorithm="biphone"))
# print(test_word.transcription)

#print(get_informativity(corpus, "p"))

ai = all_informativity(corpus)
for key in ai:
    print(key, ai[key])

