#!/bin/bash
# Start all services for nfs-misconfig target

# Start SSH
/usr/sbin/sshd

# Start RPC services
rpcbind

# Export NFS shares
exportfs -ra

# Start NFS server
rpc.nfsd 8

# Start mountd (foreground to keep container alive)
exec rpc.mountd --foreground
