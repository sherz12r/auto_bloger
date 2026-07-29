def create_keyword_analyzer_prompt(website):

    prompt = f"""
Analyze these keywords.

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

{website["website"]}

-----------------------

Return ONLY valid JSON.

Do not explain anything.

If something is unknown use null.

Return exactly this schema.
[
 {
   "keyword":"dubai airport transfer",
   "intent":"commercial",
   "content_type":"service",
   "priority":95
 },
 {
   "keyword":"things to do in dubai",
   "intent":"informational",
   "content_type":"guide",
   "priority":85
 }
]
"""

    return prompt