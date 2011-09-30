#!/usr/bin/env bash
# rm data.vw to bootstrap everything
set -ex

if [ $# -ne 1 ]
then
  echo "Usage: `basename $0` {run_number}"
  exit -1
fi

function evaluate_once {
 mkdir wip/$1
 cd wip/$1
 ln -s ../../data.vw
 shuf data.vw | nice vw -f model --quiet
 cat data.vw | nice vw -t -i model -p predictions -r raw_predictions --quiet
 cat data.vw | cut -d' ' -f1-2 | sed -es/\|.*// > labels_with_ids.actual
 cat data.vw | cut -d' ' -f1 > labels.actual
 cat predictions | cut -d' ' -f1 > labels.predicted
 perf -ACC -files labels.{actual,predicted} -t 0.5 | awk '{print $2}' >> accuracy
}

echo "building data..."
./tweets_to_vowpal.py > data.vw

echo "evaluating; run $1"
rm -rf wip
mkdir wip
for i in {1..10}; do
 evaluate_once $i &
done
wait
:> accuracy.$1
find wip -name accuracy -exec cat {} \; >> accuracy.$1
head -n3 accuracy.$1

echo "calculating disagreement"
cat data.vw | cut -d' ' -f1-2 | sed -es/\|.*// > labels_with_ids.actual
./prediction_error.py labels_with_ids.actual wip/1/raw_predictions | sort -k2 -nr > disagreements.$1.out
head -n5 disagreements.$1.out
cut -f2 disagreements.$1.out | head -n100 > disagreements.$1
rm labels_with_ids.actual 

echo "flipping language for top 100"
cut -f1 disagreements.$1.out | head -n100 | ./flip_tweet_lang.py > flip.out
head -n3 flip.out
