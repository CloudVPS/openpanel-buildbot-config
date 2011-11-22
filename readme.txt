

TODO:
----

This still needs proper documenting: 
* reprepro
* slave requirements: 
** hooks folder


Setup BuildMaster
-----------------

Install a stock Debian 6.0 machine.

Add the following packages:

[quote]
------------------------
apt-get install python-dev build-essential python-virtualenv devscripts
------------------------

Add a user to run buildbot processes as. Slaves should be able to run as root
though. 

[quote]
------------------------
adduser --system buildmaster
------------------------


[quote]
------------------------
su - buildmaster
mkdir buildbot && cd buildbot
virtualenv --no-site-packages opt
source opt/bin/activate
------------------------

This should work:
[quote]
------------------------
easy_install buildbot==0.8.5
------------------------

Be specific as to what version you are going to install. This is NOT reflected
in the buildbot tutorial. 

So: 
[quote]
------------------------
pip install pycrypto==2.4.1
pip install pyasn1==0.0.13b      # <-- last known good.
------------------------



[quote]
------------------------
cd ~/buildbot
buildbot create-master master
------------------------
 
Link the master.cfg from the local hg repo to master/master.cfg
[quote]
------------------------
ln -sf  /home/buildmaster/buildbot-config/master.cfg /home/buildmaster/buildbot/master/master.cfg
buildbot start master
------------------------

Done.






Creating Slaves
---------------

Reloading master upon commit to buildbot-config repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the buildmaster, have a local clone of the hg repository. 

[quote]
------------------------
hg clone http://hg.openpanel.com/buildbot-config
------------------------

Add a hook to /home/buildmaster/buildbot-config/.hg/hgrc

[quote]
------------------------
[paths]
default = http://hg.openpanel.com/buildbot-config

[hooks]
incoming = /home/buildmaster/buildbot-config/bin/reconfig-master
------------------------


* Set a cronjob to run hg pull && hg up regularly.




Enterprise Linux (RHEL, CentOS, ...)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First we need to enable EPEL in order to install python-virtualenv.
[quote]
--------------
su -c 'rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm'
--------------

And install python-virtualenv
[quote]
----------------
yum install python-virtualenv
----------------


You will also need some/all of the development tools. 

[quote]
----------------
yum groupinstall 'Development Tools'
----------------

Installing Buildbot
-------------------

[quote]
---------------
mkdir /opt/buildbot
virtualenv --no-site-packages sandbox
source sandbox/bin/activate
easy_install buildbot-slave==0.8.5
---------------

Creating the slave:
[quote]
---------------
cd sandbox/
buildslave create-slave centos5 141.138.195.186 centos5-slave pass
---------------

Starting the slave:

[quote]
---------------
source sandbox/bin/activate
cd sandbox/
buildslave start $VIRTUAL_ENV/centos5
---------------


Building RPM Packages:
---------------------

Requirements:
* install mock
* adduser mock
* adduser buildslave to group mock

Mock: 
* yum -y install mock
* make a tarball of hg checkou. Look in .spec file for what name .spec is
  looking for (head $specfile | grep ^Name:)

adduser -g buildslave mock

mock --clean
mock --init
hg clone http://hg.openpanel.com/grace
rpmbuild -bs  rpm/libgrace.spec --define "_sourcedir `pwd`"

mock --buildsrpm --spec=rpm/opencore.spec 

buildrpm --define "_sources /foo/bar"



What to do when...
-----------------

Pypi.python.org is down.
~~~~~~~~~~~~~~~~~~~~~~~~

If pypi.python.org is down, do this:

Add this stanza to '~/.pydistutils.cfg':

[quote]
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
