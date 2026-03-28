from .models import GameState, Tile, Unit, City


class GameStateSerializer:
    @staticmethod
    def to_json(state: GameState) -> str:
        return state.model_dump_json(indent=2)

    @staticmethod
    def to_compact_text(state: GameState) -> str:
        summary = []
        summary.append(f"[Polysistia] Turn {state.turn} | {state.player_tribe.title()}")
        summary.append(f"Score: {state.score}  Stars: {state.stars} (+{state.star_income}/turn)")

        if state.cities:
            city_strs = [f"{c.name} Lv{c.level}" for c in state.cities]
            summary.append(f"Cities ({len(state.cities)}): {', '.join(city_strs)}")
        else:
            summary.append("Cities: none detected")

        if state.enemy_cities:
            ec_strs = [f"{c.name} [{c.owner_tribe}]" for c in state.enemy_cities]
            summary.append(f"Enemy Cities ({len(state.enemy_cities)}): {', '.join(ec_strs)}")

        if state.units:
            unit_strs = [f"{u.unit_type.value}({u.health:.0%})" for u in state.units[:6]]
            extra = f" +{len(state.units)-6} more" if len(state.units) > 6 else ""
            summary.append(f"Units ({len(state.units)}): {', '.join(unit_strs)}{extra}")
        else:
            summary.append("Units: none detected")

        if state.enemy_units:
            eu_strs = [f"{u.unit_type.value}[{u.owner_tribe}]" for u in state.enemy_units[:4]]
            extra = f" +{len(state.enemy_units)-4} more" if len(state.enemy_units) > 4 else ""
            summary.append(f"Enemy Units ({len(state.enemy_units)}): {', '.join(eu_strs)}{extra}")

        return "\n".join(summary)

    @staticmethod
    def to_summary(state: GameState) -> str:
        return (
            f"Turn {state.turn} | {state.stars} Stars (+{state.star_income}) | "
            f"{len(state.units)} Units | {len(state.cities)} Cities"
        )
