from endstone.scoreboard import (
    Criteria,
    DisplaySlot,
    ObjectiveSortOrder,
    RenderType,
)

STONEPERMS_SERVICE = "stoneperms.permissions.v1"


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
        
    def _get_stoneperms(self):
        return self.plugin.server.service_manager.load(
            STONEPERMS_SERVICE
        )

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
    
        return self._render_stoneperms(
            player,
            rendered,
        )
    
    def _render_stoneperms(
        self,
        player,
        text: str,
    ) -> str:
        if "{stoneperms:" not in text:
            return text
    
        service = self._get_stoneperms()
    
        if service is None:
            return text
    
        replacements = {}
    
        static_placeholders = {
            "{stoneperms:primary_group}": (
                service.get_primary_group(player)
            ),
            "{stoneperms:groups}": ", ".join(
                service.get_groups(player)
            ),
            "{stoneperms:prefix}": (
                service.get_prefix(player)
            ),
            "{stoneperms:suffix}": (
                service.get_suffix(player)
            ),
            "{stoneperms:tracks}": self._format_tracks(
                service.get_user_tracks(player)
            ),
        }
    
        for placeholder, value in static_placeholders.items():
            if value is not None:
                replacements[placeholder] = str(value)
    
        meta_map = service.get_meta_map(player)
    
        if "{stoneperms:meta_map}" in text:
            replacements["{stoneperms:meta_map}"] = (
                self._format_meta_map(meta_map)
            )
    
        for key, value in meta_map.items():
            placeholder = f"{stoneperms:meta:{key}}"
    
            if placeholder in text:
                replacements[placeholder] = str(value)
    
        for placeholder, value in replacements.items():
            text = text.replace(
                placeholder,
                value,
            )
    
        return self._render_stoneperms_dynamic(
            service,
            player,
            text,
        )
    
    def _render_stoneperms_dynamic(
        self,
        service,
        player,
        text: str,
    ) -> str:
        marker = "{stoneperms:"
    
        while marker in text:
            start = text.find(marker)
            end = text.find("}", start)
    
            if end == -1:
                break
    
            placeholder = text[start:end + 1]
            parameter = text[
                start + len(marker):end
            ]
    
            replacement = self._resolve_stoneperms_parameter(
                service,
                player,
                parameter,
            )
    
            if replacement is None:
                break
    
            text = text.replace(
                placeholder,
                str(replacement),
                1,
            )
    
        return text
        
    def _resolve_stoneperms_parameter(
        self,
        service,
        player,
        parameter: str,
    ):
        if parameter.startswith("permission:"):
            permission = parameter[
                len("permission:"):
            ]
    
            if not permission:
                return None
    
            decision = service.check_permission(
                player,
                permission,
            )
    
            return decision.value
    
        if parameter.startswith("has_permission:"):
            permission = parameter[
                len("has_permission:"):
            ]
    
            if not permission:
                return None
    
            return service.has_permission(
                player,
                permission,
            )
    
        if parameter.startswith("track:"):
            track_name = parameter[
                len("track:"):
            ]
    
            if not track_name:
                return None
    
            tracks = service.get_user_tracks(player)
    
            groups = tracks.get(track_name)
    
            if groups is None:
                return None
    
            return ", ".join(groups)
    
        return None

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
    
    @staticmethod
    def _format_tracks(
        tracks: dict[str, tuple[str, ...]],
    ) -> str:
        return ", ".join(
            f"{name}: {', '.join(groups)}"
            for name, groups in tracks.items()
        )
    
    @staticmethod
    def _format_meta_map(
        meta: dict[str, str],
    ) -> str:
        return ", ".join(
            f"{key}={value}"
            for key, value in meta.items()
        )