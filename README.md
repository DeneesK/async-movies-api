# MovieAPI

#### API Service for flexible search in the database of films and actors, with the ability to rank responses and specify additional parameters.

# To launch project:

- сreate .env files based on env.examples
- `docker-compose up`

OpenApi: `http://127.0.0.1:8000/api/openapi#/`

# To run tests:

### 1. Build service image in fastapi-solution/ run:
`docker-compose build`
### 2. Next, you can run the container with tests in fastapi-solution/tests:
`docker-compose up`

### 3. URL Swagger:
`http://127.0.0.1:8000/api/openapi#/`
