
import json
import csv
import time
import statistics
from pathlib import Path

from recommender import recommend_tracks

BASE_DIR = Path(__file__).resolve().parent
QUERY_FILE = BASE_DIR / "benchmark_queries.json"
CATALOG_FILE = BASE_DIR / "catalog.json"
OUTPUT_FILE = BASE_DIR / "benchmark_results.csv"

TOP_K = 5


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def safe_list(value):
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value]
    if value:
        return [str(value).strip().lower()]
    return []


def matches_expected(track, field, expected):
    if not expected:
        return None

    actual = safe_list(track.get(field, []))
    expected_value = str(expected).strip().lower()

    return expected_value in actual


def evaluate_track(track, test):
    mood = matches_expected(track, "mood", test.get("expected_mood", ""))
    activity = matches_expected(
        track, "activities", test.get("expected_activity", "")
    )
    genre = matches_expected(track, "genre", test.get("expected_genre", ""))

    checks = [
        value for value in (mood, activity, genre)
        if value is not None
    ]

    combined = all(checks) if checks else None

    return {
        "mood": mood,
        "activity": activity,
        "genre": genre,
        "combined": combined
    }


def calculate_metrics(rows, key):
    values = [
        row[key] for row in rows
        if row[key] is not None
    ]

    if not values:
        return None

    return sum(values) / len(values)


def main():
    queries = load_json(QUERY_FILE)
    catalog = load_json(CATALOG_FILE)

    all_rows = []
    latencies = []

    metric_data = {
        "mood": [],
        "activity": [],
        "genre": [],
        "combined": []
    }

    query_hit_counts = {
        "mood": [0, 0],
        "activity": [0, 0],
        "genre": [0, 0],
        "combined": [0, 0]
    }

    reciprocal_ranks = {
        "mood": [],
        "activity": [],
        "genre": [],
        "combined": []
    }

    print("\n========== SONORA AI BENCHMARK ==========\n")
    print("Catalogue tracks:", len(catalog))
    print("Test queries:", len(queries))
    print("Top K:", TOP_K)

    for test in queries:
        query = test["query"]
        mode = test["mode"]

        start = time.perf_counter()

        recommendations = recommend_tracks(
            query,
            mode=mode,
            user_preferences=None
        )

        latency = (time.perf_counter() - start) * 1000
        latencies.append(latency)

        top_tracks = recommendations[:TOP_K]
        evaluations = [
            evaluate_track(track, test)
            for track in top_tracks
        ]

        print(f"\nQuery {test['id']}: {query}")
        print(f"Mode: {mode} | Latency: {latency:.2f} ms")

        for metric in metric_data:
            relevant_positions = [
                index + 1
                for index, result in enumerate(evaluations)
                if result[metric] is True
            ]

            # Evaluate only when this query has an expected label.
            has_label = any(
                result[metric] is not None for result in evaluations
            )

            if has_label:
                query_hit_counts[metric][1] += 1
                hit = bool(relevant_positions)
                query_hit_counts[metric][0] += int(hit)

                reciprocal_ranks[metric].append(
                    1 / relevant_positions[0]
                    if relevant_positions else 0
                )

                metric_data[metric].extend(
                    result[metric]
                    for result in evaluations
                    if result[metric] is not None
                )

        for rank, track in enumerate(top_tracks, start=1):
            result = evaluations[rank - 1]

            print(
                f"  {rank}. {track.get('title', 'Unknown')} "
                f"- {track.get('artist', 'Unknown')} "
                f"| Genre: {track.get('genre', 'Unknown')}"
            )

            all_rows.append({
                "query_id": test["id"],
                "query": query,
                "mode": mode,
                "rank": rank,
                "track_id": track.get("id", ""),
                "title": track.get("title", ""),
                "artist": track.get("artist", ""),
                "genre": json.dumps(track.get("genre", [])),
                "mood": json.dumps(track.get("mood", [])),
                "activities": json.dumps(track.get("activities", [])),
                "expected_genre": test.get("expected_genre", ""),
                "expected_mood": test.get("expected_mood", ""),
                "expected_activity": test.get("expected_activity", ""),
                "mood_relevant": result["mood"],
                "activity_relevant": result["activity"],
                "genre_relevant": result["genre"],
                "combined_relevant": result["combined"],
                "latency_ms": round(latency, 3)
            })

    fieldnames = [
        "query_id", "query", "mode", "rank", "track_id",
        "title", "artist", "genre", "mood", "activities",
        "expected_genre", "expected_mood", "expected_activity",
        "mood_relevant", "activity_relevant", "genre_relevant",
        "combined_relevant", "latency_ms"
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print("\n========== BENCHMARK SUMMARY ==========")
    print("Queries processed:", len(queries))
    print("Recommendation rows:", len(all_rows))
    print("Average latency:", round(statistics.mean(latencies), 2), "ms")
    print("Maximum latency:", round(max(latencies), 2), "ms")

    for metric in metric_data:
        hit_count, evaluated_queries = query_hit_counts[metric]
        precision = calculate_metrics(all_rows, metric + "_relevant") if False else None

        if evaluated_queries:
            hit_rate = hit_count / evaluated_queries * 100
            values = metric_data[metric]
            precision_at_5 = (
                sum(values) / (evaluated_queries * TOP_K) * 100
            )

            mrr = statistics.mean(reciprocal_ranks[metric])

            print(f"\n{metric.upper()} METRICS")
            print(f"Evaluated queries: {evaluated_queries}")
            print(f"Hit@{TOP_K}: {hit_rate:.2f}%")
            print(f"Precision@{TOP_K}: {precision_at_5:.2f}%")
            print(f"MRR: {mrr:.4f}")
        else:
            print(f"\n{metric.upper()} METRICS: No expected labels found.")

    print("\nResults saved to:", OUTPUT_FILE)
    print("\nIMPORTANT:")
    print("- Metrics are provisional metadata-based estimates.")
    print("- Genre labels must match the catalogue's genre format.")
    print("- Human review is required before claiming recommendation accuracy.")


if __name__ == "__main__":
    main()
