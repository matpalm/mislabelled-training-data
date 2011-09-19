#!/usr/bin/env python                                                                                                                          
import pymongo

db = pymongo.Connection("localhost", 27018).tweets

for tweet in db.tweets.find():#.limit(10)#({'id':12294922859})
    text = tweet['text'].lower()
    
    # remove user_mentions                                                                                                                    
    for user_mention in tweet['entities']['user_mentions']:
        screen_name = user_mention['screen_name'].lower() # screen names potential given in caps even if tweet not in caps
        text = text.replace("@"+screen_name, '')    

    # remove hashtags
    for hashtag in tweet['entities']['hashtags']:
        hashtag_text = hashtag['text'].lower()
        text = text.replace("#"+hashtag_text, '')

    # remove urls
    for url in tweet['entities']['urls']:
        url_text = url['url'].lower() 
        text = text.replace(url_text, '')

    text = text.replace("\n",' ').replace(' ','S').replace(':','C')

    bigrams = set()
    for i in range(0,len(text)-1):
        bigrams.add(text[i:i+2])

    trigrams = set()
    for i in range(0,len(text)-2):
        trigrams.add(text[i:i+3])

    # build up vowpal example
    eg = ""

    if tweet['user']['lang']=='en':
        eg += '1'
    else:
        eg += '0'
      
    eg += ' id_' + str(tweet['id'])  
    eg += '|bigrams ' + ' '.join(bigrams)
    eg += ' |trigrams ' + ' '.join(trigrams)

    print eg.encode('utf-8')





