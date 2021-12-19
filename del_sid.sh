#!/bin/sh

stats=$(sudo iscsiadm -m session -P 3)
sid=$(echo $stats | grep SID | cut -d ":" -f2)

ids=$(sudo iscsiadm -m session | cut -d "[" -f2 | cut -d "]" -f1)
for id in $ids; do
  sudo iscsiadm -m session -P 3 -r $id | grep -q "transport-offline"
  if [ $? !=0 ]; then
    echo $id
    # sudo iscsiadm -m session -r $id -u
  fi

done

# delcmd=$(sudo iscsiadm -m session -r $sid -u)
