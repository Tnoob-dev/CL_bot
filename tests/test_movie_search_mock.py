"""The movie-info provider should serve fixtures when mocking is enabled."""

from cinemalibrarybot.services import movie_search


async def test_get_results_returns_fixture_titles():
    results = await movie_search.get_results("shawshank")
    assert results
    assert any(r["primaryTitle"] == "The Shawshank Redemption" for r in results)
    # Each result carries the fields the /info buttons need.
    for r in results:
        assert "id" in r and "primaryTitle" in r and "startYear" in r


async def test_get_results_limits_to_five():
    results = await movie_search.get_results("")
    assert len(results) <= 5


async def test_get_info_by_id_returns_full_record():
    movie = await movie_search.get_info_by_id("tt0903747")
    assert movie is not None
    assert movie["primaryTitle"] == "Breaking Bad"
    assert movie["type"] == "tvSeries"
    assert movie["rating"]["aggregateRating"] == 9.5
    assert "Drama" in movie["genres"]
    assert movie["primaryImage"]["url"]


async def test_get_info_by_id_unknown_returns_none():
    assert await movie_search.get_info_by_id("tt0000000") is None
