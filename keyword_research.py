import json


def generate_keyword_seeds(business):

    keywords = []


    # Services
    for service in business["offerings"]["services"]:
        keywords.append(service)


    # Customer questions
    for question in business["customer_questions"]:
        keywords.append(question)


    # Content topics + locations
    for topic in business["content_topics"]:

        for location in business["locations"]:

            keywords.append(
                f"{topic} {location}"
            )


    # Remove duplicates
    keywords = list(set(keywords))


    # Remove very long questions
    keywords = [
        k
        for k in keywords
        if len(k.split()) <= 5
    ]


    return keywords