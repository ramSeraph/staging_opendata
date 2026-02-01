#!/bin/bash

uvx --from wmsdump wms-extractor explore --geoserver-url https://idc.goa.gov.in/geoserver -o layers.txt

cat data/layers.txt| grep NDUSTRIAL_ESTATE | xargs -I {} uvx --from wmsdump wms-extractor extract --geoserver-url https://idc.goa.gov.in/geoserver -m extent -d data {}

cat data/layers.txt| grep -i plot_ | xargs -I {} uvx --from wmsdump wms-extractor extract --geoserver-url https://idc.goa.gov.in/geoserver -k Unique_ID -d data {}

cat data/layers.txt| grep -i ROAD_ | xargs -I {} uvx --from wmsdump wms-extractor extract --geoserver-url https://idc.goa.gov.in/geoserver -k EntityHand -d data {}
uvx --from wmsdump wms-extractor extract --geoserver-url https://idc.goa.gov.in/geoserver goa-idc:ROAD_PILERNE -k gid -d data

cat data/layers.txt| grep "goa-idc" | grep -v ROAD | grep -vi PLOT_ | grep -v INDUSTRIAL | grep -v State | grep -v District | grep -v Taluka | xargs -I {}  uvx --from wmsdump wms-extractor extract --geoserver-url https://idc.goa.gov.in/geoserver -d data {}
