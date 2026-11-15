# Makefile for SWRO Backend Docker operations (UV-optimized)

.PHONY: help build up down logs shell bash clean test health migrate collectstatic createsuperuser restart rebuild ps disk-usage prune clickhouse-cli redis-cli format lint isort quality env stats

# Default target
help:
    @echo "SWRO Backend Docker Operations (UV-optimized)"
    @echo "============================================="
    @echo ""
    @echo "Primary commands:"
    @echo "  make build       - Build UV Docker images"
    @echo "  make up          - Start all services with UV"
    @echo "  make down        - Stop and remove all containers"
    @echo "  make logs        - View container logs"
    @echo "  make shell       - Open Django shell in container"
    @echo "  make bash        - Open bash shell in Django container"
    @echo "  make test        - Run tests in container"
    @echo "  make migrate     - Run database migrations"
    @echo "  make collectstatic - Collect static files"
    @echo "  make health      - Check application health"
    @echo ""
    @echo "Maintenance commands:"
    @echo "  make clean       - Remove all containers, volumes, and images"
    @echo "  make restart     - Restart all services"
    @echo "  make rebuild     - Rebuild and restart all services"
    @echo "  make ps          - Show running containers"
    @echo ""
    @echo "Development commands:"
    @echo "  make format      - Format code with black"
    @echo "  make lint        - Lint code with flake8"
    @echo "  make isort       - Sort imports"
    @echo "  make quality     - Run all code quality checks"
    @echo ""
    @echo "Service-specific commands:"
    @echo "  make clickhouse-cli - Open ClickHouse CLI"
    @echo "  make redis-cli      - Open Redis CLI"

# Build UV Docker images
build:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env build --no-cache

# Build with cache (faster)
build-cache:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env build

# Start services with UV in production mode
up:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env up -d
    @echo "Waiting for services to be ready..."
    @sleep 30
    @make health

# Stop UV services
down:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env down

# View UV logs
logs:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env logs -f

# View logs for specific UV service
logs-%:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env logs -f $*

# Open Django shell in UV container
shell:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django python manage.py shell

# Open bash shell in UV Django container
bash:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django bash

# Run tests in UV container
test:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django python manage.py test

# Run specific tests in UV container
test-%:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django python manage.py test $*

# Run database migrations in UV container
migrate:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django python manage.py migrate

# Make migrations in UV container
makemigrations:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django python manage.py makemigrations

# Collect static files in UV container
collectstatic:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django python manage.py collectstatic --noinput

# Create superuser in UV container
createsuperuser:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django python manage.py createsuperuser

# Check UV application health
health:
    @curl -f http://localhost:8000/health/ && echo "\nApplication is healthy!" || echo "\nApplication health check failed!"

# Clean UV everything (containers, volumes, images)
clean:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env down -v --rmi all

# Clean UV containers and volumes only (keep images)
clean-data:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env down -v

# Restart UV services
restart:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env restart

# Rebuild and restart UV services
rebuild: down build up

# Show running UV containers
ps:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env ps

# Show Docker disk usage
disk-usage:
    docker system df

# Prune unused Docker resources
prune:
    docker system prune -f

# UV ClickHouse specific commands
clickhouse-cli:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec clickhouse clickhouse-client

# UV Redis specific commands
redis-cli:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec redis redis-cli

# Run pre-commit hooks (requires pre-commit installed)
pre-commit:
    pre-commit run --all-files

# Format code with black in UV container
format:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django black .

# Lint code with flake8 in UV container
lint:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django flake8 . --exclude=venv,.venv,__pycache__,.git

# Sort imports with isort in UV container
isort:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django isort . --profile black

# Run all code quality checks in UV container
quality: format isort lint

# Show environment variables in UV container
env:
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django env | sort

# Backup Delta Lake data
backup-delta:
    mkdir -p backups
    docker-compose -f docker/docker-compose.uv.yml --env-file .env exec django tar czf /tmp/delta-backup.tar.gz /app/data
    docker cp $$(docker-compose -f docker/docker-compose.uv.yml --env-file .env ps -q django):/tmp/delta-backup.tar.gz ./backups/delta-backup-$$(date +%Y%m%d-%H%M%S).tar.gz
    @echo "Backup created in ./backups/"

# Show UV container stats
stats:
    docker stats --no-stream $$(docker-compose -f docker/docker-compose.uv.yml --env-file .env ps -q)