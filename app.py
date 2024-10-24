import os
import requests
import schedule
import time

API_KEY = os.getenv("RADARR_API_KEY")
RADARR_URL = os.getenv("RADARR_URL")
REFRESH_MINUTES = int(os.getenv("REFRESH_MINUTES", 10))

if not API_KEY or not RADARR_URL:
    print("Missing RADARR_API_KEY or RADARR_URL environment variables.")
    exit(1)

def monitor_collections():
    url = f"{RADARR_URL}/api/v3/collection"
    headers = {"X-Api-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        collections = response.json()
        
        for collection in collections:
            if not collection["monitored"]:
                collection["monitored"] = True
                update_url = f"{RADARR_URL}/api/v3/collection/{collection['id']}"
                response = requests.put(update_url, headers=headers, json=collection)
                if response.status_code == 200:
                    print(f"Monitored collection: {collection['title']}")
                    monitor_and_search_movies(collection['id'])
                else:
                    print(f"Failed to monitor collection: {collection['title']} (status code: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving collections: {e}")

def monitor_and_search_movies(collection_id):
    url = f"{RADARR_URL}/api/v3/movie"
    headers = {"X-Api-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers, params={"collectionId": collection_id})
        response.raise_for_status()
        movies = response.json()
        
        for movie in movies:
            if not movie["monitored"]:
                movie["monitored"] = True
                movie_url = f"{RADARR_URL}/api/v3/movie/{movie['id']}"
                response = requests.put(movie_url, headers=headers, json=movie)
                if response.status_code == 200:
                    print(f"Monitored movie: {movie['title']}")
                    search_movie(movie['id'])
                else:
                    print(f"Failed to monitor movie: {movie['title']} (status code: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving movies: {e}")

def search_movie(movie_id):
    url = f"{RADARR_URL}/api/v3/command"
    headers = {"X-Api-Key": API_KEY}
    data = {"name": "MoviesSearch", "movieIds": [movie_id]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"Search initiated for movie ID: {movie_id}")
        else:
            print(f"Failed to initiate search for movie ID: {movie_id} (status code: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Error initiating movie search: {e}")

print(f'Scheduling to run every {REFRESH_MINUTES} minutes')
schedule.every(REFRESH_MINUTES).minutes.do(monitor_collections)

print(f'Doing first run!')
monitor_collections()

while True:
    schedule.run_pending()
    time.sleep(1)
