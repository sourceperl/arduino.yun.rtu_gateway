# arduino.yun.rtu_gateway
Arduino Yun gateway between RTU and LPWAN network


### Setup on Yun openWRT

    # set root passwd (use by arduino web manager to connect to it)
    passwd
    # add sftp-server and python tool easy_install
    opkg update
    opkg install openssh-sftp-server
    opkg install distribute
    opkg install pyserial
    # download python package
    wget https://files.pythonhosted.org/packages/86/2f/dba4265b4072116350051f76fc57fe22b1fb24ee253ba581cd18f35038e6/pyModbusTCP-0.1.8.tar.gz --no-check-certificate
    wget https://files.pythonhosted.org/packages/fd/31/599a3387c2e98c270d5ac21a1575f3eb60a3712c192a0ca97a494a207739/schedule-0.5.0.tar.gz --no-check-certificate
    # install python package
    easy_install pyModbusTCP-0.1.8.tar.gz
    easy_install schedule-0.5.0.tar.gz
    # clean
    rm pyModbusTCP-0.1.8.tar.gz schedule-0.5.0.tar.gz


### Setup on Yun arduino web panel

Connect to http://arduino.local/cgi-bin/luci/webpanel/homepage with password
Click on "Configure" then click on "advanced configuration panel"


### Setup with advanced configuration panel (luci)

In System > System set "Europe/Paris" to timezone.

In System > Startup part "Local Startup", update rc.local content like this :

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


### Copy/Update files

Connect a remote directory to sftp://root@arduino.local/
Copy modbus2sigfox.py to /root/modbus2sigfox.py then do a "chmod +x modbus2sigfox.py"

Disable OpenWRT shell on /dev/ttyATH0 bridge (Serial1 ATMega 32U4)
Edit file /etc/inittab and add a comment "#" before line ttyATH0::askfirst:/bin/ash --login
After this a reboot of the Yun is need
