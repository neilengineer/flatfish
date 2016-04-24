#!/bin/sh

debug_en=$1
log='log.txt'

scrapy crawl craig -a debug=$debug_en -s LOG_FILE=$log



