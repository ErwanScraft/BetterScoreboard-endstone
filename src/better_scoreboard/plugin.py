from .config import BetterScoreboardConfig
from .manager import BetterScoreboardManager
from endstone.event import event_handler
from endstone.event.player import PlayerJoinEvent
from endstone.plugin import Plugin


class BetterScoreboardPlugin(Plugin):
    api_version = "0.11"

    def on_enable(self) -> None:
        self.save_resources("config.yml")
    
        self._config = BetterScoreboardConfig(self)
        self._config.load()
    
        self._scoreboard_manager = BetterScoreboardManager(self)
        self._scoreboard_manager.create()
    
        self.logger.info("BetterScoreboard enabled.")
        
    def on_disable(self) -> None:
        self._scoreboard_manager.destroy()
    
        self.logger.info("BetterScoreboard disabled.")
    
    @event_handler
    def on_player_join(self, event: PlayerJoinEvent) -> None:
        self._scoreboard_manager.show(event.player)