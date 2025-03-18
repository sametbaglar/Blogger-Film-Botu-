from flask import Flask, request, render_template_string, redirect, url_for, flash
import requests, smtplib, os, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")

def search_movies(query, language='tr-TR'):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}&language={language}"
    return requests.get(url).json().get('results', [])[:10]

def advanced_search_movies(query, year=None, genre_id=None, language='tr-TR'):
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&language={language}"
    params = {}
    if query:
        params['query'] = query
    if year:
        params['primary_release_year'] = year
    if genre_id:
        params['with_genres'] = genre_id
    return requests.get(url, params=params).json().get('results', [])[:10]

def get_genres(language='tr-TR'):
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}&language={language}"
    return requests.get(url).json().get('genres', [])

def get_movie_details(movie_id, language='tr-TR'):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language={language}"
    return requests.get(url).json()

def get_movie_credits(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}&language=tr-TR"
    return requests.get(url).json()

def get_movie_videos(movie_id, language='tr-TR'):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language={language}"
    videos = requests.get(url).json().get('results', [])
    for video in videos:
        if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
            return f"https://www.youtube.com/embed/{video.get('key')}"
    return None

def get_watch_providers(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}"
    return requests.get(url).json().get('results', {}).get('TR', {})

def get_movie_keywords(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/keywords?api_key={TMDB_API_KEY}"
    return requests.get(url).json().get('keywords', [])

def get_imdb_rating(imdb_id):
    omdb_api_key = os.getenv("OMDB_API_KEY")
    if not omdb_api_key:
        return None
    url = f"http://www.omdbapi.com/?apikey={omdb_api_key}&i={imdb_id}"
    return requests.get(url).json().get("imdbRating")

def send_email(subject, html_content):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = BLOGGER_EMAIL
    msg.attach(MIMEText(html_content, 'html'))
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ADDRESS, BLOGGER_EMAIL, msg.as_string())
    server.quit()

