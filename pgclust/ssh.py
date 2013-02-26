import socket, os
import libssh2
import variables

BUFFER_SIZE = 4096

class SSHConnection(object):
    """docstring for SSHConnection"""
    def __init__(self, hostname, username, password, port=22, private_key=None, public_key=None):
        super(SSHConnection, self).__init__()
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

        if variables.VERBOSE:
            print '[%s@%s] Opening session' % (self.username, self.hostname)

        if not private_key is None:
            self.private_key = os.path.expanduser(private_key)
        else:
            self.private_key = private_key

        if not public_key is None:
            self.public_key = os.path.expanduser(public_key)
        else:
            self.public_key = public_key

        self.session = libssh2.Session()
        self.session.set_banner()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.hostname, self.port))

            self.session.startup(sock)

            if not self.private_key:
                self.session.userauth_password(self.username, self.password)
            else:
                self.session.userauth_publickey_fromfile(self.username, self.public_key, self.private_key, self.password)
        except Exception as e:
            print str(e)
            raise Exception, self.session.last_error()

    def execute(self, command):
        if variables.VERBOSE:
            print '[%s@%s] Executing %s' % (self.username, self.hostname, command)
        output = ''
        channel = self.session.open_session()
        rc = channel.execute(command)
        while True:
            data = channel.read(BUFFER_SIZE)
            if (data == '' or data is None):
                break
            output += data
        if variables.VERBOSE:
            print output
        channel.close()
        return output

    def upload(self, local_path, remote_path=None, mode=0644):
        if not remote_path:
            remote_path = local_path

        if variables.VERBOSE:
            print '[%s@%s] Uploading %s -> %s' % (self.username, self.hostname, local_path, remote_path)
        with open(local_path, 'rb') as input:
            input.seek(0, input.SEEK_END)
            input_size = input.tell()
            input.seek(0, input.SEEK_SET)
            channel = self.session.scp_send(remote_path, mode, input_size)
            while True:
                data = input.read(BUFFER_SIZE)
                if not data:
                    break
                channel.write(data)
            channel.close()

    def upload_data(self, data, remote_path, mode=0644):
        if variables.VERBOSE:
            print '[%s@%s] Uploading -> %s' % (self.username, self.hostname, remote_path)
        input_size = len(data)
        channel = self.session.scp_send(remote_path, mode, input_size)
        channel.write(data)
        channel.close()

    def download(self, remote_path):
        if variables.VERBOSE:
            print '[%s@%s] Downloading %s' % (self.username, self.hostname, remote_path)
        return self.execute('sudo cat "%s"' % (remote_path, ))

    def __del__(self):
        if variables.VERBOSE:
            print '[%s@%s] Closing session' % (self.username, self.hostname)
        self.session.close()

