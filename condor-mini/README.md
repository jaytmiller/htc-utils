# Condor Mini

## Overview

Condor-mini is a stripped down version of the excellent but large
https://github.com/htcondor/htc-minimal-notebook.

The goal of condor-mini is to enable development of condor based
systems using containers to store the master node and some token
number of workers.   To reduce the size of the image/container,
condor-mini strips out JupyterLab, one of the main puposes of
htc-minimal-notebook,  leaving only the personal condor.

## Architecture

Condor-mini consists of a small stack of two images based directly
on the architecture of htc-minimal-notebook:

- condor-base is based on Ubuntu and a barebones miniconda installation.

- condor-mini adds a personal htcondor system to condor-base.

## Building

Building can be performed by running the root build script to
build both components:  condor-base and condor-mini.

```$ ./build```

Child scripts also exist to to development on either component
seperately.

## Running

Running condor-mini can be accomplished by executing:

```$ ./run
Started HTCondor
jovyan@68e47ed84c73:~$ condor_status
Name               OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime

slot1@68e47ed84c73 LINUX      X86_64 Unclaimed Idle      0.000 4748  0+00:00:03

               Total Owner Claimed Unclaimed Matched Preempting Backfill  Drain

  X86_64/LINUX     1     0       0         1       0          0        0      0

         Total     1     0       0         1       0          0        0      0
jovyan@68e47ed84c73:~$ condor_q


-- Schedd: jovyan@68e47ed84c73 : <172.17.0.2:9618?... @ 03/29/20 17:43:06
OWNER BATCH_NAME      SUBMITTED   DONE   RUN    IDLE   HOLD  TOTAL JOB_IDS

Total for query: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended 
Total for all users: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended

jovyan@68e47ed84c73:~$ condor_restart
Sent "Restart" command to local master
```

By default ths will start htcondor and place the user at an interactive
bash prompt.


