from Tools.cworker import episode_worker, Bot
import asyncio
import os 
import shutil
from aiohttp import web

# 1. Zero-Disk Policy: Wipe everything on startup
downloads_path = ['Downloads', 'downloads']
for download_path in downloads_path:
    if os.path.exists(download_path) and os.path.isdir(download_path):
        shutil.rmtree(download_path)
        print(f"Wiped {download_path} successfully.")

# 2. Render Keep-Alive: Dummy Web Server
async def web_server():
    async def handle(request):
        # When Render pings the bot, it will see this message
        return web.Response(text="✲『SCANIME』✲ Engine is Online.")
    
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Binds to Port 8080 (or whatever Render assigns)
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Dummy Web Server running on port {port}")

# 3. Core Engine: Start Web Server & Workers
async def start_services():
    await web_server()
    
    # EXACTLY 3 Workers to protect 512MB RAM limit
    for i in range(3):
        asyncio.create_task(episode_worker(i))
    print("3 Workers initialized.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
    # Start the Pyrogram Bot
    Bot.run()
