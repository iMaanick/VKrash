class State:
    def __init__(self, state: str = None):
        self.state = state or self.__class__.__name__

    def __str__(self):
        return self.state


class StatesGroup:
    def __init_subclass__(cls, **kwargs):
        cls._states = {}
        for name, value in vars(cls).items():
            if isinstance(value, State):
                value.state = f"{cls.__name__}:{name}"
                cls._states[name] = value

    @classmethod
    def states(cls):
        return cls._states.values()
