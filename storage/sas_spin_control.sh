#!/bin/sh

# If your SAS drives are connected through a HBA card, Linux doesn't automatically spin them down when shuting down.
# To resolve this issue, you need to set `manage_system_start_stop` and `manage_runtime_start_stop` to 1 for the drives.

cat > /etc/systemd/system/sas_spin_control.service << EOL
[Unit]
Description=SAS drive spin control

[Service]
Type=oneshot
ExecStart=/bin/sh -c "for i in /sys/class/scsi_disk/*; do echo 1 > "$i"/manage_system_start_stop; echo 1 > "$i"/manage_runtime_start_stop; done"

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl start sas_spin_control.service && systemctl enable sas_spin_control.service