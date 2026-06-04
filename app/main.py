from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create FastAPI instance
app = FastAPI()

# Define a GET endpoint
@app.get("/")
def read_root():
    """
    Root endpoint returning a simple Hello World message.
    """
    return JSONResponse(content={"message": "Hello, World!"})
