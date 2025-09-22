#!/usr/bin/env python3
"""
Simple Messenger Thread Downloader
Downloads all photos, videos, and messages from a specific Facebook Messenger thread.
"""

import os
import json
import time
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import requests
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class MessengerDownloader:
    def __init__(self):
        self.email = os.getenv('FACEBOOK_EMAIL')
        self.password = os.getenv('FACEBOOK_PASSWORD')
        self.thread_url = os.getenv('MESSENGER_THREAD_URL')

        if not all([self.email, self.password, self.thread_url]):
            raise ValueError("Missing required environment variables. Check .env file.")

        # Create output directories
        self.output_dir = Path('output')
        self.photos_dir = self.output_dir / 'photos'
        self.videos_dir = self.output_dir / 'videos'

        self.output_dir.mkdir(exist_ok=True)
        self.photos_dir.mkdir(exist_ok=True)
        self.videos_dir.mkdir(exist_ok=True)

        self.messages = []
        self.downloaded_files = set()
        self.browser = None
        self.page = None

    async def setup_browser(self):
        """Setup browser and navigate to messenger - fully manual login"""
        print("🌐 Opening Chromium browser...")

        # Launch browser in visible mode
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        context = await self.browser.new_context()
        self.page = await context.new_page()

        # Navigate to messenger
        print(f"📱 Navigating to your thread: {self.thread_url}")
        await self.page.goto(self.thread_url)

        print("\n" + "="*60)
        print("🔐 MANUAL LOGIN REQUIRED")
        print("="*60)
        print("👆 The browser window is now open")
        print("🔑 Please log in manually (handle all CAPTCHAs, 2FA, etc.)")
        print("📱 Enter the 6-digit conversation code if asked")
        print("✅ When you can see the conversation messages...")
        print("💬 Press ENTER in this terminal to continue downloading!")
        print("="*60)

    def wait_for_user_ready(self):
        """Wait for user to press Enter when ready"""
        input()  # This blocks until user presses Enter
        print("🚀 Starting download process...")

    async def scroll_to_load_all_content(self, page):
        """Scroll through the entire conversation to load all messages"""
        print("Scrolling to load all conversation history...")

        previous_height = 0
        scroll_attempts = 0
        max_attempts = 100  # Prevent infinite loop

        while scroll_attempts < max_attempts:
            # Scroll to top to load older messages
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(2000)

            # Get current scroll height
            current_height = await page.evaluate("document.body.scrollHeight")

            if current_height == previous_height:
                print("Reached the beginning of the conversation.")
                break

            previous_height = current_height
            scroll_attempts += 1

            if scroll_attempts % 10 == 0:
                print(f"Scrolled {scroll_attempts} times, still loading...")

        print(f"Finished scrolling after {scroll_attempts} attempts.")

    async def extract_messages(self, page):
        """Extract all text messages with metadata"""
        print("Extracting text messages...")

        # Try different selectors for messages
        message_selectors = [
            '[role="main"] [role="gridcell"]',
            '[data-testid="conversation"] div[role="gridcell"]',
            '[role="main"] div[dir="auto"]',
            'div[data-scope="messages_table"]',
            '.x78zum5.x1q0g3np',  # Common message container class
            '[role="main"] div'  # Fallback to any div in main
        ]

        all_messages = []

        for selector in message_selectors:
            try:
                messages = await page.query_selector_all(selector)
                if messages and len(messages) > 5:  # Only use if we find substantial content
                    print(f"Found {len(messages)} message elements with selector: {selector}")

                    for i, msg in enumerate(messages[:100]):  # Limit for testing
                        try:
                            text = await msg.inner_text()
                            if text and len(text.strip()) > 3 and len(text.strip()) < 1000:  # Filter reasonable messages
                                timestamp = datetime.now().isoformat()  # Placeholder
                                all_messages.append({
                                    'id': i,
                                    'text': text.strip(),
                                    'timestamp': timestamp,
                                    'sender': 'Unknown'  # Will need better extraction
                                })
                        except Exception as e:
                            continue

                    if len(all_messages) > 0:
                        break  # Use the first selector that gives us results

            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue

        self.messages = all_messages
        print(f"Extracted {len(self.messages)} messages.")

    async def download_media(self, page):
        """Download all photos and videos from the conversation"""
        print("Finding and downloading media files...")

        # Find all images - try multiple selectors for better quality
        image_selectors = [
            'img[src*="scontent"]',
            'img[src*="fbcdn"]',
            'img[data-src*="scontent"]',
            'img[style*="background-image"]',
            '[role="img"]'
        ]

        all_images = set()  # Use set to avoid duplicates

        for selector in image_selectors:
            images = await page.query_selector_all(selector)
            for img in images:
                try:
                    # Try to get highest resolution source
                    src = await img.get_attribute('src')
                    data_src = await img.get_attribute('data-src')

                    # Prefer data-src (usually higher quality) over src
                    image_url = data_src if data_src else src

                    if image_url and ('scontent' in image_url or 'fbcdn' in image_url):
                        # Try to get full resolution by modifying URL
                        if '_s.jpg' in image_url:
                            image_url = image_url.replace('_s.jpg', '_o.jpg')  # s=small, o=original
                        elif '_n.jpg' in image_url:
                            image_url = image_url.replace('_n.jpg', '_o.jpg')  # n=normal, o=original

                        all_images.add(image_url)

                except Exception as e:
                    continue

        print(f"Found {len(all_images)} unique images.")

        photo_count = 0
        for image_url in all_images:
            try:
                # Get file extension from URL
                ext = 'jpg'
                if '.png' in image_url.lower():
                    ext = 'png'
                elif '.gif' in image_url.lower():
                    ext = 'gif'

                filename = f"photo_{photo_count:03d}.{ext}"
                await self.download_file(image_url, self.photos_dir / filename)
                photo_count += 1

                if photo_count % 5 == 0:
                    print(f"Downloaded {photo_count} photos...")

            except Exception as e:
                print(f"Error downloading image: {e}")
                continue

        # Find all videos
        videos = await page.query_selector_all('video')
        print(f"Found {len(videos)} videos.")

        video_count = 0
        for i, video in enumerate(videos):
            try:
                src = await video.get_attribute('src')
                if src and src.startswith('blob:'):
                    # Blob URLs require different handling
                    print(f"Found video with blob URL (may need screen recording): {src}")
                elif src:
                    filename = f"video_{video_count:03d}.mp4"
                    await self.download_file(src, self.videos_dir / filename)
                    video_count += 1

            except Exception as e:
                print(f"Error downloading video {i}: {e}")
                continue

        print(f"Downloaded {photo_count} photos and {video_count} videos.")

    async def download_file(self, url, filepath):
        """Download a file from URL to local path"""
        if url in self.downloaded_files:
            return

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.downloaded_files.add(url)

        except Exception as e:
            print(f"Error downloading {url}: {e}")

    async def save_messages(self):
        """Save all messages to JSON file"""
        messages_file = self.output_dir / 'messages.json'

        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(self.messages, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(self.messages)} messages to {messages_file}")

    async def run(self):
        """Main execution method"""
        print("Starting Messenger downloader...")

        try:
            # Setup browser and navigate to thread
            await self.setup_browser()

            # Wait for user to complete manual login
            self.wait_for_user_ready()

            # Now start the download process
            await self.scroll_to_load_all_content(self.page)
            await self.extract_messages(self.page)
            await self.download_media(self.page)
            await self.save_messages()

            print("\n✅ Download completed!")
            print(f"📁 Check the 'output' folder for your files:")
            print(f"   📷 Photos: {len(list(self.photos_dir.glob('*.*')))} files")
            print(f"   🎥 Videos: {len(list(self.videos_dir.glob('*.*')))} files")
            print(f"   💬 Messages: {len(self.messages)} messages")

        except Exception as e:
            print(f"❌ Error during execution: {e}")

        finally:
            if self.browser:
                await self.browser.close()

def main():
    """Main entry point"""
    try:
        downloader = MessengerDownloader()
        asyncio.run(downloader.run())
    except KeyboardInterrupt:
        print("\n⏹️ Download cancelled by user.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()