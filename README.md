# an exercise in handling mislabelled training data

## intro

as part of my <a>diy twitter client project</a> 
i've been trying to use the twitter sample stream as a source
of unlabelled data for some bigram analysis.

now the twitter <a>sample streams</a> 
are a great source of a large number of random tweets but include tweets in other languages.

in the perfect world a tweet['user']['lang'] would be 100% representative of the language a tweet
is in and for the majority of cases it's correct but there are lots of times it's not. i guess it
doesn't have to be either; the native language of a user has nothing to do with the language they
choose to tweet in. can we use this value as a starting point at least?

character bigram / trigram models are a tried and true way of doing language identification but
i've never had the chance to play with them.... until now! 

one approach is then to 
# build a classifier with the collected tweets assuming the 'lang' field is correct
# have the classifier reclassify the same data and see which ones stand out

we can "correct" the label for the cases the classifier correctly identifies as being wrong and
iterate.

## method

first we need some tweets. we'll load this into <a>mongodb</a> because it fits with 
the code i've been using for the diy twitter client but all this could easiest be done without it.

 mongod --dbpath=db &
 mongo ensure_tweet_id_indexed.js

(
 mongo tweets
 db.tweets.ensureIndex({id:1})
)

we then stream a bunch of tweets into the db. leave this running until bored. (it's about 30 tweets / sec )

 curl -u user:password https://stream.twitter.com/1/statuses/sample.json | ./load_into_mongo.py

for this exp we have 100,000 tweets

convert the tweets into a form that can be loaded into <a>vowpal wabbit</a>, an easy to use fast
logistic regression implementation. we'll lowercase the tweet text (sans hashtags, user mentions and urls)
and split it into character unigrams, bigrams and trigrams. 
additionally we'll swap characters for space and colon to 'S' and 'C' respectively 
so we can format for vowpal (since we don't care about the actual character meaning this is safe to do)

 ./tweets_to_vowpal.py > data.vw
 head -n 3 data.vw
 0 id_116170912956551168|unigrams 、 最 開 ろ れ ん ？ . 原 い う か が こ 何 作 た だ っ て 早 h な o 展 |bigrams う展 いう 、か って h. んだ ろう .. 早こ だろ った 展開 これ だっ 原作 かな たん う？ な？ 開、 oh 最早 ？o 何が れ何 てい 作だ が原 ？っ |trigrams だろう 何が原 これ何 h.. 展開、 ？って ていう ってい 最早こ ったん たんだ 作だっ かな？ ろう？ んだろ ... oh. う？っ いう展 な？o だった れ何が う展開 原作だ 開、か が原作 ？oh 、かな 早これ
 1 id_116170912981721089|unigrams a c b e g i h k j s o l S n u t w v z |bigrams ck el en ev zi Sz ee ah is ge lS je et ew nS ie ig ve le gS no li wo aS tj eS be we sS Sw wh kS Si So Sn Sl Sb ha Sg oo on ut oc ou |trigrams Sis jeS aha igS ckS Swe enS gSg Sle elS kSo haS out hah ock eli ewo Sno sSw wel woo zie iel Sbe ven onS tje wha isS oon eSz noc lig lev nSl gew Szi lSb nSn eet eve bee Sou etj aSi Sge
 0 id_116170912969146368|unigrams a d p u t x |bigrams aa pu ut xd ax ta |trigrams uta aaa taa axd put aax

we can now train a vowpal model using this data as a training set

 mkdir wip; cd wip
 ln -s ../data.vw
  shuf data.vw | vw -f model

and then apply the model to the <em>same data</em> as a test set 

 cat data.vw | vw -t -i model -p predictions -r raw_predictions

of course using testing a model against the same data it was trained against is in general a big no
no but let's see what we can get from it.

the predictions from vowpal wabbit by default are a value between 0 (predicting the negative case) and 1 (predicting
the positive case) but we can also get access to the a raw prediction value that isn't clipped. this is useful
because it's magnitude in some way describes the model's confidence in the decision.

some examples where the model agrees include 

text: watching a episode of law & order this sad awww
marked as english? 1.0 # yes
raw prediction     0.998317 # model _just_ agrees it's english

text: こけむしは『高杉晋助、沖田総悟、永倉新八、神威、白石蔵ノ介』に誘われています。誰を選ぶ？
marked as english? 0.0 # marked as ja
raw prediction     -1.06215 # model agrees, _definitely_ not english

just out of interest we can check the "accuracy" of this model using <a>perf</a>. given the hack we're doing of testing
against the training data it's not really an accuracy, more of an "agreement" with the original data.
 cat data.vw | cut -d' ' -f1 > labels.actual
 cat predictions | cut -d' ' -f1 > labels.predicted
 perf -ACC -files labels.{actual,predicted} -t 0.5 | awk '{print $2}'

training the model from scratch (since it involves a shuffle) x10 times gives

> summary(d$V1)
   Min. 1st Qu.  Median    Mean 3rd Qu.    Max. 
 0.8126  0.8204  0.8224  0.8221  0.8249  0.8269 
> d$V1
 [1] 0.82496 0.81260 0.82690 0.82654 0.82454 0.82354 0.82078 0.82023 0.82120 0.81990

so it's pretty good.

what's more interesting is the cases the model doesn't agree with the label but is actually right

text: [천국이 RT이벤트]2011 대한민국 소비자신뢰 대표브랜드 대상수상! 알바천국이 여러분의 사랑에힘입어
marked as english? 1.0 # yes (hmmm)
prediction:        -0.52598 # ie model disagrees it's english
error:             1.52598

this is great! the model has correctly identified this instance is mislabelled. in fact the top 200+ are
cases like this, a tweet marked as 'en' that isn't.

looks pretty clean; ranked the tweets the model disagrees with and we see the top 500 don't even include a single 
latin character but are all marked 'en'

* GRAPH of magnitude of error *
sh
 cut -f2,5 disagreements.out > d
R
 d = read.delim('d',header=F)
 names(d) <- c('d','lang')
 d$index = 1:nrow(d)

some examples include...
prediction tweet
-6.823713 メモ☞芸能人目撃談、関西の高校生にもっさん赤っ恥w、藤原家おまごちゃんパワー♡、、、もう思い出せん(^_^
-5.375258 "やはり東電は破綻させて一時国有化し、現行の経営陣を入れ替えた上で、すべての情報を強制的に開示
-4.571936 พักนี้หลังจากอัลบั้มใหม่ของเจย์-ซี+คานเยเวสต์ ก็ฟังแต่เพลงโซลแฮะ

( recall a prediction < 0.5 denotes not english & > 0.5 denotes english so in these cases the model
 _strongly_ disagrees with these being english )

so at this stage the model is good enough to use.

but, since i seem to agree with it for the top cases it disagrees, can we strengthen it by relabelling these tweets based on
it's predictions and rerunning?

 cd wip
 cat data.vw | cut -d' ' -f1-2 | sed -es/\|.*// > labels_with_ids.actual
 ../prediction_error.py labels_with_ids.actual raw_predictions | sort -k2 -nr > disagreements.out
 cd ..
 head -n100 disagreements.out | cut -f1 | ./flip_tweet_lang.py

rerunning perf we get 
0.885 0.719 0.885

so not a huge difference...
and the disagreement of the model is less and less..
* another graph of magnitude of error *

iterate
 - x5 evalulate
 - graph of magnitude of top 100 disagreements
 - top100 'en' cases set to non_en; or limit to just maybe 'en' cases where disagreement > 2?
 - start again


 
caught in the traffic. coding would be easier. if bus didnt bounce. #haiku

