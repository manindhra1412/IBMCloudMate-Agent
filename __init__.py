# myapp/__init__.py
from fastapi import FastAPI
from . import routes  # import your routes

app = FastAPI()

# Include routes here if needed
app.include_router(routes.router)
