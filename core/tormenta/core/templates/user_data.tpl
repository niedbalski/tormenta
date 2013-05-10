disable_root: True
hostname:{{ hostname }}
sudo:
        - ALL=(ALL) ALL
runcmd:
 - [ sudo, -Hu, ubuntu, sh, -c, 'printf "\n%s" -- "{{ public_key }}" >> ~/.authorized_keys' ]
 - [ sudo, -Hu, ubuntu, sh, -c, 'chmod 0600 ~/.authorized_keys' ]
 - [ sudo, -Hu, ubuntu, sh, -c, 'grep "cloud-init.*running" /var/log/cloud-init.log > ~/runcmd.log' ]
 - [ sudo, -Hu, ubuntu, sh, -c, 'read up sleep < /proc/uptime; echo $(date): runcmd up at $up | tee -a ~/runcmd.log' ]
 - [ sudo, -Hu, ubuntu, sh, -c, *user_setup ]
