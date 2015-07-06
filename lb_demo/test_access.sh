#!/bin/bash

acc_times=100
acc_interval=.1

if [ $# -ne 4 ];then
    echo "Usage:"
    echo "      `basename $0` -t access_times -i access_interval"
    exit 0
fi

acc_times=$2
acc_interval=$4

for ((i=0;i<$acc_times;i++));do curl -X GET http://127.0.0.1:8080/; sleep $acc_interval; done
