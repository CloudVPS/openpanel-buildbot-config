#!/usr/bin/env python
import httplib, urllib
import getopt
import optparse
import textwrap
import getpass
import os

# Find a working json module.  Code is from
# Paul Wise <pabs@debian.org>:
#   http://lists.debian.org/debian-python/2010/02/msg00016.html
try:
    import json # python 2.6
except ImportError:
    import simplejson as json # python 2.4 to 2.5
try:
    _tmp = json.loads
except AttributeError:
    import warnings
    import sys
    warnings.warn("Use simplejson, not the old json module.")
    sys.modules.pop('json') # get rid of the bad json module
    import simplejson as json

# Make a dictionary with options from command line
def buildURL( options ):
    urlDict = {}
    if options.who:
        who = options.who
    else:
        who = getpass.getuser()
 
    urlDict['who'] = who
    
    if options.files:
        urlDict['files'] = json.dumps(options.files)

    if options.comments:
        urlDict['comments'] = options.comments
    else:
        # A comment is required by the buildbot DB
        urlDict['comments'] = 'post_build_request submission'

    if options.links:
        urlDict['links'] = json.dumps(options.links)

    if options.revision:
        urlDict['revision'] = options.revision

    if options.when:
        urlDict['when'] = options.when

    if options.branch:
        urlDict['branch'] = options.branch

    if options.category:
        urlDict['category'] = options.category

    if options.revlink:
        urlDict['revlink'] = options.revlink

    if options.properties:
        urlDict['properties'] = json.dumps(options.properties)

    if options.repository:
        urlDict['repository'] = options.repository

    if options.project:
        urlDict['project'] = options.project

    return urlDict

def propertyCB(option, opt, value, parser):
    pdict=eval(value)
    for key in pdict.keys():
        parser.values.properties[key]=pdict[key]

__version__='0.1'

description=""

usage="""%prog [options]

This script is used to submit a change to the buildbot master using the
/change_hook web interface. Options are url encoded and submitted
using a HTTP POST. The repository and project must be specified.

This can be used to force a build. For example, create a scheduler that
listens for changes on a category 'release':

releaseFilt    = ChangeFilter(category="release")
s=Scheduler(name="Release", change_filter=releaseFilt,
            treeStableTimer=10,
            builderNames=["UB10.4 x86_64 Release"]))
c['schedulers'].append(s)

Then run this script with the options:

--repostitory <REPOSTORY> --project <PROJECT> --category release
"""

parser = optparse.OptionParser(description=description,
                               usage=usage,
                               add_help_option=True,
                               version=__version__)

parser.add_option("-w", "--who", dest='who', metavar="WHO",
            help=textwrap.dedent("""\
            Who is submitting this request.
            This becomes the Change.who attribute.
            This defaults to the name of the user running this script
            """))
parser.add_option("-f", "--file", dest='files', action="append", metavar="FILE",
            help=textwrap.dedent("""\
            Add a file to the change request.
            This is added to the Change.files attribute.
            NOTE: Setting the file URL is not supported
            """))
parser.add_option("-c", "--comments", dest='comments', metavar="COMMENTS",
            help=textwrap.dedent("""\
            Comments for the change. This becomes the Change.comments attribute
            """))
parser.add_option("-l", "--link", dest='links', action="append", metavar="LINKS",
            help=textwrap.dedent("""\
            These are links for the source. 
            This becomes the Change.links attribute.
            """))
parser.add_option("-R", "--revision", dest='revision', metavar="REVISION",
            help=textwrap.dedent("""\
            This is the revision of the change. 
            This becomes the Change.revision attribute.
            """))
parser.add_option("-W", "--when", dest='when', metavar="WHEN",
            help=textwrap.dedent("""\
            This this the date of the change. 
            This becomes the Change.when attribute.
            """))
parser.add_option("-b", "--branch", dest='branch', metavar="BRANCH",
            help=textwrap.dedent("""\
            This this the branch of the change. 
            This becomes the Change.branch attribute.
            """))
parser.add_option("-C", "--category", dest='category', metavar="CAT",
            help=textwrap.dedent("""\
            Category for change. This becomes the Change.category attribute, which
            can be used within the buildmaster to filter changes.
            """))
parser.add_option("--revlink", dest='revlink', metavar="REVLINK",
            help=textwrap.dedent("""\
            This this the revlink of the change. 
            This becomes the Change.revlink.
            """))
parser.add_option("-p", "--property", dest='properties', action="callback", callback=propertyCB, 
            type="string", metavar="PROP",
            help=textwrap.dedent("""\
            This adds a single property. This can be specified multiple times.
            The argument is a string representing python dictionary. For example,
            {'foo' : [ 'bar', 'baz' ]}
            This becomes the Change.properties attribute.
            """))
parser.add_option("-r", "--repository", dest='repository', metavar="PATH",
            help=textwrap.dedent("""\
            Repository for use by buildbot slaves to checkout code.
            This becomes the Change.repository attribute.
            Exmaple: :ext:myhost:/cvsroot
            """))
parser.add_option("-P", "--project", dest='project', metavar="PROJ",
            help=textwrap.dedent("""\
            The project for the source. Often set to the CVS module being modified. This becomes
            the Change.project attribute.
            """))
parser.add_option("-v", "--verbose", dest='verbosity', action="count",
            help=textwrap.dedent("""\
            Print more detail. If specified once, show status. If secified twice,
            print all data returned. Normally this will be the json version of the Change.
            """))
parser.add_option("-H", "--host", dest='host', metavar="HOST",
            default='localhost:8010',
            help=textwrap.dedent("""\
            Host and optional port of buildbot. For example, bbhost:8010
            Defaults to %default
            """))
parser.add_option("-u", "--urlpath", dest='urlpath', metavar="URLPATH",
            default='/change_hook/openpanel_hook',
            help=textwrap.dedent("""\
            Path portion of URL. Defaults to %default
            """))
parser.add_option("-t", "--testing", action="store_true", dest="amTesting", default=False,
            help=textwrap.dedent("""\
            Just print values and exit.
            """))
parser.set_defaults(properties={})

(options, args) = parser.parse_args()


'''
 Not in our house. 

if options.repository is None:
    print "repository must be specified"
    parser.print_usage()
    os._exit(2)
'''

if options.project is None:
    print "project must be specified"
    parser.print_usage()
    os._exit(2)

urlDict = buildURL(options)

params = urllib.urlencode(urlDict)
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/plain"}
if options.amTesting:
    print "params: %s" % params
    print "host: %s" % options.host
    print "urlpath: %s" % options.urlpath
else:
    conn = httplib.HTTPConnection(options.host)
    conn.request("POST", options.urlpath, params, headers)
    response = conn.getresponse()
    data = response.read()
    exitCode=0
    if response.status is not 200:
        exitCode=1
    if options.verbosity >= 1:
        print response.status, response.reason
        if response.status is 200:
            res =json.loads(data)
            print "Request %d at %s" % (res[0]['number'], res[0]['at'])
        if options.verbosity >= 2:
            print "Raw response %s" % (data)
    conn.close()
    os._exit(exitCode)

