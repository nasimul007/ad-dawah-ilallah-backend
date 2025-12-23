# Docker Setup for Ad Dawah Ilallah Backend

This guide explains how to run the Django application using Docker and Docker Compose.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

## Files Created

1. **Dockerfile** - Defines the Django application container
2. **docker-compose.yml** - Orchestrates the Django app and PostgreSQL database
3. **.dockerignore** - Excludes unnecessary files from the Docker build

## Quick Start

### 1. Build and Start the Containers

```bash
docker-compose up --build
```

This command will:
- Build the Django application image
- Start the PostgreSQL database container
- Run database migrations automatically
- Start the Django development server on port 8000

### 2. Access the Application

Once the containers are running, access the application at:
- **API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin

### 3. Stop the Containers

```bash
docker-compose down
```

To stop and remove volumes (database data):
```bash
docker-compose down -v
```

## Environment Variables

The application uses environment variables from your `.env` file. The docker-compose.yml provides defaults:

- `DB_NAME`: ad_dawah
- `DB_USER`: ad_dawah
- `DB_PASSWORD`: 123456
- `DB_HOST`: db (automatically set to the database service)
- `DB_PORT`: 5432

You can override these by creating or modifying your `.env` file.

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
```

### Run Django Management Commands
```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Make migrations
docker-compose exec web python manage.py makemigrations

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic
```

### Access Django Shell
```bash
docker-compose exec web python manage.py shell
```

### Access PostgreSQL Database
```bash
docker-compose exec db psql -U ad_dawah -d ad_dawah
```

### Rebuild Containers
```bash
docker-compose up --build
```

## Production Considerations

For production deployment, you should:

1. **Update settings.py**:
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS`
   - Use environment variables for `SECRET_KEY`
   - Remove SSL requirement from database if not needed

2. **Use a production server**:
   - Replace `runserver` with Gunicorn or uWSGI
   - Add Nginx as a reverse proxy

3. **Security**:
   - Use strong passwords
   - Enable SSL/TLS
   - Configure proper firewall rules

4. **Database**:
   - Use managed PostgreSQL service or configure backups
   - Remove the database port exposure if not needed externally

## Volumes

The docker-compose setup creates three volumes:

- `postgres_data`: Persists database data
- `static_volume`: Stores Django static files
- `media_volume`: Stores user-uploaded media files

## Troubleshooting

### Database Connection Issues
If the web service can't connect to the database, ensure:
- The database service is healthy: `docker-compose ps`
- Check logs: `docker-compose logs db`

### Port Already in Use
If port 8000 or 5432 is already in use, modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change host port
```

### Permission Issues
If you encounter permission issues with volumes on Linux:
```bash
sudo chown -R $USER:$USER media static
```
