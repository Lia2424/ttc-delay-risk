# API Structure

This document explains the organization of the FastAPI application.

## Directory Structure

```
api/
├── main.py              # Application entry point
├── config.py            # Configuration settings
├── models.py            # Pydantic request/response models
├── dependencies.py      # FastAPI dependencies (model loading)
├── routes/              # API route handlers
│   ├── health.py        # Health check and model info endpoints
│   └── predictions.py   # Prediction endpoints
├── services/            # Business logic
│   └── prediction_service.py  # Prediction service
└── start.sh            # Startup script
```

## File Responsibilities

### `main.py`
- Creates the FastAPI application instance
- Configures CORS middleware
- Registers routers
- Handles startup events (model loading)

### `config.py`
- Centralized configuration
- Path definitions
- API metadata
- Settings

### `models.py`
- Pydantic models for request validation
- Pydantic models for response serialization
- Schema examples for API documentation

### `dependencies.py`
- Model loading logic
- Dependency injection functions
- Global state management

### `routes/health.py`
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /model/info` - Model information

### `routes/predictions.py`
- `POST /predict` - Single prediction
- `POST /predict/batch` - Batch predictions

### `services/prediction_service.py`
- Business logic for predictions
- Risk level calculation
- Feature engineering coordination

## Benefits of This Structure

1. **Separation of Concerns**: Each file has a single responsibility
2. **Maintainability**: Easy to find and modify specific functionality
3. **Testability**: Services and routes can be tested independently
4. **Scalability**: Easy to add new routes or services
5. **Readability**: Clear organization makes the codebase easier to understand

## Adding New Features

### Adding a New Endpoint

1. Create route handler in `routes/` directory
2. Define request/response models in `models.py`
3. Add business logic in `services/` if needed
4. Register router in `main.py`

### Adding a New Service

1. Create service file in `services/` directory
2. Implement business logic
3. Import and use in route handlers

### Modifying Configuration

1. Update `config.py` with new settings
2. Import where needed

