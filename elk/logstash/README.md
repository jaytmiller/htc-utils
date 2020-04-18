# HTCondor EventLog Logstash Notes

## Overview

The baseline for this HTCondor EventLog processing effort was derived
from material in this presentation from HTCondor Week:

       https://agenda.hep.wisc.edu/event/1325/session/16/contribution/2/material/slides/0.pdf

described parsing EventLog using Logstash and forwarding those results
to Elasticsearch and Kibana for display on a dashboard.

This related github repo included a baseline Logstash configuration for parsing
EventLog on ELK 5:

     https://github.com/fifemon/logstash-config

Primarily the "seed" content included pipeline/logstash.conf,
patterns/condor, and config/htc-eventlog.json, updated/fixed by
STScI for ELK 6.

## About HTCondor EventLog

In addition to being an optional log file, the contents of EventLog
are highly configurable with ~100 attributes to enable/disable.  Our
initial condor config (not included here) was basic and included only
these additional attributes in addition to the standard log event
attributes:

```
EVENT_LOG_JOB_AD_INFORMATION_ATTRS = \
 Owner \
 DAGManJobId \
 MachineAttrMachine0 \
 JobCurrentStartDate \
 ImageSize
```

NOTE: adding/removing attributes to the condor EventLog config may
change the format of EventLog events and require corresponding changes
to these logstash config files, patterns, etc. to maintain pattern
matching.

## About this Logstash application

One logstash configuration is intended to be run for each DMS string
to process the HTCondor EventLog from that string.  The prototype
string is configured for JWST TEST string 2 and can be viewed at:

```
https://test.dmdelk.stsci.edu/app/kibana
```

Each of the Kibana artifacts stored in export.json begins with some
form of the string "htc".   The dashboard is named HTCondor EventLog.

## Configuration files

This is pretty standard Logstash setup by the EventLog app customizes
each of these.

### pipeline/logstash.conf

This file defines the Logstash input, filter, and output configuration
including the target Elasticsearch server.

The input and filter sections first combine multi-line EventLog
messages into one line and then parse the lines with different
patterns and logstash filter plugins to produce key-value pairs for
Elasticsearch.    There's an aggregation process

### patterns/condor

This file defines Logstash grok regexes used in logstash.conf above.  These
may need to change if EventLog message formats change or if additional
information needs to be parsed out of the existing messages.

### config/htc-eventlog.json

This template files assigns types to the different fields log messages are
split into.

### export.json

Strictly speaking,  this is not a Logstash config file,  it is an export of
the Kibana index, searches, visualizations, and dashboard.  It can currently
be reloaded by going to the Kibana management page,  selecting Saved Objects,
selecting "import",  and uploading export.json.

## Points of Customization

First off,  all customization other than the Docker image name is now captured
in the `./run` script.   But discussing further...

In order to target multiple strings,   initially there are 3 potential
points of customization:

   1. pipeline/logstash.conf specifies the elasticsearch server to
   target in the `output` section.

   2. pipeline/logstash.conf adds a `pool` field in the input section which
   should be used to denote the string.   During usage, it will be necessary
   for operators to customize searches by adding a filter based on `pool`.

   3. As delivered the `run` script bind mounts a string's Condor log *directory*
   into the Docker container.  The container name defined by `run` should also be
   customized to indicate the string the container supports.

To enable usage of a single common Docker image, key environment variables are
set in the `./run` script and passed into the container,  see below.

## Notes on /internal/data1/apps/*

## Building

Dockerfile.logstash was derived from instructions on the Elasticsearch
website for setting up a self-contained Docker container.  This setup
approach creates a fully configured logstash image with customized
files built-in, overlaying the standard Logstash config.

There is a simple build script which in its current form uses sudo
internally to run docker:

```
./build
```

This downloads the standard Logstash image from Elasticsearch and adds
a very thin layer of STScI configuration files to set it up for EventLog.

Currently no registry is set up, pulling really seems no better than
building for this use case.

## Running

There is a run script to start the container:

```
./run
```

The `./run` script defines all of the string customization variables in the
environment and passes them into a generic `htc-logstash` image creating a container
targeted at one DMS string:

