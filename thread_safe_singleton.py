from threading import Lock

class Singleton:
    _is_initialized = False
    _instance = None
    _lock = Lock()
    
    def __new__(cls, val=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, val=None):
        if not self._is_initialized:
            with self._lock:
                if not self._is_initialized:
                    self.val = val 
                    self.__class__._is_initialized = True
    
    
s1 = Singleton("db_connect_1")
s2 = Singleton("db_connect_2")
s3 = Singleton("db_connect_3")

print(s1 is s2)
print(s1.val)
print(s2.val)
print(s3.val)