
OpenPanel BuildBot Documentation
================================
Author:  "Maarten Verwijs <contact@maartenverwijs.nl>"
Revision: 
rev2, Mon Jan 16 12:03:02 CET 2012


Useful Table of Information
---------------------------

[width="15%"]
|=======
|*Address* | *Node Type* | *Builds* | *Builds Using...* | *Runs As* | *Extra Groups* | *Comment*
|141.138.195.13 | Master |- | - | buildmaster | - | -
|141.138.195.13 | Slave | Debian/Ubuntu | - | root | - | Slave for testing and PostProcessing
|141.138.195.186 | Slave | Debian/Ubuntu | pbuilder | root | - | -
|141.138.195.185 | Slave | RHEL | mock | buildslave | mock | -
|=======

BuildBot is a master-slave setup. It has one master and three slaves. 

The following table tries to explain some of the differences between the master
and slaves. 

Nightly Builds end up here: 141.138.195.13/dev

Release Builds end up here: 141.138.195.13/stable

Daily Usage
-----------

Checking Nightly Builds
~~~~~~~~~~~~~~~~~~~~~~~
* Go to the consolde view of the webinterface of the buildmaster: http://141.138.195.13:8010/console
* Check for any non-green bulbs. 
* Randomly check any of the green (supergreen!) bulbs. Click through till you
  reach the actual buildlog. 
* Verify that the +Build Properties+ make sense. 
* Check the +stdio+ of the most important buildstep (probably the step before the +uploading+  step).


Starting a Manual Build
~~~~~~~~~~~~~~~~~~~~~~~

There are two ways of starting a manual build. One is through the webinterface.
The other using the commandline (which actually triggers a build using the
webinterface).


Using the WebInterface
^^^^^^^^^^^^^^^^^^^^^^

* Go to the webinterface: http://141.138.195.13:8010/builders
* Pick out the builder you wish to get built. Or select multiple (scroll down a
  bit....)
* Click on the builder. 
* Click the _Force Build_ button.


Using the CLI
^^^^^^^^^^^^^
* Log into the _buildmaster node_ as user _buildmaster_. 
* Execute the following command: 

----
/home/buildmaster/buildbot-config/bin/post_build_request.py -u /change_hook/openpanel_hook --project BUILDERNAME
----

Where _BUILDERNAME_ is the name of the builder. Obviously.

Cancelling (Stopping) a Build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NOTE: There are many reasons for cancelling a build. It's easy to do, but
can also cause a lot of hurt. Use with caution. Better to simply let the build
fail.

