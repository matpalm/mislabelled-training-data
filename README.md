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
 mongo db ensure_tweet_id_indexed.js

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

# stop mongo
rm -rf db; mkdir db
# start mongo
zcat ../sample.2011-09-24-2.json.gz | head -n100000 | ./load_into_mongo.py

./evaluate.sh 1
./evaluate.sh 2
...
./evaluate.sh 9

 r1 = data.frame(acc=read.delim('accuracy.1',header=F)$V1, run='r1')
 r2 = data.frame(acc=read.delim('accuracy.2',header=F)$V1, run='r2')
 r3 = data.frame(acc=read.delim('accuracy.3',header=F)$V1, run='r3')
 r4 = data.frame(acc=read.delim('accuracy.4',header=F)$V1, run='r4')
 r5 = data.frame(acc=read.delim('accuracy.5',header=F)$V1, run='r5')
 r6 = data.frame(acc=read.delim('accuracy.6',header=F)$V1, run='r6')
 r7 = data.frame(acc=read.delim('accuracy.7',header=F)$V1, run='r7')
 r8 = data.frame(acc=read.delim('accuracy.8',header=F)$V1, run='r8')
 r9 = data.frame(acc=read.delim('accuracy.9',header=F)$V1, run='r9')
 d = rbind(r1,r2,r3,r4,r5,r6,r7,r8,r9)
 ggplot(d, aes(run,acc)) + geom_boxplot()  
 # acc_vs_run.png
 
 r1 = data.frame(disagreement=read.delim('disagreements.1',header=F)$V1, run='r1')
 r2 = data.frame(disagreement=read.delim('disagreements.2',header=F)$V1, run='r2')
 r3 = data.frame(disagreement=read.delim('disagreements.3',header=F)$V1, run='r3')
 r4 = data.frame(disagreement=read.delim('disagreements.4',header=F)$V1, run='r4')
 r5 = data.frame(disagreement=read.delim('disagreements.5',header=F)$V1, run='r5')
 r6 = data.frame(disagreement=read.delim('disagreements.6',header=F)$V1, run='r6')
 r7 = data.frame(disagreement=read.delim('disagreements.7',header=F)$V1, run='r7')
 r8 = data.frame(disagreement=read.delim('disagreements.8',header=F)$V1, run='r8')
 r9 = data.frame(disagreement=read.delim('disagreements.9',header=F)$V1, run='r9')
 d = rbind(r1,r2,r3,r4,r5,r6,r7,r8,r9)
 gplot(d, aes(1:100,disagreement, group=run)) + geom_line(aes(colour=run)) + facet_grid(~run) + xlab('index')

 # disagreement_vs_index.png

doesnt actually look that good so try something simpler...

 reload data
 ./evaluate.sh 10a
 ./tweet_lang_text.py > tweet_lang_text.tsv
 grep -f non_english_chars tweet_lang_text.tsv | cut -f1 | ./set_tweet_lang.py not_en
 rm data.vw
 ./evaluate.sh 10b

 r10a = data.frame(acc=read.delim('accuracy.10a',header=F)$V1, run='r10a')
 r10b = data.frame(acc=read.delim('accuracy.10b',header=F)$V1, run='r10b')
 d = rbind(r10a,r10b)
 ggplot(d, aes(run,acc)) + geom_boxplot()

117683592905232384	 9.931163	-8.931163	1.0	en	k5na	@aikonoiland なにげにおしゃまさんも好き、トゥーティッキ。通常子安は痒いけど、画面がスナフキンだとなんかもうあれだね、世界情勢のいざこざまで全て許せる。それくらいこころが広くなれる。愛って大事だよねとか普通に言える。シラミの卵でもわかる愛の形を教えてくれるムムリク族。
117686768001757184	 9.142681	-8.142681	1.0	en	anecon	リキッドでSBTRKTめっちゃよかった。渾身のライブだったと思う。聴きたかった曲一通り聴けたし前で聞いたけど後ろまで盛り上がってて、アレンジも効いててアンコールの一曲もあって特に大阪みたいに短くは感じなかったよ。エモさに浸りながらもたっぷり動けてスッキリやで。
117676898812837888	 8.037859	-7.037859	1.0	en	tozaki	ま、ある意味戦略といってしまえば戦略。それを責めるのは青臭いと一蹴してもよい。評価が多次元で不明瞭なフィールドに一歩踏み込むだけで、周りに惑わされて小難しく論じようとする。そこで汎用性を求める必要はないし、同調する必要も無い。
117685807518715904	 7.771722	-6.771722	1.0	en	satokotherese	MJが天国に帰ってから2年。ようやく、何でか知らないけれど、This Is It を見ることができた。MJは中学時代の私にとって大事な存在で、しょっちゅう聞かなくなっても、愛するアーティストであった事に変わりはなかったことを、皮肉にも彼の死で知った。
117687481025052672	 7.540459	-6.540459	1.0	en	naokimed	イギリスに行くので、ガイドブックを買ってきた。今日行った本屋は結構大きいのだけど、イギリス関係のガイドブックはロンドンに集中してた。たしかに、フランスでイギリスは観光地としてのイメージがない気がする。パリからロンドンに行く人はかなりいると思うけど。


