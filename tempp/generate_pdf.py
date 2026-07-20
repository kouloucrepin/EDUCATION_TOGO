import asyncio
import sys
import os
from playwright.async_api import async_playwright

HTML_PATH = os.path.join(os.path.dirname(__file__), "methodologie.html")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "Methodologie_Dashboard_Education_Togo.pdf")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2,
        )
        page = await context.new_page()

        file_url = "file://" + HTML_PATH.replace("\\", "/")
        await page.goto(file_url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        await page.pdf(
            path=OUTPUT_PATH,
            format="A4",
            margin={"top": "0.4in", "bottom": "0.4in", "left": "0.4in", "right": "0.4in"},
            print_background=True,
            display_header_footer=False,
            prefer_css_page_size=False,
        )

        await browser.close()
        print(f"PDF generated: {OUTPUT_PATH}")
        print(f"Size: {os.path.getsize(OUTPUT_PATH) / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    asyncio.run(main())
