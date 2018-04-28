import logging
import praw

from config.cst import *
from evaluator.Dispatchers.abstract_dispatcher import AbstractDispatcher
from services import RedditService


class RedditDispatcher(AbstractDispatcher):
    def __init__(self, config):
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.subreddits = None
        self.counter = 0
        self.social_config = {}

        # check presence of twitter instance
        if RedditService.is_setup_correctly(self.config):
            self.reddit_service = self.config[CONFIG_CATEGORY_SERVICES][CONFIG_REDDIT][CONFIG_SERVICE_INSTANCE]
            self.is_setup_correctly = True
        else:
            self.logger.warning("Required services are not ready")
            self.is_setup_correctly = False

    # merge new config into existing config
    def update_social_config(self, config):
        if CONFIG_REDDIT_SUBREDDITS in self.social_config:
            self.social_config[CONFIG_REDDIT_SUBREDDITS] = {**self.social_config[CONFIG_REDDIT_SUBREDDITS],
                                                            **config[CONFIG_REDDIT_SUBREDDITS]}
        else:
            self.social_config[CONFIG_REDDIT_SUBREDDITS] = config[CONFIG_REDDIT_SUBREDDITS]

    def _init_subreddits(self):
        self.subreddits = ""
        for symbol in self.social_config[CONFIG_REDDIT_SUBREDDITS]:
            for subreddit in self.social_config[CONFIG_REDDIT_SUBREDDITS][symbol]:
                if subreddit not in self.subreddits:
                    if self.subreddits:
                        self.subreddits = self.subreddits + "+" + subreddit
                    else:
                        self.subreddits = self.subreddits + subreddit

    def _get_data(self):
        if not self.subreddits:
            self._init_subreddits()

    def _something_to_watch(self):
        return CONFIG_REDDIT_SUBREDDITS in self.social_config and self.social_config[CONFIG_REDDIT_SUBREDDITS]

    def run(self):
        if self.is_setup_correctly:
            if self._something_to_watch():
                self._get_data()
                subreddit = self.reddit_service.get_endpoint().subreddit(self.subreddits)
                try:
                    for entry in subreddit.stream.submissions():
                        self.counter += 1
                        subreddit_name = entry.subreddit.display_name.lower()
                        self.notify_registered_clients_if_interested(subreddit_name,
                                                                     {CONFIG_REDDIT_ENTRY: entry
                                                                      })
                except Exception as e:
                    self.logger.error("Error when receiving Reddit feed: '" + str(e) + \
                                      "' this may mean that reddit login info in config.json are wrong.")
        self.logger.warning("Nothing to monitor, dispatcher is going to sleep.")
