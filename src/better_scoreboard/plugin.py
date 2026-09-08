from endstone.command import Command, CommandSender
from endstone.event import PlayerJoinEvent, event_handler
from endstone.plugin import Plugin

from .commands.betterscoreboard import BetterScoreboardCommand
from .config import BetterScoreboardConfig
from .manager import BetterScoreboardManager


class BetterScoreboardPlugin(Plugin):
    api_version = "0.11"
    authors = ["ErwanScraft"]
    soft_depend = [
        "stoneperms",
        "simplepapi",
    ]

    commands = {
        "betterscoreboard": {
            "description": "Manage BetterScoreboard.",
            "usages": [
                "/betterscoreboard help",
                "/betterscoreboard reload",
                "/betterscoreboard toggle",
            ],
            "aliases": ["bs"],
            "permissions": ["betterscoreboard.command"],
        }
    }

    permissions = {
        "betterscoreboard.command": {
            "description": (
                "Allows using BetterScoreboard commands."
            ),
            "default": "op",
        },
    }

    def on_enable(self) -> None:
        self.save_resources("config.yml")
    
        self._config = BetterScoreboardConfig(self)
        self._config.load()
    
        self._scoreboard_manager = BetterScoreboardManager(self)
        self._scoreboard_manager.create()
        self._command = BetterScoreboardCommand(self)
    
        self.register_events(self)
    
        self.logger.info("BetterScoreboard enabled.")
        
    def on_disable(self) -> None:
        self._scoreboard_manager.destroy()
    
        self.logger.info("BetterScoreboard disabled.")
    
    @event_handler
    def on_player_join(self, event: PlayerJoinEvent) -> None:
        self._scoreboard_manager.show(event.player)
    
    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        return self._command.on_command(
            sender,
            command,
            args,
        )