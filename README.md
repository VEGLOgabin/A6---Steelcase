# SteelCaseScraper

## Overview
SteelCaseScraper is a Python-based web scraper that extracts product details from the Steelcase website. It leverages Playwright for browser automation and BeautifulSoup for HTML parsing, allowing users to retrieve specifications, images, descriptions, and documentation for various products.

## Features
- Automates product searches based on manufacturer number or model name.
- Extracts product specifications, images, dimensions, certifications, and warranty details.
- Downloads product-related PDFs (brochures, spec sheets, and manuals).
- Stores extracted data in an Excel file.
- Supports headless browsing for efficiency.

## Requirements
Ensure you have the following dependencies installed:

```bash
pip install asyncio pandas playwright rich beautifulsoup4 openpyxl
```

Additionally, you must install Playwright browsers:

```bash
playwright install
```

## Usage
### Running the Scraper
To use the scraper, create an instance of `SteelCaseScraper` with the required parameters:

```python
from scraper import SteelCaseScraper
import asyncio

scraper = SteelCaseScraper(
    excel_path="input.xlsx", 
    output_filename="output.xlsx", 
    baseurl="https://www.steelcase.com/", 
    found=0, 
    missing=0, 
    headless=True
)

asyncio.run(scraper.run())
```

### Parameters
- `excel_path` : Path to the input Excel file containing product details.
- `output_filename` : Path to save the extracted data.
- `baseurl` : Base URL of the Steelcase website.
- `found` : Counter for successfully found products.
- `missing` : Counter for missing products.
- `headless` : Boolean flag to run the browser in headless mode.

### Output
The extracted data is stored in an Excel file, including:
- Product URL
- Product Image
- Description
- Specifications
- Dimensions (height, width, depth, weight)
- Green certification status
- PDFs (brochure, spec sheet, manual)

## Notes
- Ensure your Excel file contains the necessary columns (`mfr number`, `model name`).
- The script handles cookies and pop-ups automatically.
- Adjust timeouts if necessary to accommodate slow-loading pages.

## License
This project is licensed under the MIT License.
