from fastapi import FastAPI

app = FastAPI(title="CampusVolt API")


# Report that the service is up.
@app.get("/v1/health")
def health():
    return {"status": "ok"}
