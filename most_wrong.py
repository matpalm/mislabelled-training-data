#!/usr/bin/env python
import sys, pymongo, math

if not len(sys.argv)==3:
    raise "expected ACTUAL PREDICTED"
actual_file, predicted_file = sys.argv[1:]

db = pymongo.Connection("localhost", 27018).tweets.tweets

actual_f    = open(actual_file, 'r')
predicted_f = open(predicted_file, 'r')

for actual_row in actual_f:

    # extract data from files
    actual, actual_id = actual_row.split()
    predicted, predicted_id = predicted_f.readline().split()
    actual = float(actual)
    predicted = float(predicted)
    # minor sanity check
    if actual_id != predicted_id:
        print "ERROR!"

    # clip to 0,1 for testing correctness of prediction
    clipped_prediction = None
    if predicted > 1.0:
        clipped_prediction = 1.0
    elif predicted < 0.0:
        clipped_prediction = 0.0
    else:
        clipped_prediction = predicted

    # dump tweet (and some info) if prediction was very wrong 
    if actual != clipped_prediction:
        error = math.fabs(predicted - actual)
        if error > 0.8:
            tweet_id = long(actual_id.replace('id_',''))
            tweet = db.find({'id':long(tweet_id)}).__getitem__(0)
            print tweet_id, error, actual, predicted, tweet['text'].encode('utf-8')
