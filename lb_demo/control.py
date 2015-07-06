#!/usr/bin/env python
# Author: calvinshao
# email: dysj4099@gmail.com

import sys
import subprocess
from docker import Client

def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

def add_node(cli, num, image_str, cmd_str):
    rtn_info = []
    for i in xrange(0, num):
        new_con = cli.create_container(image=image_str, command=cmd_str, stdin_open=True, tty=True)
        cli.start(new_con)
        info = cli.inspect_container(new_con)
        rtn_info.append({'id': new_con['Id'][0:6], 'ip':info['NetworkSettings']['IPAddress']})
    refresh_haproxy(cli)
    return rtn_info

def start_node(cli, con_str):
    start_info = cli.start(container=con_str)
    refresh_haproxy(cli)
    return start_info

def stop_node(cli, con_str):
    stop_info = cli.stop(container=con_str)
    refresh_haproxy(cli)
    return stop_info

def list_nodes(cli):
    run_cons = [c['Id'][0:6] for c in cli.containers()]
    all_cons = [c['Id'][0:6] for c in cli.containers(all=True)]

    print 'id	status	image'
    for i in all_cons:
        con_image = cli.inspect_container(i)['Config']['Image']

        con_status = 'stop'
        if i in run_cons:
            con_status = 'running'
            
        print '%s	%s	%s' %(i, con_status, con_image)

def refresh_haproxy(cli):
    new_content = ''
    cons_info = {}

    # get containers info
    cons = [c['Id'][0:6] for c in cli.containers()]
    for i in cons:
        con_ip = cli.inspect_container(i)['NetworkSettings']['IPAddress']
        cons_info[i] = con_ip

    with open('/etc/haproxy/haproxy.cfg') as f_ha:
        for line in f_ha.xreadlines():
            if not line.strip().startswith('server'):
                new_content += line

        for con_id, con_ip in cons_info.items():
            new_content += '	server	%s	%s:8800	check inter 2000 rise 2 fall 3\n' %(con_id, con_ip)
    write_file('/etc/haproxy/haproxy.cfg', new_content)
    subprocess.Popen('/bin/bash reload_haproxy.sh', shell=True)

if __name__=='__main__':
    cli = Client(base_url='unix://var/run/docker.sock')
    
    if len(sys.argv) == 2:
        if 'refresh' == sys.argv[1]:
            refresh_haproxy(cli)
        elif 'help' == sys.argv[1]:
            print 'ADD: python %s add num\nSTART: python %s %s\nSTOP: python %s %s' %(sys.argv[0], sys.argv[0], 'con_id_str', sys.argv[0], 'con_id_str')
            sys.exit(0)
        elif 'list' == sys.argv[1]:
            list_nodes(cli)
    elif len(sys.argv) == 3:
        if 'start' == sys.argv[1]:
            print 'Start node %s, %s' %(sys.argv[2], start_node(cli, sys.argv[2]))
        elif 'stop' == sys.argv[1]:
            print 'Stop container %s, %s' %(sys.argv[2], stop_node(cli, sys.argv[2]))
        elif 'add' == sys.argv[1]:
            print add_node(cli, int(sys.argv[2]), 'ubuntu:py27tor2', 'python /root/httpserver.py')

