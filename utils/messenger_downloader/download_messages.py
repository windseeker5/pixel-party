#!/usr/bin/env python3
"""
Messenger Content Downloader
Uses saved cookies to download photos, videos, and messages from thread.
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
import requests
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class MessageDownloader:
    def __init__(self):
        self.thread_url = os.getenv('MESSENGER_THREAD_URL')
        self.cookies_file = Path('session_cookies.json')

        if not self.thread_url:
            raise ValueError("Missing MESSENGER_THREAD_URL in .env file")

        if not self.cookies_file.exists():
            raise ValueError("No cookies file found. Please run: python login_helper.py first")

        # Create output directories
        self.output_dir = Path('output')
        self.photos_dir = self.output_dir / 'photos'
        self.videos_dir = self.output_dir / 'videos'

        self.output_dir.mkdir(exist_ok=True)
        self.photos_dir.mkdir(exist_ok=True)
        self.videos_dir.mkdir(exist_ok=True)

        self.messages = []
        self.downloaded_files = set()

    async def load_session(self, context):
        """Load saved cookies into browser context"""
        print("🍪 Loading saved login session...")

        with open(self.cookies_file, 'r') as f:
            cookies = json.load(f)

        await context.add_cookies(cookies)
        print("✅ Session loaded successfully")

    async def navigate_to_thread(self, page):
        """Navigate to the thread using saved session"""
        print(f"📱 Navigating to thread: {self.thread_url}")
        await page.goto(self.thread_url)
        await page.wait_for_timeout(5000)

        # Check if we're logged in
        if 'login' in page.url or 'checkpoint' in page.url:
            print("❌ Session expired. Please run: python login_helper.py")
            return False

        print("✅ Successfully accessed thread")

        # Wait 30 seconds for any 6-digit code entry
        print("⏳ Waiting 30 seconds for any 6-digit conversation code...")
        print("   (Enter the code if prompted, or just wait)")
        await page.wait_for_timeout(30000)
        print("✅ Proceeding with download...")

        return True

    async def scroll_to_load_all_content(self, page):
        """Scroll through the entire conversation to load all messages"""
        print("📜 Scrolling to load all conversation history...")

        previous_height = 0
        scroll_attempts = 0
        max_attempts = 50  # Reasonable limit

        while scroll_attempts < max_attempts:
            # Scroll to top to load older messages
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(3000)  # Wait for content to load

            # Get current scroll height
            current_height = await page.evaluate("document.body.scrollHeight")

            if current_height == previous_height:
                print("✅ Reached the beginning of conversation")
                break

            previous_height = current_height
            scroll_attempts += 1

            if scroll_attempts % 10 == 0:
                print(f"⏳ Scrolled {scroll_attempts} times, still loading...")

        print(f"📜 Finished scrolling after {scroll_attempts} attempts")

    async def extract_messages(self, page):
        """Extract all text messages with metadata"""
        print("💬 Extracting text messages...")

        # Try different selectors for messages
        message_selectors = [
            '[role="main"] [role="gridcell"]',
            '[data-testid="conversation"] div[role="gridcell"]',
            '[role="main"] div[dir="auto"]',
            'div[data-scope="messages_table"]',
            '[role="main"] div'
        ]

        all_messages = []

        for selector in message_selectors:
            try:
                messages = await page.query_selector_all(selector)
                if messages and len(messages) > 10:  # Only use if substantial content
                    print(f"📝 Found {len(messages)} message elements")

                    for i, msg in enumerate(messages[:200]):  # Reasonable limit
                        try:
                            text = await msg.inner_text()
                            if text and 5 < len(text.strip()) < 500:  # Filter reasonable messages
                                timestamp = datetime.now().isoformat()
                                all_messages.append({
                                    'id': i,
                                    'text': text.strip(),
                                    'timestamp': timestamp,
                                    'sender': 'Unknown'
                                })
                        except:
                            continue

                    if len(all_messages) > 0:
                        break

            except Exception as e:
                continue

        self.messages = all_messages
        print(f"✅ Extracted {len(self.messages)} messages")

    async def download_media(self, page):
        """Download all photos and videos from the conversation"""
        print("📸 Finding and downloading media files...")

        # Find images with multiple selectors for better coverage
        image_selectors = [
            'img[src*="scontent"]',
            'img[src*="fbcdn"]',
            'img[data-src*="scontent"]',
            'img[data-src*="fbcdn"]',
            '[role="img"] img'
        ]

        all_images = set()

        for selector in image_selectors:
            images = await page.query_selector_all(selector)
            for img in images:
                try:
                    # Get best quality source
                    src = await img.get_attribute('src')
                    data_src = await img.get_attribute('data-src')

                    image_url = data_src if data_src else src

                    if image_url and ('scontent' in image_url or 'fbcdn' in image_url):
                        # Try to get original resolution
                        if '_s.jpg' in image_url:
                            image_url = image_url.replace('_s.jpg', '_o.jpg')
                        elif '_n.jpg' in image_url:
                            image_url = image_url.replace('_n.jpg', '_o.jpg')

                        all_images.add(image_url)

                except:
                    continue

        print(f"📸 Found {len(all_images)} unique images")

        # Download images
        photo_count = 0
        for image_url in all_images:
            try:
                ext = 'jpg'
                if '.png' in image_url.lower():
                    ext = 'png'
                elif '.gif' in image_url.lower():
                    ext = 'gif'

                filename = f"photo_{photo_count:03d}.{ext}"
                await self.download_file(image_url, self.photos_dir / filename, page)
                photo_count += 1

                if photo_count % 5 == 0:
                    print(f"📥 Downloaded {photo_count} photos...")

            except Exception as e:
                continue

        # Find videos using multiple selectors
        video_selectors = [
            'video',
            '[role="presentation"] video',
            'div[data-testid*="video"]',
            'div[aria-label*="video"]',
            'div[aria-label*="Video"]',
            'video[src]',
            'video[data-src]'
        ]

        all_videos = set()
        for selector in video_selectors:
            videos = await page.query_selector_all(selector)
            for video in videos:
                try:
                    # Try to get video source
                    src = await video.get_attribute('src')
                    data_src = await video.get_attribute('data-src')
                    poster = await video.get_attribute('poster')

                    video_url = data_src if data_src else src

                    if video_url and not video_url.startswith('blob:'):
                        all_videos.add(video_url)
                    elif src and src.startswith('blob:'):
                        # For blob URLs, try to extract from parent elements
                        parent = await video.query_selector('..')
                        if parent:
                            parent_html = await parent.inner_html()
                            # Look for video URLs in parent HTML
                            import re
                            urls = re.findall(r'https://[^"\'>\s]+\.mp4[^"\'>\s]*', parent_html)
                            for url in urls:
                                all_videos.add(url)

                except Exception as e:
                    continue

        print(f"🎥 Found {len(all_videos)} video URLs")

        # Also try to find video attachments
        video_attachments = await page.query_selector_all('[aria-label*="video attachment"], [aria-label*="Video attachment"]')
        print(f"📎 Found {len(video_attachments)} video attachments")

        video_count = 0
        for video_url in all_videos:
            try:
                # Get file extension
                ext = 'mp4'
                if '.mov' in video_url.lower():
                    ext = 'mov'
                elif '.avi' in video_url.lower():
                    ext = 'avi'

                filename = f"video_{video_count:03d}.{ext}"
                await self.download_file(video_url, self.videos_dir / filename, page)
                video_count += 1

                if video_count % 2 == 0:
                    print(f"🎥 Downloaded {video_count} videos...")

            except Exception as e:
                print(f"❌ Error downloading video: {e}")
                continue

        # Try alternative method for videos embedded in messages
        if video_count == 0:
            print("🔍 Searching for videos in message attachments...")
            await self.try_extract_video_from_attachments(page)

        # Also try searching page source for video URLs
        if video_count == 0:
            print("🔍 Searching page source for video URLs...")
            video_count += await self.search_page_source_for_videos(page)

        print(f"✅ Downloaded {photo_count} photos and {video_count} videos")

    async def try_extract_video_from_attachments(self, page):
        """Try to find videos in message attachments"""
        try:
            # Look for video play buttons or video thumbnails
            video_elements = await page.query_selector_all(
                'div[aria-label*="play"], '
                'div[role="button"][aria-label*="video"], '
                '[data-testid*="video"], '
                'div[aria-label*="Play video"], '
                'svg[aria-label*="play"]'
            )

            print(f"🎬 Found {len(video_elements)} potential video elements")

            video_count = 0
            for element in video_elements[:5]:  # Limit to first 5 to avoid spam
                try:
                    # Try clicking to reveal video source
                    await element.click()
                    await page.wait_for_timeout(2000)

                    # Look for video elements that appeared
                    new_videos = await page.query_selector_all('video[src]:not([src^="blob:"])')
                    for video in new_videos:
                        src = await video.get_attribute('src')
                        if src and src not in self.downloaded_files:
                            filename = f"video_attachment_{video_count:03d}.mp4"
                            await self.download_file(src, self.videos_dir / filename, page)
                            video_count += 1

                except Exception as e:
                    continue

            if video_count > 0:
                print(f"🎥 Downloaded {video_count} videos from attachments")

        except Exception as e:
            print(f"⚠️ Could not extract videos from attachments: {e}")

    async def search_page_source_for_videos(self, page):
        """Search page source for video URLs"""
        try:
            # Get page content
            content = await page.content()

            # Look for video URLs in the HTML
            import re
            video_patterns = [
                r'https://[^"\'>\s]+\.mp4[^"\'>\s]*',
                r'https://[^"\'>\s]+\.mov[^"\'>\s]*',
                r'https://[^"\'>\s]+\.avi[^"\'>\s]*',
                r'https://video[^"\'>\s]+fbcdn[^"\'>\s]+',
                r'https://scontent[^"\'>\s]+\.mp4[^"\'>\s]*'
            ]

            found_videos = set()
            for pattern in video_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Clean up the URL
                    video_url = match.split('&')[0] if '&' in match else match
                    if len(video_url) > 50:  # Reasonable length check
                        found_videos.add(video_url)

            print(f"🔍 Found {len(found_videos)} video URLs in page source")

            video_count = 0
            for video_url in list(found_videos)[:10]:  # Limit to 10
                try:
                    filename = f"video_source_{video_count:03d}.mp4"
                    await self.download_file(video_url, self.videos_dir / filename, page)
                    video_count += 1
                    print(f"🎥 Downloaded video from source: {video_url[:50]}...")

                except Exception as e:
                    continue

            return video_count

        except Exception as e:
            print(f"⚠️ Could not search page source for videos: {e}")
            return 0

    async def download_file(self, url, filepath, page):
        """Download file using browser context (preserves authentication)"""
        if url in self.downloaded_files:
            return

        try:
            # Use the browser context to download (preserves cookies/auth)
            response = await page.request.get(url)

            if response.status == 200:
                content = await response.body()
                with open(filepath, 'wb') as f:
                    f.write(content)
                self.downloaded_files.add(url)
            else:
                print(f"❌ Status {response.status} for {url}")

        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")

    async def save_messages(self):
        """Save messages to JSON file"""
        messages_file = self.output_dir / 'messages.json'

        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(self.messages, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved {len(self.messages)} messages to {messages_file}")

    async def run(self):
        """Main download process"""
        print("🚀 Starting Messenger content download...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Load saved session
                await self.load_session(context)

                # Navigate to thread
                if not await self.navigate_to_thread(page):
                    return

                # Download everything
                await self.scroll_to_load_all_content(page)
                await self.extract_messages(page)
                await self.download_media(page)
                await self.save_messages()

                print("\n🎉 Download completed successfully!")
                print(f"📁 Check the 'output' folder:")
                print(f"   📷 Photos: {len(list(self.photos_dir.glob('*.*')))} files")
                print(f"   🎥 Videos: {len(list(self.videos_dir.glob('*.*')))} files")
                print(f"   💬 Messages: {len(self.messages)} messages")

            except Exception as e:
                print(f"❌ Error: {e}")

            finally:
                await browser.close()

def main():
    """Main entry point"""
    try:
        downloader = MessageDownloader()
        asyncio.run(downloader.run())
    except KeyboardInterrupt:
        print("\n⏹️ Download cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()