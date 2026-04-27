from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import yt_dlp
import os
import urllib.request
import urllib.parse

app = FastAPI()

# Tarayıcı güvenlik engellerini aşmak için CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Klasördeki diğer dosyalar için
app.mount("/static", StaticFiles(directory="."), name="static")

# 1. ANA SAYFA ROTASI
@app.get("/")
async def home():
    if os.path.exists("main.html"):
        return FileResponse('main.html')
    return {"durum": "hata", "mesaj": "main.html dosyasi bulunamadi!"}

# 2. LİNK ÇÖZME VE VİDEO BİLGİSİ ALMA ROTASI
@app.get("/link-coz")
async def link_coz(video_url: str):
    ayarlar = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt', # Kısıtlamaları aşmak için
        'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'web_safari']}},
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1'
    }
    try:
        with yt_dlp.YoutubeDL(ayarlar) as ydl:
            bilgi = ydl.extract_info(video_url, download=False)
            return {
                "durum": "basarili",
                "baslik": bilgi.get('title', 'Video'),
                "indirme_linki": bilgi.get('url') or bilgi.get('webpage_url'),
                "kapak": bilgi.get('thumbnail', '')
            }
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}

# 3. İSİM DEĞİŞTİRME VE İNDİRME KÖPRÜSÜ (TÜRKÇE KARAKTER KORUMALI)
@app.get("/video-indir")
async def video_indir(url: str, baslik: str):
    # Türkçe karakterleri İngilizce karşılıklarına çeviriyoruz
    degisim = {
        'ğ':'g', 'Ğ':'G', 'ş':'s', 'Ş':'S', 'ç':'c', 'Ç':'C', 
        'ı':'i', 'İ':'I', 'ö':'o', 'Ö':'O', 'ü':'u', 'Ü':'U'
    }
    for turkce_harf, ingilizce_harf in degisim.items():
        baslik = baslik.replace(turkce_harf, ingilizce_harf)

    # Dosya adında hata çıkaracak sembolleri siliyoruz
    temiz_baslik = "".join(c for c in baslik if c.isalnum() or c in " ._-()[]").strip()
    
    # Son güvenlik duvarı: Sadece ASCII karakterler kalsın (FastAPI çökmesin diye)
    temiz_baslik = temiz_baslik.encode('ascii', 'ignore').decode('ascii')
    
    if not temiz_baslik:
        temiz_baslik = "Indirilen_Video"

    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    try:
        response = urllib.request.urlopen(req)
        
        def iterfile():
            while True:
                chunk = response.read(65536) # Videoyu parça parça aktar
                if not chunk:
                    break
                yield chunk

        # Temizlenmiş ve güvenli başlıkla indirme emri veriyoruz
        headers = {'Content-Disposition': f'attachment; filename="{temiz_baslik}.mp4"'}
        return StreamingResponse(iterfile(), media_type='video/mp4', headers=headers)
        
    except Exception as e:
        return {"hata": "Indirme basarisiz: " + str(e)}