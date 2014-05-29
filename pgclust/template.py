
REPLICATION_NODE_TEMPLATE = """
host     repmgr           repmgr      %(hostname)s         trust
host     replication      all         %(hostname)s         trust
"""

PG_CONFIG_TEMPLATE = """
# Minimal postgresql configuration file

data_directory = '/var/lib/postgresql/%(pgversion)s/%(cluster)s'
hba_file = '/etc/postgresql/%(pgversion)s/%(cluster)s/pg_hba.conf'
ident_file = '/etc/postgresql/%(pgversion)s/%(cluster)s/pg_ident.conf'

port = 5432
listen_addresses='*'
max_connections = 100
unix_socket_directory = '/tmp'
ssl = false

wal_level = 'hot_standby'
archive_mode = on
archive_command = 'cd .'    # we can also use exit 0, anything that
                            # just does nothing
max_wal_senders = 10
wal_keep_segments = 5000    # 80 GB required on pg_xlog
hot_standby = on

shared_buffers = 2048MB
effective_cache_size = 4096MB
checkpoint_segments = 32
maintenance_work_mem = 512MB
work_mem = 160MB
wal_buffers = 16MB
synchronous_commit = on
checkpoint_completion_target = 0.7
log_line_prefix = '%%t '
datestyle = 'iso, mdy'
lc_messages = 'en_US.UTF-8'
lc_monetary = 'en_US.UTF-8'
lc_numeric = 'en_US.UTF-8'
lc_time = 'en_US.UTF-8'
default_text_search_config = 'pg_catalog.english'
"""

PG_HBA_CONFIG_TEMPLATE = """

host     repmgr           repmgr      127.0.0.1/32         trust
host     repmgr           repmgr      ::1/128              trust
host     replication      all         127.0.0.1/32         trust
host     repmgr           repmgr      samehost             trust
host     replication      all         samehost             trust


# Database administrative login by Unix domain socket
local   all             postgres                                peer

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     peer
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# IPv6 local connections:
host    all             all             ::1/128                 md5
# IPv4 remote connections:
host    all             all             all                     md5

"""

REPMGR_CONFIG_TEMPLATE = """
cluster=main
node=%(node)s
node_name=%(name)s
conninfo='host=%(hostname)s user=repmgr dbname=repmgr'
"""

SSH_CONFIG = """
StrictHostKeyChecking no
UserKnownHostsFile=/dev/null
"""
