from game.high_scores import HighScoreTable
from game.state import GameState


def test_high_score_table_ranks_rooms_and_persists(tmp_path):
    score_path = tmp_path / "scores.json"
    table = HighScoreTable(score_path, max_entries=3)

    table.submit(2)
    table.submit(5)
    table.submit(3)
    table.submit(4)

    assert [entry.room_reached for entry in table.display_entries()] == [5, 4, 3]

    reloaded = HighScoreTable(score_path, max_entries=3)
    assert [entry.room_reached for entry in reloaded.display_entries()] == [5, 4, 3]
    assert reloaded.best_room == 5


def test_game_state_tracks_room_reached():
    state = GameState()
    assert state.room_reached == 1
