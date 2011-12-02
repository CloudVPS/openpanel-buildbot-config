
Buildbot
========
Author:  "Maarten Verwijs <contact@maartenverwijs.nl>"
Revision: 
rev1, Tue Nov 29 11:02:11 CET 2011


About this document
------------------

This document describes how to setup and maintain buildbot for OpenPanel.
Buildbot is a framework that allows for the automation of fetching sourcecode,
compiling it, packaging it and presenting feedback for the developers. 

The goal is to provide a continuous integration platform for developers to
increase the speed of development and quality of code. 

The order of the document is as follows: 

* Design Overview
* Installation 
* Configuration
* Daily Usage
* Manipulation 

It should also have: 

* Details on all the buildsteps that are taken when doing a build.

Design Overview
---------------

In essence, buildbot works in a master/slave setup. 

Like so: 

image:design.png[Buildbot basics]

The master tells the slaves what buildsteps to step through. They pass
the results (files, successes or failures) back to the master.

Buildbot -like most of the continuous integration platforms available- makes
the assumption that there are only a few different code repositories per
project. OpenPanel, however, has more than 70.

The fact that BuildBot is written in Python and therefor extensible makes it
possible to manage this ammount.

However, the current design makes a 'factory' for every combination of the
following:

* Distribution
* Distributionversion
* Distribution Architecture (hardware)
* Component
 
Given the total number of those variables, our current BuildBot config is
handling about 4300+ different factories. 

This is not a Good Thing, IMHO, and should be addressed. 

Buildbot Terminology
~~~~~~~~~~~~~~~~~~~~

There are a couple of buildbot-specific terms that are useful to know. 

* BuildMaster - This is the software you will interface with the most. It
  handles the logic of the CIS.
* BuildSlave - The worker-drone. There can be many slaves to a single
  BuildMaster. 
* VCS - Version Control System (E.g. Mercurial)
* Change - A notification of a change in the sourcetree that requires action
  from BuildBot. The manner by which the notification is done may vary. We use
  ChangeHook.
* ChangeHook - Triggers a Change by commiting a HTTP POST to BuildBot.
* Scheduler - When triggered (internally or remotely), this will schedule a
  build with a Builder. You will not find a reference to Schedulers in the
  webinterface. 
* Builder - Recieves a projectname from a Scheduler that needs to be built. 
  Determines a BuildSlave and sends required BuildSteps to that BuildSlave.
* BuildStep - Steps needed to complete a build (unpack, configure, make, make
  install. The guts of the system)

Other terms: 

* Mock - Software used on RHEL-based distros to create .rpms in a chroot
  environment.
* Pbuilder - Sort of kind of same as +mock+, only for Debian (+derivatives).
* reprepro - Creates a repository of .deb files to be used with APT.
* createrepo - Creates a repository of .rpm files to be used with YUM. 
* keychain - Enable re-usage of GPG agents between logins. 


Installing BuildBot
-------------------

Unfortunatly, the official manual is not a good guide here. It makes quite a few assumptions
that will bite. Please follow these steps instead. 

There are two major components that are to be installed: 

. Buildbot Master (aka buildmaster)
. Buildbot Slave (aka buildslave)

NOTE: The buildmaster should ab-so-lu-te-ly not be run as root, since some
 components may fail silently (Bad Thing).


Buildmaster Install
~~~~~~~~~~~~~~~~~~

Install a stock Debian 6.0 AMD64 machine.

Add the following packages:

------------------------
apt-get install python-dev build-essential python-virtualenv devscripts mercurial
------------------------

Add a user to run buildbot processes as. 


------------------------
adduser --system buildmaster
------------------------

Switch to that user:

------------------------
su - buildmaster
------------------------

NOTE: From now on it is *crucial* to execute all commands on the buildmaster as
user 'buildmaster'!

------------------------
mkdir buildbot && cd buildbot
virtualenv --no-site-packages opt
source opt/bin/activate
------------------------

This should work:

------------------------
easy_install buildbot==0.8.5
------------------------

NOTE: It is crucial to specify the exact version, else easy_install (and pip)
will install the 'latest and greatest'. Doing that could break compatibility with
the current setup. This is not mentioned in the official manual.

Install the following dependencies if you want to enable a man-hole for easy
debugging:

------------------------
pip install pycrypto==2.4.1
pip install pyasn1==0.0.13b      # <-- last known good.
------------------------

Now create your master buildbot environment. 

------------------------
cd ~/buildbot
buildbot create-master master
------------------------
 
Clone the buildbot-config Mercurial repository:

------------------------
hg clone http://hg.openpanel.com/buildbot-config
------------------------

