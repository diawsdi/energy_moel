from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.json_encoders import custom_jsonable_encoder

# Create a custom response class that uses our custom JSON encoder
class CustomJSONResponse(JSONResponse):
    def render(self, content):
        return super().render(custom_jsonable_encoder(content))

# Configure FastAPI to use our custom response class
app = FastAPI(
    title=settings.PROJECT_NAME, 
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    default_response_class=CustomJSONResponse
)
origins = ["*"]
# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "Welcome to the Energy Model API!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"} 