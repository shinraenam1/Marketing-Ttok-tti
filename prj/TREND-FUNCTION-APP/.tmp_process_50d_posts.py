import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.services.scoring import tokenize

IN_PATH = Path("c:/Users/User/trend-function-app/.tmp_collect_all_50d_full_posts.json")
OUT_PATH = Path("c:/Users/User/trend-function-app/.tmp_collect_all_50d_processed.json")


def _norm_text(value):
    return str(value or "").strip()


def _top_counter_items(counter, k):
    return [{"term": t, "count": int(c)} for t, c in counter.most_common(k)]


def main():
    raw = json.loads(IN_PATH.read_text(encoding="utf-8"))
    posts = raw.get("posts", [])

    per_post_term_counts = []
    per_post_unique_terms = []

    global_term_freq = Counter()
    global_doc_freq = Counter()

    processed_posts = []

    # 1) Stopword processing and term extraction per post.
    for idx, post in enumerate(posts, start=1):
        title = _norm_text(post.get("title"))
        emphasis = _norm_text(post.get("emphasis_text"))
        body = _norm_text(post.get("body_text"))

        clean_title = _norm_text(post.get("clean_title"))
        clean_emphasis = _norm_text(post.get("clean_emphasis_text"))
        clean_body = _norm_text(post.get("clean_body_text"))

        title_tokens = tokenize(clean_title or title)
        emphasis_tokens = tokenize(clean_emphasis or emphasis)
        body_tokens = tokenize(clean_body or body)

        # Weighted term count: emphasize repeated/shared signals and explicit highlighted text.
        term_counts = Counter()
        for t in body_tokens:
            term_counts[t] += 1.0
        for t in title_tokens:
            term_counts[t] += 1.6
        for t in emphasis_tokens:
            term_counts[t] += 1.9

        unique_terms = set(term_counts.keys())
        global_term_freq.update(term_counts)
        global_doc_freq.update(unique_terms)

        per_post_term_counts.append(term_counts)
        per_post_unique_terms.append(unique_terms)

        processed_posts.append(
            {
                "post_id": idx,
                "source": post.get("source", ""),
                "url": post.get("url", ""),
                "published_at": post.get("published_at", ""),
                "title": title,
                "emphasis_text": emphasis,
                "stopword_processed": {
                    "title_tokens": title_tokens,
                    "emphasis_tokens": emphasis_tokens,
                    "body_top_terms": _top_counter_items(Counter(body_tokens), 25),
                },
            }
        )

    if not processed_posts:
        out = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "note": "No posts in input file.",
            "window_days": raw.get("window_days"),
            "total_posts": 0,
            "posts": [],
        }
        OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"total_posts": 0, "out_path": str(OUT_PATH)}, ensure_ascii=False, indent=2))
        return

    max_doc_freq = max(global_doc_freq.values()) if global_doc_freq else 1
    max_term_freq = max(global_term_freq.values()) if global_term_freq else 1

    # 2) Duplicate-information weighting.
    global_weight = {}
    for term in global_doc_freq:
        doc_norm = global_doc_freq[term] / float(max_doc_freq)
        tf_norm = float(global_term_freq[term]) / float(max_term_freq)
        global_weight[term] = 0.65 * doc_norm + 0.35 * tf_norm

    for i, post in enumerate(processed_posts):
        term_counts = per_post_term_counts[i]
        weighted_terms = []

        for term, tf in term_counts.items():
            dup_score = global_weight.get(term, 0.0)
            post_score = math.log1p(tf) * (1.0 + 2.0 * dup_score)
            weighted_terms.append(
                {
                    "term": term,
                    "tf": round(float(tf), 3),
                    "doc_freq": int(global_doc_freq.get(term, 0)),
                    "duplicate_weight": round(float(post_score), 4),
                }
            )

        weighted_terms.sort(key=lambda x: x["duplicate_weight"], reverse=True)
        post["duplicate_weighted_terms"] = weighted_terms[:20]
        post["duplicate_signal_strength"] = round(
            float(sum(item["duplicate_weight"] for item in weighted_terms[:20])), 4
        )

    global_rank = []
    for term, df in global_doc_freq.most_common(120):
        global_rank.append(
            {
                "term": term,
                "doc_freq": int(df),
                "global_tf": round(float(global_term_freq.get(term, 0.0)), 3),
                "global_duplicate_weight": round(float(global_weight.get(term, 0.0)), 4),
            }
        )

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": "stage2_stopword_and_duplicate_weighting",
        "window_days": raw.get("window_days"),
        "collection_config": raw.get("collection_config", {}),
        "source_health": raw.get("source_health", {}),
        "doc_counts": raw.get("doc_counts", {}),
        "total_posts": len(processed_posts),
        "global_duplicate_terms": global_rank[:80],
        "posts": processed_posts,
    }

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    preview = {
        "total_posts": len(processed_posts),
        "out_path": str(OUT_PATH),
        "global_duplicate_terms_top10": out["global_duplicate_terms"][:10],
        "sample_post": {
            "post_id": processed_posts[0]["post_id"],
            "title": processed_posts[0]["title"],
            "emphasis_text": processed_posts[0]["emphasis_text"],
            "duplicate_weighted_terms_top10": processed_posts[0]["duplicate_weighted_terms"][:10],
        },
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