Link the master.cfg from the local hg repo to master/master.cfg

------------------------
ln -sf  /home/buildmaster/buildbot-config/master.cfg /home/buildmaster/buildbot/master/master.cfg
------------------------

And start the master: 

------------------------
buildbot start master
------------------------


Start Master @reboot
^^^^^^^^^^^^^^^^^^^^

In order to have the buildbot-master to survive a reboot, add this cronjob:

------------------------
@reboot . /home/buildmaster/buildbot/opt/bin/activate && cd buildbot && buildbot start master
------------------------

Auto-Reloading Master
^^^^^^^^^^^^^^^^^^^^^

Whenever we're going to update the HG-repo of the buildbot configs, we want to
the changes to automatically be applied on the running buildbot-master. 

This is done through the use of hg-hooks and cron. 

First: ensure the hooks are in place inside the hgrc file
(/home/buildmaster/buildbot-config/.hg/hgrc):

------------------------
[hooks]
update = /home/buildmaster/buildbot-config/bin/reconfig-buildmaster
incoming = hg update
------------------------

This will make sure that everytime there an +hg pull+ is done, it is followed
by an +hg update+ to fetch the changes. 

And everytime an +hg update+ is done, it is followed by a reconfigure of the
buildmaster. 

Now all we need to do is automate that a bit via cron. So add this cronjob:

------------------------
* * * * * cd /home/buildmaster/buildbot-config && hg pull  > /dev/null 2>&1
------------------------

We now have a running working BuildBot Master running on port 8010 and waiting
for slaves to connect to it. 





Creating Slaves
~~~~~~~~~~~~~~~

Creating slaves consists of the following steps:

* Installing the buildbot-slave software on a machine ; 
* Configuring a username/password on the slave ; 
* Configuring that same username/password on the master.



Enterprise Linux (RHEL, CentOS, ...)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First we need to enable EPEL in order to install python-virtualenv.

--------------
su -c 'rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm'
--------------

And install python-virtualenv

----------------
yum install python-virtualenv
----------------

You will also need some/all of the development tools. 

----------------
yum groupinstall 'Development Tools'
----------------


Create a place to install the buildbot-slave: 

---------------
mkdir /opt/buildbot
virtualenv --no-site-packages sandbox
source sandbox/bin/activate
easy_install buildbot-slave==0.8.5
---------------

NOTE: Again: be specific in your versions.

Now that we have the slave software installed, we can create a slave with it:

---------------
cd sandbox/
buildslave create-slave centos5 141.138.195.186 centos5-slave pass
---------------

NOTE: If you wish to change the password later on, that is possible in the
buildbot.tac file. 

Starting the slave:

---------------
source sandbox/bin/activate
cd sandbox/
buildslave start $VIRTUAL_ENV/centos5
---------------

If you surf to buildmaster:8010/ you should see your slave connecting.

Debian
~~~~~~

In order to build Debian packages (for both Debian and Ubuntu), we need to have
a BuildSlave running on Debian. The BuildSlave will be using +pbuilder+ for the
creation of .deb packages.


Therefore install pbuilder: 

-----
apt-get install pbuilder
-----

The BuildSlave on Debian is perfectly able to run as root. In fact, pbuilder
prefers it. So we shall do that then.


NOTE: The tarballed chroots that pbuilder uses all point their sources.list to
the IP of the current buildbotmaster. Should that IP change, steps need to be
taken to update those sources.lists.


Configuring Buildbot
--------------------

(FIXME)


BuildSteps
----------

The following is some detail on the actual buildsteps. More information can
also be found in the comments of the +master.cfg+ file.

Building RPM Packages:
~~~~~~~~~~~~~~~~~~~~~~

Mock is not Pbuilder. But it is somewhat similar. A few differences of note: 

* Mock has to be run as a non-privileged user that is part of the 'mock' group,
  whereas pbuilder can simply be run as root. 
* Mock cannot/willnot use tarballs. Instead, it uses a cache system with a
  freshness parameter (default=15 days). 


Requirements:
* install mock
* pull the mock configuration files from
 http://hg.openpanel.com/buildbot-config/mock
* adduser mock
* adduser buildslave to group mock

Mock: 
* yum -y install mock
* make a tarball of hg checkout. Look in .spec file for what name .spec is
  looking for (head $specfile | grep ^Name:)

adduser -g buildslave mock

mock --clean
mock --init
hg clone http://hg.openpanel.com/grace
rpmbuild -bs  rpm/libgrace.spec --define "_sourcedir `pwd`"

mock --buildsrpm --spec=rpm/opencore.spec 

buildrpm --define "_sources /foo/bar"


Signing RPM packages
~~~~~~~~~~~~~~~~~~~~

