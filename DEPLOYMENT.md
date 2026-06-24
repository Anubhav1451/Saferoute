# SafeRoute AI - Deployment Guide

This guide covers deployment options for SafeRoute AI, including Docker, manual deployment, and production considerations.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Docker and Docker Compose (for containerized deployment)
- Python 3.8+ (for manual deployment)
- Node.js 18+ (for manual deployment)
- Mapbox Access Token

### Required Services
- Database: SQLite (development) or PostgreSQL (production)
- Reverse Proxy: Nginx (recommended for production)
- Process Manager: PM2 or systemd (for production)

## Environment Configuration

### Environment Variables

Create environment files based on the provided examples:

#### Root `.env` (for Docker Compose)
```bash
cp .env.example .env
# Edit .env and add your Mapbox token
```

#### Backend Environment
```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
```

#### Frontend Environment
```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local with your Mapbox token
```

### Key Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAPBOX_TOKEN` | Mapbox GL access token | - | Yes |
| `DATABASE_URL` | Database connection string | `sqlite:///./saferoute.db` | No |
| `DEBUG` | Debug mode | `False` | No |
| `SECRET_KEY` | JWT secret key | Auto-generated | No |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` | No |

## Docker Deployment

### Quick Start with Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-repo/saferoute-ai.git
cd saferoute-ai

# Copy environment files
cp .env.example .env
# Edit .env and add your MAPBOX_TOKEN

# Build and start services
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Docker Compose Commands

```bash
# Start services
docker-compose up

# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# Rebuild services
docker-compose up --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart
```

### Individual Docker Builds

#### Backend
```bash
cd backend

# Build image
docker build -t saferoute-backend .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./saferoute.db \
  -e DEBUG=False \
  saferoute-backend
```

#### Frontend
```bash
cd frontend

# Build image
docker build -t saferoute-frontend .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_MAPBOX_TOKEN=your_token \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  saferoute-frontend
```

## Manual Deployment

### Backend Deployment

#### 1. System Setup
```bash
# Install Python dependencies
sudo apt-get update
sudo apt-get install python3.11 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Database Setup
```bash
# Initialize database with mock data
python -m app.utils.generate_mock_data

# Or use production database
# Edit DATABASE_URL in .env to use PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost/saferoute
```

#### 3. Start Backend Server
```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 4. Process Manager (PM2)
```bash
# Install PM2
npm install -g pm2

# Start backend with PM2
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name saferoute-backend

# Save PM2 configuration
pm2 save

# Enable PM2 startup
pm2 startup
```

### Frontend Deployment

#### 1. System Setup
```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install dependencies
npm install
```

#### 2. Environment Configuration
```bash
# Create environment file
cp .env.local.example .env.local

# Add your Mapbox token
echo "NEXT_PUBLIC_MAPBOX_TOKEN=your_token_here" >> .env.local
echo "NEXT_PUBLIC_API_URL=http://your-backend-url" >> .env.local
```

#### 3. Build and Start
```bash
# Development mode
npm run dev

# Production build
npm run build
npm start
```

#### 4. Process Manager (PM2)
```bash
# Start frontend with PM2
pm2 start "npm start" --name saferoute-frontend --cwd /path/to/frontend

# Save PM2 configuration
pm2 save
```

## Production Considerations

### Database

#### PostgreSQL Migration
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb saferoute

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://saferoute:password@localhost/saferoute
```

#### Database Backups
```bash
# Backup
pg_dump saferoute > backup_$(date +%Y%m%d).sql

# Restore
psql saferoute < backup_20240101.sql
```

### Reverse Proxy (Nginx)

#### Nginx Configuration
```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name saferoute.example.com;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API Documentation
    location /docs {
        proxy_pass http://backend;
    }
}
```

#### SSL Configuration (Let's Encrypt)
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d saferoute.example.com
```

### Security

#### Firewall Configuration
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

#### Environment Variables
- Never commit `.env` files to version control
- Use strong, randomly generated `SECRET_KEY`
- Rotate secrets regularly
- Use environment-specific configurations

### Scaling

#### Horizontal Scaling
```bash
# Multiple backend workers
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name saferoute-backend-1
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8001" --name saferoute-backend-2

# Configure load balancer in Nginx
upstream backend {
    server localhost:8000;
    server localhost:8001;
}
```

#### Caching
- Implement Redis for session storage
- Cache API responses with appropriate TTL
- Use CDN for static assets

## Monitoring and Maintenance

### Health Checks

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend health check
curl http://localhost:3000
```

### Logging

#### Backend Logging
```bash
# View logs
pm2 logs saferoute-backend

# Log rotation
pm2 install pm2-logrotate
```

#### Frontend Logging
```bash
# View logs
pm2 logs saferoute-frontend
```

### Updates

#### Backend Updates
```bash
# Pull latest changes
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Restart service
pm2 restart saferoute-backend
```

#### Frontend Updates
```bash
# Pull latest changes
git pull origin main

# Install new dependencies
npm install

# Rebuild
npm run build

# Restart service
pm2 restart saferoute-frontend
```

## Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check if port is in use
lsof -i :8000

# Check logs
pm2 logs saferoute-backend

# Verify database connection
python -c "from app.db.session import SessionLocal; print('DB OK')"
```

#### Frontend Build Fails
```bash
# Clear cache
rm -rf .next
rm -rf node_modules
npm install

# Check environment variables
cat .env.local
```

#### Database Connection Issues
```bash
# Verify database file exists
ls -la saferoute.db

# Check database permissions
chmod 644 saferoute.db

# Test database connection
python -c "from app.db.session import SessionLocal; db = SessionLocal(); print('OK')"
```

#### Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose up --build

# Check container logs
docker-compose logs backend
docker-compose logs frontend

# Remove volumes and start fresh
docker-compose down -v
docker-compose up --build
```

### Performance Optimization

#### Backend
- Increase worker count: `--workers 4`
- Enable connection pooling
- Use PostgreSQL instead of SQLite
- Implement caching

#### Frontend
- Enable production build optimizations
- Use CDN for static assets
- Implement lazy loading
- Optimize images

## Support

For deployment issues, refer to:
- API Documentation: `API_DOCUMENTATION.md`
- Troubleshooting section in README
- GitHub Issues: [your-repo/issues]

---

**Note**: This deployment guide is optimized for hackathon demo purposes. For production deployment, additional security hardening, monitoring, and scaling considerations are required.
