from endstone.scoreboard import (
    Criteria,
    DisplaySlot,
    ObjectiveSortOrder,
)


class BetterScoreboardManager:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.scoreboard = plugin.server.create_scoreboard()
        self.objective = None

    def create(self) -> None:
        config = self.plugin._config.get_feature("scoreboard")

        if not config.get("enabled", True):
            return

        self._create_objective(config)

    def _create_objective(self, config: dict) -> None:
        title = config.get(
            "title",
            "§6§lBetterScoreboard",
        )

        self.objective = self.scoreboard.add_objective(
            "better_scoreboard",
            Criteria.Type.DUMMY,
            title,
        )

        self.objective.set_display(
            DisplaySlot.SIDE_BAR,
            ObjectiveSortOrder.ASCENDING,
        )

        lines = config.get("lines", [])

        for index, line in enumerate(lines):
            score = self.objective.get_score(
                f"line_{index}"
            )
            score.value = len(lines) - index

    def show(self, player) -> None:
        if self.objective is None:
            return

        player.scoreboard = self.scoreboard

    def remove(self, player) -> None:
        player.scoreboard = None

    def reload(self) -> None:
        self.destroy()
        self.scoreboard = (
            self.plugin.server.create_scoreboard()
        )
        self.create()

        if self.objective is None:
            for player in self.plugin.server.online_players:
                self.remove(player)
            return

        for player in self.plugin.server.online_players:
            self.show(player)

    def toggle(self) -> bool:
        config = self.plugin._config.get_feature(
            "scoreboard"
        )

        enabled = not config.get("enabled", True)

        self.plugin._config.update_feature(
            "scoreboard",
            {"enabled": enabled},
        )

        self.plugin._config.load()

        self.reload()

        return enabled

    def destroy(self) -> None:
        if self.objective is None:
            return

        self.objective.unregister()
        self.objective = None