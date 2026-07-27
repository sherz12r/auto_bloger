from playwright.sync_api import sync_playwright
import json
import time


class AIBrowser:


    def __init__(self):
        self.prompt = ""


    def load_prompt(self):

        with open(
            "website_knowledge.json",
            "r",
            encoding="utf-8"
        ) as f:

            website = json.load(f)


        self.prompt = f"""

Analyze this website.

Return JSON only.

Website:
{website['website']}

Title:
{website['title']}

Description:
{website['description']}

Content:
{website['content'][:10000]}


Return:

{{
"business_type":"",
"services":[],
"products":[],
"audience":"",
"keywords":[]
}}

"""


    def ask_ai(self):

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()


            page.goto(
                "https://chat.openai.com"
            )


            page.wait_for_timeout(5000)


            # ChatGPT textbox
            textbox = page.locator(
                "textarea"
            )


            textbox.fill(
                self.prompt
            )


            textbox.press(
                "Enter"
            )


            page.wait_for_timeout(
                30000
            )


            response = page.locator(
                "article"
            ).last.inner_text()


            print(response)


            browser.close()



if __name__ == "__main__":

    bot = AIBrowser()

    bot.load_prompt()

    bot.ask_ai()