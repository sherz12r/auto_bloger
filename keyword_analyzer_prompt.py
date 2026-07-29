def create_keyword_analyzer_prompt(website):

    prompt = f"""
    You are an SEO expert.
Analyze these keywords.

remove all dublicates even 60% similar remove and chose best keyword between them as final keyword

For each keyword return:

keyword
intent:
- informational
- commercial
- transactional

content_type:
- guide
- comparison
- listicle
- service page

priority_score

{website}

-----------------------

Return ONLY valid JSON.

Do not explain anything.

If something is unknown use null.

Return exactly this schema.
[
 {{
   "keyword":"dubai airport transfer",
   "intent":"commercial",
   "content_type":"service",
   "priority":95
 }},
 {{
   "keyword":"things to do in dubai",
   "intent":"informational",
   "content_type":"guide",
   "priority":85
 }}
]
"""

    return prompt