def create_email_html(movie_details, trailer_url, credits, keywords, config, custom_embed):
    title = movie_details.get('title', 'Film Detayları')
    release_date = movie_details.get('release_date', 'Bilinmiyor')
    overview = movie_details.get('overview', 'Açıklama bulunamadı.')
    poster_path = movie_details.get('poster_path')
    poster_img = (f'<img src="https://image.tmdb.org/t/p/w500{poster_path}" alt="{title} Poster" style="width:300px; height:450px; object-fit: cover; display: block; margin: auto;">'
                 ) if poster_path else '<p>Poster bulunamadı.</p>'
    genres = ", ".join([g.get('name') for g in movie_details.get('genres', [])]) or "Bilinmiyor"
    vote_average = movie_details.get('vote_average', 'Bilinmiyor')
    vote_count = movie_details.get('vote_count', 'Bilinmiyor')
    runtime = movie_details.get('runtime', 'Bilinmiyor')
    budget = movie_details.get('budget', 'Bilinmiyor')
    revenue = movie_details.get('revenue', 'Bilinmiyor')
    directors = [m['name'] for m in credits.get('crew', []) if m.get('job') == 'Director']
    cast = [m['name'] for m in credits.get('cast', [])][:5]
    keyword_list = get_movie_keywords(movie_details.get("id", 0))
    tags = [k['name'] for k in keyword_list]
    tags_str = ", ".join(tags) if tags else "Bilinmiyor"
    imdb_id = movie_details.get("imdb_id")
    if imdb_id:
        imdb_rating = get_imdb_rating(imdb_id) or "Bilinmiyor"
        imdb_link = f"https://www.imdb.com/title/{imdb_id}/"
    else:
        imdb_rating = "Bilinmiyor"
        imdb_link = "#"
    meta_description = overview if len(overview) < 160 else overview[:157] + "..."
    meta_keywords = f"{title}, {genres}, {tags_str}"
    json_ld = {
      "@context": "https://schema.org",
      "@type": "Movie",
      "name": title,
      "description": overview,
      "image": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "",
      "datePublished": release_date,
      "aggregateRating": {"@type": "AggregateRating", "ratingValue": vote_average, "ratingCount": vote_count},
      "director": [{"@type": "Person", "name": d} for d in directors],
      "actor": [{"@type": "Person", "name": a} for a in cast]
    }
    trailer_section = ""
    if trailer_url and config.get("include_trailer", True):
        trailer_section = (
            '<h2 class="mt-4">Fragman</h2>'
            '<div class="embed-responsive embed-responsive-16by9 mb-3" style="margin: auto;">'
            f'<iframe class="embed-responsive-item" src="{trailer_url}" allowfullscreen></iframe>'
            '</div>'
        )
    custom_video_section = ""
    if custom_embed.strip():
        custom_video_section = (
            '<h2 class="mt-4">Ek Video</h2>'
            '<div class="embed-responsive embed-responsive-16by9 mb-3" style="margin: auto;">'
            f'{custom_embed}'
            '</div>'
        )
    content = poster_img
    if config.get("include_overview"): content += f'<p style="margin-bottom:1em;"><strong>Açıklama:</strong> {overview}</p>'
    if config.get("include_directors"): content += f'<p style="margin-bottom:1em;"><strong>Yönetmen:</strong> {", ".join(directors) or "Bilinmiyor"}</p>'
    if config.get("include_cast"): content += f'<p style="margin-bottom:1em;"><strong>Oyuncular:</strong> {", ".join(cast) or "Bilinmiyor"}</p>'
    if config.get("include_genres"): content += f'<p style="margin-bottom:1em;"><strong>Film Kategorisi (Türler):</strong> {genres}</p>'
    if config.get("include_release_date"): content += f'<p style="margin-bottom:1em;"><strong>Çıkış Tarihi:</strong> {release_date}</p>'
    if config.get("include_runtime"): content += f'<p style="margin-bottom:1em;"><strong>Film Süresi:</strong> {runtime} dakika</p>'
    if config.get("include_budget"): content += f'<p style="margin-bottom:1em;"><strong>Bütçe:</strong> {budget} USD</p>'
    if config.get("include_revenue"): content += f'<p style="margin-bottom:1em;"><strong>Hasılat:</strong> {revenue} USD</p>'
    if config.get("include_tmdb_rating"): content += f'<p style="margin-bottom:1em;"><strong>TMDB Puanı:</strong> {vote_average} (Oy Sayısı: {vote_count})</p>'
    if config.get("include_imdb"): content += f'<p style="margin-bottom:1em;"><strong>IMDb:</strong> {imdb_rating} (<a href="{imdb_link}" target="_blank">IMDb Sayfası</a>)</p>'
    content += trailer_section + custom_video_section
    content += f'<p style="margin-top:2em; font-size:0.9em;">Labels: {tags_str}</p>'
    
    html = f"""<!doctype html>
    <html lang="tr">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>{title}</title>
        <meta name="description" content="{meta_description}">
        <meta name="keywords" content="{meta_keywords}">
        <meta property="og:title" content="{title}">
        <meta property="og:description" content="{meta_description}">
        <meta property="og:image" content="https://image.tmdb.org/t/p/w500{poster_path if poster_path else ''}">
        <meta property="og:type" content="article">
        <script type="application/ld+json">
          {json.dumps(json_ld, ensure_ascii=False, indent=2)}
        </script>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
      </head>
      <body>
        <div class="container my-5 text-center">{content}</div>
      </body>
    </html>"""
    return html

