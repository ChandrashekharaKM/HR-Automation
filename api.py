from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="SwipeGen-Automation API")


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/info")
async def info():
    return JSONResponse({
        "project": "SwipeGen-Automation",
        "description": "Automation toolkit for recruitment workflows",
    })


# Example trigger endpoint (safe placeholder)
# Extend this to call existing script functions with proper authentication and validation.
@app.post("/trigger/{task}")
async def trigger_task(task: str):
    # Do NOT execute arbitrary shell commands here.
    # Map allowed task names to internal functions if needed.
    allowed = {"generate_offers": "Generate offer letters", "generate_certificates": "Generate certificates"}
    if task not in allowed:
        return JSONResponse({"error": "unknown task"}, status_code=400)
    return JSONResponse({"task": task, "status": "accepted", "description": allowed[task]})
