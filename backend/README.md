# Cover Letter Generator API

A FastAPI-based backend service for generating personalized cover letters based on CV/resume, job descriptions, and company information.

## Features

- CV/Resume parsing (PDF and DOCX)
- Job description analysis (text and image-based)
- Company information retrieval through Exa AI
- Cover letter generation using AI (OpenRouter with configurable models)
- Environment-based configuration
- Prometheus metrics and logging for monitoring
- IP-based rate limiting with configurable thresholds
- Request ID tracking for log correlation
- Docker containerization with health checks

## Setup and Installation

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for containerized deployment)

### Local Development

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your API keys:
   - `OPENROUTER_API_KEY`: For AI model access
   - `EXA_API_KEY`: For company information retrieval
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

The application uses environment variables for configuration:

- `APP_ENV`: Environment to run in (`development`, `production`)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
- `OPENROUTER_API_KEY`: API key for OpenRouter
- `OPENROUTER_MODEL`: Model to use with OpenRouter (default: google/gemini-2.0-flash-001)
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

## Monitoring and Logging

The application provides several monitoring features:

- Prometheus metrics at the `/metrics` endpoint
- Request ID tracking via `X-Request-ID` header
- Detailed logging with request IDs for correlation
- System health information at `/health` endpoint

## Project Structure

```
├── main.py                  # Main application entry point
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
├── modules/                 # Application modules
│   ├── company/             # Company information retrieval
│   ├── cover_letter/        # Cover letter generation
│   ├── document/            # Document parsing (PDF/DOCX)
│   ├── errors/              # Error handling and exceptions
│   ├── job/                 # Job description analysis
│   ├── monitoring/          # Prometheus metrics
│   └── rate_limit/          # Rate limiting implementation
```

## API Endpoints

### Main Endpoints

- `POST /generate_cover_letter`: Generate a cover letter from CV and job description
  - Accepts PDF/DOCX resume, job description (text or image), and company name

### Module-Specific Endpoints

- `POST /job/analyze_job_desc_image`: Extract job description from an image
- `POST /company/analyze_company`: Retrieve information about a company

### Utility Endpoints

- `GET /`: Welcome message
- `GET /health`: Health check with system information
- `GET /metrics`: Prometheus metrics

## License

[MIT](LICENSE) 
