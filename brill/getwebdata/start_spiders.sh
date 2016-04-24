#!/bin/sh

debug_en=$1

scrapy crawl craig -a debug=$debug_en

