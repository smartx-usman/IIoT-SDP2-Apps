import abc


class DelayType(abc.ABC):
    value_type = ''

    @abc.abstractmethod
    def add_delay(self, client, client_id, arguments):
        pass