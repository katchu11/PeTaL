from pprint import pprint
from subprocess import call
from time import time

import requests, zipfile, os

from .module import Module

'''
This is the backbone mining module for population neo4j with the initial species list
'''

# TODO: setup auto downloads from here by scraping most recent date?
col_date = '2019-05-01' # Make sure this is a valid COL release

def create_dir():
    if not os.path.isfile('.col_data/taxa.txt'):
        try:
            data = requests.get('http://www.catalogueoflife.org/DCA_Export/zip-fixed/{}-archive-complete.zip'.format(col_date))
            with open('col.zip', 'wb') as outfile:
                outfile.write(data.content)
            with zipfile.ZipFile('col.zip', 'r') as zip_handle:
                zip_handle.extractall('.col_data')
        except:
            if os.path.isfile('col.zip'):
                os.remove('col.zip')
            shutil.rmtree('.col_data')

class BackboneModule(Module):
    '''
    This module populates neo4j with Species nodes, allowing WikipediaModule and others to process them.
    Notice how BackboneModule's in_label is None, which specifies that it is independent of other neo4j nodes
    '''
    def __init__(self, in_label=None, out_label='Species', connect_label=None, name='COL', count=2700000):
        Module.__init__(self, in_label, out_label, connect_label, name, count)

    def process(self):
        '''
        All that this function does is yield Transaction() objects which create Species() nodes in the neo4j database.
        This particular process() function is simply downloading a tab-separated file and parsing it.
        '''
        create_dir() # Call the code above to download COL data if it isn't already present
        start = time()
        i = 0
        with open('.col_data/taxa.txt', 'r', encoding='utf-8') as infile:
            headers = None
            json    = dict()
            # Parse lines of the downloaded file, and add it as a default_transaction() (see yield statement)
            for line in infile:
                if i == 0:
                    headers = line.split('\t')
                    headers = ('id',) + tuple(headers[1:])
                else:
                    for k, v in zip(headers, line.split('\t')):
                        json[k] = v
                    try:
                        json.pop('isExtinct\n')
                    except KeyError:
                        pass
                    if json['taxonRank'] == 'species':
                        json['name'] = json['scientificName'].replace(json['scientificNameAuthorship'], '').strip()
                        yield self.default_transaction(json) # HERE is where the transaction is created!!
                    json = dict()
                # Display efficiency data!
                # total = i
                # duration = time() - start
                # species_per_sec = total / duration
                # total_seconds  = 1.9e6 / species_per_sec
                # eta_seconds = total_seconds - duration
                # eta = eta_seconds / 3600
                # percent = duration / total_seconds * 100.0
                # # print('Species: {}, Rate: {} species per second, ETA: {}h, Percent: {}\r'.format(total, round(species_per_sec, 1), round(eta, 1), round(percent, 5)), flush=True, end='')
                i += 1
