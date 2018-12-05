# arduino.yun.rtu_gateway
Arduino Yun gateway between RTU and LPWAN network


### Setup on Yun openWRT

    # set root passwd (use by arduino web manager to connect to it)
    passwd
    # add sftp-server and python tool easy_install
    opkg update
    opkg install openssh-sftp-server
    # download python package
    wget https://files.pythonhosted.org/packages/86/2f/dba4265b4072116350051f76fc57fe22b1fb24ee253ba581cd18f35038e6/pyModbusTCP-0.1.8.tar.gz --no-check-certificate
    wget https://files.pythonhosted.org/packages/fd/31/599a3387c2e98c270d5ac21a1575f3eb60a3712c192a0ca97a494a207739/schedule-0.5.0.tar.gz --no-check-certificate


    # for yun rev1
    opkg install distribute
    # install python package
    opkg install pyserial
    easy_install pyModbusTCP-0.1.8.tar.gz
    easy_install schedule-0.5.0.tar.gz
    # clean
    rm pyModbusTCP-0.1.8.tar.gz schedule-0.5.0.tar.gz


    # for yun rev2
    opkg install python-setuptools
    opkg install python-pyserial
    tar xvzf pyModbusTCP-0.1.8.tar.gz
    tar xvzf schedule-0.5.0.tar.gz
    # install python package
    cd /root/pyModbusTCP-0.1.8
    python setup.py install
    cd /root/schedule-0.5.0
    python setup.py install
    # clean
    cd /root
    rm -rf pyModbusTCP-0.1.8* schedule-0.5.0*


### Setup on Yun arduino web panel

- Connect to http://arduino.local/cgi-bin/luci/webpanel/homepage with password. Click
on "Configure" then click on "advanced configuration panel"


### Setup with advanced configuration panel (luci)

- In System > System set "Europe/Paris" to timezone.

- In System > Startup part "Local Startup" :

#### Update rc.local content like this :

    # Put your custom commands here that should be executed once
    # the system init finished. By default this file does nothing.

    wifi-live-or-reset
    boot-complete-notify

    # Uncomment the following line in order to reset the microntroller
    # right after linux becomes ready

    #reset-mcu

    # Uncomment the following line in order to disable kernel console
    # debug messages, thus having a silent and clean serial communication
    # with the microcontroller

    echo 0 > /proc/sys/kernel/printk

    python /root/modbus2bridge.py

    exit 0

- In Network > Interfaces define WAN eth1 to static IPv4 192.168.1.100 with 255.255.255.0 as mask.


### Copy/Update files

- Connect a remote directory to sftp://root@arduino.local/

  - Copy modbus2sigfox.py to /root/modbus2sigfox.py then do a "chmod +x modbus2sigfox.py"

- Disable OpenWRT shell on /dev/ttyATH0 serial bridge (on ATMega 32U4 serial name is Serial1)

  - Yun Rev1: Edit file /etc/inittab and add a comment "#" before line ttyATH0::askfirst:/bin/ash --login

  - Yun Rev2: Edit file /etc/inittab and add a comment "#" before line #::askconsole:/usr/libexec/login.sh

After this a reboot of the Yun is need
