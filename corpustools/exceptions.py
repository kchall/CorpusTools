import os
import sys
import traceback
import smtplib
import platform

## Base exception classes

class PCTError(Exception):
    """
    Base class for all exceptions explicitly raised in corpustools.
    """
    pass

class PCTPythonError(PCTError):
    """
    Exception wrapper around unanticipated exceptions to better display
    them to users.

    Parameters
    ----------
    exc : Exception
        Uncaught exception to be be output in a way that the GUI can interpret
    """
    def __init__(self, exc):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        self.main = 'Something went wrong that wasn\'t handled by PCT.'

        self.information = ('If you would like to help with the development of PCT, please copy and paste the '
                            'information below and send it to PCTbugs@gmail.com. Thank you!')
        self.details = ''.join(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback))
        #self.smtp_report()

    def smtp_report(self):
        try:
            fromaddr = "pctbugs@gmail.com"
            toaddrs = ["pctbugs@gmail.com"]

            msg = "{}\n\n{}\n\n{}".format(self.details, 'PCT version', platform.platform())

            server = smtplib.SMTP('smtp.gmail.com', port=587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login('pctbugs@gmail.com', 'noexceptions')
            server.sendmail(fromaddr, toaddrs, msg)
            server.quit()
        except OSError:
            pass

## Context Manager exceptions

class PCTContextError(PCTError):
    """
    Exception class for when context managers should be used and aren't.
    """
    pass

## Corpus loading exceptions

class PCTOSError(PCTError):
    """
    Exception class for when files or directories that are expected are missing.
    Wrapper for OSError.
    """
    pass

class CorpusIntegrityError(PCTError):
    """
    Exception for when a problem arises while loading in the corpus.
    """
    pass

class DelimiterError(PCTError):
    """
    Exception for mismatch between specified delimiter and the actual text
    when loading in CSV files and transcriptions.
    """
    pass

class ILGError(PCTError):
    """
    Exception for general issues when loading interlinear gloss files.
    """
    pass

class ILGWordMismatchError(PCTError):
    """
    Exception for when interlinear gloss files have different numbers of
    words across lines that should have a one-to-one mapping.

    Parameters
    ----------
    spelling_line : list
        List of words in the spelling line
    transcription_line : list
        List of words in the transcription line
    """
    def __init__(self, mismatching_lines):
        self.main = "There doesn't appear to be equal numbers of words in one or more of the glosses."

        self.information = ''
        self.details = 'The following glosses did not have matching numbers of words:\n\n'
        for ml in mismatching_lines:
            line_inds, line = ml
            self.details += 'From lines {} to {}:\n'.format(*line_inds)
            for k,v in line.items():
                self.details += '({}, {} words) '.format(k,len(v))
                self.details += ' '.join(str(x) for x in v) + '\n'

class ILGLinesMismatchError(PCTError):
    """
    Exception for when the number of lines in a interlinear gloss file
    is not a multiple of the number of types of lines.

    Parameters
    ----------
    lines : list
        List of the lines in the interlinear gloss file
    """
    def __init__(self, lines):
        self.main = "There doesn't appear to be equal numbers of orthography and transcription lines"

        self.information = ''
        self.details = 'The following is the contents of the file after initial preprocessing:\n\n'
        for line in lines:
            if isinstance(line,tuple):
                self.details += '{}: {}\n'.format(*line)
            else:
                self.details += str(line) + '\n'

class TextGridTierError(PCTError):
    """
    Exception for when a specified tier was not found in a TextGrid.

    Parameters
    ----------
    tier_type : str
        The type of tier looked for (such as spelling or transcription)
    tier_name : str
        The name of the tier specified
    tiers : list
        List of tiers in the TextGrid that were inspected
    """
    def __init__(self, tier_type, tier_name, tiers):
        self.main = 'The {} tier name was not found'.format(tier_type)
        self.information = 'The tier name \'{}\' was not found in any tiers'.format(tier_name)
        self.details = 'The tier name looked for (ignoring case) was \'{}\'.\n'.format(tier_name)
        self.details += 'The following tiers were found:\n\n'
        for t in tiers:
            self.details += '{}\n'.format(t.name)

## Analysis function exceptions

class FreqAltError(PCTError):
    """
    Base error class for exceptions in frequency of alternation function
    calls.
    """
    pass

class FuncLoadError(PCTError):
    """
    Base error class for exceptions in frequency of alternation function
    calls.
    """
    pass

class KLError(PCTError):
    """
    Base error class for exceptions in Kullback-Leibler function
    calls.
    """
    pass

class MutualInfoError(PCTError):
    """
    Base error class for exceptions in mutual information function
    calls.
    """
    pass

class NeighDenError(PCTError):
    """
    Base error class for exceptions in neighborhood density function
    calls.
    """
    pass

class PhonoProbError(PCTError):
    """
    Base error class for exceptions in phonotactic probability function
    calls.
    """
    pass

class StringSimilarityError(PCTError):
    """
    Base error class for exceptions in string similarity function
    calls.
    """
    pass

class ProdError(PCTError):
    """
    Base error class for exceptions in predictability of distribution function
    calls.

    Parameters
    ----------
    envs : list
        Environments specified in predictability of distribution function call
    missing : dict
        Dictionary of environments not specified, but found in the
        course of the function, with a list of the words of those environments as
        values
    overlapping : dict
        Dictionary of the specified environments that are overlapping
    """
    def __init__(self, envs, missing, overlapping):

        self.segs = list(envs[0].middle)
        for j in range(len(self.segs)):
            if not isinstance(self.segs[j], str):
                self.segs[j] = ','.join(self.segs[j])
        self.segs = tuple(self.segs)
        self.envs = envs
        self.missing = missing
        self.overlapping = overlapping
        self.filename = 'pred_of_dist_{}_{}_error.txt'.format(*self.segs)
        self.information = ('Please refer to file \'{}\' in the errors directory '
                'for details or click on Show Details.').format(self.filename)
        if missing and overlapping:
            self.main = 'Exhaustivity and uniqueness were both not met for the segments {}.'.format(
                        ' and '.join(self.segs))

            self.value = ('Exhaustivity and uniqueness were both not met for the segments {}. '
                            '\n\nPlease refer to file {} in the errors directory '
                            'to view them.').format(
                        ' and '.join(self.segs),self.filename)
        elif missing:
            self.main = 'The environments specified were not exhaustive.'
            if len(missing.keys()) > 20:
                self.value = ('The environments specified were not exhaustive. '
                        'The segments {} were found in environments not specified. '
                        'The number of missing environments exceeded 20. '
                        '\n\nPlease refer to file {} in the errors directory '
                        'to view them.').format(
                        ' and '.join(self.segs),self.filename)
            else:
                self.value = ('The environments specified were not exhaustive. '
                    'The segments {} were found in environments not specified. '
                    'The following environments did not match any environments specified:\n\n{}'
                    '\n\nPlease refer to file {} in the errors directory '
                        'for details.').format(
                    ' and '.join(self.segs),
                    ' ,'.join(str(w) for w in missing.keys()),self.filename)

        elif overlapping:
            self.main = 'The environments specified were not unique.'
            if len(overlapping.keys()) > 10:
                self.value = ('The environments specified for the segments {} '
                            'were not unique. '
                            '\n\nPlease refer to file {} in the errors directory '
                            'to view them.').format(
                        ' and '.join(self.segs),self.filename)
            else:
                self.value = ('The environments specified were not unique. '
                            'The following environments for {} overlapped:\n\n'
                            ).format(' and '.join(self.segs))
                for k,v in overlapping.items():
                    self.value +='{}: {}\n'.format(
                            ' ,'.join(str(env) for env in k),
                            ' ,'.join(str(env) for env in v))
                self.value += ('\nPlease refer to file {} in the errors directory '
                        'for details.').format(self.filename)

        self.details = ''
        if self.missing:
            self.details += ('The following words have at least one of the '
                            'segments you are searching for, but it occurs in '
                            'an environment not included in the list you selected.\n\n')
            self.details += 'Segments you selected: {}, {}\n'.format(self.segs[0], self.segs[1])
            self.details += 'Environments you selected: {}\n\n'.format(' ,'.join(str(env) for env in self.envs))
            self.details += 'Word\tRelevant environments (segmental level only)\n'
            for wenv,words in self.missing.items():
                for w in words:
                    self.details += '{}\t{}\n'.format(w, wenv)
            if self.overlapping:
                self.details += '\n\n\n'
        if self.overlapping:
            self.details += ('The environments you selected are not unique, '
                    'which means that some of them pick out the same environment '
                    'in the same words.\n')
            self.details += ('For example, the environments of \'_[-voice]\' '
                    'and \'_k\', are not unique. They overlap with each '
                    'other, since /k/ is [-voice].\n')
            self.details += ('When your environments are not unique, the entropy '
                    'calculation will be inaccurate, since some environments '
                    'will be counted more than once.\n\n')
            self.details += 'Segments you selected: {}, {}\n'.format(self.segs[0], self.segs[1])
            self.details += 'Environments you selected: {}\n'.format(' ,'.join(str(env) for env in self.envs))
            self.details += 'Word\tWord environment\tOverlapping environments\n'
            for envs,v in self.overlapping.items():
                for wenv,w in v.items():
                    for word in w:
                        self.details += '{}\t{}\t{}\n'.format(
                                word,wenv,', '.join(envs))
    def __str__(self):
        return self.value

    def print_to_file(self,error_directory):
        with open(os.path.join(error_directory,self.filename),'w',encoding='utf-8-sig') as f:
            if self.missing:
                print(('The following words have at least one of the '
                            'segments you are searching for, but it occurs in '
                            'an environment not included in the list you selected.'), file=f)
                print('Segments you selected: {}, {}'.format(self.segs[0], self.segs[1]),file=f)
                print('Environments you selected: {}'.format(' ,'.join(str(env) for env in self.envs)),file=f)
                print('Word\tRelevant environments (segmental level only)',file=f)
                for wenv,words in self.missing.items():
                    lines = list()
                    for w in words:
                        print('{}\t{}'.format(w, wenv),file=f)

            if self.overlapping:
                print(('The environments you selected are not unique, '
                    'which means that some of them pick out the same environment '
                    'in the same words.'),file=f)
                print(('For example, the environments of \'_[-voice]\' '
                    'and \'_k\', are not unique. They overlap with each '
                    'other, since /k/ is [-voice].'),file=f)
                print(('When your environments are not unique, the entropy '
                    'calculation will be inaccurate, since some environments '
                    'will be counted more than once.'),file=f)
                print(('This file contains all the words where this problem '
                    'could arise.'),file=f)
                print('',file=f)
                print('Segments you selected: {}, {}'.format(self.segs[0], self.segs[1]),file=f)
                print('Environments you selected: {}'.format(' ,'.join(str(env) for env in self.envs)),file=f)
                print('Word\tWord environment\tOverlapping environments',file=f)
                for envs,v in self.overlapping.items():
                    lines = list()
                    for wenv,w in v.items():
                        print('{}\t{}\t{}'.format(
                                w,wenv,', '.join(envs)),file=f)

## Other modules' exceptions

class PCTMultiprocessingError(PCTError):
    """
    Exception for multiprocessing errors.
    """
    pass
