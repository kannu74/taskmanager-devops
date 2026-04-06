# Task Manager DevOps Project

Production-ready full-stack task manager using React (Vite + Tailwind), FastAPI, Supabase PostgreSQL, Docker, Docker Compose, and GitHub Actions CI/CD.

## Project Structure

```text
task-manager-devops/
|-- frontend/
|-- backend/
|-- docker-compose.yml
|-- .env.example
|-- .github/workflows/deploy.yml
`-- README.md
```

## Features

- Create task
- View tasks
- Mark tasks complete
- Delete tasks
- Responsive frontend UI
- React to FastAPI API integration
- Supabase PostgreSQL integration
- Dockerized frontend and backend
- CI/CD pipeline with GitHub Actions

## Prerequisites

- Node.js 20+
- Python 3.12+
- Docker + Docker Compose
- Supabase project with PostgreSQL connection string

## Environment Variables

1. Copy root environment file:

```bash
cp .env.example .env
```

2. Update `.env` values:

- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role secret key
- `VITE_API_URL`: API URL for frontend
- `JWT_SECRET`: secure secret for production
- `AUTH_REQUIRED`: set `true` to enforce JWT auth

Backend-only sample is also provided at `backend/.env.example`.

## Local Development (Without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` and backend at `http://localhost:8000`.

## Run with Docker Compose

From project root:

```bash
cp .env.example .env
docker compose up --build -d
```

Services:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

Stop:

```bash
docker compose down
```

## API Endpoints

- `GET /health`
- `POST /auth/token` (optional JWT login)
- `GET /tasks`
- `POST /tasks`
- `PUT /tasks/{id}`
- `DELETE /tasks/{id}`

### Example Task Payload

```json
{
  "title": "Finish DevOps setup"
}
```

### Optional JWT Usage

If `AUTH_REQUIRED=true`, first get token:

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Use returned token as:

```text
Authorization: Bearer <token>
```

## Supabase Setup

1. Create a Supabase project.
2. Get the project URL and service role key from Supabase dashboard.
3. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`.
4. Create the `tasks` table in Supabase SQL editor.
5. Optional SQL file exists at `backend/scripts/init.sql`.

## Deploy on Render

1. Push this repository to GitHub.
2. In Render, create a new Web Service for backend:
  - Environment: `Docker`
  - Root Directory: `backend`
  - Port: `8000`
  - Health Check Path: `/health`
3. Add backend environment variables in Render:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `CORS_ORIGINS`
  - `AUTH_REQUIRED`
  - `JWT_SECRET`
  - `JWT_ALGORITHM`
  - `JWT_EXPIRE_MINUTES`
  - `DEMO_USERNAME`
  - `DEMO_PASSWORD`
4. Create a second Web Service for frontend:
  - Environment: `Docker`
  - Root Directory: `frontend`
  - Build Arg: `VITE_API_URL=https://<your-backend-service>.onrender.com`
  - Port: `80`
5. Update backend `CORS_ORIGINS` to include frontend Render URL.
6. Trigger deploy for both services.

## Bad Deploy Fallback / Rollback

- Render keeps the previous healthy instance running if the new deploy fails during build or startup/health checks.
- If a bad deploy goes live but behaves incorrectly, Render does not auto-rollback application logic by default.
- Use Render dashboard `Manual Rollback` to redeploy the previous good version.
- For safer CI/CD, gate deploys with test and smoke-check jobs in GitHub Actions before triggering Render deploy hooks.

## CI/CD with GitHub Actions

Workflow file: `.github/workflows/deploy.yml`

### Trigger

- Push to `main` branch

### Pipeline Steps

- Checkout code
- Set up Docker Buildx
- Docker Hub login
- Build and push backend image
- Build and push frontend image
- Deploy to server over SSH using Docker Compose

### Required GitHub Secrets

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `VITE_API_URL`
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `DEPLOY_PORT`
- `DEPLOY_PATH`

## Deployment Instructions (Docker-based)

On target server:

1. Install Docker and Docker Compose.
2. Create deployment directory and copy `docker-compose.yml` + `.env`.
3. Ensure image tags in compose match pushed registry images if using remote pull strategy.
4. Run:

```bash
docker compose pull
docker compose up -d --remove-orphans
```

## Useful Commands

```bash
# Rebuild containers
docker compose up --build -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop stack
docker compose down
```
