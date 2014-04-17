DEFAULT_DISTANCE = 100

class User(object):
    def __init__(self):
        self.name = 'User'
        self.email = None
        self.authentication_services = {}
        self.token = None
        self.distance = DEFAULT_DISTANCE
        self.friends = []

    def get_api_token(self):
        if self.token is None:
            from uuid import uuid4
            token = uuid4()
            self.token = str(token)

        return self.token


    def add_friend(self, email):
        if email not in self.friends:
            self.friends.append(email)

    def get_friends_email_list(self):
        return self.friends

    def update_info(self, info):
        if 'name' in info:
            self.name = info['name']

        if 'email' in info:
            self.email = info['email']

        if 'auth_service' in info:
            auth_service = info['auth_service']
            if auth_service not in self.authentication_services:
                self.authentication_services[auth_service] = {}

            if 'auth_service_id' in info:
                auth_id = info['auth_service_id']
                if auth_id not in self.authentication_services[auth_service]:
                    self.authentication_services[auth_service][auth_id] = {}

                    if 'auth_service_token' in info:
                        token = info['auth_service_token']
                        self.authentication_services[auth_service][auth_id]['token'] = token


class UserCollection(object):
    def __init__(self):
        self._list = {}

    def get_by_email(self, email):
        if email in self._list:
            return self._list[email]

        return None

    def get_or_create_by_email(self, email):
        if email in self._list:
            return self._list[email]

        u = User()
        u.update_info( {'email': email, 'name': email} )
        self._list[email] = u
        return u;