```
#! /bin/sh

# Design is for one container per condor string, but one combined
# index for all strings discriminated using "pool" index field.

# Must be customized for each string:
HTC_EVENTLOG_SCHED_HOST="tljwdmscsched2"
HTC_EVENTLOG_ELASTIC_HOST="https://test.dmdelk.stsci.edu:443/elastic"
HTC_EVENTLOG_CONDOR_LOG_DIR="/ifs/archive/test/jwst/store/condor/logs/tljwdmscsched2"  # Note the /ifs/archive/test...

# Generic / derived values which theoretically take care of themselves.
HTC_EVENTLOG_CONTAINER_NAME="htc-eventlog-${HTC_EVENTLOG_SCHED_HOST}"
HTC_EVENTLOG_INDEX_NAME="htc-eventlog-%{+YYYY.MM.dd}"   # note generic index, use "pool" field to filter.
HTC_EVENTLOG_POOL_NAME="pool-${HTC_EVENTLOG_SCHED_HOST}"

sudo docker run -d \
       --name ${HTC_EVENTLOG_CONTAINER_NAME} \
       --mount type=bind,source=${HTC_EVENTLOG_CONDOR_LOG_DIR},destination=/var/log/condor,readonly \
       -e HTC_EVENTLOG_ELASTIC_HOST=${HTC_EVENTLOG_ELASTIC_HOST} \
       -e HTC_EVENTLOG_INDEX_NAME=${HTC_EVENTLOG_INDEX_NAME} \
       -e HTC_EVENTLOG_POOL_NAME=${HTC_EVENTLOG_POOL_NAME} \
       htc-logstash  $*
```

The container is run in the background in daemon mode; logs can be
viewed with *sudo docker logs -f htc-logstash*.

./run mounts the suppored string's condor logs directory into the
Logstash container at the standard htcondor location as readonly.

No ports are exposed.

## Kibana for EventLog

In general all of the Kibana artifacts for EventLog are created using the Kibana
web tools or uploaded via `exports.json` described more below.  In particular,
they're not automatically loaded using a logstash command analogous to the command
used by metricbeat.

### Index

The Kibana index pattern for EventLog logstash is created after running this logstash
for the first time using the Kibana `Management` link `Index Patterns`.  It's a generic
index shared by all strings so enter `htc-eventlog-*` to capture all eventlog indices
regardless of date.  Condor pool doesn't enter the picture here except as a field to be
used to filter to specific strings later.

This index pattern is also saved in `exports.json` below so it may not be necessary to
create it seperately unless you're doing development and changing the index/template.

**CAUTION:** AFAICT Kibana is incredibly brittle and so the same index pattern created at
different times or loaded from exports.json will be different objects... hence saved
artifacts (e.g. dashboard) may/will only work with the saved index. If you change the
index you may wind up doing some dashboard maintenance/reentry as well... 

### Saving Kibana Dashboards

To save the current dashboards go to Kibana's `Management` window,  click on `Saved Objects`,
and type in the "htc" substring which is/should-be common to all EventLog Kibana artifacts:
index, searches, visualizations, dashboard, etc.   This should bring up all of the
EventLog related Kibana objects;  watch for objects which may not be for EventLog.  Select
the EventLog objects.   Click on the `Export xyz objects` link at the top right.
This should download a file named `exports.json` to your browser's current download directory.
Copy that into this repo and commit it.

### Loading Kibana Dashboards

To load the saved dashboards do the reverse.   Go to Kibana's `Management` window,  click on 
`Saved Objects`,  click on `Import` at the top right.   Upload `exports.json` saved previously.

## Adding Fields

Many of the fields in the EventLog index come from the key-value filter defined in logstash.conf
and so they're fairly automatic.  If a new pair is added to the log they may automatically be
added to the documents by the `kv` filter.

Some fields are parsed using `grok` regular expressions which can be defined in `patterns/condor`
or `pipeline/logstash.conf`.

When adding new fields you should also add to the index template in `config/htc-eventlog.json` to
define the type of the new field.

## Debug Tips

Assume the logstash docker container is named ```htc-logstash``` or substitute
the real name.

### Reviewing Logstash Logs

Running as a docker daemon, docker stores stderr and stdout and it can be dumped:

```
sudo docker logs -f htc-logstash
```

This provides great access to log output.  Further, the
pipeline/logstash.conf file has a parallel output:

```
stdout {codec =>"rubydebug"}
```

which traces what is being sent to elasticsearch.  To avoid overhead
this is nominally commented out but can be uncommented and put into
effect by re-running the build script and container.

### Accessing the Logstash API

If you're stuck with a logstash "black hole" and can't figure out
what's wiping out all your events, you can access the logstash API for
some basic info:

```
sudo docker exec -it htc-logstash /bin/bash
curl -XGET 'localhost:9600/_node/stats?pretty'
```

Exec'ing into the container and referring to localhost should work
anywhere regardless of firewalling.  The ```_node/stats``` URL can
provide information on the basic dataflow through your logstash which
can give clues as to "where everything is getting dropped."

