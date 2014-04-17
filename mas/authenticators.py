from mas.configuration import app_config
import json


facebook = app_config['facebook']

class AuthenticationServiceValidator(object):
    @classmethod
    def is_service_name(service):
        return False

    @classmethod
    def validate_token(cls, serviceToken):
        return False

    @classmethod
    def get_user_info(cls, token):
        return []


class AuthenticationServiceValidator_FB(object):
    @staticmethod
    def is_service_name(service):
        service_names = ['facebook', 'fb']
        if service.lower() in service_names:
            return True

        return False

    @classmethod
    def validate_token(cls, serviceToken):
        url = AuthenticationServiceValidator_FB.build_oauth_url(serviceToken)
        result = AuthenticationServiceValidator_FB.make_curl_request(url)

        if result.find("error") is not -1:
            return False

        return True

    @staticmethod
    def build_oauth_url(serviceToken):
        url = facebook['endpoint']
        url += 'oauth/access_token?grant_type=fb_exchange_token'
        url += '&client_id=' + facebook['app_id']
        url += '&client_secret=' + facebook['app_secret']
        url += '&fb_exchange_token=' + serviceToken
        return url

    @staticmethod
    def make_curl_request(url):
        import urllib
        req = urllib.urlopen(url)
        result = req.read()

        return result

    @classmethod
    def get_user_info(cls, token):
        url = AuthenticationServiceValidator_FB.build_basic_info_url(token)
        result = AuthenticationServiceValidator_FB.make_curl_request(url)
        result = json.loads(result)

        info = {}
        info['name'] = result['name'];
        info['email'] = result['email'];
        info['auth_service'] = 'facebook'
        info['auth_service_id'] = result['id']
        info['auth_service_token'] = token

        return info

    @staticmethod
    def build_basic_info_url(serviceToken):
        url = facebook['endpoint']
        url += '/me?access_token=' + serviceToken
        return url

authentication_service_validators = [
    AuthenticationServiceValidator_FB
]
