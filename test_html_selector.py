import asyncio
import pandas as pd
from playwright.async_api import async_playwright, expect
from rich import print
import re
from fractions import Fraction
from bs4 import BeautifulSoup
import os



async def launch_browser():
    """Initialize Playwright and open the browser."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    baseurl = "https://www.steelcase.com/products/monitor-arms-desk-accessories/soto-mobile-caddy"
    await page.goto(baseurl)

    html_content = await page.content()
    soup = BeautifulSoup(html_content, 'html.parser')

    with open("product-1.html", "w", encoding="utf-8") as file:
        file.write(soup.prettify())


asyncio.run(launch_browser())