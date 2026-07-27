import json


def create_analyzer_prompt():

    with open(
        "website_knowledge.json",
        "r",
        encoding="utf-8"
    ) as file:

        website = json.load(file)


    prompt = f"""
You are an SEO business analyst.

Analyze this website information.

Website:
{website.get('website')}


Title:
{website.get('title')}


Description:
{website.get('description')}


Headings:
{website.get('headings')}


Content:
{website.get('content')[:12000]}


Return ONLY JSON.

Required format:

{{
    "business_name":"",
    "business_type":"",
    "industry":"",
    "products":[],
    "services":[],
    "target_audience":"",
    "countries":"",
    "brand_tone":"",
    "main_keywords":[],
    "existing_topics":[],
    "recommended_blog_topics":[]
}}

"""

    return prompt



if __name__ == "__main__":

    prompt = create_analyzer_prompt()

    print(prompt)