#!/bin/bash
# Start all services for smb-share-enum target

# Start SSH
/usr/sbin/sshd

# Start Samba (foreground to keep container alive)
exec smbd --foreground --no-process-group
