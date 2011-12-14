#!/usr/bin/env python

""" 
Uses keychain + ssh-agent + cached passphrase to sync files across to
bob.openpanel.com.
"""


import commands
import sys
import os

hostname = commands.getoutput('hostname -f')
print(hostname)

# keychain contains the location of our SSH_AGENT:
keychain = "/home/buildmaster/.keychain/%s-sh" % hostname

# Open keychain and read it
f = open(keychain, 'r')
ssh_auth_sock = f.readline()
ssh_agent_pid = f.readline()
f.close()

# Only interested in the middle bit of that file:
ssh_auth_sock = ssh_auth_sock.split("=")[1].split(';')[0]
os.environ['SSH_AUTH_SOCK'] = ssh_auth_sock

# Dito.
ssh_agent_pid = ssh_agent_pid.split("=")[1].split(';')[0]
os.environ['SSH_AGENT_PID'] = ssh_agent_pid

rsync = commands.getoutput('rsync -larv /srv/repository/ buildmaster@bob.openpanel.com:/srv/buildbot/repository/')
print(rsync)
print("Done. Bob's your uncle.")
sys.exit(0)
