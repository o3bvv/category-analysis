#!/usr/bin/bash

set -e

pip install -r requirements.txt \
&& python -m nltk.downloader "stopwords" \
&& python -m nltk.downloader "punkt" \
&& python -m nltk.downloader "wordnet" \
&& python -m nltk.downloader "omw-1.4" \
&& python -m nltk.downloader "maxent_ne_chunker" \
&& python -m nltk.downloader "averaged_perceptron_tagger" \
&& python -m nltk.downloader "words" \
&& python -m nltk.downloader "tagsets"