We want our nightly built RPMs to be signed automatically with a development
GPG key. 

This brings some twists and glitches 

* The buildmaster is to the signing of the RPM packages. However: the
  buildmaster is a Debian machine. 
* In order not to enter a passphrase everytime we sign an RPM, we need a
  GPG agent. 
* RPM does NOT support GPG agents. 
* When executing shellcommands, Buildbot is not actually opening an interactive
  shell. 


First we're going to need GNUPG

----------
apt-get install gnupg
---------

We will also need rpm:

-------
apt-get install rpm
-------

Login as the user +buildmaster+. Do NOT use +su -+, but actually create a new
session like logging in with ssh. 

-----
mkdir .gnupg
-----

Generate a key and give logical answers. Possibly consult this link:
http://fedoranews.org/tchung/gpg/

------
gpg --gen-key
-------


Verify that the key generation works: 

------
gpg --list-keys
------

In order to make RPM aware of our key, we need to import the key into RPM. In
order to do that, we must first 'export' our key from GPG. Like so: 

-----
 gpg --export -a 'Name Of Your Key' > RPM-GPG-KEY-yourname
-----

As root:

-----
 rpm --import RPM-GPG-KEY-yourname
-----

In uses a variable in a file called +rpmmacros+ to know which key to use when
signing. Usually, this file is in the homedir of the user that does the
signing. However, with buildbot I could not get this to work. To resolve this,
I used another file. 

As root:

-----
mkdir /etc/rpm

cat > /etc/rpm/macros <<EOF
%_signature gpg
%_gpg_path ~/.gnupg
%_gpg_name OpenPanel Development Key <dev@openpanel.com>
EOF
-----

Now, in order to solve the biggest issue (passing the passphrase), we need to
do some loopy hacking in order to stay somewhat secure. 

As said before: we want to use a passphrase, with a GPG agnet, but RPM does not
support this. When signing an .rpm, RPM will *always* ask for a passphrase.
Thanks RedHat!

Now, +expect+ can be used to feed the passphrase to +rpm+ when it asks for it.
However, we do not want our passphrase plaintext in a file. So, we're going to
do the following: 

. Put our passphrase in a plaintext file. 
. Encrypt that using our own Development key (and removing the unencrypted
file, obviously).
. Start up a GPG agent with a limited time-to-live.
. Give our passphrase to the agent. 
. Write a python script that will use the GPG agent to decrypt the file, read the passphrase, start rpm and pass the passphrase when requested by rpm. 


So, place your passphrase in a file called: '~/.phrase' and encrypt it like so: 

-----
gpg -e ~/.phrase
-----

When prompted for the name of a key, reply:

-----
Dev
-----

and hit enter. 

Remove the unencrypted version of the file: 

----
rm .phrase
----

Test that you can decrypt the file:

----
gpg -d .phrase.gpg
----

This will ask you for the passphrase. After entering it, you should see the
decrypted contents of the .phrase.gpg file (oddly enough, this is also your
passphrase...).

Now it gets complicated. We're now going to start a daemon that will cache the
passphrase for a set timeperiod, so you (or buildbot) don't have to enter it
every time gpg is called. 

Install and start +keychain+

-----
apt-get install keychain
keychain
-----

Keychain will start gpg-agent and place the details on how to connect to the
agent in '~/.keychain'. Looking in that folder you should see something like
this: 

-----
buildmaster@dev-openpanel2:~$ ls ~/.keychain
dev-openpanel2.xlshosting.net-csh      dev-openpanel2.xlshosting.net-fish-gpg
dev-openpanel2.xlshosting.net-csh-gpg  dev-openpanel2.xlshosting.net-sh
dev-openpanel2.xlshosting.net-fish     dev-openpanel2.xlshosting.net-sh-gpg
-----

We're intested in the 'dev-openpanel2.xlshosting.net-sh-gpg' file. We're going
to source it: 

-----
source dev-openpanel2.xlshosting.net-sh-gpg
env | grep GPG  # <--- this should output something!
-----


The gpg-agent will remember the passphrase for some time. That time is the
time-to-live of the passphrase. It is configured here:

----
$HOME/buildmaster/.gnupg/gpg-agent.conf
----

Now, the next time you decrypt a file you will be asked for a passphrase. This
time, gpg will hand the phrase to the agent. There it will be cached for as
long as is defined in '~/.gnupg/gpg-agent.conf'. 

So the second time you decrypt a file, the cached phrase will be used to
decrypt. 

To test, run a decrypt. Twice. 

----
gpg -d .phrase.gpg    # <--- enter your phrase
gpg -d .phrase.gpg    # <--- no phrase needed to get entered!
----

