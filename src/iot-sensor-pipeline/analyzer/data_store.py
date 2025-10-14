import abc


class DataStore(abc.ABC):
    @abc.abstractmethod
    def connect_db(self):
        pass

    @abc.abstractmethod
    def store_data(self):
        pass
