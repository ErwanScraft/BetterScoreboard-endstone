from endstone.plugin import Plugin


class BetterScoreboardPlugin(Plugin):
    api_version = "0.11"

    def on_enable(self) -> None:
        self.save_resources("config.yml")
    
        self.logger.info("BetterScoreboard enabled.")

    def on_disable(self) -> None:
        self.logger.info("BetterScoreboard disabled.")