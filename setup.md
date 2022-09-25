
Copy secondaryFan.sh (Secondary fan boot script)
```commandline
sudo cp secondaryFan.sh /etc/init.d/secondaryFan
sudo chmod +x /etc/init.d/secondaryFan
sudo chown root /etc/init.d/secondaryFan
sudo chgrp root /etc/init.d/secondaryFan
sudo update-rc.d secondaryFan defaults
```

Remove secondaryFan service
```commandline
sudo update-rc.d -f secondaryFan remove
sudo rm /etc/init.d/secondaryFan
```