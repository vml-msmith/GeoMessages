from flask import Flask, abort, jsonify, request
import requests
import tempfile

from mas.configuration import app_config
from mas.authenticators import authentication_service_validators, \
    AuthenticationServiceValidator
from mas.user import UserCollection
from mas.apitoken import ApiTokenCollection
from mas.utilities import haversine

from uuid import uuid4

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

from time import time

UPLOAD_FOLDER = ''
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'png'])

ERRORS = {
    'bad_service_token': {'message': 'Bad service token'},
    'bad_api_token': {'message': 'Corrupt or expired token'}
}


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def json_error(error):
    """Return a jsonified error message"""
    response = {'status': 'error', 'message': error['message']}
    return jsonify(response)


def json_success(data):
    response = {'status': 'success', 'response': data}
    return jsonify(response)


class TopId(object):
    top_id = 1

    @staticmethod
    def get_top_id():
        id = TopId.top_id
        TopId.top_id = TopId.top_id + 1
        return id


class GeoMessage(object):
    def __init__(self):
        self._id = TopId.get_top_id()

        self._coordinates = (0,0)
        self.title = 'Message'
        self.body = ''
        self.author = None
        self.video = None
        self.photo = None
        self.date = time()
        self._distances = {}

    def set_coordinates(self, coords):
        self._coordinates = (round(float(coords[0]), 4), round(float(coords[1]), 4))

    def distance_to_coordinates(self, coords, r = None):
        if r is None:
            r = app_config['default_measurement']

        lat1 = round(self._coordinates[0], 5)
        lon1 = round(self._coordinates[1], 5)
        lat2 = round(coords[0], 5)
        lon2 = round(coords[1], 5)

        distance_key = str(lon2) + ',' + str(lat2) + ',' + str(lon1) + ',' + str(lat1) + ' - ' + str(r)

        if r in self._distances:
            if distance_key in self._distances[r]:
                return self._distances[r][distance_key]
        else:
            self._distances[r] = {}

        d = haversine(lon1, lat1, lon2, lat2, r)
        self._distances[r][distance_key] = d

        return d

    def is_intended_viewer(self, user):
        # we need to make sure the messages author and the user are friends.
        # Or maybe this message is public?
        # or the user is part of a group maybe
        # or the user wants to see specific events
        return True


class GeoMessageCollection(object):
    def __init__(self):
        buckets = {}

        self._buckets = buckets

    def get_buckets(self, coordinates, bucket):
        lat = coordinates[0]
        lon = coordinates[1]

        r = []
        for x in range(-3,3):
            r.append(float(x) * .01)

        b = []
        for x in r:
            b.append(round(lon + x,2))

        results = []
        for x in r:
            x = str(round(lat + x, 2))
            if x in bucket:
                for l in b:
                    if str(l) in bucket[x]:
                        for node in bucket[x][str(l)]:
                            results.append(node)

        return results

    def add_to_bucket(self, node):
        coordinates = node._coordinates

        lat = coordinates[0]
        lon = coordinates[1]

        lat_b = str(round(lat,2))
        lon_b = str(round(lon,2))

        if lat_b not in self._buckets:
            self._buckets[lat_b] = {}

        if lon_b not in self._buckets[lat_b]:
            self._buckets[lat_b][lon_b] = []

        self._buckets[lat_b][lon_b].append(node)

    def find_nearby(self, coordinates, r):
        return self.get_buckets(coordinates, self._buckets)

users = UserCollection()
api_tokens = ApiTokenCollection()
coords = GeoMessageCollection()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/public/getToken/<service>/<token>')
@crossdomain(origin='*')
def get_token(service, token):
    """Generate an API token for the service and token sent."""
    validator = AuthenticationServiceValidator

    # find the correct validator for <service>
    for item in authentication_service_validators:
        if item.is_service_name(service) is True:
            validator = item

    # validate the <token> is a good token that came from us.
    if validator.validate_token(token) is not True:
        return json_error(ERRORS['bad_service_token'])


    # TODO: lost the ability to verify it's real. Need to add that back.

    # get basic user information from the service
    basic_info = validator.get_user_info(token)

    # get or create user
    u = users.get_or_create_by_email(basic_info['email'])
    u.update_info(basic_info)

    # get or generate an api token
    api_token = u.get_api_token()
    api_tokens.add(api_token, u)

    return json_success({'token': api_token})


