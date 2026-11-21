from fastapi import FastAPI


app = FastAPI(title="Plant Disease Project")


@app.get("/", tags=["health"])
def hello_world() -> dict[str, str]:
    """Return a simple health-check response."""
    return {"message": "Hello World"}
