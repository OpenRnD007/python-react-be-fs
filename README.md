# React Fullstack with Python and PostgreSQL (Complete)
## Backend Service to store data that was in the static json file from part 1

Starlette and PostgreSQL that can hold the data that was in the static
json le from part 1 in a sensible way.

## Features

•  Token-based authentication for secure API access

•  Create and Read operations for shipping data

•  Version tracking for data changes


## Prerequisites

Before you begin, ensure you have met the following requirements:

•  You have installed `Python 3.6` or above

•  You have installed the required dependencies listed in `requirements.txt`


## Configuration

Create a `.env` file in the root directory of the project with the following content:


`DATABASE_URL="your-database-url"`

`SECRET_KEY="your-secret-key"`


## Installation
For gitpod

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/OpenRnD007/python-react-be-fs)

For docker
```
docker-compose up --build
```

OR

To install the project without docker, follow these steps:

```
pip install -r requirements.txt
```

## Usage

To start the application, run the following command:

```
uvicorn app:app --reload
```

## API Endpoints

### GET /

Retrieves the current version of shipping data and returns it along with the shipping list.
```
curl -X POST http://localhost:8000/ -H 'Authorization: Token ENV_SECRET_KEY' -H 'Content-Type: application/json' -d '{"rf":"DATETIME | BLANK"}'
```

### POST /

Creates a new shipping entry in the database and updates the version information.
```
curl -X POST http://localhost:8000/ \
-H 'Content-Type: application/json' \
-H 'Authorization: Token ENV_SECRET_KEY' \
-d '{"type": "bill-of-lading", "title": "Bill of Lading", "position": 1, "image": "https://images.unsplash.com/photo-1612532275214-e4ca76d0e4d1?q=80&w=1887&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"}'

```

## Pydantic Models

### Shipping

Validates the input data for shipping-related operations.

### DateParam

Validates the input data for date-related operations.

## Database Tables

### shippingT

Stores information about shipping items.

### sversionT

Stores version information for all tables.

## Middleware

Includes custom `TokenAuthBackend` for authentication and `CORSMiddleware` for cross-origin requests.

## Event Handlers

Handles `startup` and `shutdown` events for managing database connections and schema creation.

## License
- MIT

## Author
Sumedh M
