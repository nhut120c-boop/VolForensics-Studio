"""
FastAPI Server for VolForensics Studio
Provides REST API, SSE streaming, file dialogs, and plugin management.
"""

import os
import sys
import uuid
import json
import asyncio
import subprocess
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .plugin_catalog import VOLATILITY_3_PLUGINS, VOLATILITY_2_PLUGINS, QUICK_TRIAGE_RECIPES
from .volatility_runner import VolatilityRunner, tasks_store

app = FastAPI(title="VolForensics Studio API")

# Current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
WORKSPACE_DIR = os.path.dirname(BASE_DIR)

runner = VolatilityRunner(workspace_dir=WORKSPACE_DIR)
background_jobs = set()


def launch(coroutine):
    job = asyncio.create_task(coroutine)
    background_jobs.add(job)
    job.add_done_callback(background_jobs.discard)


async def validate_request(req, plugin_name=None):
    req.image_path = req.image_path.strip().strip('"')
    try:
        await asyncio.to_thread(runner.validate, req.engine, req.image_path, plugin_name)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

# Request Models
class RunTaskRequest(BaseModel):
    engine: str = "vol3" # vol3 or vol2
    image_path: str
    plugin_name: str
    profile: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    custom_args: Optional[str] = None

class ConfigUpdateRequest(BaseModel):
    vol3_command: Optional[str] = None
    vol2_python: Optional[str] = None
    vol2_script: Optional[str] = None
    vol2_custom_exe: Optional[str] = None
    output_dir: Optional[str] = None

class QuickTriageRequest(BaseModel):
    engine: str = "vol3"
    image_path: str
    profile: Optional[str] = None


@app.get("/api/config")
def get_config():
    """Returns detected Volatility environment configuration"""
    return runner.get_config()


@app.post("/api/config")
def update_config(req: ConfigUpdateRequest):
    """Updates binary locations"""
    try:
        runner.update_config(req.model_dump(exclude_unset=True))
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return runner.get_config()


@app.post("/api/pick-file")
def pick_file():
    """Opens native Windows file picker dialog to choose memory dump"""
    ps_script = """
    Add-Type -AssemblyName System.Windows.Forms
    $f = New-Object System.Windows.Forms.OpenFileDialog
    $f.Filter = "Memory Dumps (*.raw;*.vmem;*.dmp;*.dd;*.img;*.bin;*.mem)|*.raw;*.vmem;*.dmp;*.dd;*.img;*.bin;*.mem|All Files (*.*)|*.*"
    $f.Title = "Select Memory Dump File"
    if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        Write-Output $f.FileName
    }
    """
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps_script], capture_output=True, text=True, timeout=120)
        if res.returncode:
            raise RuntimeError(res.stderr.strip() or 'Không mở được hộp chọn file.')
        selected_path = res.stdout.strip()
        if selected_path and os.path.isfile(selected_path):
            file_size_mb = round(os.path.getsize(selected_path) / (1024 * 1024), 2)
            return {"status": "ok", "path": selected_path, "size_mb": file_size_mb}
        return {"status": "cancelled", "path": None}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/pick-folder")
def pick_folder():
    """Opens native Windows folder picker dialog"""
    ps_script = """
    Add-Type -AssemblyName System.Windows.Forms
    $f = New-Object System.Windows.Forms.FolderBrowserDialog
    $f.Description = "Select Folder"
    if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        Write-Output $f.SelectedPath
    }
    """
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps_script], capture_output=True, text=True, timeout=120)
        if res.returncode:
            raise RuntimeError(res.stderr.strip() or 'Không mở được hộp chọn thư mục.')
        selected_path = res.stdout.strip()
        if selected_path and os.path.isdir(selected_path):
            return {"status": "ok", "path": selected_path}
        return {"status": "cancelled", "path": None}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/plugins")
def get_plugins():
    """Returns available plugins for Volatility 2 and Volatility 3"""
    return {
        "vol3": VOLATILITY_3_PLUGINS,
        "vol2": VOLATILITY_2_PLUGINS,
        "recipes": QUICK_TRIAGE_RECIPES
    }


@app.post("/api/run")
async def run_plugin(req: RunTaskRequest, background_tasks: BackgroundTasks):
    """Starts execution of a single volatility plugin"""
    await validate_request(req, req.plugin_name)
    if req.engine == 'vol2' and req.plugin_name not in ('imageinfo', 'kdbgscan') and not (req.profile or '').strip():
        raise HTTPException(status_code=400, detail='Nhập profile Volatility 2 hoặc chạy imageinfo để nhận diện trước.')
    catalog = VOLATILITY_3_PLUGINS if req.engine == 'vol3' else VOLATILITY_2_PLUGINS
    plugin = next(p for p in catalog if p['name'] == req.plugin_name)
    for option in plugin.get('options', []):
        if option.get('required') and not str((req.options or {}).get(option['name'], '')).strip():
            raise HTTPException(status_code=400, detail='Thiếu tùy chọn bắt buộc: ' + option['name'])
    task_id = str(uuid.uuid4())
    try:
        runner.create_task(task_id, req.engine, req.image_path, req.plugin_name, req.profile, req.options, req.custom_args)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    launch(
        runner.run_task(
            task_id=task_id,
            engine=req.engine,
            image_path=req.image_path,
            plugin_name=req.plugin_name,
            profile=req.profile,
            options=req.options or {},
            custom_args=req.custom_args
        )
    )

    return {"status": "started", "task_id": task_id}


