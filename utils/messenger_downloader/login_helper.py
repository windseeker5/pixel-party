#!/usr/bin/env python3
"""
Messenger Login Helper
Opens browser, lets you login manually, saves cookies for later use.
"""

import os
import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class LoginHelper:
    def __init__(self):
        self.thread_url = os.getenv('MESSENGER_THREAD_URL')
        self.cookies_file = Path('session_cookies.json')

        if not self.thread_url:
            raise ValueError("Missing MESSENGER_THREAD_URL in .env file")

    async def start_login_session(self):
        """Open browser for manual login and save cookies"""
        print("🌐 Starting Messenger login helper...")

        async with async_playwright() as p:
            # Launch browser in visible mode
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Navigate to your specific thread
            print(f"📱 Opening your thread: {self.thread_url}")
            await page.goto(self.thread_url)

            print("\n" + "="*60)
            print("🔐 LOGIN MANUALLY")
            print("="*60)
            print("👆 Browser window is now open")
            print("📝 Please complete the following steps:")
            print()
            print("1. 🔑 Enter your Facebook credentials")
            print("2. 🧩 Solve any CAPTCHAs")
            print("3. 📱 Handle 2FA if required")
            print("4. 🔢 Enter 6-digit conversation code if asked")
            print("5. ✅ Wait until you can see the conversation messages")
            print()
            print("When you can see the conversation:")
            print("🚪 Simply CLOSE the browser window")
            print("🍪 Cookies will be saved automatically")
            print("="*60)

            try:
                # Wait for the browser to close (user closes it manually)
                await page.wait_for_event('close', timeout=0)  # No timeout
            except:
                # Alternative: wait for browser to close
                try:
                    while not browser.is_closed():
                        await asyncio.sleep(1)
                except:
                    pass

            # Save cookies before closing
            print("\n💾 Saving login session...")
            cookies = await context.cookies()

            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)

            print(f"✅ Session saved to {self.cookies_file}")
            print("🎯 You can now run: python download_messages.py")

            await browser.close()

def main():
    """Main entry point"""
    try:
        helper = LoginHelper()
        asyncio.run(helper.start_login_session())
    except KeyboardInterrupt:
        print("\n⏹️ Login cancelled by user.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()