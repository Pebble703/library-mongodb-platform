#!/bin/bash
# 固定静态 IP 与主机名：set_ip.sh <节点号> <IP>
set -e
NODE=$1
IP=$2

hostnamectl set-hostname "nosql$NODE"
grep -q "nosql$NODE" /etc/hosts || echo "127.0.1.1 nosql$NODE" >> /etc/hosts

CON=$(nmcli -t -f NAME,DEVICE connection show | grep ':ens33$' | head -1 | cut -d: -f1)
echo "connection name: $CON"

nmcli connection modify "$CON" \
  ipv4.method manual \
  ipv4.addresses "$IP/24" \
  ipv4.gateway 192.168.78.2 \
  ipv4.dns "8.8.8.8 114.114.114.114"

nmcli connection up "$CON" >/dev/null
sleep 2

echo "hostname: $(hostname)"
ip -4 addr show ens33 | grep inet
ip route | grep default
