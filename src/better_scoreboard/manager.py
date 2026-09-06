from endstone.scoreboard import Criteria, DisplaySlot


class BetterScoreboardManager:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.scoreboard = plugin.server.create_scoreboard()
        self.objective = None

    def create(self) -> None:
        config = self.plugin._config.get_feature("scoreboard")

        if not config.get("enabled", True):
            return

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
            0,
        )

    def show(self, player) -> None:
        if self.objective is None:
            return

        player.scoreboard = self.scoreboard

    def remove(self, player) -> None:
        player.scoreboard = None

    def destroy(self) -> None:
        if self.objective is None:
            return

        self.objective.unregister()
        self.objective = None