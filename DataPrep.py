from pymongo import MongoClient
import gzip
import json
import base64
import zlib
import time
import pandas as pd
import numpy as np

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Open up the isbn to book_id database
with open('bookID_to_ISBN.json') as json_file:
    bookID_to_ISBN = json.load(json_file)

# Count for current document
count = 0

# File where reviews and their text is held
file_name = '/Users/calummcmeekin/Downloads/goodreads_reviews_dedup.json.gz'

# Connect to Mongo client
client = MongoClient("mongodb+srv://cluster0.pdjrf.mongodb.net/Reviews_Data",
    username='CalumMcM',
    password=<Buy Me Dinner First Then Ill Git Push My Password>)

db = client.Reviews_Data

# Open the reviews.json and begin parsing it uploading
# 100,000 reviews at a tTIME
with gzip.open(file_name) as fin:

    start_time = time.time()

    array_json = []

    for l in fin:

        # Insert 100,000 records to the database 'review_data'
        if (count % 100000 == 0 and count > 0):

            print (bcolors.OKBLUE + "\n\nUPLOADING DOCUMENTS: {} THROUGH {}...".format(count-100000, count) + bcolors.ENDC)
            result=db.review_data.insert_many(array_json)
            print (bcolors.OKGREEN + "COMPLETE\n\n" + bcolors.ENDC)

            array_json = []

        if (count > 16000000):
            break

        d = json.loads(l)

        doc_json = {}

        # Extract book_id
        doc_json['book_id'] = d['book_id']

        # Get the isbn number corresponding to the book_id
        doc_json['isbn'] = bookID_to_ISBN[d['book_id']]

        # Do not upload document if it does not
        # have a corresponding ISBN number
        if (doc_json['isbn'] != ''):
            array_json.append(doc_json)

            # Extract and Compress the review text
            compress_review_text = zlib.compress(bytes(d['review_text'], 'utf-8'))

            doc_json['review_text'] = compress_review_text

            # Decompress the compressed code
            #decompress = zlib.decompress(temp_json['review_text']))

        # Update progress of current record
        if (count % 10000 == 0):
            lapsed_time = time.time() - start_time
            print ("PROGRESS: {:.2f} % \tTIME: {:.2f}".format((count/15739966)*100, lapsed_time)) #15739966

        count += 1
