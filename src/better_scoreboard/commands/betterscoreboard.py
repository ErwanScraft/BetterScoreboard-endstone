from endstone.command import Command, CommandSender


class BetterScoreboardCommand:
    def __init__(self, plugin) -> None:
        self.plugin = plugin

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        if command.name != "betterscoreboard":
            return False

        if not args or args == ["help"]:
            self._send_help(sender)
            return True

        if args == ["reload"]:
            return self._reload(sender)

        if args == ["toggle"]:
            return self._toggle(sender)

        sender.send_message("§cUnknown command.")
        sender.send_message(
            "§eUsage: /betterscoreboard help"
        )
        return True

    @staticmethod
    def _send_help(sender: CommandSender) -> None:
        sender.send_message(
            "§6§lBetterScoreboard Commands"
        )
        sender.send_message(
            "§e/betterscoreboard help §7- Show this help."
        )
        sender.send_message(
            "§e/betterscoreboard reload §7- Reload configuration."
        )
        sender.send_message(
            "§e/betterscoreboard toggle §7- Toggle scoreboard."
        )

    def _reload(self, sender: CommandSender) -> bool:
        try:
            self.plugin._config.load()
            self.plugin._scoreboard_manager.reload()
        except Exception as error:
            sender.send_message(
                f"§cFailed to reload configuration: {error}"
            )
            self.plugin.logger.error(
                f"Failed to reload config.yml: {error}"
            )
            return True

        sender.send_message(
            "§aBetterScoreboard configuration reloaded."
        )
        return True

    def _toggle(self, sender: CommandSender) -> bool:
        try:
            enabled = (
                self.plugin._scoreboard_manager.toggle()
            )
        except Exception as error:
            sender.send_message(
                f"§cFailed to toggle scoreboard: {error}"
            )
            self.plugin.logger.error(
                f"Failed to toggle scoreboard: {error}"
            )
            return True

        if enabled:
            sender.send_message(
                "§aBetterScoreboard enabled."
            )
        else:
            sender.send_message(
                "§cBetterScoreboard disabled."
            )

        return True