@app.route('/private/<token>/getFriendsList')
@crossdomain(origin='*')
def get_friends_list(token):
    """Get a list of friends for the user identified by token"""
    u = api_tokens.find_user_by_token(token)
    if u is None:
        return json_error(ERRORS['bad_api_token'])

    friends_list = {'count': 0, 'records': {}}
    friends_emails = u.get_friends_email_list()

    for e in friends_emails:
        f = users.get_by_email(e)
        friends_list['count'] = friends_list['count'] + 1
        if f is not None:
            friends_list['records'][e] = {'name': f.name}
        else:
            friends_list['records'][e] = {'name': e}


    return json_success(friends_list)


@app.route('/private/<token>/addFriend/<friendsList>')
@crossdomain(origin='*')
def add_friend(token, friendsList):
    """Get a list of friends for the user identified by token"""
    u = api_tokens.find_user_by_token(token)
    if u is None:
        return json_error(ERRORS['bad_api_token'])

    from email.utils import parseaddr
    friends_list = friendsList.split(',')

    emails = []
    for e in friends_list:
        e = parseaddr(e)
        if e == u.email:
            continue

        if str(e[1]) is not '':
            u.add_friend(str(e[1]))

    return json_success('done')


def message_output(node, dist):
    author = users.get_by_email(node.author)
    obj = {}
    obj['id'] = node._id
    obj['longitude'] = node._coordinates[0]
    obj['latitude'] = node._coordinates[1]

    obj['title'] = node.title
    obj['author'] = author.email
    obj['author_name'] = author.name

    obj['video'] = node.video
    obj['photo'] = node.photo
    obj['date'] = node.date
    obj['note'] = node.body
    obj['distance'] = dist

    if node.video is not None:
      obj['thumbnail'] = 'http://img.youtube.com/vi/' + node.video + '/0.jpg';
    elif node.photo is not None:
      obj['thumbnail'] = node.photo
    else:
      obj['thumbnail'] = None

    return obj;


@app.route('/private/<token>/getMessages/<coordinates>/<range>')
@crossdomain(origin='*')
def get_messages(token, coordinates, range):
    """Ble bloop"""
    u = api_tokens.find_user_by_token(token)
    if u is None:
        return json_error(ERRORS['bad_api_token'])

    geo = coordinates.split(',')
    loc = (float(geo[0]), float(geo[1]))

    range = float(range)
    # TODO: 100? That's bad too. What is 100?
    near = coords.find_nearby(loc, 100)
    results = {}
    for node in near:
        if node.is_intended_viewer(u) is False:
            continue

        dist = node.distance_to_coordinates(loc)
        # TODO: This is bad. What does * 1000 mean? It's for KMs, I know that.. but it's bad
        dist = dist * 1000
        if dist < range:
            results[node._id] = message_output(node, dist)

    return json_success(results)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/private/<token>/postMessage', methods = ['POST'])
@crossdomain(origin="*")
def post_message(token):
    """More bles and bloops"""
    u = api_tokens.find_user_by_token(token)
    if u is None:
        return json_error(ERRORS['bad_api_token'])

    if request.method == 'POST':
        # Get the title
        # Get the body
        # Get the file
        # come up with a title from the body
        # validate the title len
        # validate body len
        # validate file type
        # validate file size
        # create new node
        # copy image to host
        # add file URL to node
        # send back success
        file = request.files['file']
        if file and allowed_file(file.filename):
            with tempfile.NamedTemporaryFile(delete=True) as tfile:

                tfile.write(file.read())
                tfile.flush()
                import pyimgur

                API_KEY = 'cc50f44153dce31'
                image_path = tfile.name
                im = pyimgur.Imgur(API_KEY)
                uploaded_image = im.upload_image(image_path, title="My image")
                print(uploaded_image.title)
                print(uploaded_image.link)
                print(uploaded_image.size)
                print(uploaded_image.type)

            #filename = secure_filename(file.filename)

            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return json_success("blah")

    if request.headers['Content-Type'] == 'application/octet-stream':
        f = open('./binary', 'wb')
        f.write(request.data)
        f.close()
        print "Binary message written!"


    return json_success("blah")

    if request.headers['Content-Type'] == 'application/octet-stream':
        f = open('./binary', 'wb')
        f.write(request.data)
        f.close()
        print "Binary message written!"



