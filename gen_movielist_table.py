import requests, opencc, os
from dotenv import load_dotenv
import pandas as pd

class get_movie_info():
    def __init__(self, access_token, language):
        self.access_token = access_token
        self.headers = {
            "accept": "application/json",
            "Authorization": self.access_token
        }
        self.lang = language


    def get_id(self, name):
        SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
        query_param = {
            'query': name,
            'include_adult': 'true',
            'language': self.lang,
            'page': 1
        }
        response = requests.get(SEARCH_URL, headers=self.headers, params=query_param)
        
        if response.status_code != 200:
            print('Request failed!')
            return None
        response = response.json()
        
        if len(response['results']) == 0:
            return None
        else:
            movie_id = response['results'][0]['id']
            return movie_id


    def get_attr(self, ID):
        if ID == None:
            return (None,)*8
        
        POSTER_URL = 'https://image.tmdb.org/t/p/w500'
        DETAIL_URL = f'https://api.themoviedb.org/3/movie/{ID}'
        query_param = {
            'language': self.lang
        }
        response = requests.get(DETAIL_URL, headers=self.headers, params=query_param)
        if response.status_code != 200:
            print('Request failed!')
            return None
        response = response.json()
        
        tmdb_url = f'https://www.themoviedb.org/movie/{ID}'
        original_title = response['original_title']
        poster = f"{POSTER_URL}{response['poster_path']}"
        imdb_url = f"https://www.imdb.com/title/{response['imdb_id']}"
        description = self.s2t(response['overview']).replace('\t', '').replace('\r', '')
        year = response['release_date'].split('-')[0]
        movie_length = f"{response['runtime']//60}hrs {response['runtime']%60}mins"
        genres = [self.s2t(t['name']) for t in response['genres']]
        
        return original_title, poster, year, description, genres, movie_length, imdb_url, tmdb_url
        
        
    def get_movie_full_detail(self, movie_name):
        tmdb_id = self.get_id(movie_name)
        return self.get_attr(tmdb_id)
        
    def s2t(self, text):
        converter = opencc.OpenCC('s2tw.json')
        return converter.convert(text)


def generate_html_table(filmlist_filepath, db_lang):
    dbStruct = {
        'Film Name': [],
        'Film Poster': [],
        'Release Year': [],
        'Overview': [],
        'Genres': [],
        'Running Time': [],
        'Alt. External URL': []
    }
    with open(filmlist_filepath, 'r', encoding='utf-8') as f:
        filmlist = f.read().splitlines()  
        
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASE_DIR, '.env'))
    tmdb = get_movie_info(access_token=os.getenv("TMDB_ACCESS_TOKEN"), language=db_lang)

    for i, film in enumerate(filmlist):
        name, poster, year, desc, genre, runtime, imdburl, tmdburl = tmdb.get_movie_full_detail(film)
        
        db_name = f'<a href="{imdburl}">{film}</a>' if imdburl else film
        db_poster = f'<img src="{poster}" alt="{name}" width="100">' if poster else ''
        db_year = year if year else ''
        db_overview = desc if desc else ''
        db_genres = '<br/>'.join(genre) if (genre != None and len(genre) > 0) else ''
        db_runtime = runtime if runtime else ''
        db_exturl = f'<a href="{tmdburl}">TMDB</a>' if tmdburl else 'TMDB'

        dbStruct['Film Name'].append(db_name)
        dbStruct['Film Poster'].append(db_poster)
        dbStruct['Release Year'].append(db_year)
        dbStruct['Overview'].append(db_overview)
        dbStruct['Genres'].append(db_genres)
        dbStruct['Running Time'].append(db_runtime)
        dbStruct['Alt. External URL'].append(db_exturl)
        
        print(f'Progress: {i}', end='\r')
        
    film_df = pd.DataFrame(dbStruct)
    film_html = film_df.to_html(index=True, escape=False, justify='center')
    
    with open('./src/index.html', 'w', encoding='utf-8') as out:
        out.write(film_html)
    

if __name__ == '__main__':
    generate_html_table('./nameList.txt', 'zh-HK')