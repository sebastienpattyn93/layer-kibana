#!/usr/bin/python3
# Copyright (c) 2016, James Beedy <jamesbeedy@gmail.com>

import os
from sys import exit as quit
from subprocess import call

from charms.reactive import (when,
                             when_not,
                             set_state,
                             remove_state)

from charmhelpers.core import hookenv

from charmhelpers.core.host import (service_restart,
                                    service_running,
                                    service_start)

from charmhelpers.core.templating import render

from charms.layer.nginx import configure_site

import charms.apt


config = hookenv.config()


KIBANA_CONF = 'kibana.yml'
KIBANA_CONF_DIR = '/opt/kibana/config'
KIBANA_FQ_CONF = os.path.join(KIBANA_CONF_DIR, KIBANA_CONF)
KIBANA_CONF_CTXT = {}
ES_SERVERS = [{'host': 'localhost', 'port': 9200}]


def _render_kibana_conf(ctxt):
    '''Render kibana.cfg
    '''
    if os.path.exists(KIBANA_FQ_CONF):
        os.remove(KIBANA_FQ_CONF)
    render(source=KIBANA_CONF,
           target=KIBANA_FQ_CONF,
           owner='root',
           perms=0o644,
           context=ctxt)


@when_not('kibana.installed',
          'apt.installed.kibana')
def install_kibana():
    hookenv.status_set('maintenance',
                       'Installing kibana')

    charms.apt.queue_install(['kibana'])

    charms.apt.install_queued()
    hookenv.status_set('active',
                       'kibana installed')
    set_state('kibana.installed')


@when('kibana.installed',
      'nginx.available',
      'apt.installed.kibana')
@when_not('apt.queued_installs',
          'kibana.initialized')
def configure_kibana_nginx():
    hookenv.status_set('maintenance',
                       'Configuring kibana')

    # Add system startup for kibana
    call('sudo update-rc.d kibana defaults 96 9'.split(), shell=False)

    # Render kibana.cfg
    _render_kibana_conf(KIBANA_CONF_CTXT)

    # Configure nginx for kibana
    configure_site('kibana', 'kibana.conf', port=config['port'])

    # Configure nginx for kibana_lb
    configure_site('kibana_lb', 'kibana_lb.conf')

    # Configure nginx for es_cluster
    configure_site('es_cluster', 'es_cluster.conf', es_servers=ES_SERVERS)

    # Start/restart kibana
    if not service_running('kibana'):
        service_start('kibana')
    else:
        service_restart('kibana')

    # Open kibana frontend port
    hookenv.open_port(config['port'])

    # Set active status
    hookenv.status_set('active',
                       'kibana available')
    # Set state
    set_state('kibana.initialized')


@when('nginx.available',
      'kibana.initialized',
      'elasticsearch.available')
@when_not('kibana.available')
def elastic_search_available(elasticsearch):
    hookenv.status_set('maintenance',
                       'Configuring kibana for elasticsearch')
    ES_SERVERS = []
    for unit in elasticsearch.list_unit_data():
        ES_SERVERS.append({'host': unit['host'], 'port': unit['port']})

    # Configure nginx for es_cluster
    configure_site('es_cluster', 'es_cluster.conf', es_servers=ES_SERVERS)

    # Open elastic search port
    hookenv.open_port(9200)

    # Restart kibana
    service_restart('kibana')
    hookenv.status_set('active',
                       'kibana available')
    # Set state
    set_state('kibana.available')


@when('kibana.initialized',
      'nginx.available', 
      'website.available')
def configure_website(website):
    website.configure(port=config['port'])


@when('elasticsearch.departed')
def rerender_es_conf():
    hookenv.status_set('maintenance',
                       'ES member departed cluster, '
                       'reconfiguring Kibana for ES')
    remove_state('kibana.available')


@when_not('kibana.available')
@when('elasticsearch.departed')
def set_no_es_block():
    """If no elasticsearch, block and exit
    """
    hookenv.status_set('blocked',
                       'Need relation to elasticsearch')
    quit(1)