So - we now have a fairly secure way to fetch our phrase. Simply connect to the
gpg-agent and decrypt the +.phrase.gpg+ file. 

We can use that to feed rpm using a python script!

-----

#!/usr/bin/env python
# This is 'rpmsign.py'
#
# Ain't it fun?

import pexpect
import commands
import sys
import os
import gnupg

gpg = gnupg.GPG(use_agent=True)

# Take the first argument given to this script and find rpm files there:
pkgs = commands.getoutput('find %s -iname *.rpm | xargs' % sys.argv[1])
pkgs = pkgs.split(' ')

# keychain contains the location of our GPG_AGENT:
keychain = "/home/buildmaster/.keychain/dev-openpanel2.xlshosting.net-sh-gpg"

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

-----

NOTE: Don't test by su'ing to user buildmaster. This does not work. Instead, ssh into
the machine as the user 'buildmaster'. 

NOTE: It would be so much nicer if the python-code above were incorporated in
master.cfg as special BuildStep!

As you can see in the script above, python imports a module called gnupg. We
need to install that, as root, on system level. 

I hate that as much as you do.

So as root do:

----
pip install python-gnupg
----



BuildBot Usage 
--------------

Start a GPG Agent
~~~~~~~~~~~~~~~~~

Steps to follow (very precisely)

* Kill all gpg agents with 'keychain --stop'. 
* Start new gpg agents with 'keychain'. This will also create a file in
 /home/buildmaster/.keychain that needs to be sourced.
* Source the file. 
* Decrypt an encrypted file so the gpg-agent can cache the passphrase. 


Start BuildBot Master
~~~~~~~~~~~~~~~~~~~~~

This should have happened during boot time, but if it didn't:

Switch to user +buildmaster+

----
su - buildmaster
---- 

change to the buildbot directory:

----
cd buildbot
----

Source the BuildBot virtualenv:

----
source opt/bin/activate
----

and run:

----
buildbot start master
----

This should start the master just fine. 




// ----- end of RPM Signing


What to do when...
-----------------

Pypi.python.org is down.
~~~~~~~~~~~~~~~~~~~~~~~~

If pypi.python.org is down, do this:

Add this stanza to '~/.pydistutils.cfg':


-----------------------------
[easy_install]
index_url = http://d.pypi.python.org/simple
-----------------------------

From: http://jacobian.org/writing/when-pypi-goes-down/

Buildbot IRCbot will not connect
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Are you running the mster buildbot process as root? Don't

External References 
-----------------

* http://www.jacobian.org/writing/buildbot/ci-is-hard/
* http://icedtea.classpath.org/hg/buildbot/file/51a64788c03b/icedtea/master.cfg
* http://buildbot.net/buildbot/docs/current/full.html
* http://jacobian.org/writing/when-pypi-goes-down/
* http://backreference.org/2011/10/08/buildbot-in-5-minutes/
* https://github.com/jacobian/django-buildmaster/blob/master/djangobotcfg/buildsteps.py
* http://buildbot.net/buildbot/docs/0.8.1/full.html#BuildStep-URLs (search for 'Build Step Index')
* http://hg.openpanel.com/autobuilder/file/da3c80144ff2/build.py
* http://stolennotebook.com/anthony/2007/01/19/18/
* http://backreference.org/2011/10/08/buildbot-in-5-minutes/
* http://fedoranews.org/tchung/gpg/
* https://www.redhat.com/archives/rpm-list/2002-August/msg00074.html - no batch  mode signing for you!
* http://www.linux-archive.org/centos/463658-howto-batch-sign-rpm-packages.html

# This is not the hard part.

New tech: 

pip/easy_install/virtualenv for python, and what that means.
reprepro
buildd
hg

Known tech:
createrepo
pbuilder

TODO:
----

This still needs proper documenting: 

* reprepro
* slave requirements: 
** hooks folder

* post_build_request.py needs python-simplejson installed on centos5
* post_build_request.py: describe the why of this. (hg hook needs  buildbot installed on same machine as hg repo)



Known Issues: 
------------

a new repository should at least have a Packages.gz, as pbuilder does an
apt-get update and expects it to work. There should be some non-failing

chown the repo. Mention umask!

There is no way to have a use a Property that has been set during a BuildStep,
other than as a Property. Sometimes I think it would be handy to use, e.g. the
result of 'cat /etc/debian_version' to determine my next BuildStep. This is not
possible.

Order is important. In order for the latest version of opencore to work, it
needs an installation of the latest version of libgrace. Therefor, libgrace
needs to be installed, packaged, uploaded to apt/yum repo, etc.... Only then
can opencore building start.

