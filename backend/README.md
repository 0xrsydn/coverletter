# Cover Letter Generator API

A FastAPI-based backend service for generating personalized cover letters based on CV/resume, job descriptions, and company information.

## Features

- CV/Resume parsing (PDF and DOCX)
- Job description analysis (text and image)
- Company information retrieval
- Cover letter generation using AI
- Environment-based configuration
- Prometheus metrics for monitoring
- IP-based rate limiting to prevent abuse

## Setup and Installation

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for containerized deployment)

### Local Development

1. Clone the repository
2. Create a virtual environment:
   ```
   uv venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your API keys
5. Run the application:
   ```
   uvicorn main:app --reload
   ```

### Docker Deployment

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your API keys
3. Build and start the container:
   ```
   docker-compose up -d
   ```

## Environment Configuration

The application uses environment variables for configuration. The following variables are available:

- `APP_ENV`: The environment to run in (`development`, `production`)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
- `OPENROUTER_API_KEY`: API key for OpenRouter
- `OPENROUTER_MODEL`: Model to use with OpenRouter
- `EXA_API_KEY`: API key for Exa AI

## Rate Limiting

The API implements IP-based rate limiting to prevent abuse:

- Production limits:
  - Global: 30 requests per minute per IP
  - Cover letter generation: 5 requests per hour per IP
  - Company analysis: 15 requests per hour per IP
  - Job description analysis: 10 requests per hour per IP

- Development limits:
  - Global: 60 requests per minute per IP
  - Cover letter generation: 10 requests per hour per IP
  - Company analysis: 30 requests per hour per IP
  - Job description analysis: 20 requests per hour per IP

Clients can check rate limit status through the following response headers:
- `X-RateLimit-Limit`: Maximum number of requests allowed
- `X-RateLimit-Remaining`: Number of requests left in current time window
- `X-RateLimit-Reset`: Time when the limit will reset

## Monitoring with Prometheus and Grafana

The application exposes Prometheus metrics at the `/metrics` endpoint. To enable monitoring:

1. Uncomment the Prometheus and Grafana services in `docker-compose.yml`
2. Create the necessary volume directories:
   ```
   mkdir -p prometheus grafana/dashboards grafana/provisioning/datasources grafana/provisioning/dashboards
   ```
3. Start the containers with `docker-compose up -d`
4. Access Grafana at `http://localhost:3000` (default credentials: admin/admin)
5. The Cover Letter API dashboard should be automatically provisioned

## Project Structure

```
├── main.py                  # Main application entry point
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
├── modules/                 # Application modules
│   ├── company/             # Company information module
│   ├── cover_letter/        # Cover letter generation module
│   ├── document/            # Document processing module
│   ├── errors/              # Error handling module
│   ├── job/                 # Job description module
│   └── monitoring/          # Monitoring and metrics module
├── prometheus/              # Prometheus configuration
└── grafana/                 # Grafana configuration
```

## API Endpoints

- `GET /`: Welcome message
- `GET /health`: Health check
- `GET /metrics`: Prometheus metrics
- `POST /generate_cover_letter`: Generate a cover letter
- `POST /job/analyze_job_desc_image`: Analyze job description from image
- `POST /company/analyze_company`: Analyze company information

## License

[MIT](LICENSE) 
