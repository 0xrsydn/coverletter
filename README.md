# Cover Letter Generator API

A FastAPI-based web application that automatically generates tailored cover letters based on your resume, job descriptions, and company information using AI. The frontend is served directly via Jinja2 templates and styled with Tailwind CSS / Daisy UI.

## Overview

This project uses AI to streamline the job application process by generating personalized cover letters. It features a clean, responsive UI served directly by the Python backend.

### Key Features

- **Resume Parsing**: Extract key skills and experience from your CV/resume (PDF, DOCX)
- **Job Description Analysis**: Identify key requirements from job postings (text or image)
- **Company Research**: Automatically gather company information via Exa AI (optional)
- **AI-Powered Generation**: Create tailored, professional cover letters using AI (via OpenRouter)
- **Integrated Frontend**: UI built with Jinja2 templates, styled with Tailwind CSS and Daisy UI
- **Environment-based Configuration**: Easily configure API keys, CORS, rate limits, etc.
- **Monitoring & Logging**: Prometheus metrics, request ID tracking, and detailed logging
- **Rate Limiting**: Protects API endpoints from abuse
- **Docker Containerization**: Easy deployment with Docker and Docker Compose

## Architecture

- **Backend**: FastAPI (Python)
- **Templating**: Jinja2
- **Styling**: Tailwind CSS with Daisy UI (built using PostCSS/Node.js)
- **Containerization**: Docker

## Getting Started

### Prerequisites

- Python 3.9+
- `pip` or `uv` (Python package installer)
- Node.js and npm (Required *only* if you need to modify/rebuild CSS)
- Docker and Docker Compose (Optional, for containerized deployment)

### Installation & Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/0xrsydn/coverletter.git
    cd coverletter/src
    ```

2.  **Set up Python Environment:**
    ```bash
    # Create a virtual environment (optional but recommended) using uv
    uv venv
    source .venv/bin/activate  # Linux/Mac
    # .venv\Scripts\activate    # Windows

    # Install Python dependencies using uv
    uv pip install -r requirements.txt
    # Or using pip:
    # python -m venv .venv 
    # pip install -r requirements.txt
    ```

3.  **Configure Environment:**
    ```bash
    cp .env.example .env
    # Edit .env and add your API keys (OPENROUTER_API_KEY, EXA_API_KEY)
    ```

4.  **(Optional) Frontend Asset Development:**
    If you need to modify the CSS:
    ```bash
    # Install Node.js dependencies
    npm install

    # Watch for CSS changes and rebuild automatically
    npm run watch:css

    # Or build CSS once for production
    # npm run build:css:prod
    ```
    *Note: Pre-built CSS (`static/css/main.css`) is included, so Node.js/npm is not needed just to run the app.*

5.  **Run the Application:**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    Access the application at http://localhost:8000

### Docker Deployment

1.  **Ensure `.env` file is configured** in the `src/` directory with your production settings (especially `APP_ENV=production` and API keys).
2.  **Build and run using Docker Compose:**
    ```bash
    # From the project root (coverletter/)
    docker compose -f src/docker-compose.yml up -d --build
    ```
    The application will be available at http://localhost:8000 (or your server's IP). For development environment, you can      
    comment out Loki logging configuration if you don't need it.

## Environment Configuration

The application uses environment variables defined in the `.env` file:

-   `APP_ENV`: Environment (`development`, `production`) - controls debugging, rate limits, CORS.
-   `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins (use `*` for development if needed).
-   `OPENROUTER_API_KEY`: API key for OpenRouter.
-   `OPENROUTER_MODEL`: Model to use (default: `google/gemini-2.0-flash-001`).
-   `EXA_API_KEY`: API key for Exa AI.

*(Refer to `config.py` and `.env.example` for more details)*

## Rate Limiting

IP-based rate limiting is applied (configurable in `config.py` based on `APP_ENV`). Check response headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) for status.

## Monitoring and Logging

-   **Prometheus Metrics**: `/metrics` endpoint
-   **Health Check**: `/health` endpoint
-   **Request ID**: `X-Request-ID` header in responses and logs
-   **Logging**: Detailed logs with request IDs sent to standard output (or configured Docker logging driver).

## Project Structure (`src/`)

```
├── main.py              # FastAPI app, middleware, main endpoint
├── config.py            # Load configuration from .env
├── requirements.txt     # Python dependencies
├── Dockerfile           # Defines the production container image
├── docker-compose.yml   # Docker Compose for production deployment
├── docker-compose.local.yml # Docker Compose for local development
├── modules/             # Core application logic modules
│   ├── company/         # Company info retrieval
│   ├── cover_letter/    # Cover letter generation logic
│   ├── document/        # CV/Resume parsing
│   ├── errors/          # Custom exceptions and handlers
│   ├── job/             # Job description analysis
│   ├── monitoring/      # Prometheus metrics setup
│   └── rate_limit/      # Rate limiting logic
├── static/              # Static files (CSS, JS, images)
│   └── css/
│       └── main.css     # Compiled production CSS
│       └── tailwind.css # Input CSS for PostCSS
├── templates/           # Jinja2 HTML templates
│   └── index.html       # Main HTML page
├── package.json         # Node.js dependencies (for CSS build)
├── tailwind.config.js   # Tailwind configuration
├── postcss.config.js    # PostCSS configuration
└── .env.example         # Example environment variables
```

## API Endpoints

-   `GET /`: Serves the main HTML interface.
-   `POST /api/generate_cover_letter`: Generate cover letter (used by the frontend form).
-   `GET /health`: Health check endpoint.
-   `GET /metrics`: Prometheus metrics endpoint.
-   *(Module-specific endpoints exist under `/job/`, `/company/` etc. but are primarily used internally by the main generation logic)*

## License

[MIT](LICENSE) 