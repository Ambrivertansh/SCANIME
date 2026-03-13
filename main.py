from Tools.cworker import episode_worker, Bot
import asyncio
import os 
import shutil

downloads_path = ['Downloads', 'downloads']

for download_path in downloads_path:
  if os.path.exists(download_path) and os.path.isdir(download_path):
    shutil.rmtree(download_path)


if __name__ == "__main__":
  loop = asyncio.get_event_loop()
  for i in range(6):
    loop.create_task(episode_worker(i))
  Bot.run()


