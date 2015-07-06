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

max_rate = 0
min_rate = 0
repeat = {'mode':'normal', 'times':0}

def auto_adjust(cur_rate):
    global max_rate
    global min_rate
    global repeat

    if max_rate == min_rate and max_rate == 0:
        return 'normal'
    else:
        # normal state
        if min_rate <= cur_rate and cur_rate <= max_rate:
            if repeat['mode'] == 'normal':
                repeat['times'] += 1
            else:
                repeat['mode'] = 'normal'
                repeat['times'] = 0
        else:
            if repeat['mode'] == 'abnormal':
                repeat['times'] += 1
            else:
                repeat['mode'] == 'abnormal'
                repeat['times'] = 0

        if repeat['mode'] == 'normal':
            if repeat['times'] >= 2:
                return 'normal'
            else:
                return 'adjust'
        if repeat['mode'] == 'abnormal':
            if repeat['times'] < 5:
                return 'normal'
            else:
                return 'adjust'

def main(cli):
    global cnt_new
    global cnt_old
    global rate
    global max_rate
    global min_rate

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

        rate_avg = 0.0
        if rate:
            rate_avg = float(sum(rate.values()))/len(rate)
        print 'total num: %s, average rate: %s' %(len(cons), rate_avg)
        print auto_adjust(rate_avg)
        print '==' * 10
        time.sleep(1)
        cnt_total += 1 

if __name__=='__main__':
    cli = Client(base_url='unix://var/run/docker.sock')

    if len(sys.argv) == 2:
        if 'help' == sys.argv[1]:
            print 'NORMAL: python %s normal\nAUTO: python %s auto min-max\n' %(sys.argv[0], sys.argv[0])
            sys.exit(0)
        elif 'normal' == sys.argv[1]:
            pass
    elif len(sys.argv) == 3:
        if 'auto' == sys.argv[1]:
            tmp = sys.argv[2].split('-')
            min_rate = float(tmp[0])
            max_rate = float(tmp[1])
            if min_rate > max_rate:
                t = min_rate
                min_rate = max_rate
                max_rate = t

    print '%s-%s' %(min_rate, max_rate)
    try:
        main(cli)
    except KeyboardInterrupt:
        print 'Bye~~~'
        sys.exit(0)

