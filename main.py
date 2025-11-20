from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from TikTokApi import TikTokApi
import asyncio
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="templates")

async def get_api():
    api = TikTokApi()
    ms_token = os.getenv("MS_TOKEN", "")  # Render'da environment variable olacak
    await api.create_sessions(ms_tokens=[ms_token] if ms_token else [], num_sessions=1, sleep_after=5)
    return api

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.get_template("index.html").render({"request": request})

@app.post("/", response_class=HTMLResponse)
async def get_story(request: Request, username: str = Form(...)):
    username = username.lstrip("@").strip()
    try:
        api = await get_api()
        user = api.user(username=username)
        user_info = await user.info()
        stories = await user.stories()

        story_list = []
        for story in stories:
            if story.get("video"):
                story_list.append({
                    "video_url": story["video"]["playAddr"][0],
                    "cover": story["video"]["cover"][0],
                    "type": "video"
                })
            elif story.get("image"):
                story_list.append({
                    "images": story["image"]["urlList"],
                    "cover": story["image"]["urlList"][0],
                    "type": "image"
                })

        return templates.get_template("index.html").render({
            "request": request,
            "username": username,
            "stories": story_list,
            "user_info": user_info
        })
    except Exception as e:
        return templates.get_template("index.html").render({
            "request": request,
            "error": "Story yok, hesap gizli veya hata oluştu."
        })
