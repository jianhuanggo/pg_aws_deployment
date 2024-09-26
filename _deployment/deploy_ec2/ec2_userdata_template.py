from jinja2 import Template

user_data_streamlit_template = """Content-Type: multipart/mixed; boundary="//"
MIME-Version: 1.0

--//
Content-Type: text/cloud-config; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="cloud-config.txt"

#cloud-config

--//
Content-Type: text/x-shellscript; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="userdata.txt"

#!/bin/bash

sleep 5

yum install docker docker containerd.io docker-buildx-plugin docker-compose-plugin -y

sleep 5

systemctl start docker

sleep 5

aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin {{ aws_account_number }}.dkr.ecr.{{ aws_region }}.amazonaws.com

sleep 5

sudo docker run -d {{ forwarding_port_string }} {{ aws_account_number }}.dkr.ecr.{{ aws_region }}.amazonaws.com/{{ ecr_repo }}:latest

sleep 10

--//
"""