117675422409424897	5.702881	5.702881	0.0	ko	LycansPresent	호날두는 이제 완전히 어른이 되어 버린 것 같다. 얼굴에 나잇살이 붙었는지 부드러움이 있어 보이고 더욱 멋지게 변했네. 메시 날두 루니 내 또래 애들은 성장곡선의 정점에 가까이 올라가고 있는데 난 왜 점점 시간에 잠식당해가냐. 급반등 기대해 봅니다.
117687803973869568	5.140752	5.140752	0.0	ko	xgirl_bot	사실 카톡이 친구추천 하는 것 따위 필요 없어. 어차피 네 번호도 알고 네 집도 알고 네가 심심하면 어디서 뭐 하고 노는지 내가 다 아는데. 이렇게 되면 손모가지가 아니라 발모가지라도 분질러야 할까.
117675191697539073	5.071322	5.071322	0.0	ru	Volchica11	Поняла …что Она совсем не нужна Ему. Поняла… что ожидала от Него того…чего он не может дать. Не хватило всего лишь самой малости…
117679964819693568	5.047944	5.047944	0.0	ru	forever_in_hell	меня бесят когда говорят что уже ничего нельзя не изменить УЕБОК ЗАКРОЙ РОТ БЛЯТЬ ВСЕ МОЖНО ИЗМЕНИТЬ ЭТОГО ТОЛЬКО НАДО СИЛЬНО ЗАХОТЕТЬ И ВСЕ
117685773955895296	4.650966	4.650966	0.0	ko	thisisthat777	@constellayoom ㅍㅎㅎㅎㅎㅎㅎㅎㅎ 책하고 음반을... 도와 드릴 수도 없고ㅋ 잔영이 오래 남아 괴롭게 하는군요. 안 좋은건 보지도 가까이도 안 하는게 좋죠. 저도 잔영은 오래 가는 편인데 거기에 스스로 편집해~-^);; 좀극대화 해보는데ㅋ


 
117674839392796675	2.865339	-1.865339	1.0	en	Kyle_EH_EM	@illias_van  เกย์ลีน -  อื้ออออ ม...ไม่ถึงขนาดนั้นหรอกค่ะ  ,,&gt;  &lt;,,   *จับแก้มตัวเอง*
117686109475053568	2.735102	-1.735102	1.0	en	Bothtwice	RT @js100radio: 02.20น.เพลิงไหม้ โลตัส เอ็กซ์เพรส หน้า ม.รัตนโกสินทร์ 200 ปี ถ.รังสิต-ปทุม
117675921510645761	2.70498		-1.70498	1.0	en	krufiat		ไปที " เปิดหลักสูตรสนทนา Chameleon Man 40 ชม.เต็ม " เวลา 9 ตุลาคมตั้งแต่ 13:00 ถึง 15:00 เพิ่มเติม . หลักสูตร... http://t.co/Th9r8w4r
117673325265821696	2.657126	-1.657126	1.0	en	alteefnews	بقلم :( د .عبده الدباني) أيها الجنوبيون:تقاربوا..سووا صفوفكم..استووا...ينصركم الله - شبكة الطيف الإخبارية: http://t.co/FmlK7LqJ via @AddThis
117680782704783360	2.645035	-1.645035	1.0	en	Tyatyamaru48	@tgsk48 １３期生過去最多の３３人ですか 個人的には誰ひとり欠けることなく研究生として 見れることを願ってます


117678538768908290	2.281852	2.281852	0.0	it	nuclearmission	AHHHH my brother made it into Senior Regional Orchestra! He doesn't know seating yet but I'm so happy for him. He really needed this.
117683253174992896	2.160351	2.160351	0.0	es	sayno_tofood	soo... i just realize i lost 1 pound... that makes me super happy!!! like if i keep losing 1 pound a week i'll make it to my goal
117681994892197888	2.155557	-1.155557	1.0	en	ankostis	RT @comzeradd: RT @chimeres Η πιο όμορφη κατάληψη http://t.co/NrNDMLjC | η οποία διαλύθηκε προσφάτως απ τις "αρχές" http://t.co/3F2Kcgxr
117682821165883392	2.154213	2.154213	0.0	es	allier77	RT @YoNoMeExplico: DA RT SI TE GUSTA LA: █▀░█▀█░█▀░█▀█░░█▀░█▀█░█░░█▀█░ █░░█░█░█░░█▀█░░█░░█░█░█░░█▀█░ ▀▀░▀▀▀░▀▀░▀░▀░░▀▀░▀▀▀░▀▀░▀░▀░
117673706947485696	2.145417	2.145417	0.0	es	ecuaselenator	RT @MyHomeGirlSel: Im really glad that Selena's happy with justin! She's smiling all the time and that makes me happy! SELENA OWNS THE N ...

117675401425334273	2.362696	-1.362696	1.0	en	Lartis2010	\"Книга о Прашкевиче, или От Изысканного жирафа до Белого мамонта\" выходит в издательстве \"Шико\" http://t.co/Q9H3YvsO
117681730621673472	2.360148	-1.360148	1.0	en	ivannovi	впереди в сегодняшней программе - просмотр фильма "Ирина Палм сделает это лучше" и спаааать)
117678115160997888	2.33375		-1.33375	1.0	en	momokoly	มันถูกกำหนกไว้แล้ว ให้เราได้พบ"กัน"(:
117680325534023680	2.266024	-1.266024	1.0	en	max_whitewizard	"Лилль" сыграл вничью с "Лорьяном", "Лион" переиграл "Бордо" - Футбол  http://t.co/8KhAemx0
117675321725173760	2.112755	-1.112755	1.0	en	Hoseki_JEGirl	@pammeemy @tukkatakashita ฮ่าๆ มันสุนกน้า วันนี้พี่ก็เลนไป5ชัวโมง กีากก
