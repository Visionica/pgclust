import subprocess
import os
import errno
import variables

def shell(cmd, err=False, retcode=False, environment=None):
    output = ''
    code = 0
    if variables.VERBOSE:
        print '[Local] executing %s' % (cmd, )
    try:
        output = subprocess.check_output(cmd, stderr=None if not err else subprocess.STDOUT, shell=True, env=environment)
        if variables.VERBOSE:
            print output
    except subprocess.CalledProcessError as e:
        output = e.output
        code = e.returncode
    finally:
        if not retcode:
            return output
        else:
            return (code, output)

def write_file(path, data):
    if variables.VERBOSE:
        print '[Local] Writing file ' + path
        print data
    with open(os.path.expanduser(path), 'wb') as output:
        output.write(data)

def read_file(path):
    if variables.VERBOSE:
        print '[Local] Reading file ' + path
    with open(os.path.expanduser(path), 'rb') as inp:
        return ''.join(inp.readlines())

def mkdir_notexist(path):
    if os.path.exists(path):
        return
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def generate_key(name):
    if variables.VERBOSE:
        print 'Generating key ' + name
    path = os.path.expanduser('~/pgclust/key_%s' % (name,))
    shell('rm "%s" "%s.pub"' % (path, path))
    shell('ssh-keygen -t rsa -N "" -q -f "%s"' % (path, ))
    return path
