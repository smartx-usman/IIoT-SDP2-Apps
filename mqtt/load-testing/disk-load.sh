#!/bin/bash

low=30
hgh=60

fallocate -l 600M file-a
sleep 30
fallocate -l 600M file-b
sleep 30

while :; do
  echo "Press <CTRL+C> to exit."
  for count in {1..10}; do
    if [[ $count -le 5 ]]; then
      fallocate -l 300M file-$count
    fi

    if [[ $count -ge 6 ]]; then
      fileno=$((count - 5))
      rm -rf file-$fileno
    fi

    rand=$((low + RANDOM % (1 + hgh - low)))
    echo "Sleeping for $rand"
    sleep $rand

  done

  sleep 30
done


curl -X GET "localhost:9200/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title":   "Search"        }},
        { "match": { "content": "Elasticsearch" }}
      ],
      "filter": [
        { "term":  { "status": "published" }},
        { "range": { "publish_date": { "gte": "2015-01-01" }}}
      ]
    }
  }
}
'
