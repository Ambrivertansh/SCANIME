FROM python:3.12

WORKDIR /app

RUN apt-get update && apt-get upgrade -y
RUN apt-get install git wget pv jq aria2 python3-dev mediainfo gcc libsm6 libxext6 libfontconfig1 libxrender1 -y
RUN apt-get install -y curl libcurl4-openssl-dev
RUN apt-get install -y gnupg libnss3 libatk-bridge2.0-0 libxcomposite1 libxdamage1 libxrandr2
RUN apt-get install -y libgbm1 libasound2 libpangocairo-1.0-0 libcups2 
RUN rm -rf /var/lib/apt/lists/*


COPY --from=mwader/static-ffmpeg:6.1 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:6.1 /ffprobe /usr/local/bin/


COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt


RUN pip install --upgrade yt-dlp[curl-cffi,default]

RUN playwright install chromium
RUN playwright install-deps chromium

COPY . /app

CMD ["bash", "start.sh"]
