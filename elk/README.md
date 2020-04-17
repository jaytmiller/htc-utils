This setup is used for doing standalone development with ELK.

Initially it supports Elasticsearch, Kibana, and HTCondor EventLog's Logstash.

There are a number of scripts which all iterate over those "components":

```
./build  [<component>]           #  create docker image
./run    [<component>]           #  run component container
./stop   [<component>]           #  stop component and prune containers
./cycle  [<component>]           #  perform one dev iteration for component: stop, build, clean up, restart
```

If no component is specified these scripts perform that operation on
each component listed in the ```components``` file in order.

There are related cleanup scripts:

```
./cleanup                        # Removes orphaned docker images with name <none>
./wipeall                        # Wipes out all docker images,  period.
```
