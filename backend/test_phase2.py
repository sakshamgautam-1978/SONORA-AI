
"""
SONORA AI - Phase 2 Integration Tests
Corrected test initialization order.
"""

import sys
import numpy as np

from recommender import (
    SEMANTIC_INDEX,
    calculate_hybrid_similarity,
    recommend_tracks,
    get_semantic_stats,
)


def test_semantic_model():

    print("\nTEST 1: Semantic model")

    # Trigger lazy model loading first
    scores = SEMANTIC_INDEX.query_scores(
        "relaxing blues music"
    )

    assert scores is not None, "Embedding model failed to load"

    status = get_semantic_stats()

    assert status["embedding_requested"] is True
    assert status["embedding_loaded"] is True

    print("PASS: Model loaded")
    print("Model:", status["model"])


def test_catalogue_vectors():

    print("\nTEST 2: Catalogue vectors")

    status = get_semantic_stats()

    assert status["vector_count"] == 500, (
        f"Expected 500 vectors, got {status['vector_count']}"
    )

    assert status["dimension"] == 384, (
        f"Expected 384 dimensions, got {status['dimension']}"
    )

    print("PASS: Catalogue vectors")
    print("Tracks:", status["vector_count"])
    print("Dimensions:", status["dimension"])


def test_semantic_query():

    print("\nTEST 3: Semantic query")

    scores, method = calculate_hybrid_similarity(
        "relaxing blues music"
    )

    assert len(scores) == 500
    assert np.all(np.isfinite(scores))

    assert method == "hybrid"

    print("PASS: Hybrid scoring")
    print("Method:", method)
    print("Top score:", round(float(np.max(scores)), 4))


def test_recommendations():

    print("\nTEST 4: Familiar recommendations")

    results = recommend_tracks(
        "relaxing blues music",
        mode="familiar"
    )

    assert len(results) > 0

    print("PASS: Familiar recommendations")
    print("Results:", len(results))


def test_discovery_mode():

    print("\nTEST 5: Discovery recommendations")

    results = recommend_tracks(
        "relaxing blues music",
        mode="discovery"
    )

    assert len(results) > 0

    print("PASS: Discovery recommendations")
    print("Results:", len(results))


def test_similar_tracks():

    print("\nTEST 6: Similar-track retrieval")

    similar = SEMANTIC_INDEX.similar_indices(
        index=0,
        limit=5
    )

    assert similar is not None
    assert len(similar) == 5

    print("PASS: Similar-track retrieval")

    for index, score in similar:

        print(
            "Track index:",
            index,
            "| Similarity:",
            round(score, 4)
        )


def run_tests():

    tests = [
        test_semantic_model,
        test_catalogue_vectors,
        test_semantic_query,
        test_recommendations,
        test_discovery_mode,
        test_similar_tracks,
    ]

    passed = 0
    failed = 0

    print("=" * 55)
    print("SONORA AI - PHASE 2 TEST SUITE")
    print("=" * 55)

    for test in tests:

        try:
            test()
            passed += 1

        except Exception as error:

            failed += 1

            print("\nFAILED:", test.__name__)
            print("ERROR:", repr(error))

    print("\n" + "=" * 55)
    print("PHASE 2 TEST SUMMARY")
    print("=" * 55)

    print("Passed:", passed)
    print("Failed:", failed)

    if failed:
        sys.exit(1)

    print("\nALL PHASE 2 TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
