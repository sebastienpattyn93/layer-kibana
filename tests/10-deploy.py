#!/usr/bin/python3

# This is a very basic test for to verify the kibana charm.

import amulet
import unittest

seconds = 1100
port = 82


class TestDeployment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Perform a one time setup for this class deploying the charms."""
        cls.deployment = amulet.Deployment(series='xenial')

        cls.deployment.add('kibana')
        cls.deployment.configure('kibana', {'port': port})
        cls.deployment.add('elasticsearch', units=3)
        cls.deployment.relate('kibana', 'elasticsearch:client')
        cls.deployment.expose('kibana')

        try:
            cls.deployment.setup(timeout=seconds)
            cls.deployment.sentry.wait()
        except amulet.helpers.TimeoutError:
            message = "The deploy did not setup in {0} seconds".format(seconds)
            amulet.raise_status(amulet.SKIP, msg=message)
        except:
            raise
        cls.kibana_unit = cls.deployment.sentry['kibana'][0]
        cls.elasticsearch_units = cls.deployment.sentry['elasticsearch']

    def test_elasticsearch(self):
        """Make sure elasticsearch is running and get health status."""
        for unit in self.elasticsearch_units:
            # Verify the Elasticsearch service is installed and running.
            status = 'service elasticsearch status'
            output, code = unit.run(status)
            print(output)
            if code != 0:
                message = 'Elasticsearch is not running.'
                amulet.raise_status(amulet.FAIL, msg=message)
            # Get the health from Elasticsearch.
            get = 'curl -X GET http://127.0.0.1:9200/_cat/health'
            output, code = unit.run(get)
            print(output)
            if 'green' not in output:
                message = 'Health output is not green:\n{0}'.format(output)
                amulet.raise_status(amulet.FAIL, msg=message)

    def test_kibana(self):
        """Make sure that kibana is installed and running correctly."""
        # Verify the service is installed and running.
        status = 'service kibana status'
        output, code = self.kibana_unit.run(status)
        print(output)
        if code != 0:
            message = 'Kibana is not running.'
            amulet.raise_status(amulet.FAIL, msg=message)
        # Ensure each elasticsearch node address is in the ngnix site file.
        file = '/etc/nginx/sites-available/es_cluster'
        es_cluster = self.kibana_unit.file_contents(file)
        for es_unit in self.elasticsearch_units:
            address, code = es_unit.run('unit-get private-address')
            if address in es_cluster:
                print('Found {0} in the nginx config file.'.format(address))
            else:
                message = 'Elasticsearch {0} was not in {0}'.format(address,
                                                                    file)
                amulet.raise_status(amulet.FAIL, msg=message)
        # Test the proxy from Kibana to Elasticsearch is working.
        get = 'curl -X GET http://localhost:9200/_cat/health/'
        output, code = self.kibana_unit.run(get)
        print(output)
        if 'green' not in output or code != 0:
            message = 'The proxy to Elasticsearch is not working.'
            amulet.raise_status(amulet.FAIL, msg=message)
        # Test that Kibana is running and hosting http on this unit.
        kibana = 'curl http://localhost:{0}'.format(port)
        output, code = self.kibana_unit.run(kibana)
        print(output)
        if 'kibana' not in output or code != 0:
            amulet.raise_status(amulet.FAIL,
                                msg="Error getting kibana page.")

if __name__ == '__main__':
    unittest.main()
