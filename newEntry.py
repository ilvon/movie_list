import requests, opencc, os
from dotenv import load_dotenv
from lxml import etree
from datetime import date

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


def print_html_table(film_search_str, db_lang): # film_search_str = [display name, tmdb search name]
    film_search_element = film_search_str.split(',')
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASE_DIR, '.env'))
       
    tmdb = get_movie_info(access_token=os.getenv("TMDB_ACCESS_TOKEN"), language=db_lang)

    film = film_search_element[1]
    if film.startswith('mid='):
        name, poster, year, desc, genre, runtime, imdburl, tmdburl = tmdb.get_attr(film[4:])
    else:
        name, poster, year, desc, genre, runtime, imdburl, tmdburl = tmdb.get_movie_full_detail(film)
    
    db_name = f'<a href="{imdburl}">{film_search_element[0]}</a>' if imdburl else film_search_element[0]
    db_poster = f'<img src="{poster}" alt="{name}" width="100"/>' if poster else ''
    db_year = year if year else ''
    db_overview = desc if desc else ''
    db_genres = '<br/>'.join(genre) if (genre != None and len(genre) > 0) else ''
    db_runtime = runtime if runtime else ''
    db_exturl = f'<a href="{tmdburl}">TMDB</a>' if tmdburl else 'TMDB'
    
    formatted_info = f'''
    <tr>
        <th>0</th>
        <td>{db_name}</td>
        <td>{db_poster}</td>
        <td>{db_year}</td>
        <td>{db_overview}</td>
        <td>{db_genres}</td>
        <td>{db_runtime}</td>
        <td>{db_exturl}</td>
    </tr>
    '''
    
    edit_html_file = input('Edit the html file directly? (Y/Any key): ')
    if edit_html_file == 'Y' or edit_html_file == 'y':
        result_index = insert_new_entry(film_search_element[0], formatted_info)
        print(f'Inserted entry: #{result_index} {film}')
    else:
        print(formatted_info)


def insert_new_entry(displayName, raw_new_entry):
    with open('./src/index.html', 'r', encoding='utf-8') as fin:
        rawhtml = fin.read()
    
    root = etree.HTML(rawhtml)
    new_entry = etree.fromstring(raw_new_entry)

    tbody = root.xpath('.//tbody')[0]

    tbody.append(new_entry)

    entries_unsorted = root.xpath('.//tbody/tr')
    entries_sorted = sorted(entries_unsorted, key=lambda r: r.xpath(".//a[contains(@href, 'imdb')]/text()"))
    tbody.clear()
    
    for i, row in enumerate(entries_sorted):
        row.xpath('.//th')[0].text = str(i)
        tbody.append(row)

    div_info_text = root.xpath('./body/div[@class="container"]/h4')
    div_info_text[0].text = f"Last Update: {date.today().strftime('%d-%m-%Y')}"
    div_info_text[1].text = f"Total Entries: {len(root.xpath('.//tbody/tr'))}"
    
    with open('./src/index.html', 'wb') as fout:
        fout.write(etree.tostring(root, encoding='utf-8'))
    
    newEntry_location = tbody.xpath(f"./tr[contains(.//a/text(), '{displayName}')]")[0]
    return newEntry_location.find('./th').text


if __name__ == '__main__':
    search_string = input('String(DisplayName, SearchName(or TMDB id startwith \'mid=\')): ')
    print_html_table(search_string, 'zh-TW')