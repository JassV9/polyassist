from polysistia.knowledge.tech_tree import tech_tree
from polysistia.knowledge.units import unit_knowledge
from polysistia.knowledge.buildings import building_knowledge
from polysistia.knowledge.tribes import tribe_knowledge
from polysistia.knowledge.strategies import strategy_knowledge

def test_tech_tree_loading():
    climbing = tech_tree.get_tech("climbing")
    assert climbing is not None
    assert climbing.tier == 1
    assert "mining" in climbing.leads_to
    assert "xin-xi" in climbing.starting_tech_of

def test_unit_stats():
    warrior = unit_knowledge.get_unit("warrior")
    assert warrior is not None
    assert warrior.attack == 2
    assert warrior.defense == 2
    assert warrior.max_health == 10
    assert "dash" in warrior.skills

def test_building_stats():
    farm = building_knowledge.get_building("farm")
    assert farm is not None
    assert farm.population == 2
    assert farm.cost == 5
    assert farm.required_tech == "farming"

def test_tribe_metadata():
    bardur = tribe_knowledge.get_tribe("bardur")
    assert bardur is not None
    assert bardur.starting_tech == "hunting"
    assert bardur.t0_capable is True

def test_strategy_knowledge():
    bardur_strat = strategy_knowledge.get_strategy("bardur")
    assert bardur_strat is not None
    assert len(bardur_strat.opening_sequence) > 0
    assert "hunting" in bardur_strat.tech_paths["economy_focus"]