@app.post('/api/preview')
def preview_command(req: RunTaskRequest):
    try:
        cmd = runner.build_command(req.engine, req.image_path, req.plugin_name, req.profile, req.options, req.custom_args)
        return {'command': subprocess.list2cmdline(cmd)}
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/run-triage")
async def run_triage(req: QuickTriageRequest):
    """Enqueues standard triage plugins for 1-click investigation"""
    await validate_request(req)
    recipes = QUICK_TRIAGE_RECIPES[req.engine]
    task_ids = []
    
    # Launch first task immediately
    for item in recipes:
        task_id = str(uuid.uuid4())
        task_ids.append({
            "task_id": task_id,
            "plugin": item["name"],
            "label": item["label"],
            "desc": item["desc"]
        })
        runner.create_task(task_id, req.engine, req.image_path, item['name'], req.profile)

    async def execute_sequence():
        profile = req.profile
        for item in task_ids:
            task = tasks_store[item['task_id']]
            if task['status'] == 'KILLED':
                continue
            if req.engine == 'vol2' and item['plugin'] != 'imageinfo' and not profile:
                task.update(status='ERROR', end_time=__import__('time').time(), duration=0)
                task['raw_logs'].append('Không nhận diện được profile. Nhập profile Volatility 2 và chạy lại.')
                continue
            if profile:
                task['profile'] = profile
                task['command_list'] = runner.build_command(req.engine, req.image_path, item['plugin'], profile, output_subfolder=task['output_dir'])
                task['command'] = subprocess.list2cmdline(task['command_list'])
            await runner.run_task(item['task_id'], req.engine, req.image_path, item['plugin'], profile)
            if req.engine == 'vol2' and not profile and item['plugin'] == 'imageinfo':
                import re
                match = re.search(r'Suggested Profile\(s\)\s*:\s*([^,\s]+)', '\n'.join(task['raw_logs']))
                if match:
                    profile = match.group(1)
    launch(execute_sequence())
    return {"status": "started", "tasks": task_ids}


@app.get("/api/tasks")
def list_tasks():
    """Lists all executed tasks with summary"""
    results = []
    for tid, t in sorted(tasks_store.items(), key=lambda x: x[1]["start_time"], reverse=True):
        results.append({
            "id": tid,
            "engine": t["engine"],
            "plugin": t["plugin"],
            "image_path": os.path.basename(t["image_path"]),
            "status": t["status"],
            "start_time": t["start_time"],
            "duration": t["duration"],
            "rows_count": t.get('json_export', {}).get('rows_count', len(t.get("table_data", {}).get("rows", []))),
            "files_count": len(t.get("extracted_files", []))
        })
    return results


@app.get("/api/task/{task_id}")
def get_task(task_id: str):
    """Returns full details and output data of a specific task"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="Task not found")
    stored = tasks_store[task_id]
    is_memmap = stored['plugin'] in ('memmap', 'windows.memmap')
    if is_memmap:
        runner.prepare_legacy_memmap_export(stored)
    task = stored.copy()
    if is_memmap:
        task['table_data'] = {'columns': [], 'rows': []}
        task['raw_logs'] = stored.get('raw_logs', [])[-10:]
    # Remove internal process object for serialization
    task.pop("process", None)
    return task


@app.get('/api/task/{task_id}/export-json')
def download_task_json(task_id: str):
    get_task(task_id)
    export = tasks_store[task_id].get('json_export')
    if not export or not os.path.isfile(export['path']):
        raise HTTPException(status_code=404, detail='JSON chưa sẵn sàng; đợi tác vụ hoàn tất thành công.')
    return FileResponse(export['path'], media_type='application/json', filename=f'memmap_{task_id[:8]}.json')


@app.get("/api/task/{task_id}/stream")
async def stream_task_logs(task_id: str):
    """Server-Sent Events (SSE) streaming live logs for real-time terminal display"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        sent_index = 0
        while True:
            task = tasks_store.get(task_id)
            if not task:
                break
            
            logs = task["raw_logs"]
            while sent_index < len(logs):
                line = logs[sent_index]
                sent_index += 1
                yield f"data: {json.dumps({'line': line, 'status': task['status']})}\n\n"

            if task["status"] in ["SUCCESS", "FAILED", "ERROR", "CANCELLED", "KILLED"]:
                yield f"data: {json.dumps({'done': True, 'status': task['status'], 'duration': task['duration']})}\n\n"
                break

            await asyncio.sleep(0.3)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/task/{task_id}/kill")
def kill_task(task_id: str):
    """Terminates running task"""
    ok = runner.kill_task(task_id)
    return {"status": "killed" if ok else "not_running"}


@app.get("/api/open-folder")
def open_folder(path: str = Query(...)):
    """Opens folder in Windows Explorer"""
    if not os.path.isdir(path):
        raise HTTPException(status_code=404, detail='Không tìm thấy thư mục.')
    try:
        os.startfile(path)
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@app.get("/api/file-info")
def file_info(path: str = Query(...)):
    """Returns quick file stats (size, exists)"""
    if os.path.isfile(path):
        sz = os.path.getsize(path)
        return {"exists": True, "size_bytes": sz, "size_mb": round(sz / (1024 * 1024), 2)}
    return {"exists": False}


# Mount static assets
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>VolForensics Studio - UI loading...</h1>"
