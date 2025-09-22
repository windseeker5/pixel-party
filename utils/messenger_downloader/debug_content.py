#!/usr/bin/env python3
"""
Debug script to see what content is actually accessible
"""

import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class ContentDebugger:
    def __init__(self):
        self.thread_url = os.getenv('MESSENGER_THREAD_URL')
        self.cookies_file = Path('session_cookies.json')

    async def debug_content(self):
        """Debug what content we can actually see and access"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Load cookies
            if self.cookies_file.exists():
                import json
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)

            # Navigate to thread
            await page.goto(self.thread_url)
            await page.wait_for_timeout(5000)

            print("=== DEBUGGING MESSENGER CONTENT ===")

            # Check page title and URL
            title = await page.title()
            url = page.url
            print(f"Page title: {title}")
            print(f"Current URL: {url}")

            # Look for all images
            all_images = await page.query_selector_all('img')
            print(f"\n📸 Found {len(all_images)} total <img> elements")

            # Check what types of src attributes we have
            src_types = {}
            for i, img in enumerate(all_images[:20]):  # Check first 20
                src = await img.get_attribute('src')
                if src:
                    if src.startswith('data:'):
                        src_types['data_url'] = src_types.get('data_url', 0) + 1
                    elif src.startswith('blob:'):
                        src_types['blob'] = src_types.get('blob', 0) + 1
                    elif 'scontent' in src:
                        src_types['scontent'] = src_types.get('scontent', 0) + 1
                    elif 'fbcdn' in src:
                        src_types['fbcdn'] = src_types.get('fbcdn', 0) + 1
                    else:
                        src_types['other'] = src_types.get('other', 0) + 1
                        print(f"  Other type: {src[:50]}...")

            print(f"Image src types: {src_types}")

            # Look for videos
            all_videos = await page.query_selector_all('video')
            print(f"\n🎥 Found {len(all_videos)} <video> elements")

            # Check video sources
            for i, video in enumerate(all_videos):
                src = await video.get_attribute('src')
                poster = await video.get_attribute('poster')
                print(f"  Video {i}: src={src[:50] if src else 'None'}")
                print(f"            poster={poster[:50] if poster else 'None'}")

            # Look for potential video containers
            video_containers = await page.query_selector_all('[aria-label*="video"], [aria-label*="Video"]')
            print(f"\n🎬 Found {len(video_containers)} elements with video labels")

            # Look for play buttons
            play_buttons = await page.query_selector_all('[aria-label*="play"], [aria-label*="Play"]')
            print(f"▶️  Found {len(play_buttons)} play button elements")

            # Look for media attachments
            attachments = await page.query_selector_all('[aria-label*="attachment"], [role="button"][aria-label*="media"]')
            print(f"📎 Found {len(attachments)} attachment elements")

            # Take a screenshot for debugging
            await page.screenshot(path='debug_screenshot.png')
            print(f"\n📷 Screenshot saved as debug_screenshot.png")

            # Try to access one image URL to test authentication
            scontent_images = await page.query_selector_all('img[src*="scontent"]')
            if scontent_images:
                first_img = scontent_images[0]
                img_src = await first_img.get_attribute('src')
                print(f"\n🔍 Testing image access: {img_src[:50]}...")

                try:
                    response = await page.request.get(img_src)
                    print(f"   Status: {response.status}")
                    if response.status != 200:
                        print(f"   Headers: {dict(response.headers)}")
                except Exception as e:
                    print(f"   Error: {e}")

            print("\n=== END DEBUG ===")

            input("Press Enter to close browser...")
            await browser.close()

async def main():
    debugger = ContentDebugger()
    await debugger.debug_content()

if __name__ == "__main__":
    asyncio.run(main())