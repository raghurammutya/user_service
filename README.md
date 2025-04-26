# User Service

## Overview

The `user_service` is a Python-based microservice built using FastAPI and RabbitMQ. It provides features such as user registration, authentication (Keycloak, Google, Facebook), and family group management.

## Features

- Register and authenticate users with username/password or third-party logins.
- Modify, query, and delete user data.
- Create and manage family groups.
- Integrates with Keycloak for user management.
- Publishes user-related events via RabbitMQ.

## Prerequisites

- Docker and Docker Compose installed.
- Python 3.10+ for local development.

## Getting Started

### Running Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/stocksblitz-user-service.git
   cd stocksblitz-user-service
   ```
2. Create a file for local development:
   ```bash
   cp .env.example .env
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the service:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

# Dev Trigger Test
