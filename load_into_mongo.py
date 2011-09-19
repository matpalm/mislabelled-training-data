#!/usr/bin/env python
import sys, pymongo, json
db = pymongo.Connection("localhost", 27017).tweets.tweets
for line in sys.stdin:
    tweet = json.loads(line.strip())
    if not 'delete' in tweet:
        db.save(tweet)
