# app/lambda_handler.py

from mangum import Mangum
from app.main import app   # uses your existing FastAPI app
handler = Mangum(app)
