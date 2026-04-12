import os, random, requests
from PIL import Image, ImageDraw, ImageFilter
from config import *

def download_pexels_images(count):
    images = []
    queries = random.sample(PEXELS_QUERIES, min(count, len(PEXELS_QUERIES)))
    per_query = max(1, count // len(queries))

    for q in queries:
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": q, "per_page": per_query, "orientation": "landscape"},
                headers={"Authorization": PEXELS_KEY},
                timeout=15
            )
            if resp.status_code != 200:
                # print(f"  Pexels API Error {resp.status_code}")
                continue
            for photo in resp.json().get("photos", []):
                img_url = photo["src"]["large"]
                img_resp = requests.get(img_url, timeout=20)
                if img_resp.status_code == 200:
                    path = os.path.join(IMGS, f"pexels_{photo['id']}.jpg")
                    with open(path, "wb") as f:
                        f.write(img_resp.content)
                    images.append(path)
                    if len(images) >= count:
                        return images
        except Exception as e:
            print(f"  Query '{q}' failed: {e}")
    return images

def generate_dark_image(index, w=1280, h=720):
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    base_r, base_g, base_b = random.randint(5,20), random.randint(5,15), random.randint(15,35)
    for y in range(h):
        factor = 1.0 - (y / h) * 0.4
        draw.line([(0, y), (w, y)], fill=(int(base_r*factor), int(base_g*factor), int(base_b*factor)))
    cx, cy = random.randint(w//4, 3*w//4), random.randint(h//4, 3*h//4)
    for radius in range(200, 0, -5):
        draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=(80, 10, 15))
    img = img.filter(ImageFilter.GaussianBlur(8))
    path = os.path.join(IMGS, f"gen_{index:03d}.jpg")
    img.save(path, quality=90)
    return path

def main():
    os.makedirs(IMGS, exist_ok=True)
    total_needed = IMAGES_PER_VIDEO + IMAGES_PER_SHORT
    print(f"Downloading {total_needed} images from Pexels...")
    images = download_pexels_images(total_needed)
    print(f"Got {len(images)} real images")
    idx = len(images)
    while len(images) < total_needed:
        images.append(generate_dark_image(idx))
        idx += 1
    print(f"Total: {len(images)} images ready")

if __name__ == "__main__":
    main()
