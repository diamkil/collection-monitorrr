import os
import requests
import schedule
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = os.getenv("RADARR_API_KEY")
RADARR_URL = os.getenv("RADARR_URL")
REFRESH_MINUTES = int(os.getenv("REFRESH_MINUTES", 10))  # Ensure it's an integer
QUALITY_PROFILE = os.getenv("RADARR_QUALITY_PROFILE", "Any")  # Default to "Any"
ROOT_FOLDER_PATH = os.getenv("RADARR_ROOT_FOLDER_PATH", "/movies")  # Default to /movies
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 3))  # Default to 3 threads if not set
RETRY_COUNT = 5
RETRY_DELAY = 10  # in seconds

if not API_KEY or not RADARR_URL:
    print("Missing RADARR_API_KEY or RADARR_URL environment variables.")
    exit(1)

def get_quality_profile_id(profile_name):
    url = f"{RADARR_URL}/api/v3/qualityProfile"
    headers = {"X-Api-Key": API_KEY}
    
    for attempt in range(RETRY_COUNT):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            profiles = response.json()
            for profile in profiles:
                if profile['name'].lower() == profile_name.lower():
                    return profile['id']
            print(f"Quality profile '{profile_name}' not found.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving quality profiles (attempt {attempt + 1}/{RETRY_COUNT}): {e}")
            time.sleep(RETRY_DELAY)
    
    print("Failed to retrieve quality profile ID after multiple attempts. Exiting.")
    return None

QUALITY_PROFILE_ID = get_quality_profile_id(QUALITY_PROFILE)
if not QUALITY_PROFILE_ID:
    exit(1)

# Cache to store Radarr movie data
radarr_movies_cache = None

def get_radarr_movies():
    global radarr_movies_cache
    if radarr_movies_cache is None:
        print("Fetching all movies from Radarr...")
        radarr_movies_url = f"{RADARR_URL}/api/v3/movie"
        headers = {"X-Api-Key": API_KEY}
        try:
            response = requests.get(radarr_movies_url, headers=headers)
            response.raise_for_status()
            radarr_movies_cache = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving Radarr movies: {e}")
            radarr_movies_cache = []
    return radarr_movies_cache

def monitor_collections():
    global radarr_movies_cache
    print('Starting Run!')
    
    # Reinitialize the cache at the beginning of the run
    radarr_movies_cache = None
    get_radarr_movies()
    
    url = f"{RADARR_URL}/api/v3/collection"
    headers = {"X-Api-Key": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        collections = response.json()

        # Use ThreadPoolExecutor to parallelize the collection checks
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(check_for_missing_movies_in_collection, collection['id'], collection['title'])
                for collection in collections
            ]
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise any exceptions that occurred in the threads
                except Exception as e:
                    print(f"Error in collection check: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Error retrieving collections: {e}")
    
    print('Done running!')

def check_for_missing_movies_in_collection(collection_id, collection_title):
    print(f"Checking collection: {collection_title}")
    # Fetch the collection details with the list of movies
    collection_movies_url = f"{RADARR_URL}/api/v3/collection/{collection_id}"
    headers = {"X-Api-Key": API_KEY}
    try:
        response = requests.get(collection_movies_url, headers=headers)
        response.raise_for_status()
        collection = response.json()

        # Retrieve cached Radarr movies
        radarr_movies = get_radarr_movies()
        radarr_movie_titles = {movie['title'] for movie in radarr_movies}

        # Identify missing movies in the collection
        for movie in collection['movies']:
            if movie['title'] not in radarr_movie_titles:
                print(f"Missing movie in Radarr: {movie['title']}, adding...")
                add_movie_to_radarr(movie)
    except requests.exceptions.RequestException as e:
        print(f"Error checking for missing movies: {e}")

def add_movie_to_radarr(movie):
    # Add the missing movie to Radarr by constructing the payload
    add_movie_url = f"{RADARR_URL}/api/v3/movie"
    headers = {"X-Api-Key": API_KEY}
    data = {
        "title": movie['title'],
        "qualityProfileId": QUALITY_PROFILE_ID,  # Use environment variable
        "monitored": True,
        "year": movie['year'],
        "tmdbId": movie['tmdbId'],
        "rootFolderPath": ROOT_FOLDER_PATH,  # Use environment variable
        "addOptions": {
            "searchForMovie": True
        }
    }
    try:
        response = requests.post(add_movie_url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"Successfully added movie: {movie['title']}")
        else:
            print(f"Failed to add movie: {movie['title']} (status code: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Error adding movie to Radarr: {e}")

print(f'Scheduling to run every {REFRESH_MINUTES} minutes')
schedule.every(REFRESH_MINUTES).minutes.do(monitor_collections)

monitor_collections()

while True:
    schedule.run_pending()
    time.sleep(1)
