mongod --dbpath=db --port 26566

curl -u user:password https://stream.twitter.com/1/statuses/sample.json | ./load_into_mongo.py

./tweets_to_vowpal.py > data.vw

wc -l data.vw
337867

mkdir wip
cd wip
ln -s ../data.vw
shuf data.vw | vw -f model
cat data.vw | vw -t -i model -p predictions -r raw_predictions

# perf accuracy
cat data.vw | cut -d' ' -f1 > labels.actual
cat predictions | cut -d' ' -f1 > labels.predicted
perf -ACC -files labels.actual labels.predicted -t 0.5 | awk '{print $2}'
0.888

# most "wrong" cases
cat data.vw | cut -d' ' -f1-2 | sed -es/\|.*// > labels_with_ids.actual
../most_wrong.py labels_with_ids.actual raw_predictions | sort -k5 -nr > most_wrong.out



