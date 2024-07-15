import json
import time
import requests
from random import choice
import os
import argparse
from subprocess import call

# Check if step 1 is installed
if "step1_installed_flag" not in globals():
    raise Exception("Please run step 1 first!")

# Arguments
parser = argparse.ArgumentParser(description='Scrape images from Rule34')
parser.add_argument('--tags', type=str, default='zukafu_shimoto', help='Tags for scraping images')
parser.add_argument('--max_resolution', type=int, default=3072, help='Maximum resolution for images')
parser.add_argument('--include_posts_with_parent', type=bool, default=True, help='Include posts with parent')
args = parser.parse_args()

tags = args.tags
max_resolution = args.max_resolution
include_posts_with_parent = args.include_posts_with_parent

tags = tags.replace(" ", "+")\
           .replace("(", "%28")\
           .replace(")", "%29")\
           .replace(":", "%3a")\
           .replace("&", "%26")

url = "https://rule34.xxx/index.php?page=dapi&json=1&s=post&q=index&limit=100&tags={}".format(tags)
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59"
]
limit = 100 # hardcoded by rule34
total_limit = 1000 # you can edit this if you want but I wouldn't recommend it
supported_types = (".png", ".jpg", ".jpeg")

def ubuntu_deps():
    print("🏭 Installing dependencies...\n")
    call(['apt', '-y', 'install', 'aria2'])
    return True

if "step2_installed_flag" not in globals():
    if ubuntu_deps():
        step2_installed_flag = True
    else:
        print("❌ Error installing dependencies, attempting to continue anyway...")

def get_json(url):
    headers = {"User-Agent": choice(user_agents)}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def filter_images(data):
    return [p["file_url"] if p["width"] * p["height"] <= max_resolution**2 else p["sample_url"]
            for p in data
            if (p["parent_id"] == 0 or include_posts_with_parent)
            and p["file_url"].lower().endswith(supported_types)]

def download_images():
    data = get_json(url)
    count = len(data)

    if count == 0:
        print("📷 No results found")
        return

    print(f"🎯 Found {count} results")
    test_url = "https://rule34.xxx/index.php?page=post&s=list&tags={}".format(tags)
    print(f"🔽 Will download to {images_folder.replace('/content/drive/', '')} (A confirmation box should appear below, otherwise run this cell again)")
    inp = input("❓ Enter the word 'yes' if you want to proceed with the download: ")

    if inp.lower().strip() != 'yes':
        print("❌ Download cancelled")
        return

    print("📩 Grabbing image list...")

    image_urls = set()
    image_urls = image_urls.union(filter_images(data))
    for i in range(total_limit // limit):
        count -= limit
        if count <= 0:
            break
        time.sleep(0.1)
        image_urls = image_urls.union(filter_images(get_json(url + f"&pid={i + 1}")))

    scrape_file = os.path.join(config_folder, f"scrape_{project_subfolder}.txt")
    with open(scrape_file, "w") as f:
        f.write("\n".join(image_urls))

    print(f"🌐 Saved links to {scrape_file}\n\n🔁 Downloading images...\n")
    old_img_count = len([f for f in os.listdir(images_folder) if f.lower().endswith(supported_types)])

    os.chdir(images_folder)
    call(['aria2c', '--console-log-level=warn', '-c', '-x', '16', '-k', '1M', '-s', '16', '-i', scrape_file])

    new_img_count = len([f for f in os.listdir(images_folder) if f.lower().endswith(supported_types)])
    print(f"\n✅ Downloaded {new_img_count - old_img_count} images.")

download_images()
