import abc
from typing import Any, Optional
import json
import datetime
import logging


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Save state to local storage"""
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Load state from local storage"""
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: Optional[str] = None):
        if not file_path:
            self.file_path = './state_file.json'

    def save_state(self, state: dict) -> None:
        # let's check existing state values and append or modify new ones
        if present_state := self.retrieve_state():
            for key, value in state.items():
                try:
                    present_state[key] = value
                except KeyError:
                    # we have new key to save in state file
                    present_state.update({key: value})
            state = present_state
        with open(self.file_path, 'w') as state_file:
            json.dump(state, state_file, ensure_ascii=False, default=str)

    def retrieve_state(self) -> dict:
        try:
            with open(self.file_path, 'r') as state_file:
                state = json.load(state_file)
        except FileNotFoundError:
            return
        return state


class State:
    """Main class to handle save state function."""

    def __init__(self):
        self.storage = JsonFileStorage()

    def set_state(self, state_dict: dict) -> None:
        logger = logging.getLogger(__name__)
        logger.info('Saving current state...')
        self.storage.save_state(state_dict)

    def get_state(self) -> Any:
        logger = logging.getLogger('main_log')
        logger.info('Reading current state...')
        state = {}
        state_dict = self.storage.retrieve_state()
        if not state_dict:
            state['last_sync'] = datetime.datetime.fromtimestamp(0)
            state['query_offset'] = 0
            return state
        return state_dict
