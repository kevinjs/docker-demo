#!/usr/bin/env python
# author: calvinshao
# email: dysj4099@gmail.com

import sys
import os
import time
import json
import subprocess
from docker import Client

cnt_new = {}
cnt_old = {}
rate = {}

max_rate = 0
min_rate = 0
repeat = {'normal':0, 'abnormal':0}

report = {}
is_rp = False

def append_file(filename, wrt_line):
    with open(filename, 'a') as f:
        f.write('%s\n'%wrt_line)

def create_report(filename):
    global report
    #print report
    col_num = len(report) - 1
    row_num = len(report['total'])
    con_ids = list(set(report.keys()).difference(set(['average', 'total', 'start_time', 'end_time'])))

    wrt_title = '%s,%s,%s' %('time', 'total', 'avg')
    for i in con_ids:
        wrt_title += ',%s' %i
    #print wrt_title
    append_file(filename, wrt_title)

    for i in xrange(0, row_num):
        wrt_line = '%s,%s,%s' %(i, report['total'][i], report['average'][i])
        for j in con_ids:
            value = 0
            if i in report[j]:
                value = report[j][i]
            wrt_line += ',%s' %value
        #print wrt_line
        append_file(filename, wrt_line)
    append_file(filename, '%s,%s'%(report['start_time'], report['end_time']))

def adjust(cli, cur_rate):
    global repeat
    global max_rate
    global min_rate

    run_cons = [c['Id'][0:6] for c in cli.containers()] 
    all_cons = [c['Id'][0:6] for c in cli.containers(all=True)]
    avail_cons = [i for i in all_cons if i not in run_cons]

    #print '%s %s %s' %(len(run_cons), len(all_cons), len(avail_cons)) 
    #print '%s %s %s' %(min_rate, cur_rate, max_rate)

    if cur_rate > max_rate or len(run_cons) < 1:
        if avail_cons:
            subprocess.Popen(['python', 'control.py', 'start', avail_cons[0]])
        else:
            subprocess.Popen(['python', 'control.py', 'add', '1'])
    if cur_rate < min_rate:
        if len(run_cons) >= 2:
            subprocess.Popen(['python', 'control.py', 'stop', run_cons[0]])
    repeat['abnormal'] = 0
    repeat['normal'] = 0

def auto_adjust(cli, cur_rate):
    global max_rate
    global min_rate
    global repeat

    # Not AUTO mode.
    if max_rate == min_rate and max_rate == 0:
        return 'normal'
    else:
        # normal state
        if min_rate <= cur_rate and cur_rate <= max_rate:
            repeat['normal'] += 1

            if repeat['abnormal'] <= 4:
                repeat['abnormal'] = 0
        else:
            repeat['abnormal'] += 1
            
            if repeat['abnormal'] >= 4:
                repeat['normal'] = 0

        #print repeat

        if repeat['normal'] > 3:
            #repeat['abnormal'] = 0
            #if cur_rate == 0:
            #    repeat['normal'] = 0
            return 'normal'
        if repeat['abnormal'] > 3:
            #repeat['normal'] = 0
            adjust(cli, cur_rate)
            return 'adjust'

def main(cli):
    global cnt_new
    global cnt_old
    global rate
    global max_rate
    global min_rate
    global report
    global is_rp

    if is_rp:
        report['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        report['total'] = {}
        report['average'] = {}

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
            if is_rp and (i not in report):
                report[i] = {}

            con_ip = cli.inspect_container(i)['NetworkSettings']['IPAddress']
            acc_num = 0
            acc_rate = 0
            tmp = cli.logs(i, tail=1).split(':')

            if len(tmp) == 2:
                acc_num = tmp[1].strip()
                acc_num_v = 0
                try:
                    acc_num_v = int(acc_num)
                except ValueError:
                    acc_num = 'err'
                    acc_num_v = 0
                if tik == 0:
                    cnt_old[i] = acc_num_v
                elif tik == 3:
                    cnt_new[i] = acc_num_v
            else:
                acc_num = 'err'

            if tik == 3:
                if i in cnt_new and i in cnt_old:
                    acc_rate = round((cnt_new[i] - cnt_old[i])/3.0, 4)
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
            if is_rp:
                report[i][cnt_total] = acc_rate

        rate_avg = 0.0
        length_cons = 1
        sum_rate_cons = 0

        if rate:
            if cons:
                length_cons = len(cons)
            for c_i in cons:
                if c_i in rate:
                    sum_rate_cons += rate[c_i]
            rate_avg = round(float(sum_rate_cons)/length_cons, 4)
            if is_rp:
                report['total'][cnt_total] = sum_rate_cons
        else:
            if is_rp:
                report['total'][cnt_total] = 0
        print 'total num: %s, average rate: %s' %(len(cons), rate_avg)
        if is_rp:
            report['average'][cnt_total] = rate_avg
        if tik == 3:
            auto_adjust(cli, rate_avg)
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
            is_rp = False
            tmp = sys.argv[2].split('-')
            min_rate = float(tmp[0])
            max_rate = float(tmp[1])
            if min_rate > max_rate:
                t = min_rate
                min_rate = max_rate
                max_rate = t
        elif 'report' == sys.argv[1]:
            is_rp = True
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
        if is_rp:
            t_t = time.time()
            report['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t_t))
            filename = 'report_%s.csv' %(time.strftime('%Y%m%d%H%M%S', time.localtime(t_t)))
            create_report(filename)
        print 'Bye~~~'
        sys.exit(0)

