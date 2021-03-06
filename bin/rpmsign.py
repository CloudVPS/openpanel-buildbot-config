#!/usr/bin/env python

""" 
 rpm packages can be signed with GPG keys. This process is flawed, however, in
that it ignores gpg-agents. This script allows you to use a gpg-agent to
decrypt a file containing the gpg-passphrase you need to feed to rpm in order
to sign it. 

 Ain't it fun?
"""


import pexpect
import commands
import sys
import os
import gnupg


hostname = commands.getoutput('hostname -f')

gpg = gnupg.GPG(use_agent=True)


# Take the first argument given to this script and find rpm files there:
pkgs = commands.getoutput('find %s -iname *.rpm | xargs' % sys.argv[1])
pkgs = pkgs.split(' ')

# keychain contains the location of our GPG_AGENT:
keychain = "/home/buildmaster/.keychain/%s-sh-gpg" %  hostname

# Open keychain and read it
f = open(keychain, 'r')
gpg_agent = f.readline()

# Only interested in the middle bit of that file:
gpg_agent = gpg_agent.split("=")[1].split(';')[0]

# Add the result to the environment:
os.environ['GPG_AGENT_INFO'] = gpg_agent

# Use gpg_agent to decrypt our passphrase:
p = open('/home/buildmaster/.phrase.gpg', 'rb')      # opening the encrypted file...
m = gpg.decrypt_file(p)    # decrypt and place in a Crypt object
s=str(m)                   # Make that Crypt object a string 
p = s.strip()              # Strip that string of any cruft

# For every rpm we found, add our GPG sig using our retrieved passphrase.
for pkg in pkgs:
    child = pexpect.spawn("rpm --addsign %s" % pkg)
    child.expect("Enter pass phrase: ")
    child.sendline("%s\r" % p)
    child.status

