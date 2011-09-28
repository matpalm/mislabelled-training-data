#!/usr/bin/env python
import sys, pymongo

if not len(sys.argv)==2:
    raise "usage: set_tweet_lang.py <lang>"

lang = sys.argv[1]

db = pymongo.Connection("localhost", 27017).tweets.tweets

for tweet_id in sys.stdin:
    tweet = db.find({'id':long(tweet_id)}).__getitem__(0)
    print "setting from", tweet['user']['lang'], "to", lang
    if not 'original_lang' in tweet['user']:
        tweet['user']['original_lang'] = tweet['user']['lang']
    tweet['user']['lang'] = lang
    db.save(tweet)