That being said: In order to cancel a build, simply go to the build in the
webinterface (http://141.138.195.13:8010/), find the build and press the
_Cancel Build_ button. 

Known issue: cancelling a .deb build will result cruft left behind in
_/var/cache/pbuilder/build_. 

Since that location is a tmpfs mounted partition, it will cause subsequent
builds to fail due to insufficient diskspace. 

When cancelling a .deb build, make sure you unmount all binded mounts and remove
any content in _/var/cache/pbuilder/build_. 

Be carefull that you do not remove any files that are in use by another
buildprocess. 



Doing A Release
----------------

A new release has the following properties: 

* The resulting packages are signed.
* The resulting packages are placed in the 'stable' repository (/srv/repository-stable). 
* The versioning is more concise / shorter.

In order to start building a release, all that is needed is to give the
buildproperty 'release=true' to any builder. 

This can be done in two ways: 

. Webinterface
. Commandline

Furthermore, this can be done for a single builder or for the all builders at
once. 

NOTE: Before anything related to releasing, make sure that GPG and SSH agents
work nicely by running _gpg-init.sh_ prior to _release.sh_. 


Single Builder
~~~~~~~~~~~~~

For a single builder, use one of the following methods.


Webinterface
^^^^^^^^^^^^

Webinterface: Surf to the webinterface and give the 'release' 'true'
as a property name and value in the 'Force Build' form, e.g.:  

 http://141.138.195.13:8010/builders/Apache2.module_ubuntu_10.04_amd64

Commandline
^^^^^^^^^^^^

Alternatively, use the commandline. Like so:

----
 /home/buildmaster/buildbot-config/bin/post_build_request.py -u /change_hook/openpanel_hook -p '{"release": "true"}' --project coreval_debian_6_amd64
----

All Builders
~~~~~~~~~~~~

If a release build is needed for all available builders, there are two ways to
go about that: 

. Webinterface
. Commandline

Webinterface
^^^^^^^^^^^^

. Surf here: http://141.138.195.13:8010/builders
. Scroll to the bottom
. Fill in the _Force All Builds_ Form and hit the correct button. 


Commandline
^^^^^^^^^^^

I've written a small script that uses the +post_build_request.py+ script to
initiate a release build of all OpenPanel projects for all supported
distributions. 

Use it by logging into the buildbot master as _buildmaster_ and run:

----
 ~/buildbot-config/bin/release.sh
----

NOTE: There is a 5 second delay for every added build in order to make sure
that buildbot builds in the correct order. 


Managing BuildBot
-----------------

There are several tasks that may need to be performed on a daily or weekly
basis. 

NOTE: In order to perform actions on a buildbot system,  you need to login to
the server using the correct user. This differs per system.  Please check the
table above if you're not sure. 

NOTE: In order to perform any action on a buildbot system, you need to have the
correct ENV. Make sure that you source _buildbot/opt/bin/activate_ (Should be
in the .bashrc of the user you logged into the machine as). 

On the Buildbot Master:

* Log into the master as +buildmaster+.
* The BuildBot environment is automatically set in .bashrc
* The GPG and SSH agents are automatically set in .bashrc

On Debian/Ubuntu Slaves:

Log into the slave as root and run:

-----
cd /opt/buildbot/sandbox
source bin/activate
----

On RHEL Slaves: 

Log into the slave as user _buildslave_ and run: 

-----
source bin/activate
----


Buildbot Slaves 
~~~~~~~~~~~~~~~

The Buildbot slaves are rather maintenance free.

Starting / Stopping Builbot Slaves
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Run: _buildslave start $SLAVENAME_ (e.g. _buildslave start debian6_amd64_)

Or replace _start_ with _stop_ in order to stop it. 

Buildbot Master
~~~~~~~~~~~~~~~

The most common tasks are: 

* stop/start/restarting the buildmaster
* testing a new master.cfg
* Re-initializing GPG and SSH agents. 
* Checking logfiles, configurations, diskspace

Checking the sanity of a new configuration: 

----
 cd ~/buildbot && buildbot checkconfig master
----

This should yield the result:

-----
 Config file is good!
-----


BuildSlave upload their results into /tmp/incoming. There, they are processed
by MasterShellCommands (see +master.cfg+). When no builds are running, the
/tmp/incoming should not contain any .deb or .rpm files. So this command should
yield no result: 

 find /tmp/incoming -iname *.deb


Installation and Setup
----------------------

This describes the actual setup and installation of the Buildbot environment
for OpenPanel. 


Design Overview
~~~~~~~~~~~~~~~~

Buildbot works in a master/slave setup. 

image:overview.png[Buildbot basics]

The master tells the slaves what buildsteps to step through. They pass
the results (files, successes or failures) back to the master.

Buildbot -like most of the continuous integration platforms available- makes
the assumption that there are only a few different code repositories per
project. OpenPanel, however, has more than 70.

The fact that BuildBot is written in Python and therefor extensible makes it
possible to manage this ammount.

However, the previous design made a 'factory' for every combination of the
following:

* Distribution
* Distributionversion
* Distribution Architecture (hardware)
* Component
 
This left us with 4300+ factories. Instead, I opted for the creation of 1
factory per distro_distroversion_architecture. Within these factories, all
OpenPanel components are built for this architecture. 

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
* Builder - The worker drone. Recieves a projectname from a Scheduler that
  needs to be built. Determines a BuildSlave and sends required BuildSteps to
  that BuildSlave.
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
~~~~~~~~~~~~~~~~~~~

Unfortunatly, the official manual is not a good guide here. It makes quite a few assumptions
that will bite. Please follow these steps instead. 

There are two major components that are to be installed: 

. Buildbot Master (aka buildmaster)
. Buildbot Slave (aka buildslave)

NOTE: The buildmaster should ab-so-lu-te-ly not be run as root, since some
 components may fail silently (Bad Thing).


Buildmaster Install
^^^^^^^^^^^^^^^^^^^

Install a stock Debian 6.0 AMD64 machine.

Add the following packages:

------------------------
apt-get install python-dev build-essential python-virtualenv devscripts mercurial
apt-get build-dep python-mysqldb
# Also rpm stuff:
apt-get install rpm elfutils rpm-i18n createrepo 
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
pip install MySQL-python
------------------------

NOTE: There is a slight API change in pyasn1 > 0.0.13b that breaks Buildbot. 

Now create your master buildbot environment. 

------------------------
cd ~/buildbot
buildbot create-master master
------------------------
 
Clone the buildbot-config Mercurial repository:

------------------------
cd ~/
hg clone http://hg.openpanel.com/buildbot-config
------------------------

Link the master.cfg from the local hg copy to master/master.cfg:

------------------------
ln -s /home/buildmaster/buildbot-config/master.cfg /home/buildmaster/buildbot/master/master.cfg
------------------------

And start the master: 

------------------------
buildbot start master
------------------------

BuildMaster umask:
++++++++++++++++++

The umask of the BuildMaster is clobbered by Twistd and set to 077. Very
strict. I did not find a nice way to fix this other than to edit twistd's
files. A bug was reported that would hopefully address the issue:

http://trac.buildbot.net/ticket/2169


Edit this file:
./lib/python2.6/site-packages/Twisted-11.1.0-py2.6-linux-x86_64.egg/twisted/scripts/_twistd_unix.py

Look for lines like: 

----
if daemon and umask is None:
            umask = 077
----

and alter it to: 

----
if daemon and umask is None:
            umask = 022
----

You will have to restart the daemon in order for this change to take effect: 


----
buildbot stop  master
buildbot start  master
----


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

It kinda looks like this: 

image:buildbot_auto_reconfig.png[BuildBot Master Auto-reconfig]

To set this up first ensure the hooks are in place inside the hgrc file
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

Build Hooks (change_hook)
^^^^^^^^^^^^^^^^^^^^^^^^^

In order to be able to remotely trigger a build (from HG hooks, for example),
buildbot can be enabled to handle this via POST requests. How these requests
are handled can be configured through enabling hooks. 

The default hook (+base+) assumes that one repository is used and requires a
repository to be handed to the hook before the hook will trigger a build. Even
worse: the repository overrides any other setting of the repository. This
breaks the way we do things. 

In order to remedy that, we removed the setting of the repository from +./opt/lib/python2.6/site-packages/buildbot-0.8.5-py2.6.egg/buildbot/status/web/hooks/base.py+ and renamed it +openpanel_hook.py+. 

When installing a BuildMaster, the +openpanel_hook.py+ must be placed in
+$BUILDBOTHOME/buildbot-0.8.5-py2.6.egg/buildbot/status/web/hooks/+

+~/buildbot-config/bin/post_build_request.py+ was
also changed to leave out the requirement for specifying a repository. 

The +post_build_request.py+ can be used from the commandline or an HG-hook to
trigger a build.



Extra Master Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^

Several of the BuildSteps are performed on the BuildMaster itself. Some of the
se require extra software / configuration. 

Debian Repository
+++++++++++++++++

The newly created .deb packages will require a repository to be placed into.

----
mkdir /srv/repository
----

Make sure that +buildmaster+ and apache (www-data) can write to the repository: 

----
chown buildmaster:www-data -R /srv/repository
----

Install +reprepro+ to handle the creation of the APT repository:

----
apt-get install reprepro gnupg-agent
----

Place the +hooks+ folder (found in HG:/buildbot_config/hooks) in
+/srv/repository/hooks+.

When Debian packages get built by BuildBot, those hooks will automatically get
triggered.


APT expects certain files to exist when connecting to a repository. Those files
do not come into existense until this command is run: 

----
reprepro -b /srv/repository export
----



Creating Slaves
~~~~~~~~~~~~~~~

Creating slaves consists of the following steps:

* Installing the buildbot-slave software on a machine ; 
* Configuring a username/password on the slave ; 
* Configuring that same username/password on the master.



Enterprise Linux (RHEL, CentOS, ...) Specific 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Installing Mock
+++++++++++++++

Since our CentOS Slave is to build RPM packages, it needs the infrastructure to
do that. 

Mock is used to do that. It is somewhat similar to pbuilder, but there are
differences.

* Mock has to be run as a non-privileged user that is part of the 'mock' group,
  whereas pbuilder can simply be run as root. 
* Mock cannot/willnot use tarballs. Instead, it uses a cache system with a
  freshness parameter (default=15 days). 

Requirements:

----
yum install mock
----

* pull the mock configuration files from

----
 http://hg.openpanel.com/buildbot-config/mock
----

Add the user that mock will run as:

----
adduser buildslave
----

Make sure that user is in the correct group:

-----
 adduser buildslave to group mock
-----

Your buildslave should now be able to run mock processes. 


Debian Specific
^^^^^^^^^^^^^^^

In order to build Debian packages (for both Debian and Ubuntu), we need to have
a BuildSlave running on Debian. The BuildSlave will be using +pbuilder+ for the
creation of .deb packages.

Therefore install pbuilder: 

-----
apt-get install pbuilder
-----

When +pbuilder+ is run it -by default- does not do an +apt-get update+, which
is annoying. This is solved by using a +hook+ to tell pbuilder to run the
update. 

Copy the +hook+ folder from hg:/buildbot_config/hook to +/srv/hook+. BuildBot's master.cfg is configured to
use that folder when triggering pbuilder.

The BuildSlave on Debian is perfectly able to run as root. In fact, pbuilder
prefers it, so on Debian (unlike RHEL), we're going to run the Slave as root.

Since we use Mercurial, make sure it is installed as well: 

-----
apt-get install mercurial
-----

NOTE: The tarballed chroots that pbuilder uses all point their sources.list to
the IP of the current buildbotmaster. Should that IP change, steps need to be
taken to update those sources.lists.

Generic BuildSlave Install Steps
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that we've covered the Linux distro specific dependencies, we can continue
with the generic steps needed to install the BuildBot Slave software.

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

NOTE: Remember to run as the correct user depending on your distro
(Debian=root, Centos=buildslave).


Signing RPM packages
^^^^^^^^^^^^^^^^^^^^

We need to be able to sign packages (RPM + DEB) with a key, either with or
without a passphrase. 

NOTE: This is performed on the BuildMaster, not on a BuildSlave.

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

Make sure .gnupg/gpg.conf reads:

----
use-agent
----

And that .gnupg/gpg-agent.conf reads something like: 

-----
pinentry-program /usr/bin/pinentry
default-cache-ttl 31449600
max-cache-ttl 31449600
-----

As root:

-----
 rpm --import RPM-GPG-KEY-yourname
-----

In uses a variable in a file called +rpmmacros+ to know which key to use when
signing. Usually, this file is in the homedir of the user that does the
signing. However, with buildbot I could not get this to work. To resolve this,
I used another file. 

As user +buildslave+:

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

As said before: we want to use a passphrase, with a GPG agent, but RPM does not
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

Before you can sign RPM packages, you need to make sure that the GPG agent is
running and that the passphrase has been cached. 

Steps to follow (very precisely)

* Kill all gpg agents with 'keychain --stop'. 
* Start new gpg agents with 'keychain'. This will also create a file in
 /home/buildmaster/.keychain that needs to be sourced.
* Source the file. 
* Decrypt an encrypted file so the gpg-agent can cache the passphrase. 

You also need to add the ssh-key to the ssh-key-agent that was started by
keychain. 

----
ssh-add .ssh/id_rsa
----



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
Are you running the master buildbot process as root? Don't.

RPM Packages are not getting signed!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Log in as 'buildmaster'.

Is the agent still running? 

----- 
ps aux | grep gpg-agent
-----

----
. .keychain/*-sh-gpg
----

Try to decrypt the file .phrase.gpg:

----
gpg -d .phrase.gpg
----

If you get prompted for a passphrase, the TTL probably expired. 

Still doesn't work?

Get keychain to kill all agents:

----
keychain --stop
----

And restart keychain: 

----
keychain
----

Repeat: 

----
. .keychain/*-sh-gpg
----

Try to decrypt the file .phrase.gpg (again):

----
gpg -d .phrase.gpg
----

The gpg-agent should now have cached your creds for the time specified in the
+.gnupg/gpg-agent.conf+.


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
* http://purplefloyd.wordpress.com/2009/02/05/signing-deb-packages/
* http://how-to.linuxcareer.com/creating-a-package-repository-on-linux--fedora-and-debian


Known Issues: 
------------

* A new repository should at least have a Packages.gz, as pbuilder does an
apt-get update and expects it to work. Be sure to run 'reprepro -b
/srv/repository export' when setting up your repository.


* There is no way to have a use a Property that has been set during a BuildStep,
other than as a Property. Sometimes I think it would be handy to use, e.g. the
result of 'cat /etc/debian_version' to determine my next BuildStep. This is not
possible.

Order is important. In order for the latest version of opencore to work, it
needs an installation of the latest version of libgrace. Therefor, libgrace
needs to be installed, packaged, uploaded to apt/yum repo, etc.... Only then
can opencore building start.

* Sometimes a build will fail due to the fact that you just successfully did a
  build. The result of the build is a package in the repository. When you do a
  rebuild, you first need to remove the package from the repo, else the build
  will fail. 


As buildmaster on the BuildMaster server:

----
 # list matching packages:
 reprepro -b /srv/repository/  listfilter squeeze "Package (% libgrace*)"

 # remove matching packages:
 reprepro -b /srv/repository/  removefilter squeeze "Package (% libgrace*)"
----


