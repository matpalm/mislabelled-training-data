#!/usr/bin/env bash
# rm data.vw to bootstrap everything
set -ex

if [ $# -ne 1 ]
then
  echo "Usage: `basename $0` {run_number}"
  exit -1
fi

function evaluate_once {
 rm -rf wip_$1
 mkdir wip_$1
 cd wip_$1
 shuf ../data.vw | nice vw -f model --quiet
 cat ../data.vw | nice vw -t -i model -p predictions -r raw_predictions --quiet
 cat predictions | cut -d' ' -f1 > labels.predicted
 # measure ACC performance
 perf -ACC -files ../labels.actual labels.predicted -t 0.5 | awk '{print $2}' >> accuracy
 # measure disagreement, per tweet
 ../prediction_error.py ../labels_id.actual raw_predictions | sort > id_predictionerrors
}

echo "building data..."
./tweets_to_vowpal.py > data.vw
cat data.vw | cut -d' ' -f1,2 | sed -es/\|.*// > labels_id.actual
cat labels_id.actual | cut -d' ' -f1 > labels.actual

echo "evaluating; run $1"
for i in {1..10}; do
 evaluate_once $i &
done
wait

# gather accuracies into one file
:> accuracy.$1
find wip* -name accuracy -exec cat {} \; >> accuracy.$1
head -n3 accuracy.$1

# calculate mean square errors for each tweet
:> id_mse.$1
find wip* -name id_predictionerrors | xargs sort -m | ./mse.py | sort -k2 -nr > id_mse.$1
head -n3 id_mse.$1

# flip language for top 100
#cut -p1 id_mse.$1 | head -n100 | cut -f1 | ./flip_tweet_lang.py > flip.out
#head -n3 flip.out
