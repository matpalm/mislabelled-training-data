## README

see http://matpalm.com/blog/2011/10/03/mislabelled-training-data for a blog post

## RANDOM NOTES FOLLOW (YOU WERE WARNED!!!!!!!)

using mongo as underlying tweet store

 mongod --dbpath=db &
 mongo db ensure_tweet_id_indexed.js

stream a bunch of tweets into using.. (runs at about 30 tweets / sec)

 curl -u user:password https://stream.twitter.com/1/statuses/sample.json | ./load_into_mongo.py

as part of feature extraction lowercase the tweet text (sans hashtags, user mentions and urls)
and split it into character unigrams, bigrams and trigrams. 
additionally we'll swap characters for space and colon to 'S' and 'C' respectively 
so we can format for vowpal (since we don't care about the actual character meaning this is safe to do)

 ./tweets_to_vowpal.py > data.vw
 head -n 3 data.vw
 0 id_116170912956551168|unigrams 、 最 開 ろ れ ん ？ . 原 い う か が こ 何 作 た だ っ て 早 h な o 展 |bigrams う展 いう 、か って h. んだ ろう .. 早こ だろ った 展開 これ だっ 原作 かな たん う？ な？ 開、 oh 最早 ？o 何が れ何 てい 作だ が原 ？っ |trigrams だろう 何が原 これ何 h.. 展開、 ？って ていう ってい 最早こ ったん たんだ 作だっ かな？ ろう？ んだろ ... oh. う？っ いう展 な？o だった れ何が う展開 原作だ 開、か が原作 ？oh 、かな 早これ
 1 id_116170912981721089|unigrams a c b e g i h k j s o l S n u t w v z |bigrams ck el en ev zi Sz ee ah is ge lS je et ew nS ie ig ve le gS no li wo aS tj eS be we sS Sw wh kS Si So Sn Sl Sb ha Sg oo on ut oc ou |trigrams Sis jeS aha igS ckS Swe enS gSg Sle elS kSo haS out hah ock eli ewo Sno sSw wel woo zie iel Sbe ven onS tje wha isS oon eSz noc lig lev nSl gew Szi lSb nSn eet eve bee Sou etj aSi Sge
 0 id_116170912969146368|unigrams a d p u t x |bigrams aa pu ut xd ax ta |trigrams uta aaa taa axd put aax

we can now train a vowpal model using this data as a training set

 shuf data.vw | vw -f model

and then apply the model to the <em>same data</em> as a test set 

 cat data.vw | vw -t -i model -p predictions -r raw_predictions

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

we can do all this; training the model from scratch (since it involves a shuffle) x10 times giving

> summary(d$V1)
   Min. 1st Qu.  Median    Mean 3rd Qu.    Max. 
 0.8126  0.8204  0.8224  0.8221  0.8249  0.8269 
> d$V1
 [1] 0.82496 0.81260 0.82690 0.82654 0.82454 0.82354 0.82078 0.82023 0.82120 0.81990

( this x10 run is done using ./evaluate.sh 1 )

so it's not too bad...

what's more interesting that the cases were the model agreed are the cases the model <b>doesn't</b> agree

in some cases the model disagrees and is actually right

text: [천국이 RT이벤트]2011 대한민국 소비자신뢰 대표브랜드 대상수상! 알바천국이 여러분의 사랑에힘입어
user lang:  en (label 1) # hmmm, not sure this is in english :/
prediction: -0.52598 # ie model thinks it's not english
error:      1.52598

this is great! the model has correctly identified this instance is mislabelled. 

but sometimes the model disagrees and is wrong...

text: поняла …что она совсем не нужна ему.
user lang:  ru (label 0) # fair enough, looks russian to me..
prediction: 5.528163 # model strongly thinks it's english
error:      5.528163

we can in fact consider the top20 "misclassified" tweets using

 head -n100 id_mse.1 |cut -f1 |sed -es/id_// > ids
 grep -f ids tweet_lang_text.tsv

so it seems that there are enough russian tweets marked as english for it to be learnt as english :/

** this aside if we just agree with the model, mark the top 100 as the model says and reiterate say 10 times 
do the model get better?

 r1 = read.delim('eval.1/accuracy',header=F)$V1
 r2 = read.delim('eval.2/accuracy',header=F)$V1
 r3 = read.delim('eval.3/accuracy',header=F)$V1
 r4 = read.delim('eval.4/accuracy',header=F)$V1
 r5 = read.delim('eval.5/accuracy',header=F)$V1
 r6 = read.delim('eval.6/accuracy',header=F)$V1
 r7 = read.delim('eval.7/accuracy',header=F)$V1
 r8 = read.delim('eval.8/accuracy',header=F)$V1
 r9 = read.delim('eval.9/accuracy',header=F)$V1
 r10 = read.delim('eval.10/accuracy',header=F)$V1
 d = stack(list(r01=r1,r02=r2,r03=r3,r04=r4,r05=r5,r06=r6,r07=r7,r08=r8,r09=r9,r10=r10))
 ggplot(d, aes(ind,values)) + geom_boxplot() + xlab('run') + ylab('ACC')
 # acc_vs_run.png

acc_vs_run.png

> summary(r1)
   Min. 1st Qu.  Median    Mean 3rd Qu.    Max. 
 0.8186  0.8228  0.8245  0.8241  0.8255  0.8271 
> summary(r10)
   Min. 1st Qu.  Median    Mean 3rd Qu.    Max. 
 0.8239  0.8278  0.8298  0.8300  0.8323  0.8373 

so the mean has risen a little bit from 0.8245 to 0.8298 and a (non paired) t-test thinks this change is significant (p-value < 0.05)

> t.test(r1,r10)
  Welch Two Sample t-test
 data:  r1 and r10 
 t = -3.7428, df = 14.367, p-value = 0.002097
 alternative hypothesis: true difference in means is not equal to 0 
 95 percent confidence interval:
  -0.00928074 -0.00252926 
 sample estimates:
 mean of x mean of y 
  0.824054  0.829959

but it seems sensible as a first pass to set tweets with these special characters as non english regardless of the 
user lang (and while i'm at i might set another bunch of character too, such as NO )

after doing this how does the classifier do?? without having to iterate

1) reset

 bash>  mongo tweets
 mongo> db.tweets.remove() 
 bash>  zcat ../sample.2011-09-24-2.json.gz | head -n100000 | ./load_into_mongo.py

2) run once

 ./evaluate.sh 1

 r1 = read.delim('eval.1/accuracy',header=F)$V1
 > r1
  [1] 0.82711 0.82549 0.81984 0.82123 0.82482 0.82501 0.82735 0.82269 0.82255 0.82900 0.82856
 [12] 0.82118 0.82068 0.82118 0.81856 0.82696 0.82536 0.82456 0.82331 0.82363 

3) set lang

 ./tweet_lang_text.py > tweet_lang_text.tsv
 grep -f non_english_chars tweet_lang_text.tsv | cut -f1 | ./set_tweet_lang.py not_en | tee set_non_english.out

 1,500 ja set to non_en (no surprise)
 550 ru set to non_en (no surprise)
 2,500 en set to non_en !!! 

4) run again

 ./evaluate.sh 2

 r2 = read.delim('eval.2/accuracy',header=F)$V1
 > r2
  [1] 0.83374 0.83234 0.82934 0.83487 0.83331 0.83365 0.83009 0.83759 0.83513 0.83461 0.82704
 [12] 0.83668 0.83477 0.83191 0.83623 0.83529 0.83031 0.83192 0.83244 0.83302
 

 r1 = read.delim('eval.1/accuracy',header=F)$V1
 r2 = read.delim('eval.2/accuracy',header=F)$V1
 d2 = stack(list(original=r1, updated=r2))
 ggplot(d2, aes(ind,values)) + geom_boxplot() + xlab('before or after update') + ylab('ACC')
 t.test(r1,r2) 

 before_and_after_lang_set.png

 no need for a t-test to see it's better... 