@app.route("/", methods=["GET", "POST"])
def index():
    genres = get_genres()
    if request.method == "POST":
        query = request.form.get("query", "")
        year = request.form.get("year", "")
        genre_id = request.form.get("genre", "")
        movies = advanced_search_movies(query, year if year else None, genre_id if genre_id else None) if (year or genre_id) else search_movies(query)
        return render_template_string("""
        <!doctype html>
        <html lang="tr">
          <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>Film Arama Sonuçları</title>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
          </head>
          <body>
            <div class="container my-5">
              <h1 class="text-center">Film Arama Sonuçları</h1>
              <div class="list-group">
                {% for movie in movies %}
                  <a href="{{ url_for('movie_detail', movie_id=movie['id']) }}" class="list-group-item list-group-item-action">
                    <div class="d-flex align-items-center">
                      <img src="https://image.tmdb.org/t/p/w185{{ movie.poster_path }}" alt="{{ movie.title }} Poster" style="width:50px; height:75px; object-fit: cover; margin-right:10px;">
                      <div>
                        <strong>{{ movie.title }}</strong><br>
                        <small>{{ movie.get('release_date', 'Tarih bilinmiyor') }}</small>
                      </div>
                    </div>
                  </a>
                {% endfor %}
              </div>
              <div class="text-center mt-4">
                <a href="{{ url_for('index') }}" class="btn btn-secondary">Yeni Arama</a>
              </div>
            </div>
          </body>
        </html>
        """, movies=movies)
    return render_template_string("""
    <!doctype html>
    <html lang="tr">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Film Arama</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
      </head>
      <body>
        <div class="container my-5">
          <div class="row justify-content-center">
            <div class="col-md-8">
              <h1 class="text-center mb-4">Film Arama</h1>
              <form method="post">
                <div class="form-group">
                  <label for="query">Film Adı:</label>
                  <input type="text" name="query" id="query" class="form-control" required>
                </div>
                <div class="form-group">
                  <label for="year">Yayın Yılı (isteğe bağlı):</label>
                  <input type="text" name="year" id="year" class="form-control">
                </div>
                <div class="form-group">
                  <label for="genre">Tür (isteğe bağlı):</label>
                  <select name="genre" id="genre" class="form-control">
                    <option value="">Seçiniz</option>
                    {% for genre in genres %}
                      <option value="{{ genre.id }}">{{ genre.name }}</option>
                    {% endfor %}
                  </select>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Ara</button>
              </form>
            </div>
          </div>
        </div>
      </body>
    </html>
    """, genres=genres)

@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    movie = get_movie_details(movie_id)
    credits = get_movie_credits(movie_id)
    trailer_url = get_movie_videos(movie_id)
    watch_providers = get_watch_providers(movie_id)
    directors = [m['name'] for m in credits.get('crew', []) if m.get('job') == 'Director']
    return render_template_string("""
    <!doctype html>
    <html lang="tr">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>{{ movie.title }}</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
      </head>
      <body>
        <div class="container my-5 text-center">
          <h1>{{ movie.title }}</h1>
          <p><strong>Çıkış Tarihi:</strong> {{ movie.release_date }}</p>
          <p>{{ movie.overview }}</p>
          <p><strong>Yönetmen:</strong> {{ directors|join(', ') if directors else 'Bilinmiyor' }}</p>
          <h2 class="mt-4">Poster</h2>
          <div>
            {% if movie.poster_path %}
              <img src="https://image.tmdb.org/t/p/w500{{ movie.poster_path }}" alt="{{ movie.title }} Poster" class="img-fluid mb-3" style="width:300px; height:450px; object-fit: cover; margin: auto;">
            {% else %}
              <p>Poster bulunamadı.</p>
            {% endif %}
          </div>
          <h2 class="mt-4">Fragman</h2>
          <div>
            {% if trailer_url %}
              <div class="embed-responsive embed-responsive-16by9" style="margin: auto;">
                <iframe class="embed-responsive-item" src="{{ trailer_url }}" allowfullscreen></iframe>
              </div>
            {% else %}
              <p>Fragman bulunamadı.</p>
            {% endif %}
          </div>
          <div class="mt-4">
            <a href="{{ url_for('config_form', movie_id=movie.id) }}" class="btn btn-primary">Gönderi Ayarlarını Düzenle</a>
            <a href="{{ url_for('index') }}" class="btn btn-secondary ml-2">Yeni Arama</a>
          </div>
        </div>
      </body>
    </html>
    """, movie=movie, directors=directors, trailer_url=trailer_url)

