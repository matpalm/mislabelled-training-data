#!/usr/bin/env bash
set -e

function evaluate_once {
 mkdir wip/$1
 cd wip/$1
 ln -s ../../data.vw
 shuf data.vw | vw -f model --quiet
 cat data.vw | vw -t -i model -p predictions -r raw_predictions --quiet
 cat data.vw | cut -d' ' -f1-2 | sed -es/\|.*// > labels_with_ids.actual
 cat data.vw | cut -d' ' -f1 > labels.actual
 cat predictions | cut -d' ' -f1 > labels.predicted
 perf -ACC -files labels.{actual,predicted} -t 0.5 | awk '{print $2}' >> accuracy
}

if [ ! -e data.vw ]; then
 echo "building data..."
 ./tweets_to_vowpal.py > data.vw
fi

echo "evaluating"
rm -rf wip
mkdir wip
for i in {1..10}; do
 evaluate_once $i &
done
wait
:> accuracy
find wip -name accuracy -exec cat {} \; >> accuracy
cat accuracy

echo "calculating disagreement"
cat data.vw | cut -d' ' -f1-2 | sed -es/\|.*// > labels_with_ids.actual
./prediction_error.py labels_with_ids.actual wip/1/raw_predictions | sort -k2 -nr > disagreements.out
head -n5 disagreements.out
rm labels_with_ids.actual 

