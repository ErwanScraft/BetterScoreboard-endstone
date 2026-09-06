from endstone.scoreboard import (
    Criteria,
    DisplaySlot,
    ObjectiveSortOrder,
)


class BetterScoreboardManager:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.scoreboards: dict[str, object] = {}
        self._task = None

    def create(self) -> None:
        config = self.plugin._config.get_feature("scoreboard")

        if not config.get("enabled", True):
            return

        self._start_update_task()

        for player in self.plugin.server.online_players:
            self.show(player)

    def show(self, player) -> None:
        if not self.is_enabled():
            return

        scoreboard = self._create_scoreboard(player)

        self.scoreboards[player.name] = scoreboard
        player.scoreboard = scoreboard

    def remove(self, player) -> None:
        scoreboard = self.scoreboards.pop(
            player.name,
            None,
        )

        if scoreboard is None:
            return

        player.scoreboard = self.plugin.server.scoreboard

        self._destroy_scoreboard(scoreboard)

    def reload(self) -> None:
        self._stop_update_task()

        for player in self.plugin.server.online_players:
            self.remove(player)

        self.scoreboards.clear()

        self.create()

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

    def update(self) -> None:
        if not self.is_enabled():
            return

        for player in self.plugin.server.online_players:
            self._update_player(player)

    def destroy(self) -> None:
        self._stop_update_task()

        for player in self.plugin.server.online_players:
            self.remove(player)

        self.scoreboards.clear()

    def is_enabled(self) -> bool:
        config = self.plugin._config.get_feature(
            "scoreboard"
        )

        return config.get("enabled", True)

    def _create_scoreboard(self, player):
        config = self.plugin._config.get_feature(
            "scoreboard"
        )

        scoreboard = (
            self.plugin.server.create_scoreboard()
        )

        objective = scoreboard.add_objective(
            "better_scoreboard",
            Criteria.Type.DUMMY,
            config.get(
                "title",
                "§6§lBetterScoreboard",
            ),
        )

        objective.set_display(
            DisplaySlot.SIDE_BAR,
            ObjectiveSortOrder.ASCENDING,
        )

        self._set_lines(
            scoreboard,
            objective,
            player,
        )

        return scoreboard

    def _update_player(self, player) -> None:
        scoreboard = self.scoreboards.get(
            player.name
        )

        if scoreboard is None:
            self.show(player)
            return

        objective = scoreboard.get_objective(
            "better_scoreboard"
        )

        if objective is None:
            self.show(player)
            return

        self._set_lines(
            scoreboard,
            objective,
            player,
        )

        player.scoreboard = scoreboard

    def _set_lines(
        self,
        scoreboard,
        objective,
        player,
    ) -> None:
        config = self.plugin._config.get_feature(
            "scoreboard"
        )

        lines = config.get("lines", [])

        for entry in list(scoreboard.entries):
            scoreboard.reset_scores(entry)

        online = len(
            self.plugin.server.online_players
        )

        max_players = self.plugin.server.max_players

        for index, line in enumerate(lines):
            rendered = self._render_line(
                line,
                player,
                online,
                max_players,
            )

            entry = rendered + ("§r" * index)

            score = objective.get_score(entry)
            score.value = len(lines) - index

    @staticmethod
    def _render_line(
        line: str,
        player,
        online: int,
        max_players: int,
    ) -> str:
        return (
            line
            .replace("{player}", player.name)
            .replace("{online}", str(online))
            .replace(
                "{max_players}",
                str(max_players),
            )
        )

    def _start_update_task(self) -> None:
        self._stop_update_task()

        config = self.plugin._config.get_feature(
            "scoreboard"
        )

        interval = config.get(
            "update-interval",
            20,
        )

        if not isinstance(interval, int) or interval < 1:
            interval = 20

        self._task = (
            self.plugin.server.scheduler.run_task(
                self.plugin,
                self.update,
                delay=interval,
                period=interval,
            )
        )

    def _stop_update_task(self) -> None:
        if self._task is None:
            return

        self._task.cancel()
        self._task = None

    @staticmethod
    def _destroy_scoreboard(scoreboard) -> None:
        for objective in list(
            scoreboard.objectives
        ):
            objective.unregister()