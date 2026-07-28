def create_analyzer_prompt(website):

    prompt = f"""
You are an expert business analyst.

Your job is NOT to write blogs.

Your job is ONLY to understand the business.

Website

{website["website"]}

Title

{website["title"]}

Description

{website["description"]}

Headings

{website["headings"]}

Content

{website["content"][:10000]}

-----------------------

Return ONLY valid JSON.

Do not explain anything.

If something is unknown use null.

Return exactly this schema.

{{
    "company": {{
        "name": "",
        "website": "",
        "industry": "",
        "business_type": "",
        "description": ""
    }},

    "audience": {{
        "primary": [],
        "secondary": []
    }},

    "offerings": {{
        "services": [],
        "products": []
    }},

    "locations": [],

    "countries": [],

    "important_entities": [],

    "main_categories": [],

    "pain_points": [],

    "customer_questions": [],

    "content_topics": [],

    "internal_pages": []
}}

"""

    return prompt