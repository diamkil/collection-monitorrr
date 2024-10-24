import os
import requests
import schedule
import time

API_KEY = os.getenv("RADARR_API_KEY")
RADARR_URL = os.getenv("RADARR_URL")
REFRESH_MINUTES = int(os.getenv("RADARR_REFRESH_MINUTES", 10))  # Ensure it's an integer
QUALITY_PROFILE = os.getenv("RADARR_QUALITY_PROFILE", "Any")  # Default to "Any"
ROOT_FOLDER_PATH = os.getenv("RADARR_ROOT_FOLDER_PATH", "/movies")  # Default to /movies

if not API_KEY or not RADARR_URL:
    print("Missing RADARR_API_KEY or RADARR_URL environment variables.")
    exit(1)

def get_quality_profile_id(profile_name):
    url = f"{RADARR_URL}/api/v3/qualityProfile"
    headers = {"X-Api-Key": API_KEY}
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
        print(f"Error retrieving quality profiles: {e}")
        return None

QUALITY_PROFILE_ID = get_quality_profile_id(QUALITY_PROFILE)
if not QUALITY_PROFILE_ID:
    print("Failed to retrieve quality profile ID. Exiting.")
    exit(1)

def monitor_collections():
    print('Starting Run!')
    url = f"{RADARR_URL}/api/v3/collection"
    headers = {"X-Api-Key": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        collections = response.json()
        for collection in collections:
            print(f"Checking collection: {collection['title']}")
            # Check for missing movies in the collection
            check_for_missing_movies_in_collection(collection['id'])
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving collections: {e}")
    print('Done running!')

def check_for_missing_movies_in_collection(collection_id):
    # Fetch the collection details with the list of movies
    collection_movies_url = f"{RADARR_URL}/api/v3/collection/{collection_id}"
    headers = {"X-Api-Key": API_KEY}
    try:
        response = requests.get(collection_movies_url, headers=headers)
        response.raise_for_status()
        collection = response.json()
        # Fetch all movies in the Radarr library
        radarr_movies_url = f"{RADARR_URL}/api/v3/movie"
        radarr_response = requests.get(radarr_movies_url, headers=headers)
        radarr_response.raise_for_status()
        radarr_movies = radarr_response.json()
        # Create a set of movie titles in the Radarr library for quick lookup
        radarr_movie_titles = {movie['title'] for movie in radarr_movies}
        # Identify missing movies in the collection
        for movie in collection['movies']:
            if movie['title'] not in radarr_movie_titles:
                print(f"Missing movie in Radarr: {movie['title']}, adding...")
                add_movie_to_radarr(movie)
            else:
                print(f"Movie already in Radarr: {movie['title']}")
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
