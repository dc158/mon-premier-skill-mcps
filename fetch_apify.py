import os
import sys
import json
from apify_client import ApifyClient

def get_top_posts(search_query, max_results=5):
    apify_token = os.environ.get("APIFY_TOKEN")
    if not apify_token:
        return json.dumps({"error": "Variable d'environnement APIFY_TOKEN manquante."})

    client = ApifyClient(apify_token)

    run_input = {
        "searchQueries": [search_query],
        "resultsPerPage": max_results
    }

    try:
        run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input, timeout_secs=90)
        posts = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            likes = item.get("diggCount", 0)
            comments = item.get("commentCount", 0)
            shares = item.get("shareCount", 0)
            engagement = likes + (comments * 2) + (shares * 3)

            posts.append({
                "author": item.get("author", {}).get("nickname", "Inconnu"),
                "text": item.get("desc", ""),
                "url": item.get("webVideoUrl", ""),
                "engagement_score": engagement,
                "metrics": {"likes": likes, "comments": comments, "shares": shares}
            })

        posts = sorted(posts, key=lambda x: x["engagement_score"], reverse=True)
        return json.dumps(posts, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Veuillez fournir un mot-clé."}))
        sys.exit(1)
    query = sys.argv[1]
    print(get_top_posts(query))
