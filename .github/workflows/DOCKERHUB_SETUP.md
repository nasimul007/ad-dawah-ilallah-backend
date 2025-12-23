# Docker Hub CI/CD Setup - Quick Reference

## Required GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### Docker Hub Credentials
1. **DOCKERHUB_USERNAME**
   - Your Docker Hub username
   - Example: `johndoe`

2. **DOCKERHUB_TOKEN**
   - Docker Hub access token (NOT your password)
   - Create at: https://hub.docker.com/settings/security
   - Click "New Access Token"
   - Give it a description like "GitHub Actions"
   - Copy the token and save it as the secret

### Azure VM Credentials
3. **AZURE_VM_HOST**
   - Your Azure VM's public IP or hostname
   - Example: `20.123.45.67`

4. **AZURE_VM_USERNAME**
   - SSH username for the VM
   - Example: `azureuser`

5. **AZURE_VM_SSH_KEY**
   - Private SSH key for authentication
   - Copy entire content including headers

6. **AZURE_VM_PORT** (Optional)
   - SSH port, defaults to 22

7. **DEPLOY_PATH** (Optional)
   - Application directory on VM
   - Default: `/home/azureuser/ad-dawah-ilallah-backend`

8. **AZURE_CREDENTIALS** (Optional)
   - Azure service principal credentials for Azure CLI

## Docker Hub Image Naming

Your images will be pushed to Docker Hub as:
```
<DOCKERHUB_USERNAME>/di:development
<DOCKERHUB_USERNAME>/di:development-<git-sha>
```

## Update docker-compose.yml on Azure VM

Make sure your `docker-compose.yml` on the Azure VM uses the correct image:

```yaml
services:
  web:
    image: <your-dockerhub-username>/di:development
    # ... rest of config
```

Replace `<your-dockerhub-username>` with your actual Docker Hub username.

## How to Create Docker Hub Access Token

1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Description: `GitHub Actions - Ad Dawah Backend`
4. Access permissions: `Read, Write, Delete`
5. Click "Generate"
6. **IMPORTANT**: Copy the token immediately (you won't see it again)
7. Add it to GitHub Secrets as `DOCKERHUB_TOKEN`

## Testing the Workflow

1. Push to development branch:
```bash
git checkout development
git add .
git commit -m "Test Docker Hub deployment"
git push origin development
```

2. Check GitHub Actions tab to see the workflow running

3. Verify on Docker Hub:
   - Go to https://hub.docker.com/r/<your-username>/di
   - You should see the new tags

4. Verify on Azure VM:
```bash
ssh azureuser@your-vm-ip
docker images | grep di
docker compose ps
```

## Troubleshooting

### "unauthorized: incorrect username or password"
- Verify `DOCKERHUB_USERNAME` is correct
- Ensure `DOCKERHUB_TOKEN` is an access token, not your password
- Check token hasn't expired

### "repository does not exist"
- The repository will be created automatically on first push
- Ensure your Docker Hub account is active

### Image pull failed on Azure VM
- Ensure VM can access Docker Hub
- Check if you need to login on the VM manually first
- Verify the image name matches in docker-compose.yml

## Public vs Private Images

By default, Docker Hub repositories are **public**. To make it private:

1. Go to https://hub.docker.com/r/<your-username>/di/settings
2. Click "Make Private"
3. Note: Free accounts have limited private repositories

If using private images, ensure your Azure VM can authenticate:
```bash
# On Azure VM
docker login -u <username>
# Enter your Docker Hub password or token
```
