#!/usr/bin/env python
import sys, pymongo, math

if not len(sys.argv)==3:
    raise "expected ACTUAL PREDICTED"
actual_file, predicted_file = sys.argv[1:]

db = pymongo.Connection("localhost", 27017).tweets.tweets

actual_f    = open(actual_file, 'r')
predicted_f = open(predicted_file, 'r')

for actual_row in actual_f:

    # extract data from files
    actual, actual_id = actual_row.split()
    raw_predicted, predicted_id = predicted_f.readline().split()
    actual = float(actual)
    raw_predicted = float(raw_predicted)
    # minor sanity check
    if actual_id != predicted_id:
        print "ERROR!"

    # clip to 0,1 for testing correctness of prediction
    predicted = 0.0
    if raw_predicted > 0.5:
        predicted = 1.0

    # dump tweet (and some info) if prediction was very wrong 
    if actual != predicted:
        error = math.fabs(raw_predicted - actual)
        if error > 1:
            tweet_id = long(actual_id.replace('id_',''))
            tweet = db.find({'id':long(tweet_id)}).__getitem__(0)
            user_lang = tweet['user']['lang']
            screen_name = tweet['user']['screen_name']
            encoded_tweet_text = tweet['text'].replace("\n",' ').encode('utf-8')
            print "\t".join([str(f) for f in [tweet_id, error, raw_predicted, actual, user_lang, screen_name, encoded_tweet_text]])
