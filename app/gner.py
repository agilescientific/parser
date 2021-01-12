# coding: utf-8
from __future__ import unicode_literals
from typing import overload

from spacy.matcher import PhraseMatcher
from spacy.tokens.doc import Doc
from spacy.tokens.span import Span
from spacy.tokens.token import Token
from spacy.util import filter_spans


def process_csv(fname):
    '''
    Helper function to obtain a list of dictionaries from a csv file.
    Each record/row is converted to a dictionary.
    The values for start, end, and their uncertainties are converted
      to floats if they exist, but are otherwise left alone.

    Args:
    fname [str] -> location of the data file

    Returns:
    [list] -> list of dicts
    '''
    with open(fname, 'r') as f:
        header_line = f.readline().strip().split(',')
        raw_data = f.readlines()
        data = []
        for line in raw_data:
            row = {key: value for key, value in zip(header_line, line.strip().split(','))}

            try:
                row['start'] = float(row['start'])
            except:
                pass
            try:
                row['end'] = float(row['end'])
            except:
                pass
            try:
                row['start_uncertainty'] = float(row['start_uncertainty'])
            except:
                pass
            try:
                row['end_uncertainty'] = float(row['end_uncertainty'])
            except:
                pass
            data.append(row)

    return data



class ChronologyComponent(object):
    """Pipeline component that assigns entity labels and sets attributes
    on CHRONO tokens. These indicate that the given entity is a 
    geochronological interval of some kind.
    """
    name = 'geochronology' # component name, will show up in the pipeline

    def __init__(self, nlp, label='CHRONO'):
        """Initialise the pipeline component. The shared nlp instance is used
        to initialise the matcher with the shared vocab, get the label ID and
        generate Doc objects as phrase match patterns.
        """
        # Make request once on initialisation and store the data
        # We are reading a CSV derived from the ICS2020.ttl file.
        #chronologies = pd_read_csv('data/chrono_csv_ics2020.csv').to_dict(orient='records')
        chronologies = process_csv('data/chrono_csv_ics2020.csv')

        # We will use a dict to store the patterns of interest and attributes.
        self.chronologies = {c['name']: c for c in chronologies}
        self.label = nlp.vocab.strings[label]  # get entity label ID

        # Set up the PhraseMatcher with Doc patterns for each chrono unit name
        patterns = [nlp(c) for c in self.chronologies.keys()]
        self.matcher = PhraseMatcher(nlp.vocab)
        self.matcher.add('CHRONO', patterns)

        # Register attribute on the Token. We'll be overwriting this based on
        # the matches, so we're only setting a default value, not a getter.
        # If no default value is set, it defaults to None.
        Token.set_extension('is_chrono', default=False, force=True)
        Token.set_extension('start', default=False, force=True)
        Token.set_extension('end', default=False, force=True)
        Token.set_extension('rank', default=False, force=True)
        Token.set_extension('usage', default=False, force=True)
        Token.set_extension('part_of', default=False, force=True)
        Token.set_extension('source', default=False, force=True)
        Token.set_extension('start_uncert', default=False, force=True)
        Token.set_extension('end_uncert', default=False, force=True)

        # Register attributes on Doc and Span via a getter that checks if one of
        # the contained tokens is set to is_country == True.
        Doc.set_extension('has_chrono', getter=self.has_chrono, force=True)
        Span.set_extension('has_chrono', getter=self.has_chrono, force=True)


    def __call__(self, doc):
        """Apply the pipeline component on a Doc object and modify it if matches
        are found. Return the Doc, so it can be processed by the next component
        in the pipeline, if available.
        """
        matches = self.matcher(doc)
        spans = []  # keep the spans for later so we can merge them afterwards
        for _, start, end in matches:
            # Generate Span representing the entity & set label
            entity = Span(doc, start, end, label=self.label)
            spans.append(entity)
            # Set custom attribute on each token of the entity
            # Can be extended with other data returned by the API, like
            # currencies, country code, flag, calling code etc.
            for token in entity:
                token._.set('is_chrono', True)
                token._.set('start', self.chronologies[entity.text]['start'])
                token._.set('end', self.chronologies[entity.text]['end'])
                token._.set('rank', self.chronologies[entity.text]['rank'])
                token._.set('part_of', self.chronologies[entity.text]['part_of'])
                token._.set('source', self.chronologies[entity.text]['source'])
                #if np.isnan(self.chronologies[entity.text]['start_uncertainty']):
                if self.chronologies[entity.text]['start_uncertainty'] == '':
                    token._.set('start_uncert', None)
                else:
                    token._.set('start_uncert', self.chronologies[entity.text]['start_uncertainty'])
                #if np.isnan(self.chronologies[entity.text]['end_uncertainty']):
                if self.chronologies[entity.text]['end_uncertainty'] == '':
                    token._.set('end_uncert', None)
                else:
                    token._.set('end_uncert', self.chronologies[entity.text]['end_uncertainty'])
                
        spans = filter_spans(spans)
        # Overwrite doc.ents and add entity – be careful not to replace!
        doc.ents = list(doc.ents) + spans
        for span in spans:
            # Iterate over all spans and merge them into one token. This is done
            # after setting the entities – otherwise, it would cause mismatched
            # indices!
            span.merge()
        return doc  # don't forget to return the Doc!

    def has_chrono(self, tokens):
        """Getter for Doc and Span attributes. Returns True if one of the tokens
        is a chronology unit. Since the getter is only called when we access the
        attribute, we can refer to the Token's 'is_chrono' attribute here,
        which is already set in the processing step."""
        return any([t._.get('is_chrono') for t in tokens])
