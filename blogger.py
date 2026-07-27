from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from app_paths import get_app_dir
from session_logger import append_log_line
import json

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

    # async def crawl_website(self):

    #     async with AsyncWebCrawler() as crawler:

    #         result = await crawler.arun(
    #             url=self.url,
    #         )

    #         crawl_result = result[0]
    #         print("RESULT:", result)
    #         if not crawl_result.success:
    #             self._log(
    #                 f"Crawl failed: {crawl_result.error_message}"
    #             )
    #             return ""

    #         self._log(f"MARKDOWN: {result.markdown}")

    #         return {
    #             "url": self.url,
    #             "markdown": result.markdown,
    #             "html": result.html,
    #             "links": result.links
    #         }
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

    # def analyze_website(self):

    #     markdown = asyncio.run(
    #         self.crawl_website()
    #     )
    #     if not markdown:
    #         self._log("No content extracted from website")
    #         return
        
    #     self._log(markdown[:3000])
    def analyze_website(self):

        crawl_result = asyncio.run(
            self.crawl_website()
        )


        if not crawl_result:
            self._log("Website crawl failed")
            return


        website_data = self.extract_website_data(
            crawl_result
        )


        self.save_knowledge(
            website_data
        )


        self._log("Website knowledge extracted successfully")


        self._log(
            json.dumps(
                website_data,
                indent=4
            )[:3000]
        )




    # def extract_website_data(self, crawl_result):

    #     data = {
    #         "url": crawl_result["url"],
    #         "title": "",
    #         "description": "",
    #         "headings": [],
    #         "links": [],
    #         "content": crawl_result["markdown"]
    #     }


    #     metadata = crawl_result.get("metadata")

    #     if metadata:
    #         data["title"] = metadata.get("title", "")
    #         data["description"] = metadata.get("description", "")


    #     links = crawl_result.get("links", {})

    #     for link_type, items in links.items():

    #         for item in items:
    #             data["links"].append(
    #                 item.get("href")
    #             )


    #     return data
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




bot = SeoBot()
bot.analyze_website()