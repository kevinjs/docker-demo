#!/usr/bin/env python
# author: calvinshao
# email: dysj4099@gmail.com

import sys
import os
import time
import json
from docker import Client

cnt_new = {}
cnt_old = {}
rate = {}

def main():
    global cnt_new
    global cnt_old
    global rate

    cli = Client(base_url='unix://var/run/docker.sock')

    cnt_total = 0
    while(True):
        cons = [c['Id'][0:6] for c in cli.containers()]
        tik = cnt_total % 4

        print 'id	ip		acc_num	acc_rate'
        if tik == 0:
            cnt_old = dict(zip(cons, [0 for x in cons]))
        elif tik == 3:
            cnt_new = dict(zip(cons, [0 for x in cons]))

        for i in cons:
            con_ip = cli.inspect_container(i)['NetworkSettings']['IPAddress']
            acc_num = 0
            acc_rate = 0
            tmp = cli.logs(i, tail=1).split(':')

            if len(tmp) == 2:
                acc_num = tmp[1].strip()
                if tik == 0:
                    cnt_old[i] = int(acc_num)
                elif tik == 3:
                    cnt_new[i] = int(acc_num)
            else:
                acc_num = 'err'
            if tik == 3:
                if i in cnt_new and i in cnt_old:
                    acc_rate = (cnt_new[i] - cnt_old[i])/3.0
                else:
                    acc_rate = 0
                if acc_rate < 0:
                    acc_rate = 0.0
                rate[i] = acc_rate
            else:
                if i in rate:
                    acc_rate = rate[i]
                else:
                    acc_rate = 0
	    print '%s	%s	%s	%s'%(i,  con_ip, acc_num, acc_rate)
        print 'total num: %s' %len(cons)
        print '==' * 10
        time.sleep(1)
        cnt_total += 1 

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print 'Bye~~~'
        sys.exit(0)
