from app.schemas.replay import ReplayStep


URL_RULES: list[tuple[list[str], list[str], float]] = [
    (["home", "main", "feed", "index"], ["home", "feed"], 0.75),
    (["search", "query", "keyword"], ["search"], 0.82),
    (["detail", "item", "product", "video"], ["detail", "video_detail"], 0.78),
    (["profile", "user", "account", "me"], ["profile", "account"], 0.76),
    (["cart", "order", "pay", "checkout"], ["cart", "order", "payment"], 0.8),
    (["message", "chat", "im"], ["message", "chat"], 0.74),
]


def analyze_urls(urls: list[str]) -> tuple[list[ReplayStep], str]:
    steps: list[ReplayStep] = []
    for url in urls:
        lowered = url.lower()
        matches: list[str] = []
        page_types: list[str] = []
        confidence = 0.45
        for keywords, types, score in URL_RULES:
            hit = [keyword for keyword in keywords if keyword in lowered]
            if hit:
                matches.extend(hit)
                page_types.extend(types)
                confidence = max(confidence, score)
        if not page_types:
            page_types = ["unknown"]
        steps.append(
            ReplayStep(
                url=url,
                matched_keywords=sorted(set(matches)),
                possible_page_types=sorted(set(page_types)),
                confidence=confidence,
            )
        )
    summary = "URL can be mapped to graph candidates by page type and keyword rules."
    if not urls:
        summary = "No URL was provided."
    return steps, summary

