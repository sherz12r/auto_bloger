import os
import json
import re
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
from session_logger import _log


class SEOAuditor:

    def __init__(self):

        self.issues = []

        self.pages_data = []

        self.h1_map = {}
        self.content_map = {}
        self.paragraph_map = {}

        self.internal_links_map = {}
        self.external_links_map = {}
        self.all_links = []
        self.page_depth = {}

        self.keyword_data = {}

        self.schema_data = {}

        self.performance_data = {}
        



    def add_issue(
        self,
        url,
        issue,
        severity,
        suggestion
    ):

        self.issues.append(
            {
                "url": url,
                "issue": issue,
                "severity": severity,
                "suggestion": suggestion
            }
        )


        # ==========================
    # HTTP STATUS CHECK
    # ==========================

    def check_status_code(
        self,
        page
    ):

        url = page.get(
            "url",
            ""
        )

        status = page.get(
            "status",
            200
        )


        if status == 404:

            self.add_issue(
                url,
                "Page returns 404 Not Found",
                "High",
                "Fix broken URL or redirect it"
            )


        elif status >= 500:

            self.add_issue(
                url,
                "Server error",
                "High",
                "Check server configuration"
            )


        elif status in [301,302]:

            self.add_issue(
                url,
                "Redirecting page",
                "Low",
                "Avoid unnecessary redirects"
            )



    # ==========================
    # HTTPS CHECK
    # ==========================

    def check_https(
        self,
        url
    ):

        if url.startswith(
            "http://"
        ):

            self.add_issue(
                url,
                "Website not using HTTPS",
                "High",
                "Install SSL certificate and redirect HTTP to HTTPS"
            )



    # ==========================
    # ROBOTS TXT CHECK
    # ==========================

    def check_robots(
        self,
        domain
    ):

        if not domain.startswith(
            "http"
        ):

            domain = "https://" + domain


        robots_url = urljoin(
            domain,
            "/robots.txt"
        )


        try:

            response = requests.get(
                robots_url,
                timeout=10,
                verify=False
            )


            if response.status_code != 200:

                self.add_issue(
                    domain,
                    "Missing robots.txt",
                    "Medium",
                    "Create robots.txt file"
                )


        except Exception:


            self.add_issue(
                domain,
                "Cannot access robots.txt",
                "Medium",
                "Check robots.txt availability"
            )



    # ==========================
    # SITEMAP CHECK
    # ==========================

    def check_sitemap(
        self,
        domain
    ):


        if not domain.startswith(
            "http"
        ):

            domain = "https://" + domain


        sitemap_url = urljoin(
            domain,
            "/sitemap.xml"
        )


        try:

            response = requests.get(
                sitemap_url,
                timeout=10,
                verify=False
            )


            if response.status_code != 200:


                self.add_issue(
                    domain,
                    "Missing sitemap.xml",
                    "Medium",
                    "Create XML sitemap"
                )


        except Exception:


            self.add_issue(
                domain,
                "Cannot access sitemap.xml",
                "Medium",
                "Check sitemap configuration"
            )


            # ==========================
    # CHECK BROKEN LINKS
    # ==========================

    def check_link_status(
        self,
        source_url,
        link_url
    ):

        try:

            response = requests.head(
                link_url,
                timeout=8,
                allow_redirects=True,
                verify=False
            )


            if response.status_code == 404:

                self.add_issue(
                    source_url,
                    f"Broken link: {link_url}",
                    "High",
                    "Remove or replace broken link"
                )


            elif response.status_code >= 500:

                self.add_issue(
                    source_url,
                    f"Link server error: {link_url}",
                    "Medium",
                    "Check destination URL"
                )


            elif response.history:

                self.add_issue(
                    source_url,
                    f"Redirecting link: {link_url}",
                    "Low",
                    "Update link to final destination"
                )


        except Exception:


            self.add_issue(
                source_url,
                f"Unable to check link: {link_url}",
                "Low",
                "Verify external resource"
            )



    # ==========================
    # EXTRACT PAGE LINKS
    # ==========================

    def analyze_links(
        self,
        page_url,
        soup
    ):


        internal = []

        external = []


        domain = urlparse(
            page_url
        ).netloc



        for a in soup.find_all(
            "a",
            href=True
        ):


            href = a.get(
                "href"
            ).strip()


            if href.startswith("#"):

                continue


            full_url = urljoin(
                page_url,
                href
            )


            link_domain = urlparse(
                full_url
            ).netloc



            self.all_links.append(
                {
                    "from": page_url,
                    "to": full_url
                }
            )


            if link_domain == domain:

                internal.append(
                    full_url
                )

            else:

                external.append(
                    full_url
                )



        self.internal_links_map[
            page_url
        ] = internal



        self.external_links_map[
            page_url
        ] = external



        return internal, external



        # ==========================
    # SEO SCORE CALCULATION
    # ==========================

    def calculate_score(self):

        score = 100


        for issue in self.issues:


            severity = issue.get(
                "severity",
                "Low"
            )


            if severity == "High":

                score -= 3


            elif severity == "Medium":

                score -= 1.5


            elif severity == "Low":

                score -= 0.5



        if score < 0:

            score = 0


        return round(
            score,
            2
        )



    # ==========================
    # ISSUE SUMMARY
    # ==========================

    def issue_summary(self):

        summary = {

            "High": 0,

            "Medium": 0,

            "Low": 0

        }


        for issue in self.issues:

            severity = issue.get(
                "severity"
            )


            if severity in summary:

                summary[severity] += 1



        return summary



    # ==========================
    # SAVE JSON REPORT
    # ==========================

    def save_json_report(
        self,
        data,
        filename
    ):


        os.makedirs(
            "data",
            exist_ok=True
        )


        path = f"reports/{filename}.json"


        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:


            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )


        return path



    # ==========================
    # SAVE CSV REPORT
    # ==========================

    def save_csv_report(
        self,
        filename
    ):


        os.makedirs(
            "reports",
            exist_ok=True
        )


        path = f"reports/{filename}.csv"


        with open(
            path,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:


            writer = csv.writer(
                f
            )


            writer.writerow(
                [
                    "URL",
                    "Issue",
                    "Severity",
                    "Suggestion"
                ]
            )


            for issue in self.issues:


                writer.writerow(
                    [
                        issue["url"],
                        issue["issue"],
                        issue["severity"],
                        issue["suggestion"]
                    ]
                )


        return path



    # ==========================
    # HTML REPORT
    # ==========================

    def save_html_report(
        self,
        domain,
        filename
    ):


        os.makedirs(
            "reports",
            exist_ok=True
        )


        path = f"reports/{filename}.html"


        score = self.calculate_score()

        summary = self.issue_summary()



        html = f"""

<!DOCTYPE html>

<html>

<head>

<title>
SEO Audit Report - {domain}
</title>


<style>


body {{

font-family: Arial;

background:#f5f5f5;

padding:30px;

}}


.card {{

background:white;

padding:20px;

margin-bottom:20px;

border-radius:10px;

}}


.high {{

color:red;

}}


.medium {{

color:#d88900;

}}


.low {{

color:green;

}}


</style>


</head>


<body>


<h1>
SEO Audit Report
</h1>


<div class="card">


<h2>
Website:
{domain}
</h2>


<h2>
SEO Score:
{score}/100
</h2>


<p>
Generated:
{datetime.now()}
</p>


</div>



<div class="card">


<h2>
Issue Summary
</h2>


<p>
High:
{summary["High"]}
</p>


<p>
Medium:
{summary["Medium"]}
</p>


<p>
Low:
{summary["Low"]}
</p>


</div>




<div class="card">


<h2>
Issues
</h2>



<table border="1" width="100%" cellpadding="8">


<tr>

<th>
URL
</th>

<th>
Issue
</th>

<th>
Severity
</th>

<th>
Suggestion
</th>

</tr>



"""


        for issue in self.issues:


            severity = issue["severity"].lower()



            html += f"""


<tr>


<td>
{issue["url"]}
</td>


<td>
{issue["issue"]}
</td>


<td class="{severity}">
{issue["severity"]}
</td>


<td>
{issue["suggestion"]}
</td>


</tr>


"""



        html += """

</table>


</div>


</body>


</html>


"""


        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                html
            )


        return path


        # ==========================
    # ISSUE PRIORITY SCORE
    # ==========================

    def issue_priority_score(
        self,
        issue
    ):

        severity = issue.get(
            "severity",
            "Low"
        )


        score = 1


        if severity == "High":

            score = 10


        elif severity == "Medium":

            score = 5


        elif severity == "Low":

            score = 2



        return score



    # ==========================
    # GROUP ISSUES
    # ==========================

    def grouped_issues(self):


        grouped = {


            "High": [],


            "Medium": [],


            "Low": []

        }


        for issue in self.issues:


            severity = issue.get(
                "severity",
                "Low"
            )


            if severity not in grouped:

                severity = "Low"



            issue["priority_score"] = self.issue_priority_score(
                issue
            )


            grouped[severity].append(
                issue
            )



        return grouped



    # ==========================
    # TOP SEO PROBLEMS
    # ==========================

    def top_problems(
        self,
        limit=20
    ):


        sorted_issues = sorted(

            self.issues,

            key=lambda x:
            x.get(
                "priority_score",
                0
            ),

            reverse=True

        )


        return sorted_issues[:limit]



    # ==========================
    # AI PROMPT BUILDER
    # ==========================

    def create_ai_prompt(
        self,
        domain
    ):


        grouped = self.grouped_issues()

        top = self.top_problems()



        prompt = f"""

You are an SEO expert.

Analyze this website SEO audit.

Website:
{domain}


SEO Issues:


"""


        for issue in top:


            prompt += f"""

URL:
{issue['url']}

Problem:
{issue['issue']}

Severity:
{issue['severity']}

Recommended Fix:
{issue['suggestion']}


"""


        prompt += """

Provide:

1. SEO health summary

2. Most important problems

3. Step-by-step fixes

4. Technical SEO recommendations

5. Content recommendations

6. Internal linking recommendations

Return JSON format only.

"""


        return prompt



        # ==========================
    # EXTRACT KEYWORDS
    # ==========================

    def extract_keywords(
        self,
        text
    ):


        stop_words = {

            "the",
            "and",
            "for",
            "with",
            "this",
            "that",
            "from",
            "your",
            "have",
            "are",
            "was",
            "will",
            "our",
            "you",
            "they",
            "their",
            "about",
            "into",
            "more"

        }



        words = re.findall(
            r"\b[a-zA-Z]{4,}\b",
            text.lower()
        )



        keywords = {}


        for word in words:


            if word not in stop_words:


                keywords[word] = keywords.get(
                    word,
                    0
                ) + 1



        sorted_keywords = sorted(

            keywords.items(),

            key=lambda x:x[1],

            reverse=True

        )


        return sorted_keywords[:20]



    # ==========================
    # KEYWORD CHECK
    # ==========================

    def analyze_keywords(
        self,
        url,
        soup
    ):


        page_text = soup.get_text(
            " ",
            strip=True
        )


        keywords = self.extract_keywords(
            page_text
        )


        self.keyword_data[url] = keywords



        if not keywords:

            return



        main_keyword = keywords[0][0]



        # --------------------------
        # Title keyword check
        # --------------------------


        title = soup.find(
            "title"
        )


        if title:


            title_text = title.get_text(
                strip=True
            ).lower()


            if main_keyword not in title_text:


                self.add_issue(

                    url,

                    f"Main keyword '{main_keyword}' missing in title",

                    "Medium",

                    "Add primary keyword naturally into title"

                )



        # --------------------------
        # H1 keyword check
        # --------------------------


        h1 = soup.find(
            "h1"
        )


        if h1:


            h1_text = h1.get_text(
                strip=True
            ).lower()


            if main_keyword not in h1_text:


                self.add_issue(

                    url,

                    f"Main keyword '{main_keyword}' missing in H1",

                    "Medium",

                    "Include target keyword in H1"

                )



        # --------------------------
        # Meta description keyword
        # --------------------------


        meta = soup.find(
            "meta",
            attrs={
                "name":"description"
            }
        )


        if meta:


            desc = meta.get(
                "content",
                ""
            ).lower()



            if main_keyword not in desc:


                self.add_issue(

                    url,

                    f"Main keyword '{main_keyword}' missing in meta description",

                    "Low",

                    "Use keyword naturally in meta description"

                )



        # --------------------------
        # Keyword stuffing
        # --------------------------


        total_words = len(
            page_text.split()
        )


        keyword_count = dict(
            keywords
        ).get(
            main_keyword,
            0
        )


        if total_words > 0:


            density = (

                keyword_count /
                total_words

            ) * 100



            if density > 5:


                self.add_issue(

                    url,

                    f"Possible keyword stuffing: {main_keyword}",

                    "High",

                    "Reduce keyword repetition and improve natural writing"

                )


        # ==========================
    # SCHEMA ANALYSIS
    # ==========================


    def analyze_schema(
        self,
        url,
        soup
    ):


        schemas = soup.find_all(
            "script",
            attrs={
                "type":"application/ld+json"
            }
        )



        if len(schemas) == 0:


            self.add_issue(

                url,

                "Missing JSON-LD structured data",

                "Medium",

                "Add Schema.org structured data"

            )

            return



        page_schema_types = []



        for schema in schemas:


            try:


                data = json.loads(
                    schema.string
                )


                self.schema_data.setdefault(
                    url,
                    []
                ).append(
                    data
                )



                # Handle @graph

                if "@graph" in data:


                    items = data["@graph"]


                    for item in items:


                        schema_type = item.get(
                            "@type"
                        )


                        if schema_type:

                            page_schema_types.append(
                                schema_type
                            )


                else:


                    schema_type = data.get(
                        "@type"
                    )


                    if schema_type:

                        page_schema_types.append(
                            schema_type
                        )



            except Exception:


                self.add_issue(

                    url,

                    "Invalid JSON-LD structured data",

                    "High",

                    "Fix JSON syntax errors in schema markup"

                )



        # ==========================
        # ORGANIZATION CHECK
        # ==========================


        if "Organization" not in page_schema_types:


            self.add_issue(

                url,

                "Missing Organization schema",

                "Low",

                "Add Organization structured data"

            )



        # ==========================
        # BREADCRUMB CHECK
        # ==========================


        if "BreadcrumbList" not in page_schema_types:


            self.add_issue(

                url,

                "Missing Breadcrumb schema",

                "Low",

                "Add BreadcrumbList schema"

            )



        # ==========================
        # ARTICLE CHECK
        # ==========================


        content_words = len(
            soup.get_text(
                " ",
                strip=True
            ).split()
        )



        if content_words > 500:


            if (
                "Article"
                not in page_schema_types
                and
                "NewsArticle"
                not in page_schema_types
            ):


                self.add_issue(

                    url,

                    "Long content page missing Article schema",

                    "Low",

                    "Add Article or BlogPosting schema"

                )



        # ==========================
        # PRODUCT CHECK
        # ==========================


        product_words = [

            "price",

            "buy",

            "shop",

            "product",

            "cart"

        ]



        page_text = soup.get_text(
            " ",
            strip=True
        ).lower()



        if any(
            word in page_text
            for word in product_words
        ):


            if "Product" not in page_schema_types:


                self.add_issue(

                    url,

                    "Possible product page missing Product schema",

                    "Medium",

                    "Add Product structured data"

                )



        # ==========================
        # FAQ CHECK
        # ==========================


        faq_words = [

            "faq",

            "frequently asked questions",

            "questions"

        ]


        if any(
            word in page_text
            for word in faq_words
        ):


            if "FAQPage" not in page_schema_types:


                self.add_issue(

                    url,

                    "FAQ content missing FAQ schema",

                    "Low",

                    "Add FAQPage structured data"

                )


        # ==========================
    # PERFORMANCE ANALYSIS
    # ==========================


    def analyze_performance(
        self,
        url,
        soup,
        html,
        page_data
    ):


        performance = {

            "html_size_kb": 0,

            "images": 0,

            "scripts": 0,

            "stylesheets": 0

        }



        # --------------------------
        # HTML SIZE
        # --------------------------

        html_size = len(
            html.encode(
                "utf-8"
            )
        )


        html_kb = round(
            html_size / 1024,
            2
        )


        performance["html_size_kb"] = html_kb



        if html_size > 500000:


            self.add_issue(

                url,

                "HTML size is large",

                "Medium",

                "Reduce unnecessary HTML code"

            )



        # --------------------------
        # IMAGES
        # --------------------------

        images = soup.find_all(
            "img"
        )


        performance["images"] = len(
            images
        )



        for img in images:


            src = img.get(
                "src",
                ""
            )


            # Missing dimensions


            if not img.get(
                "width"
            ) or not img.get(
                "height"
            ):


                self.add_issue(

                    url,

                    "Image missing width or height attributes",

                    "Low",

                    "Add image dimensions to reduce layout shift"

                )



            # Lazy loading


            if not img.get(
                "loading"
            ):


                self.add_issue(

                    url,

                    "Image missing lazy loading",

                    "Low",

                    "Add loading='lazy' to images"

                )



        # --------------------------
        # JAVASCRIPT FILES
        # --------------------------


        scripts = soup.find_all(
            "script"
        )


        performance["scripts"] = len(
            scripts
        )



        if len(scripts) > 20:


            self.add_issue(

                url,

                "Too many JavaScript files",

                "Medium",

                "Combine or remove unnecessary scripts"

            )



        # Render blocking scripts


        for script in scripts:


            if (
                script.get("src")
                and
                not script.has_attr("async")
                and
                not script.has_attr("defer")
            ):


                self.add_issue(

                    url,

                    "Render blocking JavaScript detected",

                    "Medium",

                    "Use async or defer attributes"

                )



        # --------------------------
        # CSS FILES
        # --------------------------


        styles = soup.find_all(
            "link",
            rel="stylesheet"
        )


        performance["stylesheets"] = len(
            styles
        )



        if len(styles) > 10:


            self.add_issue(

                url,

                "Too many CSS files",

                "Low",

                "Combine CSS files where possible"

            )



        # --------------------------
        # INLINE CSS
        # --------------------------


        inline_styles = soup.find_all(
            "style"
        )


        if len(inline_styles) > 5:


            self.add_issue(

                url,

                "Too many inline style blocks",

                "Low",

                "Move CSS into external files"

            )



        # --------------------------
        # COMPRESSION CHECK
        # --------------------------


        headers = page_data.get(
            "headers",
            {}
        )



        if headers:


            encoding = headers.get(
                "content-encoding",
                ""
            ).lower()



            if not encoding:


                self.add_issue(

                    url,

                    "Compression not detected",

                    "Low",

                    "Enable GZIP or Brotli compression"

                )



            cache = headers.get(
                "cache-control",
                ""
            )



            if not cache:


                self.add_issue(

                    url,

                    "Missing cache-control headers",

                    "Low",

                    "Add browser caching headers"

                )



        self.performance_data[url] = performance
    

    def run(
        self,
        domain,
        website_data
    ):

        self.issues = []
        result = {}
        _log("running function...")
        self.pages_data = website_data.get(
            "pages",
            []
        )
        _log(self.pages_data)
        self.check_robots(
            domain
        )
        _log(self.issues)
        self.check_sitemap(
            domain
        )
        _log(self.issues)

        title_map = {}
        description_map = {}


        for page in self.pages_data:


            self.check_status_code(
                page
            )


            self.check_https(
                page.get(
                    "url",
                    ""
                )
            )


            url = page.get(
                "url",
                ""
            )

            html = page.get(
                "html",
                ""
            )


            if not html:

                self.add_issue(
                    url,
                    "Empty HTML page",
                    "High",
                    "Check crawler or server response"
                )

                continue



            soup = BeautifulSoup(
                html,
                "html.parser"
            )

                        # Schema analysis

            self.analyze_schema(
                url,
                soup
            )


                        # Keyword analysis

            self.analyze_keywords(
                url,
                soup
            )

                        # Analyze links

            internal_links, external_links = self.analyze_links(
                url,
                soup
            )


            # Check internal links

            for link in internal_links:

                self.check_link_status(
                    url,
                    link
                )


            # Check external links

            for link in external_links:

                self.check_link_status(
                    url,
                    link
                )


            page_info = {
                "url": url,
                "title": "",
                "description": "",
                "words": 0
            }

            _log("loggin page info")
            _log(page_info)

            # ==========================
            # TITLE CHECKS
            # ==========================


            titles = soup.find_all(
                "title"
            )
            _log("loggin page titles")

            _log(titles)


            if len(titles) == 0:


                self.add_issue(
                    url,
                    "Missing title tag",
                    "High",
                    "Add a unique SEO title between 50-60 characters"
                )


            elif len(titles) > 1:


                self.add_issue(
                    url,
                    "Multiple title tags",
                    "Medium",
                    "Keep only one title tag"
                )


            else:

                title_text = titles[0].get_text(
                    strip=True
                )

                page_info["title"] = title_text


                if title_text == "":

                    self.add_issue(
                        url,
                        "Empty title tag",
                        "High",
                        "Add meaningful title text"
                    )


                if len(title_text) < 30:

                    self.add_issue(
                        url,
                        "Title too short",
                        "Medium",
                        "Make title around 50-60 characters"
                    )


                if len(title_text) > 60:

                    self.add_issue(
                        url,
                        "Title too long",
                        "Medium",
                        "Reduce title length below 60 characters"
                    )


                title_map.setdefault(
                    title_text,
                    []
                ).append(url)



            # ==========================
            # META DESCRIPTION
            # ==========================


            descriptions = soup.find_all(
                "meta",
                attrs={
                    "name":"description"
                }
            )

            _log(descriptions)



            if len(descriptions) == 0:


                self.add_issue(
                    url,
                    "Missing meta description",
                    "Medium",
                    "Add unique description between 150-160 characters"
                )


            elif len(descriptions) > 1:


                self.add_issue(
                    url,
                    "Multiple meta descriptions",
                    "Low",
                    "Keep only one meta description"
                )


            else:

                desc = descriptions[0].get(
                    "content",
                    ""
                ).strip()


                page_info["description"] = desc


                if desc == "":

                    self.add_issue(
                        url,
                        "Empty meta description",
                        "Medium",
                        "Write useful description"
                    )


                if len(desc) < 70:

                    self.add_issue(
                        url,
                        "Meta description too short",
                        "Low",
                        "Use around 150-160 characters"
                    )


                if len(desc) > 160:

                    self.add_issue(
                        url,
                        "Meta description too long",
                        "Low",
                        "Reduce description length"
                    )


                description_map.setdefault(
                    desc,
                    []
                ).append(url)



            # ==========================
            # H1 CHECK
            # ==========================


            h1s = soup.find_all(
                "h1"
            )


            if len(h1s) == 0:


                self.add_issue(
                    url,
                    "Missing H1 tag",
                    "High",
                    "Add one descriptive H1 heading"
                )


            elif len(h1s) > 1:


                self.add_issue(
                    url,
                    "Multiple H1 tags",
                    "Medium",
                    "Use only one H1 heading"
                )



            # ==========================
            # WORD COUNT
            # ==========================


            text = soup.get_text(
                " ",
                strip=True
            )


            words = len(
                text.split()
            )


            page_info["words"] = words


            if words < 300:


                self.add_issue(
                    url,
                    "Thin content page",
                    "Medium",
                    "Increase useful content"
                )



            self.page_info = page_info



                # ==========================
        # DUPLICATE H1 REPORT
        # ==========================


        for h1, urls in self.h1_map.items():


            if len(urls) > 1:


                for url in urls:


                    self.add_issue(
                        url,
                        "Duplicate H1 heading",
                        "Medium",
                        "Create unique H1 headings for pages"
                    )



        # ==========================
        # DUPLICATE CONTENT REPORT
        # ==========================


        for content, urls in self.content_map.items():


            if len(urls) > 1:


                for url in urls:


                    self.add_issue(
                        url,
                        "Possible duplicate content",
                        "High",
                        "Create unique page content"
                    )



        # ==========================
        # DUPLICATE PARAGRAPH REPORT
        # ==========================


        for paragraph, urls in self.paragraph_map.items():


            if len(urls) > 1:


                for url in urls:


                    self.add_issue(
                        url,
                        "Duplicate paragraph content",
                        "Medium",
                        "Avoid repeating identical text"
                    )



        # Duplicate titles

        for title, urls in title_map.items():

            if title and len(urls) > 1:


                for url in urls:

                    self.add_issue(
                        url,
                        "Duplicate title tag",
                        "High",
                        "Create unique title for every page"
                    )



        # Duplicate descriptions

        for desc, urls in description_map.items():

            if desc and len(urls) > 1:


                for url in urls:

                    self.add_issue(
                        url,
                        "Duplicate meta description",
                        "Medium",
                        "Create unique meta description"
                    )


                    # ==========================
            # CANONICAL CHECK
            # ==========================

            canonicals = soup.find_all(
                "link",
                attrs={
                    "rel": "canonical"
                }
            )


            if len(canonicals) == 0:

                self.add_issue(
                    url,
                    "Missing canonical tag",
                    "Medium",
                    "Add a canonical URL to prevent duplicate content issues"
                )


            elif len(canonicals) > 1:

                self.add_issue(
                    url,
                    "Multiple canonical tags",
                    "High",
                    "Keep only one canonical tag per page"
                )


            else:

                canonical_url = canonicals[0].get(
                    "href"
                )


                if not canonical_url:

                    self.add_issue(
                        url,
                        "Empty canonical URL",
                        "Medium",
                        "Add valid canonical URL"
                    )



            # ==========================
            # ROBOTS META CHECK
            # ==========================


            robots = soup.find(
                "meta",
                attrs={
                    "name":"robots"
                }
            )


            if robots:

                robots_content = robots.get(
                    "content",
                    ""
                ).lower()


                if "noindex" in robots_content:

                    self.add_issue(
                        url,
                        "Page blocked by noindex",
                        "High",
                        "Remove noindex if this page should appear in search results"
                    )


                if "nofollow" in robots_content:

                    self.add_issue(
                        url,
                        "Page has nofollow directive",
                        "Low",
                        "Allow search engines to follow links if appropriate"
                    )



            # ==========================
            # CHARSET CHECK
            # ==========================


            charset = soup.find(
                "meta",
                charset=True
            )


            if not charset:

                self.add_issue(
                    url,
                    "Missing charset declaration",
                    "Low",
                    "Add UTF-8 charset meta tag"
                )



            # ==========================
            # VIEWPORT CHECK
            # ==========================


            viewport = soup.find(
                "meta",
                attrs={
                    "name":"viewport"
                }
            )


            if not viewport:

                self.add_issue(
                    url,
                    "Missing viewport meta tag",
                    "Medium",
                    "Add viewport for mobile optimization"
                )



            # ==========================
            # HTML LANGUAGE CHECK
            # ==========================


            html_tag = soup.find(
                "html"
            )


            if html_tag:


                lang = html_tag.get(
                    "lang"
                )


                if not lang:

                    self.add_issue(
                        url,
                        "Missing HTML language attribute",
                        "Low",
                        "Add lang attribute like en"
                    )


            else:

                self.add_issue(
                    url,
                    "Missing HTML tag",
                    "Medium",
                    "Use proper HTML structure"
                )



            # ==========================
            # FAVICON CHECK
            # ==========================


            favicon = soup.find(
                "link",
                attrs={
                    "rel":re.compile(
                        "icon",
                        re.I
                    )
                }
            )


            if not favicon:

                self.add_issue(
                    url,
                    "Missing favicon",
                    "Low",
                    "Add website favicon"
                )



            # ==========================
            # OPEN GRAPH CHECK
            # ==========================


            og_title = soup.find(
                "meta",
                property="og:title"
            )


            if not og_title:

                self.add_issue(
                    url,
                    "Missing Open Graph title",
                    "Low",
                    "Add og:title for social sharing"
                )



            og_description = soup.find(
                "meta",
                property="og:description"
            )


            if not og_description:

                self.add_issue(
                    url,
                    "Missing Open Graph description",
                    "Low",
                    "Add og:description"
                )



            og_image = soup.find(
                "meta",
                property="og:image"
            )


            if not og_image:

                self.add_issue(
                    url,
                    "Missing Open Graph image",
                    "Low",
                    "Add og:image"
                )



            # ==========================
            # TWITTER CARD CHECK
            # ==========================


            twitter_card = soup.find(
                "meta",
                attrs={
                    "name":"twitter:card"
                }
            )


            if not twitter_card:

                self.add_issue(
                    url,
                    "Missing Twitter Card",
                    "Low",
                    "Add twitter:card meta tag"
                )



            # ==========================
            # STRUCTURED DATA CHECK
            # ==========================


            schema = soup.find(
                "script",
                attrs={
                    "type":"application/ld+json"
                }
            )


            if not schema:

                self.add_issue(
                    url,
                    "Missing structured data",
                    "Low",
                    "Add JSON-LD schema markup"
                )



                        # ==========================
            # IMAGE SEO CHECKS
            # ==========================

            images = soup.find_all(
                "img"
            )


            for img in images:


                src = img.get(
                    "src"
                )


                # Missing ALT

                if not img.has_attr("alt"):

                    self.add_issue(
                        url,
                        "Image missing ALT attribute",
                        "Medium",
                        "Add descriptive alt text for accessibility and SEO"
                    )


                # Empty ALT

                elif img.get("alt").strip() == "":

                    self.add_issue(
                        url,
                        "Image has empty ALT text",
                        "Low",
                        "Add meaningful alt text or mark decorative images properly"
                    )


                # Missing image source

                if not src:

                    self.add_issue(
                        url,
                        "Image missing source URL",
                        "Medium",
                        "Add valid image src attribute"
                    )



            # ==========================
            # INTERNAL / EXTERNAL LINKS
            # ==========================


            internal_links = 0

            external_links = 0

            empty_links = 0



            parsed_domain = urlparse(
                url
            ).netloc



            links = soup.find_all(
                "a",
                href=True
            )



            for link in links:


                href = link.get(
                    "href"
                ).strip()



                # Empty anchor text

                text = link.get_text(
                    strip=True
                )


                if text == "":

                    empty_links += 1



                # Ignore anchors

                if href.startswith("#"):

                    continue



                full_url = urljoin(
                    url,
                    href
                )


                link_domain = urlparse(
                    full_url
                ).netloc



                if link_domain == parsed_domain:

                    internal_links += 1

                else:

                    external_links += 1



            # Too many links

            if len(links) > 300:

                self.add_issue(
                    url,
                    "Too many links on page",
                    "Low",
                    "Reduce excessive links to improve crawl efficiency"
                )



            # Empty anchor text warning

            if empty_links > 0:

                self.add_issue(
                    url,
                    "Links without anchor text",
                    "Low",
                    "Add descriptive anchor text to links"
                )



            # ==========================
            # URL STRUCTURE CHECKS
            # ==========================


            parsed_url = urlparse(
                url
            )


            # Long URL

            if len(url) > 120:

                self.add_issue(
                    url,
                    "URL too long",
                    "Low",
                    "Keep URLs short and descriptive"
                )



            # Uppercase URL

            if url != url.lower():

                self.add_issue(
                    url,
                    "URL contains uppercase characters",
                    "Low",
                    "Use lowercase URLs"
                )



            # Spaces in URL

            if " " in url:

                self.add_issue(
                    url,
                    "URL contains spaces",
                    "Medium",
                    "Encode spaces or use clean URLs"
                )



            # Underscore URLs

            if "_" in parsed_url.path:

                self.add_issue(
                    url,
                    "URL contains underscores",
                    "Low",
                    "Use hyphens instead of underscores"
                )



            # Multiple slashes

            if "//" in parsed_url.path:

                self.add_issue(
                    url,
                    "URL contains multiple slashes",
                    "Low",
                    "Clean URL structure"
                )



            # ==========================
            # CONTENT STRUCTURE CHECKS
            # ==========================


            paragraphs = soup.find_all(
                "p"
            )


            long_paragraphs = 0


            for p in paragraphs:

                words = len(
                    p.get_text(
                        " ",
                        strip=True
                    ).split()
                )


                if words > 120:

                    long_paragraphs += 1



            if long_paragraphs > 3:

                self.add_issue(
                    url,
                    "Too many long paragraphs",
                    "Low",
                    "Break content into smaller sections"
                )



            # Empty headings

            headings = soup.find_all(
                [
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6"
                ]
            )


            for heading in headings:

                if heading.get_text(
                    strip=True
                ) == "":

                    self.add_issue(
                        url,
                        "Empty heading tag",
                        "Low",
                        "Remove empty headings"
                    )


                        # ==========================
            # H1 DUPLICATE CHECK
            # ==========================


            h1_tags = soup.find_all(
                "h1"
            )


            if h1_tags:

                h1_text = h1_tags[0].get_text(
                    " ",
                    strip=True
                )


                if h1_text:

                    self.h1_map.setdefault(
                        h1_text.lower(),
                        []
                    ).append(
                        url
                    )



            # ==========================
            # PAGE CONTENT DUPLICATION
            # ==========================


            main_text = soup.get_text(
                " ",
                strip=True
            )


            clean_text = re.sub(
                r"\s+",
                " ",
                main_text.lower()
            ).strip()



            if clean_text:


                # Save first 500 chars
                # for comparison

                content_hash = clean_text[:500]


                self.content_map.setdefault(
                    content_hash,
                    []
                ).append(
                    url
                )



            # ==========================
            # DUPLICATE PARAGRAPH CHECK
            # ==========================


            paragraphs = soup.find_all(
                "p"
            )


            for paragraph in paragraphs:


                text = paragraph.get_text(
                    " ",
                    strip=True
                )


                text = text.lower()



                if len(text) > 80:

                    self.paragraph_map.setdefault(
                        text,
                        []
                    ).append(
                        url
                    )



            # ==========================
            # CONTENT QUALITY CHECK
            # ==========================


            word_count = len(
                clean_text.split()
            )



            if word_count < 100:


                self.add_issue(
                    url,
                    "Very low content page",
                    "High",
                    "Add more useful content for search visitors"
                )



            elif word_count < 300:


                self.add_issue(
                    url,
                    "Thin content",
                    "Medium",
                    "Increase content depth and usefulness"
                )



            # ==========================
            # PAGE HTML SIZE CHECK
            # ==========================


            html_size = len(
                html.encode(
                    "utf-8"
                )
            )



            # More than 2MB HTML

            if html_size > 2000000:


                self.add_issue(
                    url,
                    "HTML page size is very large",
                    "Medium",
                    "Reduce unnecessary HTML and scripts"
                )



            # ==========================
            # MISSING IMPORTANT SECTIONS
            # ==========================


            has_heading = soup.find(
                [
                    "h1",
                    "h2"
                ]
            )



            if not has_heading:


                self.add_issue(
                    url,
                    "Page has no content headings",
                    "Medium",
                    "Add H1/H2 structure for readability"
                )

                    # ==========================
            # ORPHAN PAGE CHECK
            # ==========================


            linked_pages = set()


            for links in self.internal_links_map.values():

                for link in links:

                    linked_pages.add(
                        link
                    )



            for page in self.pages_data:

                page_url = page.get(
                    "url",
                    ""
                )


                if page_url not in linked_pages:


                    self.add_issue(
                        page_url,
                        "Possible orphan page",
                        "Medium",
                        "Add internal links pointing to this page"
                    )

                    # ==========================
        # INTERNAL LINK SCORE
        # ==========================


        for url, links in self.internal_links_map.items():


            if len(links) == 0:

                self.add_issue(
                    url,
                    "Page has no internal links",
                    "Medium",
                    "Add internal links to improve crawling"
                )


            elif len(links) < 3:

                self.add_issue(
                    url,
                    "Weak internal linking",
                    "Low",
                    "Add more relevant internal links"
                )

            

        result = {


        "domain": domain,


        "audit_date": str(
            datetime.now()
        ),


        "total_pages": len(
            self.pages_data
        ),


        "seo_score": self.calculate_score(),


        "summary": self.issue_summary(),


        "total_issues": len(
            self.issues
        ),


        "issues": self.issues,


        "top_problems": self.top_problems(),


        "grouped_issues": self.grouped_issues(),


        "ai_prompt": self.create_ai_prompt(
            domain
        ),

        "keywords": self.keyword_data,

        "schema_data": self.schema_data,

        }



        self.save_json_report(
            result,
            f"{domain}_seo_audit"
        )


        self.save_csv_report(
            f"{domain}_seo_audit"
        )


        self.save_html_report(
            domain,
            f"{domain}_seo_audit"
        )


        return result