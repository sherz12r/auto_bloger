from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from session_logger import append_log_line
import json
from analyzer_prompt import create_analyzer_prompt
from keyword_analyzer_prompt import create_keyword_analyzer_prompt
from group_similar_keywords_analyzer_prompt import group_similar_keywords_analyzer_prompt
from seo_audit import SEOAuditor
from playwright.sync_api import sync_playwright
from selenium.webdriver.common.by import By
import time
from keyword_research import generate_keyword_seeds
from pytrends.request import TrendReq
import pandas as pd
from random import uniform
from urllib.parse import urlparse
from session_logger import _log

load_dotenv()

class SeoBot:
    def __init__(self):
        self.url = os.getenv("URL")
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        if not self.url:
            raise ValueError("URL not found in .env")

        if not self.url.startswith(("http://", "https://")):
            self.url = "https://" + self.url

        _log(f"URL: {self.url}")

    def random_sleep():
        time.sleep(uniform(9.8, 15.5))

    def write_header_log(self, title, width=70):
        _log("=" * width)
        _log(title.center(width))
        _log("=" * width)

  

    async def crawl_website(self):

        async with AsyncWebCrawler() as crawler:

            result = await crawler.arun(
                url=self.url
            )

            crawl = result[0]

            if not crawl.success:
                _log(
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
        try:
            self.write_header_log(
                    "Bot Started"
                )
            websites = self.get_websites()
            for web in websites:
            # if web['crawl_data'] is not None:
                domain = urlparse(web).hostname
                _log(f"working for: {domain}")
                website_data = self.get_website_knowledge(domain)

                # NEW STEP

                seo_audit = self.run_seo_audit(
                    domain,
                    website_data
                )

                self.save_file(seo_audit, f"{domain}_seo_audit")

                seo_recommendations = f"data/{domain}_seo_recommendations.json"

                # --------------------------------------------
                # Load Existing Topics
                # --------------------------------------------
                if not os.path.exists(seo_recommendations):

                    seo_recommendations = self.generate_seo_recommendations(
                        domain,
                        seo_audit
                    )

                else:
                    _log("No SEO recommendations generated")
                    seo_recommendations = {}


                _log("Analyzing Webstie Content")

                business = self.do_analysis(website_data, domain)
                _log("analysis done")

                keywords = self.get_or_create_keyword_database(domain, business)

                _log("kaywords database created")

                topics = self.get_or_create_topics(domain, business, keywords)

                # 5. Blogs
                blogs = self.get_or_create_blogs(domain, business, topics, limit=2)

                # 6. SEO Check
                checked_blogs = self.check_all_blogs(domain, blogs)

                # 7. Publish
                self.publish_pending_blogs(domain, checked_blogs)

                _log(f"{domain} completed successfully.")
                

                _log("asking Ai to analyze keywords")
        finally:

            self.close_ai_browser()


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

    
    def ask_ai(self, content, domain, filename):
    
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
            page.wait_for_timeout(5000)

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


            _log("writing ai response")
            _log(response)
           # Make sure response exists
            if response is None:
                raise Exception("Response is None")

            response = response.strip()

            if not response:
                raise Exception("Response is empty")

            # Remove Markdown code fences if present
            if response.startswith("```"):
                lines = response.splitlines()

                # Remove opening fence (``` or ```json)
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]

                # Remove closing fence
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]

                response = "\n".join(lines).strip()

            print("Response received:")
            print(response)

            try:
                analysis = json.loads(response)

            except json.JSONDecodeError as e:
                print("JSON parsing failed")
                print("Error:", e)
                print("Raw response:")
                print(repr(response))
                raise

            self.save_file(analysis, f"{domain}_{filename}")

            browser.close()

            return response
    # def ask_ai(self, content, domain, filename):
    #         if self.browser is None or not self.browser.is_connected():
    #             self.start_ai_browser()
            
    #         # with sync_playwright() as p:

    #         page = self.page

    #         editor = page.locator(
    #             "[contenteditable='true']"
    #         )


    #         editor.wait_for(
    #             state="visible",
    #             timeout=30000
    #         )


    #         # editor.fill(content)
    #         editor.click()

    #         page.keyboard.insert_text(content)

    #         # time.sleep(3)
    #         page.wait_for_timeout(2000)

    #         page.keyboard.press("Enter")

    #         page.wait_for_timeout(10000)

    #         # copy_button = page.locator(
    #         #     'button[aria-label="Copy response"]'
    #         # ).last
    #         copy_buttons = page.locator(
    #             'button[aria-label="Copy response"]:visible'
    #         )

    #         count = copy_buttons.count()

    #         _log(f"Copy buttons found: {count}")

    #         if count == 0:
    #             raise Exception("No copy button found")

    #         copy_button = copy_buttons.nth(count - 1)

    #         copy_button.wait_for(
    #             state="visible",
    #             timeout=30000
    #         )
    #         copy_button.scroll_into_view_if_needed()

    #         copy_button.click()

    #         page.wait_for_timeout(1000)

    #         response = page.evaluate(
    #             "navigator.clipboard.readText()"
    #         )


    #         _log("writing ai response")
    #         _log(response)

    #         # Remove markdown code blocks from AI response
    #         response = response.strip()

    #         if response.startswith("```json"):
    #             response = response.replace("```json", "", 1)

    #         if response.endswith("```"):
    #             response = response[:-3]

    #         response = response.strip()


    #         try:
    #             analysis = json.loads(response)

    #         except json.JSONDecodeError as e:
    #             _log(f"JSON Error: {e}")
    #             _log(repr(response))
    #             return {}

    #         self.save_file(
    #             analysis,
    #             f"{domain}_{filename}"
    #         )

    #         return analysis

              

    def chunk_list(self, data, chunk_size=20):
        """
        Split a list into chunks.
        """
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]


    def get_google_trends(self, keywords):

        results = {}

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            for keyword in keywords:

                _log(
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

                    _log(suggestions)

                    time.sleep(2)

                except Exception as e:

                    _log(
                        f"Failed for {keyword}: {e}"
                    )
            
            self.browser.close()

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

        _log(
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
        _log("getting websites")
        try:
            # response = requests.get(
            #     os.getenv("GET_API"),
            #     headers=self.get_headers(),
            #     timeout=30
            # )
            # websites = response.json()
            # _log(f"websites: {websites}")
            # return websites
            return os.getenv("URL").split(",")
        
        except Exception as e:
            _log(f"Error: {e}")

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
        _log(f"data posted successfully api response: {response}")

    def get_headers(self):
        return {
            "X-API-KEY": os.getenv("X-API-KEY"),
            "Accept": "application/json"
        }
    

    def get_website_knowledge(self, domain):
        if os.path.exists(f"data/{domain}_knowledge.json"):
            _log(
                "Existing website knowledge found. Loading..."
            )

            with open(
                f"data/{domain}_knowledge.json",
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        else:

            _log(
                "No website knowledge found. Crawling website..."
            )

            crawl_result = asyncio.run(
                self.crawl_website()
            )


            if not crawl_result:
                _log(
                    "Website crawl failed"
                )
                return


            website_data = self.extract_website_data(
                crawl_result
            )

            _log(f"TYPE: {type(website_data)}")
            _log(f"DATA: {website_data}")
            self.save_file(
                website_data, f"{domain}_knowledge"
            )
            _log(
                    "Website knowledge extracted successfully"
                )

            _log(
                "Website knowledge extracted successfully"
            )



        _log(
            json.dumps(
                website_data,
                indent=4
            )[:5000]
        )
        return website_data


    def do_analysis(self, website_data, domain):
        if not os.path.exists(f"data/{domain}_business_analysis.json"):
            analyzer = create_analyzer_prompt(website_data)

            _log("Business Analyzer Prompt Created")
            _log(analyzer)

            AI_response = self.ask_ai(analyzer, domain, "business_analysis")


            business = json.loads(
                AI_response
            )


            with open(
                f"data/{domain}_business_analysis.json",
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    business,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            return business

        else:

            with open(
                f"data/{domain}_business_analysis.json",
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

    def get_or_create_keyword_database(self, domain, business):
        keyword_db_file = f"data/{domain}_keyword_database.json"

        if not os.path.exists(keyword_db_file):
            seed = generate_keyword_seeds(business)

            _log("Working on keywords")
            _log(f"Keywords: {seed}")

            google_trends = self.get_google_trends(seed)

            refined_keywords = self.flatten_keywords(google_trends)
            refined_keywords = self.remove_duplicates(refined_keywords)

            self.save_file(refined_keywords, f"{domain}_keyword_database")

            _log("Keywords generated successfully")
            _log(refined_keywords)
        else:
            with open(keyword_db_file, "r", encoding="utf-8") as f:
                refined_keywords = json.load(f)

            _log("Loaded existing keyword database")

        return refined_keywords

    

    def get_or_create_topics(self, domain, business, keywords):

        topic_file = f"data/{domain}_topics.json"

        # --------------------------------------------
        # Load Existing Topics
        # --------------------------------------------
        if os.path.exists(topic_file):

            _log("Loading existing topics...")

            with open(
                topic_file,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        # --------------------------------------------
        # Generate New Topics
        # --------------------------------------------

        _log("Creating SEO topics...")

        all_topics = []

        keyword_chunks = list(
            self.chunk_list(
                keywords,
                70
            )
        )

        _log(
            f"Total keyword batches: {len(keyword_chunks)}"
        )

        for index, chunk in enumerate(keyword_chunks, start=1):

            _log(
                f"Processing batch {index}/{len(keyword_chunks)}"
            )

            prompt = self.create_topic_planner_prompt(
                business,
                chunk
            )

            AI_response = self.ask_ai(
                prompt,
                domain,
                f"topics_batch_{index}"
            )

            if not AI_response:

                _log(
                    f"Batch {index} returned empty response."
                )

                continue

            try:

                batch_topics = json.loads(
                    AI_response
                )

                if isinstance(batch_topics, list):

                    all_topics.extend(
                        batch_topics
                    )

                else:

                    _log(
                        "Invalid topic response."
                    )

            except Exception as e:

                _log(e)
                _log(AI_response)

        # --------------------------------------------
        # Remove duplicate titles
        # --------------------------------------------

        unique = {}

        for topic in all_topics:

            title = topic["title"].strip().lower()

            if title not in unique:

                unique[title] = topic

        final_topics = list(unique.values())

        self.save_file(
            final_topics,
            f"{domain}_topics"
        )

        _log(
            f"{len(final_topics)} Topics Created"
        )

        return final_topics



    def create_topic_planner_prompt(self,
        business,
        keywords
    ):

        return f"""
    You are an SEO strategist.

    Business Information

    {json.dumps(business, indent=4)}

    Keywords

    {json.dumps(keywords, indent=4)}

    Your task is to create SEO blog topics.

    Rules

    - One keyword = one topic
    - Remove duplicate ideas
    - Topics should target informational intent.
    - Topics should be useful for customers.
    - Do not write product pages.
    - Use natural language.
    - Create attractive blog titles.

    Return ONLY valid JSON.

    Example

    [
        {{
            "title":"How to Apply for UAE Visa from Pakistan",
            "main_keyword":"uae visa",
            "secondary_keywords":[
                "uae visa requirements",
                "uae tourist visa",
                "uae visa online"
            ],
            "search_intent":"Informational",
            "difficulty":"Medium",
            "priority":1
        }}
    ]

    Return JSON only.
    """


    def start_ai_browser(self):

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

        self.browser = self.playwright.chromium.launch(
            headless=False
        )

        self.context = self.browser.new_context(
            permissions=[
                "clipboard-read",
                "clipboard-write"
            ]
        )

        self.page = self.context.new_page()


        self.page.goto(
            "https://chat.openai.com"
        )


        self.page.wait_for_timeout(
            5000
        )


        _log(
            "AI Browser Started"
        )


    def close_ai_browser(self):

        try:

            self.browser.close()

            self.playwright.stop()


            _log(
                "AI Browser Closed"
            )


        except Exception as e:

            _log(
                str(e)
            )


    def run_seo_audit(self, domain, website_data):
        _log("Running SEO Auditor")
        auditor = SEOAuditor()
        _log("SEO Auditor finished")
        return auditor.run(domain, website_data)



    def generate_seo_recommendations(
        self,
                domain,
                audit
        ):


            prompt=f"""

        You are an SEO expert.


        Website SEO Audit:

        {json.dumps(
        audit,
        indent=4
        )}


        Create an improvement plan.


        Return JSON:


        {{
        "priority_fixes":[
        {{
        "issue":"",
        "solution":"",
        "expected_result":""
        }}
        ],

        "content_recommendations":[],

        "technical_recommendations":[]

        }}

        """


            response = self.ask_ai(
                prompt,
                domain,
                "seo_recommendations"
            )

            return response


    def get_or_create_blogs(self, domain, business, topics, limit=3):
        """
        Generate up to `limit` blog drafts from topics or load existing ones.
        """

        try:
            blogs = self.load_file(f"{domain}_blogs")

            if blogs:
                _log(f"Loaded {len(blogs)} existing blogs")
                return blogs

        except Exception:
            pass

        blogs = []

        total = min(limit, len(topics))

        for index, topic in enumerate(topics[:limit], start=1):

            title = topic.get("title", str(topic))

            _log(f"Generating blog {index}/{total}: {title}")

            prompt = f"""
    You are an SEO copywriter.

    Business Information:
    {json.dumps(business, indent=2)}

    Write a complete SEO-optimized blog post.

    Topic:
    {title}

    Return ONLY valid JSON in this format:

    {{
        "title": "",
        "slug": "",
        "meta_title": "",
        "meta_description": "",
        "keywords": [],
        "content": ""
    }}
    """

            try:
                blog = self.ask_ai(
                    prompt,
                    domain,
                    f"_blog_{index}"
                )

                if blog:
                    blogs.append(blog)

            except Exception as e:
                _log(f"Failed to generate blog '{title}': {e}")

        self.save_file(
            blogs,
            f"blogs"
        )

        _log(f"{len(blogs)} blogs created")

        return blogs


    def check_all_blogs(self, domain, blogs):
        """
        Review all generated blogs for SEO quality.
        """

        checked_blogs = []

        total = len(blogs)

        for index, blog in enumerate(blogs, start=1):

            title = blog.get("title", f"Blog {index}")

            _log(f"Checking SEO {index}/{total}: {title}")

            prompt = f"""
    You are a senior SEO editor.

    Review the following blog.

    Improve:
    - SEO
    - Readability
    - Grammar
    - Heading structure
    - Keyword placement
    - Meta title
    - Meta description
    - Internal linking opportunities
    - CTA

    Return ONLY valid JSON.

    Blog:

    {json.dumps(blog, indent=2)}
    """

            try:

                checked = self.ask_ai(
                    prompt,
                    domain,
                    f"{domain}_checked_blog_{index}"
                )

                if checked:
                    checked["status"] = "approved"
                    checked_blogs.append(checked)

            except Exception as e:
                _log(f"SEO check failed: {title} : {e}")

                blog["status"] = "failed"
                checked_blogs.append(blog)

        self.save_file(
            checked_blogs,
            f"{domain}_checked_blogs"
        )

        _log(f"{len(checked_blogs)} blogs checked")

        return checked_blogs


    def publish_pending_blogs(self, domain, blogs):
        """
        Publish all approved blogs.
        """

        published = []

        for blog in blogs:

            if blog.get("status") != "approved":
                continue

            try:

                # Future:
                # self.wordpress.publish(blog)

                blog["published"] = True

                published.append(blog)

                _log(f"Published: {blog.get('title')}")

            except Exception as e:

                blog["published"] = False

                _log(f"Publish failed: {blog.get('title')} : {e}")

        self.save_file(
            published,
            f"{domain}_published_blogs"
        )

        _log(f"{len(published)} blogs published")

        return published



bot = SeoBot()
bot.do_seo()