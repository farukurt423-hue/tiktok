from flask import Flask, request, render_template_string
from TikTokApi import TikTokApi
import asyncio
import os

app = Flask(__name__)

# !!! BURAYI GÜNCELLEYİN: Uygulamanın çalışması için bu çerez değeri kritiktir.
# Kendi güncel 'verifyFp' değerinizi tırnak işaretlerinin ("") içine yapıştırın.
VERIFY_FP = "" 

# Flask, asenkron (async) kodu çalıştırmak için bu yardımcıya ihtiyaç duyar
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    username = request.form.get('username') if request.method == 'POST' else None
    
    if request.method == 'POST':
        if not username:
            # Hata mesajı: Kullanıcı adı girilmemiş
            return render_template_string(HTML_FORM, message="Lütfen bir kullanıcı adı girin.")
        
        # Asenkron TikTokApi işlevini çağır
        results = run_async(get_tiktok_content(username))
        
    return render_template_string(HTML_FORM, username=username, results=results)

async def get_tiktok_content(username):
    """Kullanıcının Story veya normal videolarını almaya çalışır."""
    download_links = []
    
    async with TikTokApi(custom_verifyFp=VERIFY_FP) as api:
        await api.create_sessions()
        
        try:
            user = api.user(username=username)
            # Story'leri hedefleyen kesin bir API çağrısı kararlı olmadığı için,
            # daha güvenilir olan son 5 normal videoyu alıyoruz.
            videos = user.videos(count=5) 
            
            if not videos:
                download_links.append({"title": f"@{username} için güncel içerik bulunamadı.", "link": "#"})
                return download_links
            
            for i, video in enumerate(videos):
                # Video indirme URL'sini alın (HD kalitede olması beklenir)
                video_url = video.item_info.video.download_addr
                
                download_links.append({
                    "title": f"Gönderi Videosu #{i+1} ({video.id})",
                    "link": video_url
                })
                
            return download_links

        except Exception as e:
            return [{"title": f"Hata: Kullanıcı adı/API erişim hatası. {e}", "link": "#"}]

# HTML Arayüzü (Kullanıcı Adı Girdisi ve Sonuçların Gösterimi)
HTML_FORM = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>TikTok İndirici</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f7f8; }
        .container { max-width: 600px; margin: auto; padding: 25px; border-radius: 12px; background-color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #FE2C55; }
        input[type="text"] { padding: 12px; width: 65%; margin-right: 10px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
        input[type="submit"] { padding: 12px 20px; background-color: #25F4EE; color: #333; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background-color 0.3s; }
        input[type="submit"]:hover { background-color: #1ed8d3; }
        .result-box { margin-top: 25px; padding: 15px; border-top: 1px solid #eee; }
        .result-box a { display: block; margin-bottom: 15px; padding: 12px; background-color: #FE2C55; color: white; border-radius: 8px; text-decoration: none; text-align: center; font-weight: bold; }
        .result-box a:hover { background-color: #d11f4d; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📱 TikTok Video Bağlantı Oluşturucu</h2>
        <form method="POST" style="text-align: center;">
            <input type="text" name="username" placeholder="Kullanıcı Adı Girin (örn: @tiktok)" required value="{{ username if username else '' }}">
            <input type="submit" value="Bul">
        </form>

        {% if message %}
            <p class="error">{{ message }}</p>
        {% endif %}

        {% if results %}
            <div class="result-box">
                <h3>Sonuçlar: @{{ username }}</h3>
                <p style="color: #666; font-size: 14px;">Bulunan içerikler (Story/Gönderi) indirme bağlantılarıdır. İndirmek için butona tıklayın.</p>
                
                {% for item in results %}
                    <a href="{{ item.link }}" target="_blank" download="{{ item.title.replace(' ', '_') }}.mp4">
                        {{ item.title }} - İNDİR BUTONU
                    </a>
                {% endfor %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""