@app.route('/api/getMessages', methods = ['GET'])
@crossdomain(origin="*")
def api_get_messages():
    """More bles and bloops"""
    messages = {
        '1111' : {
            'id': '1111',
            'title': 'New Message',
            'from': 'mail.msmith@gmail.com',
            'to': 'Michael Smith',
            'timestamp': time(),
            'content': 'Blee b1loop blah',
        },
        '1000' : {
            'id': '1000',
            'from': 'mail.msmith@gmail.com',
            'to': 'Michael Smith',
            'title': 'Another New Message',
            'timestamp': time(),
            'content': "Lorem ipsum dolor sit amet consectetur adipiscing elit. Praesent tincidunt turpis ut est tincidunt, at dictum tortor dictum. Suspendisse vel suscipit eros, sed adipiscing velit. Fusce luctus egestas vulputate. Praesent eu elit sed leo imperdiet euismod vitae et ipsum. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec pretium ipsum a facilisis molestie. Aliquam porta, leo eget tincidunt convallis, odio augue mollis velit, sed volutpat nisi purus eget augue. Sed dapibus elementum est ut condimentum. Curabitur varius ultricies augue ultricies consectetur. Aliquam urna diam, tincidunt a ante sed, sagittis luctus enim. Nam diam lectus, faucibus at pharetra et, aliquet non ante. Nunc ultrices lobortis sem eget facilisis. Aliquam nec nulla congue, vulputate magna sed, mollis magna. Nulla facilisi.",
        }
    }
    return json_success(messages)


def setup_test_data():
    fake_users = [
        {
            'email': 'mail.msmith@gmail.com',
            'name': 'Michael Smith'
        },
        {
            'email': 'carpaten@gmail.com',
            'name': 'Paul Smith'
        },
        {
            'email': 'vmidgorden@gmail.com',
            'name': 'Victoria Midgordne'
        },
        {
            'email': 'clee@gmail.com',
            'name': 'Corey Lee'
        },
        {
            'email': 'aceinthehole@yahoo.com',
            'name': 'Nick Dodson'
        },
        {
            'email': 'jmidgorden@gmail.com',
            'name': 'Jon Midgorden'
        },
        {
            'email': 'pholley@gmail.com',
            'name': 'Patrick Holley'
        }

    ]

    photos = [
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2014-14-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2006-10-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2003-28-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2012-10-c-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2014-02-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2006-46-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-1992-17-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-1998-18-b-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2008-31-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2014-04-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-1994-02-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2007-19-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2005-12-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-1999-19-b-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2014-01-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2009-28-b-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2007-41-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2011-11-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2013-06-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2003-01-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2006-55-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2006-14-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2005-01-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-1999-12-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2007-10-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2013-23-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2006-23-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2006-24-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2006-17-c-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2011-17-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2004-04-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2007-17-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-1994-02-b-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2004-31-b-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2003-24-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2000-20-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2010-26-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2011-01-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-1995-49-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2005-04-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2009-02-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2012-10-a-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-2005-26-d-web.jpg',
        'http://imgsrc.hubblesite.org/hu/db/images/hs-1995-47-a-web.jpg',
    ]

    for user in fake_users:
        u = users.get_or_create_by_email(user['email'])
        u.update_info(user)

    from random import randint
    from random import random
    user_len = len(fake_users) - 1
    photo_len = len(photos) - 1
    for x in range(0, 500000):
        n = randint(0, user_len)
        p = randint(0, photo_len)
        #u = users.get_by_email(fake_users[n]['email'])
        node = GeoMessage()
        node.body = 'This here should be a fairly long note so we can get an idea of how the note will look on an iphone screen when it is long and such. Ta da!'
        node.photo = photos[p]
        lat = float(randint(39,40)) + random()
        lon = float(randint(-95,-94)) + random()
        node.set_coordinates((lat,lon))
        node.author = fake_users[n]['email']
        coords.add_to_bucket(node)

    u = users.get_by_email('mail.msmith@gmail.com')
    u.token = 'f84133f3-9522-4011-b348-8c658e20837c'
    api_token = u.get_api_token()
    api_tokens.add(api_token, u)

    print api_token

    node = GeoMessage()

    node.set_coordinates((39.22992,-94.6342))
    coords.add_to_bucket(node)

    loc = (39.21001,-94.63)


if __name__ == "__main__":
    # Do test stuff
    # setup_test_data()

    app.run()
