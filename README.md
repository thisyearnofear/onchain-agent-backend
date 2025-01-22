# Onchain Agent Backend

This is the backend service for the Onchain Agent project. It provides API endpoints for interacting with the agent system.

## Setup

1. Install dependencies:

```bash
poetry install
```

2. Run the development server:

```bash
poetry run python -m src.agent_backend.index
```

## Docker

To run with Docker:

```bash
docker compose up -d
```

## Production Deployment (Render)

1. Fork/push this repository to your GitHub account

2. Create a new Web Service on Render:

   - Connect your GitHub repository
   - Select "Docker" as the environment
   - Set the following:
     - Name: onchain-agent-backend
     - Branch: main
     - Root Directory: ./
     - Docker Command: leave empty (uses CMD from Dockerfile)

3. Add Environment Variables:

   - Copy variables from `.env.example`
   - Add them in Render's environment variables section
   - For the database URL, use the Internal Database URL from your Render PostgreSQL service

4. Create a PostgreSQL Database:

   - Go to "New +" → "PostgreSQL"
   - Name: onchain-agent-db
   - Copy the Internal Database URL

5. Health Check:
   - Render automatically uses the `/health` endpoint
   - Verify status at: `https://your-service.onrender.com/health`

## Features & Status

### Phase 1: Production Infrastructure ✅

- [x] Dockerfile with proper configuration
- [x] Production Docker Compose setup
- [x] Environment variable management
- [x] Health check endpoints
- [x] PostgreSQL integration

### Phase 2: Security & Monitoring ✅

- [x] Rate limiting (200/day, 50/hour per IP)
- [x] Request validation
- [x] CORS setup
- [x] Logging configuration
- [x] Health monitoring
- [x] Global error handlers

Future Improvements:

- [ ] Authentication system
- [ ] API key management
- [ ] Request encryption
- [ ] Advanced monitoring
- [ ] Audit logging

### Phase 3: Deployment & Scaling ✅

- [x] CI/CD Pipeline with GitHub Actions
  - Automated tests on push/PR
  - Docker build and push
- [x] Production deployment on Render
  - Automatic SSL/TLS
  - Zero-downtime deployments
  - Database backups
- [x] Infrastructure documentation

## Environment Variables

See `.env.example` for required environment variables.

## Docker

The production Docker setup includes:

- Memory limits (1GB for app, 512MB for PostgreSQL)
- Log rotation (10MB max size, 3 files kept)
- Health checks for both services
- Proper container dependencies
- Python path configuration
- Curl for health monitoring

### Production Configuration

The application is configured for production with:

1. Resource Management:

   - App Service: 1GB memory limit, 512MB reservation
   - PostgreSQL: 512MB memory limit, 256MB reservation
   - Log rotation: 10MB max size, 3 files retained

2. Health Monitoring:

   - App endpoint: `GET /health`
   - PostgreSQL: `pg_isready` check
   - Automatic restarts on failure
   - Health check intervals: 30s for app, 5s for PostgreSQL

3. Environment Configuration:

   ```env
   # PostgreSQL Configuration
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=onchain_agent
   POSTGRES_HOST=postgres

   # CDP Configuration
   CDP_API_KEY_NAME=your_key_name
   CDP_API_KEY_PRIVATE_KEY=your_private_key

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_key

   # Server Configuration
   FLASK_RUN_PORT=5001
   ENVIRONMENT=production
   ```

4. Volume Management:
   - PostgreSQL data persistence
   - CDP API key mounting
   - Wallet credentials persistence

## Features

- AI-powered blockchain operations
- Automated wallet management for development and production
- Support for ERC-20 token and NFT deployment
- Testnet fund management
- Balance checking capabilities

## Development Setup

### Prerequisites

- Python 3.10+
- Poetry
- Docker Desktop
- PostgreSQL (for production)

### Installation

1. Install dependencies:

```bash
poetry install
```

2. Set up environment variables in `.env`:

```env
# PostgreSQL Configuration (for production)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=onchain_agent
POSTGRES_HOST=localhost

# CDP Configuration
CDP_API_KEY_NAME=your_key_name
CDP_API_KEY_PRIVATE_KEY=your_private_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key

# Server Configuration
FLASK_RUN_PORT=5001
```

3. Start the server:

```bash
PYTHONPATH=. poetry run python src/agent_backend/index.py
```

## Database Configuration

The application supports both SQLite (development) and PostgreSQL (production) databases:

