# GitHub Actions CI/CD Setup Guide

This guide explains how to set up the GitHub Actions workflow for automatic deployment to Azure.

## Overview

The workflow (`deploy-dev.yml`) automatically:
1. Builds a Docker image when code is pushed to the `development` branch
2. Pushes the image to GitHub Container Registry (GHCR)
3. Connects to your Azure VM via SSH
4. Pulls the latest image
5. Deploys using `docker compose up`

## Prerequisites

- Azure VM with Docker and Docker Compose installed
- SSH access to the Azure VM
- GitHub repository with Actions enabled

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository:

### Navigate to: Repository Settings → Secrets and variables → Actions → New repository secret

### 1. Azure Credentials (Optional - for Azure CLI)
**Name:** `AZURE_CREDENTIALS`
**Value:** JSON output from Azure service principal
```bash
az ad sp create-for-rbac --name "ad-dawah-github-actions" --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
  --sdk-auth
```

### 2. Azure VM SSH Access
**Name:** `AZURE_VM_HOST`
**Value:** Your Azure VM's public IP address or hostname
```
Example: 20.123.45.67 or myapp.eastus.cloudapp.azure.com
```

**Name:** `AZURE_VM_USERNAME`
**Value:** SSH username for the VM
```
Example: azureuser
```

**Name:** `AZURE_VM_SSH_KEY`
**Value:** Private SSH key for authentication
```bash
# Generate SSH key pair if you don't have one
ssh-keygen -t rsa -b 4096 -C "github-actions@ad-dawah"

# Copy the PRIVATE key content (entire file including headers)
cat ~/.ssh/id_rsa
```

**Name:** `AZURE_VM_PORT` (Optional)
**Value:** SSH port (default: 22)
```
22
```

### 3. Deployment Configuration
**Name:** `DEPLOY_PATH`
**Value:** Path on Azure VM where the application is deployed
```
Example: /home/azureuser/ad-dawah-ilallah-backend
```

## Azure VM Setup

### 1. Install Docker and Docker Compose on Azure VM

```bash
# SSH into your Azure VM
ssh azureuser@your-vm-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### 2. Set Up Application Directory

```bash
# Create application directory
mkdir -p /home/azureuser/ad-dawah-ilallah-backend
cd /home/azureuser/ad-dawah-ilallah-backend

# Copy docker-compose.yml to the VM
# You can use scp or create it manually
```

### 3. Configure Environment Variables

Create a `.env` file on the Azure VM:

```bash
nano /home/azureuser/ad-dawah-ilallah-backend/.env
```

Add your environment variables:
```env
DB_NAME=ad_dawah
DB_USER=ad_dawah
DB_PASSWORD=your_secure_password
DB_HOST=your_database_host
DB_PORT=5432
DEBUG=False
```

### 4. Configure SSH Key Authentication

On your Azure VM:
```bash
# Add the public key to authorized_keys
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# Paste your public key here
chmod 600 ~/.ssh/authorized_keys
```

### 5. Open Required Ports

In Azure Portal:
1. Go to your VM → Networking → Add inbound port rule
2. Add rules for:
   - Port 22 (SSH)
   - Port 8000 (Django app) or your custom port
   - Port 80/443 (if using Nginx)

Or using Azure CLI:
```bash
az vm open-port --resource-group myResourceGroup --name myVM --port 8000
az vm open-port --resource-group myResourceGroup --name myVM --port 22
```

## Workflow Customization

### Change Docker Image Name
Edit `.github/workflows/deploy-dev.yml`:
```yaml
env:
  DOCKER_IMAGE_NAME: your-custom-name
```

### Deploy to Different Branch
Edit the trigger in `.github/workflows/deploy-dev.yml`:
```yaml
on:
  push:
    branches:
      - main  # or any other branch
```

### Use Docker Hub Instead of GHCR
Replace the registry login steps:
```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

## Testing the Workflow

### 1. Make a test commit to development branch
```bash
git checkout development
git add .
git commit -m "Test CI/CD deployment"
git push origin development
```

### 2. Monitor the workflow
- Go to your GitHub repository
- Click on "Actions" tab
- Watch the workflow execution

### 3. Check deployment on Azure VM
```bash
ssh azureuser@your-vm-ip
cd /home/azureuser/ad-dawah-ilallah-backend
docker compose ps
docker compose logs -f
```

## Troubleshooting

### SSH Connection Failed
- Verify `AZURE_VM_HOST` is correct
- Check SSH key is properly formatted (include `-----BEGIN RSA PRIVATE KEY-----`)
- Ensure VM's security group allows SSH from GitHub Actions IPs
- Test SSH manually: `ssh -i private_key azureuser@vm-ip`

### Docker Pull Failed
- Verify GitHub Container Registry permissions
- Check if the image was built and pushed successfully
- Ensure VM can access GitHub Container Registry

### Docker Compose Failed
- Check if `docker-compose.yml` exists on the VM
- Verify environment variables in `.env` file
- Check Docker and Docker Compose are installed
- Review logs: `docker compose logs`

### Image Not Found
- Verify the image name matches in both workflow and docker-compose.yml
- Check GitHub Packages to see if image was pushed
- Ensure image tag is correct (development, latest, etc.)

## Security Best Practices

1. **Use SSH Keys**: Never use password authentication
2. **Restrict SSH Access**: Limit SSH to specific IP ranges
3. **Rotate Secrets**: Regularly update SSH keys and passwords
4. **Use Environment Variables**: Never commit sensitive data
5. **Enable Firewall**: Use Azure NSG to restrict access
6. **Monitor Logs**: Regularly check deployment logs
7. **Use HTTPS**: Configure SSL/TLS for production

## Production Considerations

For production deployments:

1. **Use a reverse proxy** (Nginx) in front of Django
2. **Set up SSL certificates** (Let's Encrypt)
3. **Configure proper logging** and monitoring
4. **Set up database backups**
5. **Use managed database** (Azure Database for PostgreSQL)
6. **Implement health checks**
7. **Set up alerts** for failed deployments
8. **Use separate environments** (staging, production)

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Azure VM Documentation](https://docs.microsoft.com/en-us/azure/virtual-machines/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
