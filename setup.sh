cp secondaryFan.sh /etc/init.d/secondaryFan
chmod +x /etc/init.d/secondaryFan
chown root /etc/init.d/secondaryFan
chgrp root /etc/init.d/secondaryFan
update-rc.d secondaryFan defaults
echo "Reboot and verify"