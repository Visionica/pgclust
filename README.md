It depends on python-libssh2 package and repmgr which I am including in this message. Please also be aware that all configuration file paths etc. are Debian/Ubuntu specific.

Here are the actions one will have to perform to setup a postgres cluster. For better understanding let's assume we have (master, slave1, slave2).

1. Install postgres, python-libssh2, repmgr on all nodes
2. Install pgclust on main master (# python setup.py install)
3. passwordless-sudo-capable-user@master $ pgclust create --local master passwordless-sudo-capable-user:passwordless-sudo-capable-user-password@master-hostname

4. To verify that master was added into configuration run
passwordless-sudo-capable-user@master $ pgclust show
master node0 @ master-hostname
Access: local
Keys: /home/passwordless-sudo-capable-user/pgclust/key_node0 /home/passwordless-sudo-capable-user/pgclust/key_node0.pub
Postgres: 9.1 with `postgres' username

5. The same way, only without --local argument we add slave nodes:
passwordless-sudo-capable-user@master $ pgclust create slave passwordless-sudo-capable-user:password@slave1-hostname
passwordless-sudo-capable-user@master $ pgclust create slave passwordless-sudo-capable-user:password@slave2-hostname

6. To verify that slaves were added into configuration as well run:
passwordless-sudo-capable-user@master $ pgclust show
master node0 @ master-hostname
Access: local
Keys: /home/passwordless-sudo-capable-user/pgclust/key_node0 /home/passwordless-sudo-capable-user/pgclust/key_node0.pub
Postgres: 9.1 with `postgres' username

slave node1 @ slave1-hostname
Access: ssh://passwordless-sudo-capable-user:password@slave1-host
Keys: /home/passwordless-sudo-capable-user/pgclust/key_node1 /home/passwordless-sudo-capable-user/pgclust/key_node1.pub
Postgres: 9.1 with `postgres' username

slave node2 @ slave2-hostname
Access: ssh://passwordless-sudo-capable-user:password@slave2-host
Keys: /home/passwordless-sudo-capable-user/pgclust/key_node2 /home/passwordless-sudo-capable-user/pgclust/key_node2.pub
Postgres: 9.1 with `postgres' username

7. Initialize master
passwordless-sudo-capable-user@master $ pgclust init master

8. Setup database etc.

9. Initialize slaves
passwordless-sudo-capable-user@master $ pgclust init slave

10. Verify with repmgr that the cluster is running
$ repmgr -f /etc/postgresql/9.1/main/repmgr.conf cluster show
Role      | Connection String 
* master  | host=master-host user=repmgr dbname=repmgr
  standby | host=slave1-host user=repmgr dbname=repmgr
  standby | host=slave2-host user=repmgr dbname=repmgr

11. We have set up a master/slave cluster with streaming replication.
