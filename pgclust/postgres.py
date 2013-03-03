import os
from ssh import SSHConnection
import local
import template
import socket

class PostgresManager(object):
    """docstring for PostgresManager"""
    def __init__(self, node):
        super(PostgresManager, self).__init__()
        self.node = node
        if not node['local'] == 'true':
            self.connection = SSHConnection(
                node['hostname'],
                node['username'],
                node['password'])

    def run(self, cmd):
        if self.node['local'] == 'true':
            return local.shell(cmd)
        else:
            return self.connection.execute(cmd)

    def start(self):
        self.run('sudo /etc/init.d/postgresql start')

    def stop(self):
        self.run('sudo /etc/init.d/postgresql stop')

    def restart(self):
        self.run('sudo /etc/init.d/postgresql restart')

    def reload(self):
        self.run('sudo /etc/init.d/postgresql reload')

    def write_file(self, path, data):
        if self.node['local'] == 'true':
            local.write_file(path, data)
        else:
            self.connection.upload_data(data, path)

    def read_file(self, path):
        if self.node['local'] == 'true':
            return local.read_file(path)
        else:
            return self.connection.download(path)

    def init(self, master):
        environ = os.environ.copy()
        environ['PATH'] = '/usr/lib/postgresql/%(pgversion)s/bin:' + environ['PATH']

        self.stop()
        self.run('sudo pg_dropcluster %(pgversion)s %(cluster)s' % self.node)
        self.run('sudo pg_createcluster %(pgversion)s %(cluster)s' % self.node)
        self.run('sudo chown -R %(pguser)s:%(pguser)s /var/lib/%(pgversion)s/%(cluster)s' % self.node)
        self.write_file('/tmp/pgpostgresql.conf', template.PG_CONFIG_TEMPLATE % self.node)
        self.write_file('/tmp/pgpg_hba.conf', template.PG_HBA_CONFIG_TEMPLATE % self.node)
        self.write_file('/tmp/pgrepmgr.conf', template.REPMGR_CONFIG_TEMPLATE % self.node)
        self.run('sudo cp /tmp/pgpostgresql.conf /etc/postgresql/%(pgversion)s/%(cluster)s/postgresql.conf' % self.node)
        self.run('sudo cp /tmp/pgpg_hba.conf /etc/postgresql/%(pgversion)s/%(cluster)s/pg_hba.conf' % self.node)
        self.run('sudo cp /tmp/pgrepmgr.conf /etc/postgresql/%(pgversion)s/%(cluster)s/repmgr.conf' % self.node)
        self.run('sudo chmod 644 /etc/postgresql/%(pgversion)s/%(cluster)s/*' % self.node)
        self.run('sudo rm /tmp/pgpostgresql.conf /tmp/pgpg_hba.conf /tmp/pgrepmgr.conf')
        self.run('sudo chown %(pguser)s:%(pguser)s -R /etc/postgresql' % self.node)

        self.write_file('/tmp/sshid_rsa' % self.node, local.read_file(self.node['privkey']))
        self.write_file('/tmp/sshid_rsa.pub' % self.node, local.read_file(self.node['pubkey']))
        self.write_file('/tmp/sshconfig', template.SSH_CONFIG)
        self.run('sudo -u %(pguser)s mkdir -p ~%(pguser)s/.ssh' % self.node)
        self.run('sudo cp /tmp/sshid_rsa ~%(pguser)s/.ssh/id_rsa' % self.node)
        self.run('sudo cp /tmp/sshid_rsa.pub ~%(pguser)s/.ssh/id_rsa.pub' % self.node)
        self.run('sudo cp /tmp/sshconfig ~%(pguser)s/.ssh/config' % self.node)
        self.run('sudo rm /tmp/sshconfig /tmp/sshid_rsa /tmp/sshid_rsa.pub')
        self.run('sudo chown %(pguser)s:%(pguser)s ~%(pguser)s/.ssh/config' % self.node)
        self.run('sudo chown %(pguser)s:%(pguser)s ~%(pguser)s/.ssh/id_rsa' % self.node)
        self.run('sudo chown %(pguser)s:%(pguser)s ~%(pguser)s/.ssh/id_rsa.pub' % self.node)
        self.run('sudo chmod 644 ~%(pguser)s/.ssh/config' % self.node)
        self.run('sudo chmod 600 ~%(pguser)s/.ssh/id_rsa' % self.node)
        self.run('sudo chmod 644 ~%(pguser)s/.ssh/id_rsa.pub' % self.node)
        if self.node['type'] == 'master':
            self.start()
            self.run('sudo -u %(pguser)s createuser --login --superuser repmgr' % self.node)
            self.run('sudo -u %(pguser)s createdb repmgr' % self.node)
            self.run('sudo -u %(pguser)s repmgr --verbose -f /etc/postgresql/%(pgversion)s/%(cluster)s/repmgr.conf master register' % self.node)
        else:
            self.run('sudo -u %(pguser)s rm -rf /var/lib/postgresql/%(pgversion)s/%(cluster)s' % self.node)
            self.run('sudo -u %(pguser)s mkdir /var/lib/postgresql/%(pgversion)s/%(cluster)s' % self.node)
            self.run('sudo -u %(pguser)s chmod 700 /var/lib/postgresql/%(pgversion)s/%(cluster)s' % self.node)
            self.run(('sudo -u %(pguser)s PATH="' + environ['PATH'] + '" repmgr --verbose --force -D /var/lib/postgresql/%(pgversion)s/%(cluster)s -d repmgr -p 5432 -U repmgr -R %(pguser)s standby clone ') % self.node + master['hostname'])
            self.start()
            self.run('sudo -u %(pguser)s repmgr -f /etc/postgresql/%(pgversion)s/%(cluster)s/repmgr.conf --verbose standby register' % self.node)

    def update_nodes(self, nodes):
        records = []
        for node in nodes:
            node['hostname'] = socket.gethostbyname(node['hostname']) + '/32'
            records.append(template.REPLICATION_NODE_TEMPLATE % node)
        pg_hba = '\n\n'.join(records) + template.PG_HBA_CONFIG_TEMPLATE % self.node
        self.write_file('/tmp/pgpg_hba.conf' % self.node, pg_hba)
        self.run('sudo cp /tmp/pgpg_hba.conf /etc/postgresql/%(pgversion)s/%(cluster)s/pg_hba.conf' % self.node)
        self.run('sudo rm /tmp/pgpg_hba.conf')

    def update_keys(self, nodes):
        self.run('sudo -u %(pguser)s mkdir -p ~%(pguser)s/.ssh' % self.node)
        self.run('sudo chmod 700 ~%(pguser)s/.ssh' % self.node)
        keys = []
        for node in nodes:
            key = local.read_file(node['pubkey'])
            keys.append(key)
        self.write_file('/tmp/sshauthorized_keys' % self.node, '\n'.join(keys))
        self.run('sudo cp /tmp/sshauthorized_keys ~%(pguser)s/.ssh/authorized_keys' % self.node)
        self.write_file('/tmp/sshid_rsa' % self.node, local.read_file(self.node['privkey']))
        self.write_file('/tmp/sshid_rsa.pub' % self.node, local.read_file(self.node['pubkey']))
        self.run('sudo cp /tmp/sshid_rsa ~%(pguser)s/.ssh/id_rsa' % self.node)
        self.run('sudo cp /tmp/sshid_rsa.pub ~%(pguser)s/.ssh/id_rsa.pub' % self.node)
        self.run('sudo rm /tmp/sshauthorized_keys /tmp/sshid_rsa /tmp/sshid_rsa.pub')
        self.run('sudo chown %(pguser)s:%(pguser)s ~%(pguser)s/.ssh/authorized_keys' % self.node)
        self.run('sudo chown %(pguser)s:%(pguser)s ~%(pguser)s/.ssh/id_rsa' % self.node)
        self.run('sudo chown %(pguser)s:%(pguser)s ~%(pguser)s/.ssh/id_rsa.pub' % self.node)
        self.run('sudo chmod 600 ~%(pguser)s/.ssh/authorized_keys' % self.node)
        self.run('sudo chmod 600 ~%(pguser)s/.ssh/id_rsa' % self.node)
        self.run('sudo chmod 644 ~%(pguser)s/.ssh/id_rsa.pub' % self.node)

    def update(self, nodes):
        self.update_nodes(nodes.values())
        self.update_keys(nodes.values())
        self.reload()

