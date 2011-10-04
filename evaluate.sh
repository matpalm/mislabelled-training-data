#!/usr/bin/env bash
# rm data.vw to bootstrap everything
set -ex

if [ $# -ne 1 ]
then
  echo "Usage: `basename $0` {run_number}"
  exit -1
fi

function run_once {
 rm -rf run/$1; mkdir run/$1; cd run/$1
 find ../.. -type f -exec ln -s {} \;
 # build model and make predictions
 shuf data.vw | nice vw -f model --quiet
 cat data.vw | nice vw -t -i model -p predictions -r raw_predictions --quiet
 cat predictions | cut -d' ' -f1 > labels.predicted
 # measure ACC performance
 perf -ACC -files labels.actual labels.predicted -t 0.5 | awk '{print $2}' >> accuracy
 # measure disagreement, per tweet
 prediction_error.py labels_id.actual raw_predictions | sort > id_predictionerrors
}

export PATH=`pwd`:$PATH
rm -rf eval.$1; mkdir eval.$1; cd eval.$1

echo "building data..."
tweets_to_vowpal.py > data.vw
cat data.vw | cut -d' ' -f1,2 | sed -es/\|.*// > labels_id.actual
cat labels_id.actual | cut -d' ' -f1 > labels.actual

echo "evaluating; run $1"
rm -rf run; mkdir run
for i in {1..20}; do
 run_once $i &
done
wait

# gather accuracies into one file
:> accuracy
find run -name accuracy -exec cat {} \; >> accuracy
head -n3 accuracy

exit 0 # for set_lanG_by_chars case

# calculate mean square errors for each tweet
#:> id_mse
#find run -name id_predictionerrors | xargs sort -m | mse.py | sort -k2 -nr > id_mse
#head -n3 id_mse

# flip language for top 100
#cut -f1 id_mse | head -n100 | sed -es/id_// | flip_tweet_lang.py > flip.out
#head -n3 flip.out