### Development Mode

- Uses SQLite with `agent.db` file
- No additional configuration needed
- Tables are automatically created on startup

### Production Mode

1. Set `ENVIRONMENT=production` in your environment
2. Ensure PostgreSQL is running (via Docker or standalone)
3. Configure PostgreSQL environment variables
4. Run migrations: `poetry run alembic upgrade head`

## Development Plan Progress

### Phase 1: Production Infrastructure ✅

- [x] Database Migration Setup
  - [x] Created SQLAlchemy models
  - [x] Set up Alembic for migrations
  - [x] Created initial migration
- [x] Database Abstraction
  - [x] Implemented SQLite for development
  - [x] Added PostgreSQL support for production
  - [x] Created database configuration module
- [x] Docker Setup
  - [x] Created docker-compose.yml for PostgreSQL
  - [x] Added production database configuration
  - [x] Created Dockerfile for application
  - [x] Set up production Docker Compose with:
    - [x] Resource limits
    - [x] Health monitoring
    - [x] Log rotation
    - [x] Volume management

### Phase 2: Security & Monitoring ✅

- [x] API Security
  - [x] Added rate limiting (200/day, 50/hour global; 100/day, 30/hour for chat)
  - [x] Implemented request validation with marshmallow schemas
  - [x] Set up CORS properly
- [x] Monitoring
  - [x] Added logging configuration
  - [x] Implemented health checks with database connectivity testing
  - [x] Added request logging and error tracking
- [x] Error Handling
  - [x] Added global error handlers for validation, rate limits, and server errors
  - [x] Improved error responses with consistent JSON format
  - [x] Added request validation for all endpoints

Future Security Improvements:

- [ ] Authentication & Authorization
  - [ ] Add JWT authentication
  - [ ] Implement role-based access control
  - [ ] Add API key management
- [ ] Enhanced Security
  - [ ] Add request signing for sensitive operations
  - [ ] Implement IP whitelisting
  - [ ] Add request encryption for sensitive data
- [ ] Advanced Monitoring
  - [ ] Set up APM (Application Performance Monitoring)
  - [ ] Add distributed tracing
  - [ ] Implement advanced metrics collection

### Phase 3: Deployment & Scaling (In Progress)

- [x] CI/CD Pipeline
  - [x] Set up GitHub Actions workflow
  - [x] Added automated testing with PostgreSQL
  - [x] Configured Docker build and push
- [ ] Infrastructure
  - [ ] Choose cloud provider
  - [ ] Set up load balancing
  - [ ] Configure auto-scaling
- [ ] Documentation
  - [ ] API documentation
  - [ ] Deployment guide
  - [ ] Monitoring guide

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

1. On every push and pull request to main:

   - Runs automated tests with PostgreSQL
   - Validates code formatting
   - Checks dependencies

2. On merge to main:
   - Builds Docker image
   - Pushes to Docker Hub
   - Tags with latest version

Required Secrets:

- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub access token

### Deployment

The application can be deployed to any cloud provider that supports Docker containers. Recommended setup:

1. Infrastructure Requirements:

   - 2+ CPU cores
   - 2GB+ RAM
   - 20GB+ SSD storage
   - Managed PostgreSQL database

2. Environment Variables:

   ```env
   # Required for production
   ENVIRONMENT=production
   POSTGRES_USER=<db-user>
   POSTGRES_PASSWORD=<db-password>
   POSTGRES_DB=onchain_agent
   POSTGRES_HOST=<db-host>
   CDP_API_KEY_NAME=<your-key-name>
   CDP_API_KEY_PRIVATE_KEY=<your-private-key>
   OPENAI_API_KEY=<your-openai-key>
   ```

3. Deployment Steps:

   ```bash
   # Pull latest image
   docker pull <username>/onchain-agent-backend:latest

   # Run with production config
   docker run -d \
     --name onchain-agent \
     -p 5001:5001 \
     --env-file .env \
     -v /path/to/cdp_api_key.json:/app/cdp_api_key.json \
     <username>/onchain-agent-backend:latest
   ```

4. Health Monitoring:

   ```bash
   # Check application health
   curl http://your-domain:5001/health

   # View logs
   docker logs -f onchain-agent
   ```

## Troubleshooting

### CDP SDK Authentication Issues

There are two ways to configure the CDP SDK:

1. Using JSON file:

   - Download API key JSON from CDP Portal
   - Place in project root as `cdp_api_key.json`
   - SDK will automatically load configuration

