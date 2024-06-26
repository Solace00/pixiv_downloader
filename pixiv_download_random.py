from pixivpy3 import AppPixivAPI
import requests
import os
import random
from concurrent.futures import ThreadPoolExecutor

# Replace with your Pixiv API credentials
REFRESH_TOKEN = ''
DOWNLOAD_FOLDER = './random download'
MAX_WORKERS = 20  # Adjust the number of concurrent workers as needed
NUM_ARTISTS = 10  # Number of random artists to fetch

def download_image(url, path):
    headers = {
        'Referer': 'https://www.pixiv.net/'
    }
    try:
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f'Successfully downloaded {url} to {path}')
        else:
            print(f'Failed to download {url}. Status code: {response.status_code}')
    except Exception as e:
        print(f'Error downloading {url}: {e}')

def get_random_artists(api, num_artists):
    recommended = api.illust_recommended()
    artist_ids = list(set(illust.user.id for illust in recommended.illusts))
    random.shuffle(artist_ids)
    return artist_ids[:num_artists]

def download_artist_images(api, artist_id):
    json_result = api.user_illusts(artist_id)
    artist_name = json_result.illusts[0].user.name if json_result.illusts else str(artist_id)
    artist_folder = os.path.join(DOWNLOAD_FOLDER, artist_name)
    if not os.path.exists(artist_folder):
        os.makedirs(artist_folder)

    download_tasks = []
    while True:
        for illust in json_result.illusts:
            if illust.meta_pages:
                for page in illust.meta_pages:
                    image_url = page.image_urls.original
                    file_name = os.path.join(artist_folder, os.path.basename(image_url))
                    download_tasks.append((image_url, file_name))
            else:
                if illust.meta_single_page.get('original_image_url'):
                    image_url = illust.meta_single_page.original_image_url
                    file_name = os.path.join(artist_folder, os.path.basename(image_url))
                    download_tasks.append((image_url, file_name))
                else:
                    print(f'No image URL found for illust ID: {illust.id}')

        if json_result.next_url:
            next_qs = api.parse_qs(json_result.next_url)
            json_result = api.user_illusts(**next_qs)
        else:
            break

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(download_image, url, path) for url, path in download_tasks]
        for future in futures:
            future.result()

def main():
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    api = AppPixivAPI()
    api.auth(refresh_token=REFRESH_TOKEN)
    
    random_artist_ids = get_random_artists(api, NUM_ARTISTS)
    print(f'Random artist IDs: {random_artist_ids}')
    
    for artist_id in random_artist_ids:
        print(f'Downloading images for artist ID: {artist_id}')
        download_artist_images(api, artist_id)

if __name__ == '__main__':
    main()
