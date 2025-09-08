from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
from pathlib import Path
import uvicorn

app = FastAPI(title="Device Filter API", description="API for filtering devices, brands, series, models for spare parts")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/webapp", response_class=HTMLResponse)
async def get_webapp():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# Path to the filters JSON file
FILTERS_PATH = Path(__file__).parent / "stocks" / "filters.json"

# Load filters data
def load_filters():
    try:
        with open(FILTERS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Filters file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON in filters file")

filters_data = load_filters()

@app.get("/api/devices")
async def get_devices():
    return {"devices": list(filters_data["devices"].keys())}

@app.get("/api/brands/{device}")
async def get_brands(device: str):
    if device not in filters_data["devices"]:
        raise HTTPException(status_code=404, detail="Device not found")
    brands = filters_data["devices"][device]["brands"]
    return {"brands": list(brands.keys())}

@app.get("/api/series/{device}/{brand}")
async def get_series(device: str, brand: str):
    if device not in filters_data["devices"]:
        raise HTTPException(status_code=404, detail="Device not found")
    brands = filters_data["devices"][device]["brands"]
    if brand not in brands:
        raise HTTPException(status_code=404, detail="Brand not found")
    series = brands[brand]["series"]
    return {"series": list(series.keys())}

@app.get("/api/models/{device}/{brand}/{series}")
async def get_models(device: str, brand: str, series: str):
    if device not in filters_data["devices"]:
        raise HTTPException(status_code=404, detail="Device not found")
    brands = filters_data["devices"][device]["brands"]
    if brand not in brands:
        raise HTTPException(status_code=404, detail="Brand not found")
    series_data = brands[brand]["series"]
    if series not in series_data:
        raise HTTPException(status_code=404, detail="Series not found")
    models = series_data[series]["models"]
    return {"models": models}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)