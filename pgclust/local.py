import subprocess
import os
import errno
import variables

def shell(cmd, err=None):
    output = ''
    if variables.VERBOSE:
        print '[Local] executing %s' % (cmd, )
    try:
        output = subprocess.check_output(cmd, shell=True)
        if variables.VERBOSE:
            print output
    except subprocess.CalledProcessError as e:
        output = e.output
        raise e
    finally:
        return output

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
