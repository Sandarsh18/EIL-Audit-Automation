from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.endpoints import router
import traceback
import sys

app = FastAPI(title="EIL Audit Automation API")

@app.get("/health")
def root_health_check():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full traceback to the terminal for debugging
    print(f"Global Exception Handler caught an error on {request.method} {request.url}:", file=sys.stderr)
    traceback.print_exc()
    
    # Always return a JSON response so the frontend never gets HTML or plaintext
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
