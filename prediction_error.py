#!/usr/bin/env python
import sys, math
#import pymongo

if not len(sys.argv)==3:
    raise "expected ACTUAL PREDICTED"
actual_file, predicted_file = sys.argv[1:]

#db = pymongo.Connection("localhost", 27017).tweets.tweets

actual_f    = open(actual_file, 'r')
predicted_f = open(predicted_file, 'r')

for actual_row in actual_f:

    # extract data from files
    actual_label, actual_id = actual_row.split()
    raw_predicted_label, predicted_id = predicted_f.readline().split()
    actual_label = float(actual_label)
    raw_predicted_label = float(raw_predicted_label)

    # minor sanity check
    if actual_id != predicted_id:
        raise "ERROR!"

    # clip to 0,1 for testing correctness of prediction
    predicted_label = 0.0
    if raw_predicted_label > 0.5:
        predicted_label = 1.0

    # dump difference in prediction and actual if it's in error
    if actual_label != predicted_label:
        error = math.fabs(raw_predicted_label - actual_label)
        #    if error > 1:
        print "%s\t%.6f" % (actual_id, error)
