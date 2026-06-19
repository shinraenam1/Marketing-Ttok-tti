# Marketing Ttok-tti Dashboard

Monorepo skeleton with:
- Spring Boot 3.x backend (REST API)
- Vue 3 + Vite frontend

## Structure

```text
.
|- backend/
|- frontend/
```

## Backend

### Run

```bash
cd backend
mvn clean package -DskipTests
java -jar target/dashboard-0.0.1-SNAPSHOT.jar
```

If PowerShell cannot find `mvn` right after installation, run this once in the current terminal:

```powershell
$env:Path = "$HOME\\scoop\\apps\\maven\\current\\bin;$env:Path"
```

### API examples

- `GET /api/health`
- `GET /api/dashboard/summary`

## Frontend

### Run

```bash
cd frontend
npm install
npm run dev
```

## Azure API Key setup

Add your key in `backend/src/main/resources/application.yml` or set environment variables:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
