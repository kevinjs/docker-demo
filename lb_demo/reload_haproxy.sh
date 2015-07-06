#!/bin/bash
# author: calvinshao
# email: dysj4099@gmail.com

ps -ef | grep sbin/haproxy | grep -v grep | awk '{print $2}' | xargs -I[] kill []

sleep 1

/usr/sbin/haproxy -f /etc/haproxy/haproxy.cfg -D

pid=`ps -ef | grep sbin/haproxy | grep -v grep | awk '{print $2}'`

echo $pid
