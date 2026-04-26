from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

# Tarayıcıların (Frontend) bu API'ye bağlanabilmesi için CORS izni veriyoruz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/link-coz")
def link_coz(video_url: str):
    ayarlar = {
        'format': 'best',
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ayarlar) as ydl:
            # download=False çok önemli! Videoyu sunucuya indirmez, sadece bilgileri çeker.
            bilgi = ydl.extract_info(video_url, download=False)
            
            # Gerçek .mp4 veya yayın linkini alıyoruz
            gercek_link = bilgi.get('url') 
            
            return {
                "durum": "basarili",
                "baslik": bilgi.get('title'),
                "indirme_linki": gercek_link,
                "kapak": bilgi.get('thumbnail')
            }
    except Exception as hata:
        return {"durum": "hata", "mesaj": str(hata)}
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)