2. Using Environment Variables:
   - Set `CDP_API_KEY_NAME` and `CDP_API_KEY_PRIVATE_KEY` in `.env`
   - Ensure keys are properly formatted
   - SDK will use these variables for authentication

### Important Notes About Wallets

- In development mode, wallet data is stored in SQLite
- In production mode, wallet data is stored in PostgreSQL
- Wallet seeds should be securely stored and backed up
- ETH transfers are disabled for security reasons

## Testing

Run database tests:

```bash
PYTHONPATH=. poetry run python test_db.py
```

## Wallet Management

### Development Mode

- A new wallet is automatically created and managed by the CDP SDK
- Wallet credentials are saved in `wallet_credentials.json`
- Wallet seed is encrypted and saved in `dev_wallet_seed.json`
- Each development session maintains its own wallet for testing
- Wallet data is persisted between server restarts

### Production Mode

Set the following environment variables:

```bash
export CDP_WALLET_ID="your-production-wallet-id"
```

## Configuration

### Environment Variables

Development:

- `OPENAI_API_KEY`: Your OpenAI API key
- `FLASK_RUN_PORT`: Server port (default: 5001)

Production:

- `CDP_WALLET_ID`: Production wallet ID
- Additional environment variables as needed for production deployment

### CDP API Configuration

The CDP API requires credentials in `cdp_api_key.json`:

```json
{
  "name": "organizations/your-org-id/apiKeys/your-key-id",
  "privateKey": "your-private-key"
}
```

## Agent Capabilities

The agent can perform the following blockchain operations:

1. Deploy ERC-20 tokens

   - Required parameters: name, symbol
   - Example: "Deploy a new token called MyToken with symbol MTK"
   - Automatically saves deployed token address to database
   - Network: Base Sepolia testnet

2. Deploy NFTs

   - Required parameters: name, symbol
   - Example: "Create an NFT collection called MyNFT with symbol MNFT"
   - Automatically saves deployed NFT address to database
   - Network: Base Sepolia testnet

3. Request testnet funds

   - No parameters required
   - Automatically uses the configured wallet
   - Example: "Request testnet funds"
   - Provides Base Sepolia testnet ETH
   - Useful for covering gas fees

4. Check wallet balances
   - Required parameter: wallet address
   - Example: "Check the balance of 0x..."
   - Shows ETH balance on Base Sepolia
   - Can check any wallet address

Note: ETH transfers are disabled for security reasons.

### Conversation Examples

The agent understands natural language requests. Here are some example conversations:

1. Deploying a token:

   ```
   User: "Can you create a new token called PapaToken with symbol PAPA?"
   Agent: "I'll help you deploy an ERC-20 token called PapaToken (PAPA) on Base Sepolia..."
   ```

2. Requesting funds:

   ```
   User: "I need some testnet ETH"
   Agent: "I'll request testnet funds for your wallet..."
   ```

3. Checking balance:
   ```
   User: "What's the balance of my wallet?"
   Agent: "I'll check the balance of your wallet address..."
   ```

### Error Handling

The agent handles common errors and provides helpful feedback:

- Insufficient gas fees
- Failed transactions
- Network issues
- Invalid parameters

## Docker Deployment

### Prerequisites

- Docker Desktop installed and running
- `.env` file configured with all required variables
- CDP API credentials in `cdp_api_key.json`
- Wallet credentials in `wallet_credentials.json` (if reusing an existing wallet)

### Development

Run PostgreSQL only (for local development):

```bash
docker compose up postgres -d
```

### Production

Run the complete stack:

```bash
# Build and start all services
docker compose up --build -d

# Run database migrations
docker compose exec app poetry run alembic upgrade head

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Container Management

- Check container status: `docker compose ps`
- View logs for specific service: `docker compose logs app -f`
- Restart a service: `docker compose restart app`
- Remove volumes and containers: `docker compose down -v`

### Health Checks

- PostgreSQL: `docker compose exec postgres pg_isready -U postgres`
- Application: `curl http://localhost:5001/health`

### Troubleshooting Docker

1. If containers fail to start:
   - Check logs: `docker compose logs`
   - Verify environment variables
   - Ensure ports are not in use
2. Database connection issues:

   - Confirm PostgreSQL is healthy
   - Check database credentials
   - Verify network connectivity

3. Volume mounting issues:
   - Ensure credential files exist
   - Check file permissions
   - Verify volume paths
