
Overview
--------

This charm provides kibana from (http://kibana.org/).
Kibana is a search frontend for logstash.

Using This Charm
----------------

 using this charm :

    juju deploy kibana
    juju expose kibana

 not much use on its own ... you'll probably want the full stack

    juju deploy elasticsearch
    juju deploy logstash-indexer
    juju add-relation logstash-indexer elasticsearch:cluster
    juju deploy kibana
    juju add-relation kibana elasticsearch
    juju expose kibana

browse to http://ip-address to begin searching.


Configuration
-------------

listens only on localhost:5601.   uses rinetd to redirect ip-addr:80 to localhost:5601.
This should allow for haproxy etc to be used in front.
Could configure apache reverse proxy in front if you want SSL / .htaccess

Other
-----

* supports multiple ES servers in cluster.  This should help with balancing the load on ES and dealing with failure.

* see logstash-indexer charm's README.md file for usage examples.


Deploy / Add Dashboards
-----------------------

The Kibana charm ships with a action to deploy dashboards into
the Kibana instance. You will however, have to have them loaded into the charm
before the user deploys it, which means a pull request to the upstream charm to
include you're awesome dashboard for everyone!

For example, to deploy the included 'beats' dashboard with < Juju 2.0:

    juju action do kibana/0 load-dashboard dashboard=beats

For 2.0 +

    juju run-action kibana/0 load-dashboard dashboard=beats

This invokes the action, which in turn looks in the 'dashboards' directory for
`$DASHBOARD_NAME/load.sh`

Which is the repository layout adopted by Elasticsearch for their own dashboards.
to include your own, simply make a directory, a mirror the launch.sh script to
curl to your elasticsearch instance (by default: localhost:9200 will work as its
proxying the connection to your ES cluster) and it will declare any indexes
as well as load any dashboard JSON definitions you include. For more information
consult the `dashboards/beats/load.sh` script.

Custom dashboards can be added by uploading them via `juju scp`:

    juju scp my-dashboard/ kibana/0:dashboards/


Contact Information
-------------------

Authors: 
* Paul Czarkowski <paul@paulcz.net>
* James Beedy <jamesbeedy@gmail.com>
* Paul Czarkowski <paul@paulcz.net>
* Charles Butler <charles.butler@canonical.com>
* Matt Bruzek <matthew.bruzek@canonical.com>

Report bugs at: http://bugs.launchpad.net/charms
Location: http://jujucharms.com
