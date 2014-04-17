class ApiTokenCollection(object):
    def __init__(self):
        self._list = {}

    def add(self,token,user):
        self._list[token] = user

    def find_user_by_token(self, token):
        if token not in self._list:
            return None

        return self._list[token]