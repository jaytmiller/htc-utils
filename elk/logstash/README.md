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

Primarily the "seed" content included pipelines/logstash.conf,
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

## Configuration files

### pipelines/logstash.conf

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

This template files assigns types to the different fields logs messages are
split into.

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
a very thin layer of STScI configuration files to set it up for EventLog
and target a particular Elasticsearch host.

## Running

There is a simple run script:

```
./run
```

which internally uses sudo to execute "docker run".   Currently this does:

```
sudo docker run -d \
       --name htc-logstash \
       --mount type=bind,source=/ifs/archive/test/jwst/store/condor/logs/tljwdmscsched2,destination=/var/log/condor,readonly \
       htc-logstash  $*
```

creating a running container named "htc-logstash".  

The container is run in the background in daemon mode; logs can be
viewed with "sudo docker logs -f htc-logstash".

./run mounts the suppored string's condor logs directory into the
Logstash container at the standard htcondor location as readonly:

/ifs/archive/test/jwst/store/condor/logs/tljwdmscsched2  -->   /var/log/condor

The run command exposes container network ports 5044 (logstash beats
input) and 9600 (logstash web api calls).  Strictly speaking, neither
port is required.  For debug, port 9600 can be accessed by exec'ing
into the running container and referring to localhost:9600.  For this
application, Logstash is reading a file directly rather than
processing a filebeat so 5044 is not needed either.

## Kibana for EventLog

### Index 

### Saving and Importing Dashboards

## Adding Fields

## Debug Tips

Assume the logstash docker container is named ```htc-logstash``` or substitute
the real name.

Running as a docker daemon, docker stores stderr and stdout and it can be dumped:

```
sudo docker logs -f htc-logstash
```

This provides great access to log output.  Further, the
pipelines/logstash.conf file has a parallel output:

```
stdout {codec =>"rubydebug"}
```

which traces what is being sent to elasticsearch.  To avoid overhead
this is nominally commented out but can be uncommented and put into
effect by re-running the build script and container.

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

