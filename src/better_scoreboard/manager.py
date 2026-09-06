from endstone.scoreboard import (
    Criteria,
    DisplaySlot,
    ObjectiveSortOrder,
    RenderType,
)


class BetterScoreboardManager:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.scoreboards: dict[str, object] = {}
        self._lines: dict[str, list[str]] = {}
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
        self._lines[player.name] = []

        self._set_lines(
            scoreboard,
            scoreboard.get_objective("better_scoreboard"),
            player,
        )

    def remove(self, player) -> None:
        scoreboard = self.scoreboards.pop(
            player.name,
            None,
        )
    
        self._lines.pop(player.name, None)
    
        if scoreboard is None:
            return
    
        objective = scoreboard.get_objective(
            "better_scoreboard"
        )
    
        if objective is not None:
            objective.set_display(None)
    
        player.scoreboard = self.plugin.server.scoreboard
    
        self._destroy_scoreboard(scoreboard)

    def reload(self) -> None:
        self._stop_update_task()

        for player in self.plugin.server.online_players:
            self.remove(player)

        self.scoreboards.clear()
        self._lines.clear()

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
        self._lines.clear()

    def is_enabled(self) -> bool:
        config = self.plugin._config.get_feature(
            "scoreboard"
        )

        return config.get("enabled", True)

    def _create_scoreboard(self, player):
        config = self.plugin._config.get_feature(
            "scoreboard"
        )

        scoreboard = self.plugin.server.create_scoreboard()

        objective = scoreboard.add_objective(
            "better_scoreboard",
            Criteria.Type.DUMMY,
            config.get(
                "title",
                "§6§lBetterScoreboard",
            ),
            RenderType.INTEGER,
        )

        # Assign the scoreboard before enabling
        # the sidebar display.
        player.scoreboard = scoreboard

        objective.set_display(
            DisplaySlot.SIDE_BAR,
            ObjectiveSortOrder.DESCENDING,
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
            self.remove(player)
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

        if not isinstance(lines, list):
            lines = []

        online = len(
            self.plugin.server.online_players
        )

        max_players = self.plugin.server.max_players

        new_lines = [
            self._render_line(
                line,
                player,
                online,
                max_players,
            )
            for line in lines
            if isinstance(line, str)
        ]

        old_lines = self._lines.get(
            player.name,
            [],
        )

        old_entries = [
            self._make_entry(line, index)
            for index, line in enumerate(old_lines)
        ]

        new_entries = [
            self._make_entry(line, index)
            for index, line in enumerate(new_lines)
        ]

        total = len(new_entries)

        for index, entry in enumerate(new_entries):
            if (
                index < len(old_entries)
                and old_entries[index] == entry
            ):
                continue

            if index < len(old_entries):
                scoreboard.reset_scores(
                    old_entries[index]
                )

            objective.get_score(entry).value = (
                total - index
            )

        for entry in old_entries[total:]:
            scoreboard.reset_scores(entry)

        self._lines[player.name] = new_lines

    @staticmethod
    def _make_entry(
        line: str,
        index: int,
    ) -> str:
        return line + ("§r" * index)

    @staticmethod
    def _render_line(
        self,
        line: str,
        player,
        online: int,
        max_players: int,
    ) -> str:
        rendered = (
            line
            .replace("{player}", player.name)
            .replace("{online}", str(online))
            .replace("{max_players}", str(max_players))
        )
    
        return self._parse_placeholders(
            player,
            rendered,
        )
    
    def _parse_placeholders(
        self,
        player,
        text: str,
    ) -> str:
        try:
            from endstone_papi import PlaceholderAPI
        except ImportError:
            return text
    
        service = PlaceholderAPI.load(
            self.plugin.server.service_manager
        )
    
        if service is None or not service.active:
            return text
    
        try:
            return service.set_placeholders(
                player,
                text,
            )
        except Exception as exc:
            self.plugin.logger.warning(
                f"Failed to parse placeholders: {exc}"
            )
            return text

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

        self._task = self.plugin.server.scheduler.run_task(
            self.plugin,
            self.update,
            delay=interval,
            period=interval,
        )

    def _stop_update_task(self) -> None:
        if self._task is None:
            return

        self._task.cancel()
        self._task = None

    @staticmethod
    def _destroy_scoreboard(scoreboard) -> None:
        for objective in list(scoreboard.objectives):
            objective.unregister()