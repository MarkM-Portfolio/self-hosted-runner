#!/usr/bin/bash

sudo hostnamectl set-hostname ${ label }

echo -e "\nUpdating apt packages..."
sudo apt -y update
sudo apt -y install apt-transport-https ca-certificates software-properties-common unzip gpg gnupg

echo -e "\nAdd Docker official GPG key and repository:"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=arm64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo -e "\nAdd Hashicorp official GPG key and repository:"
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

echo -e "\nUpdating apt packages..."
sudo apt -y update

echo -e "\nInstall Docker Engine"
sudo apt -y install docker-ce docker-ce-cli containerd.io

echo -e "\nDownload AWS, Terraform and NodeJS"
curl -L "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws*
sudo apt -y install nodejs

echo -e "\nInstall Session Manager Plugin"
curl -L "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_arm64/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
sudo snap refresh amazon-ssm-agent
rm -rf session-manager-plugin.deb

echo -e "\nUpdate SSM Agent"
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
aws ssm send-command --document-name "AWS-UpdateSSMAgent" --targets "Key=InstanceIds,Values=$INSTANCE_ID" --region ${ region }

echo -e "\nCreate the docker group."
sudo groupadd docker

echo -e "\nAdd your ${ user } to the docker group."
sudo usermod -aG docker ${ user }
newgrp docker

# echo -e "\nAuthenticate to GitHub.."
# sudo apt -y install gh awscli
# GET_SECRET=`aws secretsmanager get-secret-value --region ${ region } --secret-id github/secret | grep SecretString | awk '{print$2}' | cut -d : -f2 | tr -d '\\\"},'`
# echo $GET_SECRET | /usr/bin/gh auth login --with-token

GET_SECRET=$(aws ssm get-parameter --name "/github.secret" --with-decryption --query "Parameter.Value" --region ${ region } --output text)

echo -e "\nGet ID of existing self-hosted runner"
RUNNER_ID=$(curl \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GET_SECRET" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/orgs/SapphireSystems/actions/runners | \
  grep -B1 ${ label } | grep -i id | head -n 1 | tr -d -c 0-9)

if [ ! -z $RUNNER_ID ]; then
  echo -e "\nDelete existing runner in Github"
  curl \
    -X DELETE \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $GET_SECRET" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/orgs/SapphireSystems/actions/runners/$RUNNER_ID
fi

echo -e "\nCreate a folder under the drive root"
mkdir /home/${ user }/actions-runner; cd /home/${ user }/actions-runner

echo -e "\nDownload the latest runner package"
curl -o actions-runner-linux-arm64-${ runner_version }.tar.gz -L https://github.com/actions/runner/releases/download/v${ runner_version }/actions-runner-linux-arm64-${ runner_version }.tar.gz

echo -e "\nValidate the hash"
echo "62cc5735d63057d8d07441507c3d6974e90c1854bdb33e9c8b26c0da086336e1  actions-runner-linux-arm64-${ runner_version }.tar.gz" | shasum -a 256 -c

echo -e "\nExtract the installer"
tar -xzf ./actions-runner-linux-arm64-${ runner_version }.tar.gz
chown -R ${ user }:${ user } /home/${ user }/actions-runner

echo -e "\nCreate the runner and start the configuration experience."
GET_TOKEN=$(curl \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GET_SECRET" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/orgs/SapphireSystems/actions/runners/registration-token | \
  grep "token" | awk '{print$2}' | tr -d '",')

sudo su - ${ user } -c "/usr/bin/bash /home/${ user }/actions-runner/config.sh --labels ${ label },${ account_name } --url https://github.com/SapphireSystems --token $GET_TOKEN"

echo -e "\nAdd self-hosted runner to cronjob to run after a reboot."
sudo su - ${ user } -c "echo @reboot /home/${ user }/actions-runner/run.sh > /home/${ user }/actions-runner/job.txt"
sudo su - ${ user } -c "crontab /home/${ user }/actions-runner/job.txt"
rm -rf /home/${ user }/actions-runner/job.txt

# Run as job
sudo su - ${ user } -c "/usr/bin/bash /home/${ user }/actions-runner/run.sh &"

# Run manually
# sudo su - ${ user } -c "/usr/bin/bash /home/${ user }/actions-runner/run.sh"

# SSH Troubleshooting
# sudo mkdir -p /home/${ user }/.ssh
# echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCIHGUEpNur7TTxTw8D1nXUIQuogLhA/vC38e5Sj2Y/vy89yrHmIULqYjgDNoicPRjVQHArEeaFtJZ4GSwUrjzWSdaJyTQsvP6umFbjgs/mG/nDQNnfAPhaFtutiYwkVrFGkWjJ//112I03FGfmVtkRNZzBqz4V8w+BGlNltWMrA0s23wpzT57Ioau8m5usXhwo0epJIQ7M8nsPApVreZla1GZ7r6RU+ClxNWvjD5GBbfmeq/V9MW+QVjzwnmAshZDxaRbwlLkVQPJ8a6YDDrMbqOpa9k9VY9pfuYDjPYOLKWOPKdi9vw1+Yl1pamjvPsld9oA4KIuCLW2Gn5sE7rbT self" >> /home/${ user }/.ssh/authorized_keys

# To check ${ user }data logs:
# sudo tail -300 /var/log/cloud-init-output.log
