from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.config import Config
from starlette.authentication import (AuthenticationBackend, AuthenticationError, SimpleUser, AuthCredentials)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
import databases
import sqlalchemy
import uvicorn
from datetime import datetime

# Configuration for the database and the secret key for token authentication
# The '.env' file contains environment-specific variables that are read into the application's configuration.
config = Config('.env')

# DATABASE_URL is the database connection string that is used to connect to the database.
# It is obtained from the '.env' file.
DATABASE_URL = config('DATABASE_URL', cast=str)

# SECRET_KEY is used for token authentication to ensure secure communication.
# It is obtained from the '.env' file with a default value provided if not set.
SECRET_KEY = config('SECRET_KEY', cast=str, default='your-secret-key')

# Database setup
# An instance of the Database class is created with the DATABASE_URL.
# This will be used to manage database connections.
database = databases.Database(DATABASE_URL)

# Metadata instance that will be used to bind the engine, can be used to create or drop the database schema.
metadata = sqlalchemy.MetaData()

# Pydantic models for input validation
class Shipping(BaseModel):
    type: str = Field(..., min_length=2)
    title: str = Field(..., min_length=2)
    position: int
    image: str = Field(..., min_length=2)

class DateParam(BaseModel):
    rf: str = Field(..., max_length=26)

# SQLAlchemy table for storing shipping
shippingT = sqlalchemy.Table(
    "shipping",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("type", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("position", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("title", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("image", sqlalchemy.String, nullable=False),
)

# SQLAlchemy table for storing versions information of all tables
sversionT = sqlalchemy.Table(
    "sversion",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("type", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("datetime", sqlalchemy.DateTime, nullable=False),
)

# Authentication backend
# The TokenAuthBackend class is a custom authentication backend that uses token-based authentication.
class TokenAuthBackend(AuthenticationBackend):
    # The authenticate method is an asynchronous method that checks for the presence of an 'Authorization' header in the request.
    async def authenticate(self, request):
        # If the 'Authorization' header is not present, an AuthenticationError is raised.
        if "Authorization" not in request.headers:
            raise AuthenticationError('Auth token required')
        auth = request.headers["Authorization"]
        # The 'Authorization' header is split into the scheme and the token.
        scheme, token = auth.split()
        # If the scheme is 'token' and the token matches the SECRET_KEY, authentication is successful.
        if scheme.lower() == 'token' and token == SECRET_KEY:
            return AuthCredentials(["authenticated"]), SimpleUser("admin")
        # If the token does not match, an AuthenticationError is raised.
        raise AuthenticationError('Invalid token')

# Middleware configuration
# A list of middleware is defined, including the custom TokenAuthBackend and CORSMiddleware for cross-origin requests.
middleware = [Middleware(CORSMiddleware, allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"],expose_headers=["*"]), Middleware(AuthenticationMiddleware, backend=TokenAuthBackend())]

# Application instance
# An instance of the Starlette framework is created with debugging enabled and the previously defined middleware.
app = Starlette(debug=True, routes=[], middleware=middleware)

# Event handlers for the application lifecycle
# The startup event handler connects to the database and creates the tables using SQLAlchemy.
@app.on_event("startup")
async def startup():
    await database.connect()
    # Create the tables
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)

# The shutdown event handler disconnects from the database.
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.route('/', methods=["POST"])
async def read_shippings(request):
    """
    An asynchronous route handler for POST requests on the root endpoint.
    It retrieves the current version of shipping data and returns it along with the shipping list.
    If the version has not changed since the last request, it returns an empty shipping list.
    """
    # Parse the request body as JSON and validate it against the DateParam Pydantic model.
    req = await request.json()
    data = DateParam(**req)

    # Query the 'sversion' table to get the current version of the 'shipping' data.
    sversion_query = sversionT.select().where(sversionT.c.type == 'shipping')
    sversion_result = await database.fetch_all(sversion_query)

    # Convert the result into a list of dictionaries with ISO-formatted datetimes.
    versionlist = [{key: value.isoformat() if isinstance(value, datetime) else value for key, value in dict(r).items()} for r in sversion_result]
    current_version = versionlist[0] if versionlist else {}

    # If the 'datetime' in the current version matches the 'rf' field in the request, return an empty list.
    if 'datetime' in current_version and current_version['datetime'] == data.rf:
        return JSONResponse({"shipping": [], "version": current_version})

    # Otherwise, query the 'shipping' table and return the result along with the current version.
    query = shippingT.select()
    result = await database.fetch_all(query)
    shipping_list = [dict(r) for r in result]
    
    return JSONResponse({"shipping": shipping_list, "version": current_version})

@app.route('/create', methods=["POST"])
async def create_shipping(request):
    """
    An asynchronous route handler for POST requests on the root endpoint.
    It creates a new shipping entry in the database and updates the version information.
    """
    try:
        # Parse the request body as JSON and validate it against the Shipping Pydantic model.
        data = await request.json()
        shipping = Shipping(**data)

        # Insert the new shipping data into the 'shipping' table and get the record ID.
        query = shippingT.insert().values(type=shipping.type, position=shipping.position, image=shipping.image, title=shipping.title)
        last_record_id = await database.execute(query)

        # Update or insert the version information in the 'sversion' table.
        sversion_query = sversionT.select().where(sversionT.c.type == 'shipping')
        sversion_result = await database.fetch_all(sversion_query)
        if len(sversion_result) > 0:
            squery = sversionT.update().where(sversionT.c.type == 'shipping').values(datetime=sqlalchemy.sql.func.now())
        else:
            squery = sversionT.insert().values(type="shipping", datetime=sqlalchemy.sql.func.now())
        await database.execute(squery)

        # Return the new shipping data along with the record ID.
        return JSONResponse({"id": last_record_id, "type": shipping.type, "position": shipping.position, "image": shipping.image, "title": shipping.title})
    except ValidationError as e:
        return JSONResponse({"error": e.errors()}, status_code=400)

# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)