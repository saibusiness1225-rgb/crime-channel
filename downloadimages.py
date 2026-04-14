"""
Image Downloader - OPTIMIZED
- Downloads high-quality crime/mystery images from Pexels
- Generates rich dark fallback images (NEVER black)
- Better image variety with more search queries
- Verifies image quality before including
"""
import os, random, requests
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from config import *


def download_pexels_images(count):
    """Download images from Pexels API with retry logic."""
    images = []
    queries = random.sample(PEXELS_QUERIES, min(count, len(PEXELS_QUERIES)))
    per_query = max(1, count // len(queries))

    for q in queries:
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": q, "per_page": per_query, "orientation": "landscape", "size": "large"},
                headers={"Authorization": PEXELS_KEY},
                timeout=20
            )
            if resp.status_code != 200:
                continue
            for photo in resp.json().get("photos", []):
                # Use large2x for better quality (was: large)
                img_url = photo["src"].get("large2x", photo["src"]["large"])
                try:
                    img_resp = requests.get(img_url, timeout=25)
                    if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                        path = os.path.join(IMGS, f"pexels_{photo['id']}.jpg")
                        with open(path, "wb") as f:
                            f.write(img_resp.content)
                        # Verify the image is not corrupted
                        try:
                            test = Image.open(path)
                            test.verify()
                            images.append(path)
                        except Exception:
                            os.remove(path)
                        if len(images) >= count:
                            return images
                except Exception:
                    continue
        except Exception as e:
            print(f"  Query '{q}' failed: {e}")

    return images


def generate_dark_image(index, w=1280, h=720):
    """
    IMPROVED: Generate a visually rich dark image that is NOT pure black.
    Creates moody atmospheric images with subtle light sources and textures.
    """
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    # Rich dark color palette (navy, dark purple, dark crimson)
    palettes = [
        (10, 8, 25),   # Deep navy
        (15, 5, 20),   # Dark purple
        (18, 8, 12),   # Dark crimson
        (8, 12, 18),   # Dark teal
        (12, 10, 8),   # Dark brown
    ]
    base_r, base_g, base_b = random.choice(palettes)

    # Vertical gradient
    for y in range(h):
        factor = 1.0 - (y / h) * 0.5
        draw.line([(0, y), (w, y)], fill=(int(base_r * factor), int(base_g * factor), int(base_b * factor)))

    # Add atmospheric light sources (prevents pure black appearance)
    num_lights = random.randint(1, 4)
    for _ in range(num_lights):
        cx = random.randint(w // 6, 5 * w // 6)
        cy = random.randint(h // 6, 5 * h // 6)
        max_radius = random.randint(80, 250)

        # Random warm/cool light colors
        light_colors = [
            (40, 15, 20),   # Warm red
            (20, 15, 45),   # Cool blue
            (30, 10, 35),   # Purple
            (25, 20, 15),   # Warm amber
        ]
        light_r, light_g, light_b = random.choice(light_colors)

        for radius in range(max_radius, 0, -6):
            opacity = (1 - radius / max_radius) * 0.2
            r = int(base_r * factor * (1 - opacity) + light_r * opacity)
            g = int(base_g * factor * (1 - opacity) + light_g * opacity)
            b = int(base_b * factor * (1 - opacity) + light_b * opacity)
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(r, g, b))

    # Apply slight blur for atmospheric effect
    img = img.filter(ImageFilter.GaussianBlur(6))

    # Enhance contrast
    img = ImageEnhance.Contrast(img).enhance(1.1)

    path = os.path.join(IMGS, f"gen_{index:03d}.jpg")
    img.save(path, quality=92)
    return path


def main():
    os.makedirs(IMGS, exist_ok=True)
    total_needed = IMAGES_PER_VIDEO + IMAGES_PER_SHORT + 10  # Extra buffer
    print(f"Downloading {total_needed} images from Pexels...")
    images = download_pexels_images(total_needed)
    print(f"Got {len(images)} real images")

    # Fill remaining with generated atmospheric images
    idx = len(images)
    while len(images) < total_needed:
        img = generate_dark_image(idx)
        images.append(img)
        idx += 1

    # Verify all images are valid
    valid_images = []
    for img_path in images:
        try:
            if os.path.exists(img_path) and os.path.getsize(img_path) > 3000:
                test = Image.open(img_path)
                test.verify()
                valid_images.append(img_path)
        except Exception:
            print(f"  Removing corrupt image: {img_path}")
            try:
                os.remove(img_path)
            except Exception:
                pass

    print(f"Total: {len(valid_images)} valid images ready")


if __name__ == "__main__":
    main()
