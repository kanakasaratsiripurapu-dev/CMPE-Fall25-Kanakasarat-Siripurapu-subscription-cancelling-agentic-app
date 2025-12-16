# SubScout - AI-Powered Subscription Management Platform

**SubScout** is an intelligent subscription management platform that automatically analyzes your Gmail inbox to discover, track, and cancel unwanted subscriptions. Our AI agents scan your emails, extract subscription details (cost, renewal dates, cancellation links), and present everything in a clean dashboard with real-time spending insights.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### Environment Setup

1. **Clone the repository**:
```bash
git clone https://github.com/yourorg/subscout.git
cd subscout
```

2. **Create `.env` file** in project root:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://subscout:password@localhost:5432/subscout_db
POSTGRES_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# Security
JWT_SECRET_KEY=your_super_secret_jwt_key_here
ENCRYPTION_KEY=your_32_byte_encryption_key_here

# LLM APIs (choose one)
OPENAI_API_KEY=your_openai_api_key
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key

# App Config
ENVIRONMENT=development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Start services with Docker Compose**:
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Celery Worker
- Frontend (port 3000)

4. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup (Without Docker)

#### Backend Setup:
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

#### Worker Setup (separate terminal):
```bash
cd backend
source venv/bin/activate
celery -A worker.tasks.celery_app worker --loglevel=info --concurrency=4
```

#### Frontend Setup:
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🏗️ Project Structure

```
subscout/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── config.py               # Configuration
│   │   ├── database.py             # Database connection
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── api/                    # API endpoints
│   │   ├── services/               # Business logic
│   │   │   ├── gmail_service.py    # Gmail OAuth + API
│   │   │   ├── detection_service.py # Subscription detection
│   │   │   ├── unsubscribe_service.py
│   │   │   └── llm_service.py      # LLM integration
│   │   ├── agents/                 # AI agents
│   │   └── utils/                  # Helper functions
│   ├── worker/
│   │   └── tasks/                  # Celery tasks
│   ├── tests/                      # Unit/integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js app directory
│   │   ├── components/             # React components
│   │   ├── lib/
│   │   │   ├── api.ts             # API client
│   │   │   └── auth.ts            # Auth helpers
│   │   └── types/                 # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── infrastructure/
│   ├── docker-compose.yml
│   └── nginx.conf
├── .env
└── README.md
```

## 🔑 Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:3000/auth/callback` (dev), `https://yourapp.com/auth/callback` (prod)
5. Copy Client ID and Client Secret to `.env`

## 🧪 Testing

### Run Backend Tests:
```bash
cd backend
pytest tests/ -v --cov=app
```

### Run Frontend Tests:
```bash
cd frontend
npm test
```

### Run E2E Tests:
```bash
cd frontend
npm run test:e2e
```

## 📊 Database Migrations

### Create new migration:
```bash
cd backend
alembic revision --autogenerate -m "Add new table"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback:
```bash
alembic downgrade -1
```

## 🚀 Deployment

### Production Deployment (AWS ECS)

1. **Build and push Docker image**:
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t subscout-backend ./backend
docker tag subscout-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/subscout-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/subscout-backend:latest
```

2. **Deploy to ECS**:
```bash
aws ecs update-service --cluster subscout-cluster --service subscout-api --force-new-deployment
```

3. **Frontend (Vercel)**:
- Connect GitHub repo to Vercel
- Automatic deployments on push to `main`
- Set environment variables in Vercel dashboard

### Environment Variables (Production)

Store secrets in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name subscout/production \
  --secret-string '{
    "GOOGLE_CLIENT_ID": "...",
    "GOOGLE_CLIENT_SECRET": "...",
    "JWT_SECRET_KEY": "...",
    "ENCRYPTION_KEY": "...",
    "OPENAI_API_KEY": "..."
  }'
```

## 📈 Monitoring

- **Logs**: CloudWatch Logs (AWS) or Datadog
- **Metrics**: Prometheus + Grafana dashboards
- **Errors**: Sentry for exception tracking
- **Uptime**: UptimeRobot or Pingdom

Key metrics to monitor:
- API latency (P95 < 500ms)
- Error rate (< 1%)
- Gmail API quota usage (< 80%)
- Worker queue depth (< 100 tasks)

## 🔒 Security

- All data encrypted at rest (AES-256)
- Gmail refresh tokens encrypted with user-specific keys
- HTTPS/TLS 1.3 for all communications
- Rate limiting (100 req/min per user)
- Regular security audits
- Dependency scanning (Snyk, Trivy)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🆘 Support

- Documentation: https://docs.subscout.app
- Issues: https://github.com/yourorg/subscout/issues
- Email: support@subscout.app

## 🙏 Acknowledgments

- Built with FastAPI, Next.js, PostgreSQL
- AI powered by OpenAI GPT-4 and Anthropic Claude
- Gmail integration via Google APIs
- Icons from Lucide React
- UI components from Tailwind CSS

---

**Made with ❤️ by the SubScout team**