@app.route("/config/<int:movie_id>", methods=["GET"])
def config_form(movie_id):
    movie = get_movie_details(movie_id)
    credits = get_movie_credits(movie_id)
    trailer_url = get_movie_videos(movie_id)
    directors = [m['name'] for m in credits.get('crew', []) if m.get('job') == 'Director']
    return render_template_string("""
    <!doctype html>
    <html lang="tr">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>{{ movie.title }} - Gönderi Ayarları</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
      </head>
      <body>
        <div class="container my-5 text-center">
          <h1 class="mb-4">{{ movie.title }} - Gönderi Ayarları</h1>
          <form action="{{ url_for('send_movie_email', movie_id=movie.id) }}" method="post">
            <div class="form-group">
              <label for="custom_embed">Özel Video Embed Kodu (Varsa):</label>
              <textarea name="custom_embed" id="custom_embed" class="form-control" rows="3" placeholder="Varsa özel video embed kodunu buraya yapıştırın."></textarea>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_overview" id="include_overview" class="form-check-input" checked>
              <label class="form-check-label" for="include_overview">Açıklama</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_directors" id="include_directors" class="form-check-input" checked>
              <label class="form-check-label" for="include_directors">Yönetmen</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_cast" id="include_cast" class="form-check-input" checked>
              <label class="form-check-label" for="include_cast">Oyuncular</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_genres" id="include_genres" class="form-check-input" checked>
              <label class="form-check-label" for="include_genres">Film Kategorisi</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_release_date" id="include_release_date" class="form-check-input" checked>
              <label class="form-check-label" for="include_release_date">Çıkış Tarihi</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_runtime" id="include_runtime" class="form-check-input" checked>
              <label class="form-check-label" for="include_runtime">Film Süresi</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_budget" id="include_budget" class="form-check-input" checked>
              <label class="form-check-label" for="include_budget">Bütçe</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_revenue" id="include_revenue" class="form-check-input" checked>
              <label class="form-check-label" for="include_revenue">Hasılat</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_tmdb_rating" id="include_tmdb_rating" class="form-check-input" checked>
              <label class="form-check-label" for="include_tmdb_rating">TMDB Puanı</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_imdb" id="include_imdb" class="form-check-input" checked>
              <label class="form-check-label" for="include_imdb">IMDb Puanı & Linki</label>
            </div>
            <div class="form-check">
              <input type="checkbox" name="include_trailer" id="include_trailer" class="form-check-input" checked>
              <label class="form-check-label" for="include_trailer">Otomatik Fragman (Trailer)</label>
            </div>
            <button type="submit" class="btn btn-primary btn-block mt-3">Gönderiyi Oluştur</button>
          </form>
          <div class="mt-4">
            <a href="{{ url_for('movie_detail', movie_id=movie.id) }}" class="btn btn-secondary">Geri Dön</a>
          </div>
        </div>
      </body>
    </html>
    """, movie=movie)

@app.route("/send_email/<int:movie_id>", methods=["POST"])
def send_movie_email(movie_id):
    movie = get_movie_details(movie_id)
    trailer_url = get_movie_videos(movie_id)
    credits = get_movie_credits(movie_id)
    keywords = get_movie_keywords(movie_id)
    config = {
      "include_overview": True if request.form.get("include_overview")=="on" else False,
      "include_directors": True if request.form.get("include_directors")=="on" else False,
      "include_cast": True if request.form.get("include_cast")=="on" else False,
      "include_genres": True if request.form.get("include_genres")=="on" else False,
      "include_release_date": True if request.form.get("include_release_date")=="on" else False,
      "include_runtime": True if request.form.get("include_runtime")=="on" else False,
      "include_budget": True if request.form.get("include_budget")=="on" else False,
      "include_revenue": True if request.form.get("include_revenue")=="on" else False,
      "include_tmdb_rating": True if request.form.get("include_tmdb_rating")=="on" else False,
      "include_imdb": True if request.form.get("include_imdb")=="on" else False,
      "include_trailer": True if request.form.get("include_trailer")=="on" else False,
    }
    custom_embed = request.form.get("custom_embed", "").strip()
    html_content = create_email_html(movie, trailer_url, credits, keywords, config, custom_embed)
    subject = f"{movie.get('title', 'Film Detayları')} film izle"
    try:
        send_email(subject, html_content)
        flash("Film bilgileri e-posta ile gönderildi.", "success")
    except Exception as e:
        flash(f"E-posta gönderiminde hata: {e}", "error")
    return redirect(url_for('movie_detail', movie_id=movie_id))

if __name__ == "__main__":
    app.run(debug=True)
