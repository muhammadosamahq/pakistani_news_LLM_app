from fastapi import FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every
from datetime import datetime
import os
import json

app = FastAPI()

data_directory = "../data"

@app.on_event("startup")
@repeat_every(seconds=60*60*24)  # Repeat every 24 hours
async def load_data():
    today_date = datetime.now().strftime("%Y-%m-%d")
    global data
    data = {
        "business": {
            "summary": get_all_file_paths(f"{data_directory}/{today_date}/business/summary"),
            "stats": get_all_file_paths(f"{data_directory}/{today_date}/business/stats")
        },
        "pakistan": {
            "summary": get_all_file_paths(f"{data_directory}/{today_date}/pakistan/summary"),
            "stats": get_all_file_paths(f"{data_directory}/{today_date}/pakistan/stats")
        }
    }
    print("Data loaded successfully")

def get_all_file_paths(directory):
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    return file_paths

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/load_data")
async def load_data_endpoint():
    await load_data()
    return {"status": "Data loaded successfully"}

@app.get("/summaries/{category}/all")
async def get_summaries(category: str):
    if category not in data:
        raise HTTPException(status_code=404, detail="Category not found")
    summaries = {}
    for summary_path in data[category]["summary"]:
        file_name = os.path.basename(summary_path)
        file_id = os.path.splitext(file_name)[0]
        with open(summary_path, 'r', encoding='utf-8') as file:
            summary = json.load(file)
            summaries[file_id] = summary["summary"]
    return {"summaries": summaries, "len": len(summaries)}

@app.get("/summaries/{category}/{summary_id}")
async def get_summary_by_id(category: str, summary_id: str):
    if category not in data:
        raise HTTPException(status_code=404, detail="Category not found")
    summary_path = f"{data_directory}/{datetime.now().strftime('%Y-%m-%d')}/{category}/summary/{summary_id}.json"
    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="Summary not found")
    with open(summary_path, 'r', encoding='utf-8') as file:
        summary = json.load(file)
    return {"summary": summary["summary"]}

@app.get("/meta_data/{category}/all")
async def get_meta_data(category: str):
    if category not in data:
        raise HTTPException(status_code=404, detail="Category not found")
    meta_data = {}
    for meta_data_path in data[category]["summary"]:
        file_name = os.path.basename(meta_data_path)
        file_id = os.path.splitext(file_name)[0]
        with open(meta_data_path, 'r', encoding='utf-8') as file:
            meta = json.load(file)
            meta_data[file_id] = meta["meta_data"]
    return {"meta_data": meta_data, "len": len(meta_data)}

@app.get("/meta_data/{category}/{meta_id}")
async def get_meta_data_by_id(category: str, meta_id: str):
    if category not in data:
        raise HTTPException(status_code=404, detail="Category not found")
    meta_data_path = f"{data_directory}/{datetime.now().strftime('%Y-%m-%d')}/{category}/summary/{meta_id}.json"
    if not os.path.exists(meta_data_path):
        raise HTTPException(status_code=404, detail="Meta data not found")
    with open(meta_data_path, 'r', encoding='utf-8') as file:
        meta_data = json.load(file)
    return {"meta_data": meta_data["meta_data"]}

@app.get("/stats/{category}/all")
async def get_stats(category: str):
    if category not in data:
        raise HTTPException(status_code=404, detail="Category not found")
    stats = []
    for stats_path in data[category]["stats"]:
        with open(stats_path, 'r', encoding='utf-8') as file:
            stat = json.load(file)
            stats.append(stat)
    return {"stats": stats}

@app.get("/stats/{category}/{stat_id}")
async def get_stat_by_id(category: str, stat_id: str):
    if category not in data:
        raise HTTPException(status_code=404, detail="Category not found")
    stats_path = f"{data_directory}/{datetime.now().strftime('%Y-%m-%d')}/{category}/stats/{stat_id}.json"
    if not os.path.exists(stats_path):
        raise HTTPException(status_code=404, detail="Stat not found")
    with open(stats_path, 'r', encoding='utf-8') as file:
        stat = json.load(file)
    return {"stat": stat}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)