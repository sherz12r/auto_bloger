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
from keyword_analyzer_prompt import create_keyword_analyzer_prompt
from playwright.sync_api import sync_playwright
from selenium.webdriver.common.by import By
import time
from keyword_research import generate_keyword_seeds
from pytrends.request import TrendReq
import pandas as pd
from random import uniform
from urllib.parse import urlparse


load_dotenv()

class SeoBot:
    def __init__(self):
        self.url = os.getenv("URL")

        if not self.url:
            raise ValueError("URL not found in .env")

        if not self.url.startswith(("http://", "https://")):
            self.url = "https://" + self.url

        self._log(f"URL: {self.url}")

    def random_sleep():
        time.sleep(uniform(9.8, 15.5))



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

    def do_seo(self):
        # Check if knowledge already exists
        self.write_header_log(
                    "Bot Started"
                )
        websites = self.get_websites()
        for web in websites:
        # if web['crawl_data'] is not None:
            domain = urlparse(web).hostname
            self._log(f"working for: {domain}")
            if os.path.exists(f"data/{domain}_knowledge.json"):

                self._log(
                    "Existing website knowledge found. Loading..."
                )

                with open(
                    f"data/{domain}_knowledge.json",
                    "r",
                    encoding="utf-8"
                ) as file:

                    website_data = json.load(file)
                # website_data = web['crawl_data']

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

                self._log(f"TYPE: {type(website_data)}")
                self._log(f"DATA: {website_data}")
                self.save_file(
                    website_data, f"{domain}_knowledge"
                )
                self._log(
                        "Website knowledge extracted successfully"
                    )
                # self.post_data(web['id'], json.dumps(
                #                     website_data,
                #                     indent=4
                #                 ))


                self._log(
                    "Website knowledge extracted successfully"
                )



            self._log(
                json.dumps(
                    website_data,
                    indent=4
                )[:5000]
            )
            self._log("Analyzing Webstie Content")


            if not os.path.exists(f"data/{domain}_business_analysis.json"):
                analyzer = create_analyzer_prompt(website_data)
    
                self._log("Business Analyzer Prompt Created")
                self._log(analyzer)

                AI_response = self.ask_ai(analyzer, domain)


                business = json.loads(
                    AI_response
                )


                with open(
                    f"{domain}_business_analysis.json",
                    "w",
                    encoding="utf-8"
                ) as f:

                    json.dump(
                        business,
                        f,
                        indent=4,
                        ensure_ascii=False
                    )


            else:

                with open(
                    f"data/{domain}_business_analysis.json",
                    "r",
                    encoding="utf-8"
                ) as f:

                    business = json.load(f)

            if not os.path.exists(f"data/{domain}_keyword_database.json"):
                seed = generate_keyword_seeds(
                    business
                )

            self._log("working on keywords")
            self._log(f"keywords: {seed}")
            self._log("keywords finished")

            google_trends = self.get_google_trends(seed)

            refined_keywords = self.flatten_keywords(google_trends)
            refined_keywords = self.remove_duplicates(refined_keywords)
            self.save_file(refined_keywords, f"{domain}_keyword_database")
            self._log(refined_keywords)
        else:
            with open(
                f"data/{domain}_keyword_database.json",
                "r",
                encoding="utf-8"
            ) as f:

                refined_keywords = json.load(f)
            
            keyword_classification = create_keyword_analyzer_prompt(refined_keywords)
            self._log("Keyword Analyzer Prompt Created")
            self._log(keyword_classification)

            self._log("asking Ai to analyze keywords")


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



    def save_file(self, data, name):

        os.makedirs(
            "data",
            exist_ok=True
        )
        
        with open(
            f"data/{name}.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    def ask_ai(self, content, domain):
    
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

    
                page = context.new_page()
    
    
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

                self.save_file(analysis, f"{domain}_business_analysis")

                browser.close()

                return response

              

    def chunk_list(self, items, size=5):

        for i in range(
            0,
            len(items),
            size
        ):
            yield items[i:i+size]


    def get_google_trends(self, keywords):

        results = {}

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            for keyword in keywords:

                self._log(
                    f"Searching: {keyword}"
                )

                try:

                    page.goto(
                        "https://www.google.com",
                        wait_until="networkidle"
                    )

                    # Accept cookies if shown
                    try:
                        page.get_by_role(
                            "button",
                            name="Accept all"
                        ).click(timeout=3000)
                    except:
                        pass

                    search_box = page.locator(
                        'textarea[name="q"]'
                    )

                    search_box.wait_for()

                    search_box.fill(keyword)

                    # Wait for autocomplete
                    page.wait_for_timeout(2000)

                    suggestions = []

                    items = page.locator(
                        'li[data-view-type="1"]'
                    )

                    count = items.count()

                    for i in range(count):

                        text = items.nth(i).inner_text().strip()

                        if text and text not in suggestions:

                            suggestions.append(text)

                    results[keyword] = suggestions

                    self._log(suggestions)

                    time.sleep(2)

                except Exception as e:

                    self._log(
                        f"Failed for {keyword}: {e}"
                    )

            browser.close()

        with open(
            "google_suggestions.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                results,
                f,
                indent=4,
                ensure_ascii=False
            )

        self._log(
            "Saved google_suggestions.json"
        )

        return results

    
    def load_google_suggestions():

        with open(
            "google_suggestions.json",
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    def flatten_keywords(self, data):

        keywords = []

        for seed, suggestions in data.items():

            keywords.append(seed)

            keywords.extend(suggestions)

        return keywords

    def remove_duplicates(self, keywords):

        unique = []

        seen = set()

        for keyword in keywords:

            keyword = keyword.lower().strip()

            if keyword not in seen:

                seen.add(keyword)

                unique.append(keyword)

        return unique


    def get_websites(self):
        self._log("getting websites")
        try:
            # response = requests.get(
            #     os.getenv("GET_API"),
            #     headers=self.get_headers(),
            #     timeout=30
            # )
            # websites = response.json()
            # self._log(f"websites: {websites}")
            # return websites
            return os.getenv("URL").split(",")
        
        except Exception as e:
            self._log(f"Error: {e}")

    def post_data(self, id, data):
        prams = {
            "id": id,
            "crawler": data,
        }

        response = requests.post(
            os.getenv("POST_API"),
            params=prams,
            headers=self.get_headers()
        )
        self._log(f"data posted successfully api response: {response}")

    def get_headers(seld):
        return {
            "X-API-KEY": os.getenv("X-API-KEY"),
            "Accept": "application/json"
        }


bot = SeoBot()
bot.do_seo()