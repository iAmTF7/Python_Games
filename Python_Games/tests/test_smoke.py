from game.base_entity import BaseEntity
from game.base_system import BaseSystem
from game.state import GameState


def test_state_exists(state):
    assert state.level == 1
    assert state.monsters == []
    assert state.projectiles == []
    assert state.items == []


def test_state_reset_runtime_lists():
    state = GameState(monsters=[object()], projectiles=[object()], items=[object()])
    state.reset_runtime_lists()
    assert state.monsters == []
    assert state.projectiles == []
    assert state.items == []


def test_base_interfaces_are_callable(state):
    entity = BaseEntity()
    system = BaseSystem()

    entity.update(state)
    entity.draw(None)
    entity.take_damage(1)
    assert entity.is_alive() is True

    system.handle_event(None, state)
    system.update(state)
    system.draw(None, state)
