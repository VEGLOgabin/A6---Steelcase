import asyncio
import pandas as pd
from playwright.async_api import async_playwright, expect
from rich import print
import re
from fractions import Fraction
from bs4 import BeautifulSoup
import os

class SteelCaseScraper:
    """Web scraper for extracting product details from Steelcase."""
    def __init__(self, excel_path: str, output_filename: str, baseurl : str, found : int, missing : int, headless: bool = False):
        self.filepath = excel_path
        self.output_filename = output_filename
        self.baseurl = baseurl
        self.headless = headless
        self.found = found
        self.missing = missing
        self.df = pd.read_excel(self.filepath, sheet_name="Grainger")

    async def launch_browser(self):
        """Initialize Playwright and open the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def close_browser(self):
        """Close the browser and Playwright instance."""
        await self.browser.close()
        await self.playwright.stop()

    async def search_product(self, search_term: str):
        """Search for a product by search term  and return its first result URL."""
        try:
            await self.page.wait_for_selector('input[data-js="site-search__input"]')
            search_input = self.page.locator('input[data-js="site-search__input"]')
            await search_input.fill(search_term)
            await self.page.keyboard.press("Enter")

            await self.page.wait_for_timeout(1000)
            
            cookie_button = self.page.locator('button#onetrust-reject-all-handler')
            if await cookie_button.is_visible():
                await cookie_button.click()
                await self.page.wait_for_timeout(1000)

            html_content = await self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
          
            search_result = soup.find("a", class_ = "card-link")

            if search_result:
                url = search_result.get("href")
                return url
            return None
            
        except Exception as e:
            print(f"Error occurred: {e}")
        return None
        
    async def scrape_product_details(self, url: str):
        """Extract product details from the given URL."""
        print(f"[cyan]Scraping data from:[/cyan] {url}")
        new_page = await self.context.new_page()
        await new_page.goto(url)
        await self.page.wait_for_timeout(5000)
        cookie_button = self.page.locator('button#onetrust-reject-all-handler')
        if await cookie_button.is_visible():
            await cookie_button.click()
            await self.page.wait_for_timeout(1000)

        try:
            specs_button = new_page.locator('//button[@data-drawer-name="specifications"]')
            await specs_button.wait_for(state="visible", timeout=5000)
            await specs_button.click()
            await new_page.wait_for_timeout(1000)  # Give time for content to load
        except Exception as e:
            print(f"Error clicking specs button: {e}")
        data = {
            "url": url,
            "image": "",
            "price" : "",
            "description": "",
            "specifications": {},
            "dimensions" : "",
            "green_certification" : "",
            "spec_pdf" : ""
        }

        specifications = {}

        #Extract Specificatiobns
        try:
            html_content = await new_page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract specifications from the opened "Specs" section
            specifications = {}
            specs_list = soup.find("ul", class_="spec-summary-data-list")
            if specs_list:
                for item in specs_list.find_all("li", class_="spec-summary--item"):
                    label = item.find("span", class_="spec-summary-data-item__label")
                    value = item.find("span", class_="spec-summary-data-item__content")
                    if label and value:
                        specifications[label.get_text(strip=True)] = value.get_text(strip=True)

                data["specifications"] = specifications
                data["dimensions"] = {
                    "height": specifications.get("Height", ""),
                    "width": specifications.get("Width", ""),
                    "depth": specifications.get("Depth", ""),
                    "weight": specifications.get("Product Weight", "")
                }

                print(specifications)

        except Exception as e:
            print(f"Error extracting specifications: {e}")            
        # Extract Product Image (jpg)
        try:
            
            image_locators =soup.find_all("img")
            
        except Exception as e:
            print(f"Error extracting image: {e}")

        # Extract Product Description
        try:
        
            description_locator = soup.find("ul", class_ = "product-details__info-description")
            if description_locator:
                data["description"] = description_locator.get_text().replace("\n", "").replace("\t", "")

        except Exception as e:
            print(f"Error extracting description: {e}")

        # Extract Measurements and Dimensions
        try:

            dimensions = self.extract_dimensions(data["specifications"])
            data["dimensions"] = dimensions

        except Exception as e:
            print(f"Error extracting dimensions: {e}")

        # Extract Price
        try:
            price_div = soup.find("div", class_="PriceInfoText_priceInfo__QEjy8")
        except Exception as e:
            print(f"Error extracting price: {e}")

        #Extract Specification pdf download link
        try:
            spec_pdf_div = soup.find('div', class_ = "span-sm-2 span-lg-2 spec-download")
            
        except Exception as e:
            print(f"Error extracting spec_pdf: {e}")

        #Extract green certification
        try:
            data["green_certification"]  = self.check_certification(specifications)
                
        except Exception as e:
            print(f"Error extracting certification: {e}")
        await new_page.close()
        return data


    async def run(self):
        """Main function to scrape product details and save them to an Excel file."""
        await self.launch_browser()
        await self.page.goto(self.baseurl)

        for index, row in self.df.iterrows():
            mfr_number = row["mfr number"]
            model_name = row['model name']
            url = await self.search_product(str(mfr_number))
            if not url:
                url = await self.search_product(str(model_name))
            if not url:
                self.missing += 1
            else:
                self.found += 1

            print(url)

            if url:
                product_data = await self.scrape_product_details(url)
            #     if product_data:
            #         print(f"[green]{model_name} | {mfr_number} [/green] - Data extracted successfully.")
            #         self.df.at[index, "Product URL"] = product_data.get("url", "")
            #         self.df.at[index, "Product Image (jpg)"] = product_data.get("image", "")
            #         self.df.at[index, "Product Image"] = product_data.get("image", "")
            #         self.df.at[index, "product description"] = product_data.get("description", "")
            #         self.df.at[index, "Specification Sheet (pdf)"] = product_data.get("spec_pdf", "")
            #         self.df.at[index, "unit cost"] = product_data.get("price", "")
            #         self.df.at[index, "depth"] = product_data["dimensions"].get("depth", "")
            #         self.df.at[index, "height"] = product_data["dimensions"].get("height", "")
            #         self.df.at[index, "width"] = product_data["dimensions"].get("width", "")
            #         self.df.at[index, "weight"] = product_data["dimensions"].get("weight", "")
            #         self.df.at[index, "ship_weight"] = product_data["dimensions"].get("shipping_weight", "")
            #         self.df.at[index, "green certification? (Y/N)"] = product_data.get("green_certification", "")
            #         self.df.at[index, "emergency_power Required (Y/N)"] = "N"
            #         self.df.at[index, "dedicated_circuit Required (Y/N)"] = "N"
            #         self.df.at[index, "water_cold Required (Y/N)"] = "N"
            #         self.df.at[index, "water_hot  Required (Y/N)"] = "N"
            #         self.df.at[index, "drain Required (Y/N)"] = "N"
            #         self.df.at[index, "water_treated (Y/N)"] = "N"
            #         self.df.at[index, "steam  Required(Y/N)"] = "N"
            #         self.df.at[index, "vent  Required (Y/N)"] = "N"
            #         self.df.at[index, "vacuum Required (Y/N)"] = "N"
            #         self.df.at[index, "ada compliant (Y/N)"] = "N"
            #         self.df.at[index, "antimicrobial coating (Y/N)"] = "N"
            # else:
            #     print(f"[red]{model_name} | {mfr_number} [/red] - Not found")  if not url:
              
        print(f"[red]Missing : {self.missing} [/red]")
        print(f"[green]Found : {self.found} [/green]")
        self.df.to_excel(self.output_filename, index=False, sheet_name="Grainger")
        await self.close_browser()


if __name__ == "__main__":
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    scraper = SteelCaseScraper(
        excel_path="Steelcase Content.xlsx",
        output_filename="output/Steelcase-output.xlsx",
        baseurl = "https://www.steelcase.com/?s=&engine=products",
        found = 0 ,
        missing = 0,
        headless=False
    )
    asyncio.run(scraper.run())