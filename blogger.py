from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from app_paths import get_app_dir
from session_logger import append_log_line
import json
from analyzer_prompt import create_analyzer_prompt
from playwright.sync_api import sync_playwright
from selenium.webdriver.common.by import By
import time




load_dotenv()

class SeoBot:
    def __init__(self):
        self.url = os.getenv("URL")

        if not self.url:
            raise ValueError("URL not found in .env")

        if not self.url.startswith(("http://", "https://")):
            self.url = "https://" + self.url

        self._log(f"URL: {self.url}")

    def write_header_log(self, title, width=70):
            self._log("=" * width)
            self._log(title.center(width))
            self._log("=" * width)

        
    def _log(self, message):
        print(f"[Seo Blogger] {message}")

        try:
            SCRIPT_DIR = get_app_dir()
            append_log_line(message, SCRIPT_DIR)
        except OSError:
            pass

    async def crawl_website(self):

        async with AsyncWebCrawler() as crawler:

            result = await crawler.arun(
                url=self.url
            )

            crawl = result[0]

            if not crawl.success:
                self._log(
                    f"Crawl failed: {crawl.error_message}"
                )
                return None


            crawl_result = {
                "url": crawl.url,
                "markdown": crawl.markdown,
                "html": crawl.html,
                "links": crawl.links,
                "metadata": crawl.metadata
            }


            return crawl_result

    def analyze_website(self):
        # Check if knowledge already exists
        if os.path.exists("website_knowledge.json"):

            self._log(
                "Existing website knowledge found. Loading..."
            )

            with open(
                "website_knowledge.json",
                "r",
                encoding="utf-8"
            ) as file:

                website_data = json.load(file)


        else:

            self._log(
                "No website knowledge found. Crawling website..."
            )

            crawl_result = asyncio.run(
                self.crawl_website()
            )


            if not crawl_result:
                self._log(
                    "Website crawl failed"
                )
                return


            website_data = self.extract_website_data(
                crawl_result
            )


            self.save_knowledge(
                website_data
            )


            self._log(
                "Website knowledge extracted successfully"
            )



        self._log(
            json.dumps(
                website_data,
                indent=4
            )[:3000]
        )
        self._log("Analyzing Webstie Content")

        analyzer = create_analyzer_prompt(website_data)

        self._log("Business Analyzer Prompt Created")
        self._log(analyzer)
        if not os.path.exists("business_analysis.json"):
            AI_response = self.ask_ai(analyzer)

            self._log("AI Response is below")
            self._log(AI_response)

        


    def extract_website_data(self, crawl_result):


        data = {

            "website": crawl_result["url"],

            "title": "",

            "description": "",

            "headings": [],

            "links": [],

            "content": "",

            "possible_topics": []

        }



        # Metadata

        metadata = crawl_result.get(
            "metadata"
        )


        if metadata:

            data["title"] = metadata.get(
                "title",
                ""
            )

            data["description"] = metadata.get(
                "description",
                ""
            )



        # Content

        markdown = crawl_result.get(
            "markdown"
        )


        if markdown:

            data["content"] = markdown[:10000]



        # Links

        links = crawl_result.get(
            "links",
            {}
        )


        for link_type, items in links.items():

            for item in items:

                href = item.get(
                    "href"
                )

                if href:

                    data["links"].append(
                        href
                    )



        # Extract headings from markdown

        if markdown:

            for line in markdown.split("\n"):

                line = line.strip()


                if line.startswith("#"):

                    heading = line.replace(
                        "#",
                        ""
                    ).strip()


                    if heading:

                        data["headings"].append(
                            heading
                        )



        return data



    def save_knowledge(self, data):

        with open(
            "website_knowledge.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    def ask_ai(self, content):
    
            with sync_playwright() as p:
    
                browser = p.chromium.launch(
                    headless=False
                )
                context = browser.new_context(
                    permissions=[
                        "clipboard-read",
                        "clipboard-write"
                    ]
                )

    
                page = browser.new_page()
    
    
                page.goto(
                    "https://chat.openai.com"
                )
    
    
                page.wait_for_timeout(5000)

                editor = page.locator(
                    "[contenteditable='true']"
                )


                editor.wait_for(
                    state="visible",
                    timeout=30000
                )


                # editor.fill(content)
                editor.click()

                page.keyboard.insert_text(content)

                # time.sleep(3)
                page.wait_for_timeout(2000)

                page.keyboard.press("Enter")

                page.wait_for_timeout(10000)

                copy_button = page.locator(
                    'button[aria-label="Copy response"]'
                ).last

                copy_button.wait_for(
                    state="visible",
                    timeout=30000
                )
                copy_button.scroll_into_view_if_needed()

                copy_button.click()

                page.wait_for_timeout(1000)

                response = page.evaluate(
                    "navigator.clipboard.readText()"
                )


                self._log("writing ai response")
                self._log(response)
                analysis = json.loads(response)

                self.save_business_analysis(analysis)

                input("ok")

                browser.close()

    def save_business_analysis(self, data):

        os.makedirs(
            "data",
            exist_ok=True
        )


        with open(
            "business_analysis.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )
    




bot = SeoBot()
bot.analyze_website()