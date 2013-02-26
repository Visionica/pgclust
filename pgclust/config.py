import os
from ConfigParser import SafeConfigParser
import local

class Config(object):
    """docstring for Config"""
    def __init__(self, path='~/pgclust/pgclust.conf'):
        super(Config, self).__init__()
        self.path = os.path.expanduser(path)

        self.defaults = {
            'hostname': '',
            'username': 'root',
            'password': '',
            'type': 'slave',
            'pguser': 'postgres',
            'pgversion': '9.1',
            'cluster': 'main',
            'node': '0',
            'name': 'node%(node)s',
            'privkey': '',
            'pubkey': '',
            'local': 'false'
        }

        local.mkdir_notexist(os.path.expanduser('~/pgclust'))
        self.parser = SafeConfigParser(self.defaults)
        self.parser.read(self.path)
        try:
            conf = self.config()
            self.max_node = max(conf.values(), key=(lambda key: key['node']))
            self.max_node = int(self.max_node['node'])
        except ValueError:
            self.max_node = 0

    def save(self):
        with open(self.path, 'wb') as conf:
            self.parser.write(conf)

    def nodes(self):
        return self.parser.sections()

    def print_node(self, node_name):
        node = self.config(node_name)
        print '%(type)s %(name)s @ %(hostname)s' % node
        if node['local'] == 'true':
            print 'Access: local'
        else:
            print 'Access: ssh://%(username)s:%(password)s@%(hostname)s' % node
        print 'Keys: %(privkey)s %(pubkey)s' % node
        print 'Postgres: %(pgversion)s with `%(pguser)s\' username\n' % node

    def add_node(self, node):
        self.max_node += 1
        self.parser.add_section(node['name'])
        for option in self.defaults.iterkeys():
            if option in node.iterkeys():
                self.parser.set(node['name'], option, str(node[option]))
            else:
                self.parser.set(node['name'], option, self.defaults[option])

    def remove_node(self, name):
        self.parser.remove_section(name)

    def config(self, node_name=None):
        if node_name:
            return dict(self.parser.items(node_name))

        conf = dict()
        sections = self.parser.sections()
        for section in sections:
            conf[section] = dict(self.parser.items(section))

        return conf

