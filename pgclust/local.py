import subprocess
import os
import errno
import variables

def shell(cmd, err=False, retcode=False, environment=None):
    output = ''
    code = 0
    if variables.VERBOSE:
        print '[Local] executing %s' % (cmd, )
    sp = subprocess.Popen(cmd, stderr=None if not err else subprocess.PIPE, stdout=subprocess.PIPE, shell=True, env=environment)
    output, errout = sp.communicate()
    if output is None:
        output = ''
    if errout is not None:
        output += errout
    code = sp.returncode
    if variables.VERBOSE:
        print output
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
