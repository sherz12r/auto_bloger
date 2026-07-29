def group_similar_keywords_analyzer_prompt(website):

    prompt = f"""
Group similar keywords.

remove all dublicates even 60% similar remove and chose best keyword between them as final keyword


{website}

-----------------------

Return ONLY valid JSON.

Do not explain anything.

If something is unknown use null.


"""

    return prompt