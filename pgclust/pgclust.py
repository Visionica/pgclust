import sys

from config import Config
import variables
from local import shell, generate_key
import argparse
import sys
import urlparse
from postgres import PostgresManager

class Manager(object):
    """docstring for Manager"""
    def __init__(self):
        super(Manager, self).__init__()
        self.config = Config()

    def main(self):
        parser = argparse.ArgumentParser(description='Postgres cluster manager')
        parser.add_argument('-v', '--verbose', action='store_true', default=False)
        subparsers = parser.add_subparsers()

        # create command
        parser_create = subparsers.add_parser('create')
        parser_create.set_defaults(func=self.create)
        parser_create.add_argument('type', nargs='?', default='', type=str,
            choices=['master', 'slave'],
            help='Who will be performing the action')
        parser_create.add_argument('host', nargs='?', default='', type=str,
            help='Node access info username:password@hostname')
        parser_create.add_argument('--local', action='store_true', help='Node is local')
        parser_create.add_argument('--pguser', nargs='?', default='postgres', type=str,
            help='Postgres username')
        parser_create.add_argument('--pgversion', nargs='?', default='9.1', type=str,
            help='Postgres version')

        # remove command
        parser_remove = subparsers.add_parser('remove')
        parser_remove.set_defaults(func=self.remove)
        parser_remove.add_argument('type', nargs='?', type=str,
            help='Node to remove')
        # init command
        parser_init = subparsers.add_parser('init')
        parser_init.set_defaults(func=self.init)
        parser_init.add_argument('type', nargs='?', type=str,
            help='Node to init')
        # update command
        parser_update = subparsers.add_parser('update')
        parser_update.set_defaults(func=self.update)
        parser_update.add_argument('type', nargs='?', type=str,
            help='Node to update')
        # show command
        parser_show = subparsers.add_parser('show')
        parser_show.set_defaults(func=self.show)
        parser_show.add_argument('type', nargs='?', default='cluster', type=str,
            help='Who will be performing the action')

        # repmgr command
        parser_repmgr = subparsers.add_parser('repmgr')
        parser_repmgr.set_defaults(func=self.repmgr)
        parser_repmgr.add_argument('type', nargs='?', default='', type=str,
            choices=['standby', 'master'],
            help='Who will be performing the action')
        parser_repmgr.add_argument('action', nargs='?', default='', type=str,
            choices=['register', 'clone', 'promote', 'follow'],
            help='Action to perform')
        parser_repmgr.add_argument('node', nargs='?', type=str,
            help='Node to clone from')

        args = parser.parse_args()
        if args.verbose:
            variables.VERBOSE = True

        retcode = 0
        try:
            retcode = args.func(args)
        except:
            retcode = 1
        finally:
            return retcode

    def create(self, args):
        args = vars(args)
        if args['local'] == True:
            args['local'] = 'true'
        else:
            args['local'] = 'false'
        name = ''
        node = self.config.max_node + 1
        if args['type'] == 'master':
            name = 'node0'
            node = 0
            if name in self.config.nodes():
                self.config.print_node(name)
                raise Exception('Master node already exists')
        else:
            name = 'node%d' % (self.config.max_node + 1, )

        args['privkey'] = generate_key(name)
        args['pubkey'] = args['privkey'] + '.pub'
        args['node'] = node
        args['name'] = name
        parsed = urlparse.urlparse('ssh://' + args['host'])
        args['hostname'] = parsed.hostname if not parsed.hostname == None else ''
        if args['hostname'] == '':
            raise Exception('Hostname cannot be empty')
        args['username'] = parsed.username if not parsed.username == None else ''
        args['password'] = parsed.password if not parsed.password == None else ''
        if args['local'] == 'false':
            if args['username'] == '' or args['password'] == '':
                raise Exception('Non-local nodes should have ssh credentials supplied (username:password@hostname)')
        self.config.add_node(args)
        self.config.save()

    def remove(self, args):
        args = vars(args)
        names = []
        nodes = self.config.nodes()
        conf = self.config.config()
        if args['type'] == 'cluster':
            names = nodes
        elif args['type'] == 'master':
            names = filter(lambda x: conf[x]['type'] == 'master', nodes)
        elif args['type'] == 'slave':
            names = filter(lambda x: conf[x]['type'] == 'slave', nodes)
        else:
            names = [args['type'],]

        for name in names:
            if not name in self.config.nodes():
                raise Exception('Such node does not exist')
            node = self.config.config(name)
            self.config.remove_node(name)
            self.config.save()
            shell('rm -rf "%(privkey)s" "%(pubkey)s"' % node)

    def init(self, args):
        self.check_configuration()
        args = vars(args)
        names = []
        nodes = self.config.nodes()
        conf = self.config.config()
        if args['type'] == 'cluster':
            names = filter(lambda x: conf[x]['type'] == 'slave', nodes)
            names.prepend('node0')
        elif args['type'] == 'master':
            names = filter(lambda x: conf[x]['type'] == 'master', nodes)
        elif args['type'] == 'slave':
            names = filter(lambda x: conf[x]['type'] == 'slave', nodes)
        else:
            names = [args['type'],]

        for name in names:
            node = self.config.config(name)
            manager = PostgresManager(node)
            print 'Initializing %s'  % (name, )
            manager.init(self.config.config('node0'))
            manager.update(self.config.config())
        print 'Done'

    def update(self, args):
        self.check_configuration()
        args = vars(args)
        names = []
        nodes = self.config.nodes()
        conf = self.config.config()
        if args['type'] == 'cluster':
            names = filter(lambda x: conf[x]['type'] == 'slave', nodes)
            names.prepend('node0')
        elif args['type'] == 'master':
            names = filter(lambda x: conf[x]['type'] == 'master', nodes)
        elif args['type'] == 'slave':
            names = filter(lambda x: conf[x]['type'] == 'slave', nodes)
        else:
            names = [args['type'],]

        for name in names:
            node = self.config.config(name)
            manager = PostgresManager(node)
            print 'Updating %s'  % (name, )
            manager.update(self.config.config())
        print 'Done'

    def show(self, args):
        args = vars(args)
        names = []
        nodes = self.config.nodes()
        conf = self.config.config()
        if not len(nodes):
            print 'Configuration is empty\n'
            return
        if args['type'] == 'cluster':
            names = nodes
        elif args['type'] == 'master':
            names = filter(lambda x: conf[x]['type'] == 'master', nodes)
        elif args['type'] == 'slave':
            names = filter(lambda x: conf[x]['type'] == 'slave', nodes)
        else:
            names = [args['type'],]

        for name in names:
            self.config.print_node(name)

    def repmgr(self, args):
        args = vars(args)
        cmd = 'sudo -u postgres repmgr'
        if args['type'] == 'master' and args['action'] != 'register':
            raise Exception('Incorrect action "%s" for type master' % (args['action'],))
        if args['action'] != 'clone':
            cmd += ' -f /etc/postgresql/9.1/main/repmgr.conf %(type)s %(action)s' % args
        else:
            if args['node'] == '':
                raise Exception('Node to clone from should be specified when performing "standby clone" action')
            cmd += ' -D /var/lib/postgresql/9.1/main -d repmgr -p 5432 -U repmgr -R postgres --verbose --force standby clone %(node)s' % args
        (retcode, output) = shell(cmd, err=True, retcode=True)
        print output
        return retcode

    def check_configuration(self):
        # There should be at least a master node in configuration file
        if 'node0' not in self.config.nodes():
            raise Exception('There should be at least a master node in configuration file')

def main():
    manager = Manager()
    sys.exit(manager.main())
