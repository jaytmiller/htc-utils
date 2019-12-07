#! /bin/sh

export REST_TIME=$(shuf -i 5-15 -n 1)
echo "$1 job sleeping for $REST_TIME"
sleep $REST_TIME
