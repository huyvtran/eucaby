"""Views for Eucaby API."""

import flask
from flask import current_app
import flask_restful
import itertools
import logging

from eucaby.utils import mail as utils_mail
from eucaby_api import auth
from eucaby_api import fields as api_fields
from eucaby_api.utils import api as eucaby_api
from eucaby_api import args as api_args
from eucaby_api import models
from eucaby_api import ndb_models
from eucaby_api.utils import reqparse
from eucaby_api.utils import utils as api_utils


api_app = flask.Blueprint('api', __name__)
api = eucaby_api.Api(api_app, catch_all_404s=True)


USER_NOT_FOUND = 'User not found'


class OAuthToken(flask_restful.Resource):

    method_decorators = [auth.eucaby_oauth.token_handler]

    def post(self):  # pylint: disable=no-self-use
        return None


class FriendsView(flask_restful.Resource):

    """Returns list of friends."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def get(self):  # pylint: disable=no-self-use
        user = flask.request.user
        resp = auth.facebook_request(
            'get', '/{}/friends'.format(user.username))
        return api_utils.format_fb_response(resp, api_fields.FRIENDS_FIELDS)


class RequestLocationView(flask_restful.Resource):

    """Performs user's location request."""
    method_decorators = [auth.eucaby_oauth.require_oauth('location')]

    @classmethod
    def handle_request(cls, recipient, recipient_email):
        """Handles general operations of the request."""
        recipient_username = (recipient and recipient.username) or None
        recipient_name = (recipient and recipient.name) or None
        user = flask.request.user  # Sender
        req = ndb_models.LocationRequest.create(
            user.username, recipient_username, recipient_email)

        # XXX: Add user configuration to receive notifications to email
        #      (for Eucaby users). See #18
        if recipient_email:
            # Send email copy to sender?
            # Send email notification to recipient
            noreply_email = current_app.config['NOREPLY_EMAIL']
            eucaby_url = current_app.config['EUCABY_URL']
            body = flask.render_template(
                'mail/location_request_body.txt', sender_name=user.name,
                recipient_name=recipient_name, eucaby_url=eucaby_url,
                url='{}/{}'.format(eucaby_url, req.session.key))
            utils_mail.send_mail(
                'Location Request', body, noreply_email, [recipient_email])
        logging.info('Location Request: %s', str(req.to_dict()))
        return flask_restful.marshal(
            req, api_fields.REQUEST_FIELDS, envelope='data')

    @classmethod
    def handle_email(cls, email):
        """Handles email parameter."""
        recipient = models.User.get_by_email(email)
        return cls.handle_request(recipient, email)

    @classmethod
    def handle_username(cls, username):
        """Handles username parameter."""
        recipient = models.User.get_by_username(username)
        if not recipient:
            error = dict(message=USER_NOT_FOUND, code='not_found')
            return api_utils.make_response(error, 404)
        # Note:
        #     Recipient email can be empty because Facebook doesn't guarantee it
        # See:
        #     https://developers.facebook.com/docs/graph-api/reference/v2.2/user
        #     "This field will not be returned if no valid email address is
        #     available."
        return cls.handle_request(recipient, recipient.email)

    def post(self):
        args = reqparse.clean_args(api_args.REQUEST_LOCATION_ARGS)
        if isinstance(args, flask.Response):
            return args

        username, email = args['username'], args['email']
        # Email has priority over username
        if email:
            return self.handle_email(email)
        elif username:
            return self.handle_username(username)

        error = dict(
            message=api_args.MISSING_EMAIL_USERNAME, code='invalid_request')
        return api_utils.make_response(error, 400)


class NotifyLocationView(flask_restful.Resource):

    """Notifies user's location."""
    method_decorators = [auth.eucaby_oauth.require_oauth('location')]

    @classmethod
    def handle_request(cls, recipient, recipient_email, latlng, session=None):
        """Handles general operations of the request."""
        recipient_username = (recipient and recipient.username) or None
        recipient_name = (recipient and recipient.name) or None
        user = flask.request.user  # Sender
        # Create location response
        # Note: There might be several location responses for a single session
        loc_notif = ndb_models.LocationNotification.create(
            latlng, user.username, recipient_username, recipient_email, session)

        # XXX: Add user configuration to receive notifications to email
        #      (for Eucaby users). See #18
        if recipient_email:
            # Send email copy to sender?
            # Send email notification to recipient
            noreply_email = current_app.config['NOREPLY_EMAIL']
            eucaby_url = current_app.config['EUCABY_URL']
            maps_url = 'https://www.google.com/maps/place'
            body = flask.render_template(
                'mail/location_response_body.txt', sender_name=user.name,
                recipient_name=recipient_name, eucaby_url=eucaby_url,
                location_url='{}/{}'.format(maps_url, latlng))
            utils_mail.send_mail(
                'Location Notification', body, noreply_email, [recipient_email])
        logging.info('Location Notification: %s', str(loc_notif.to_dict()))

        return flask_restful.marshal(
            loc_notif, api_fields.NOTIFICATION_FIELDS, envelope='data')

    @classmethod
    def handle_key(cls, key, latlng):
        """Handles key parameter."""
        # Get location request
        session = ndb_models.Session(key=key)
        loc_req = ndb_models.LocationRequest.query(
            ndb_models.LocationRequest.session == session).fetch(1)
        if not loc_req:
            error = dict(message='Request not found', code='not_found')
            return api_utils.make_response(error, 404)
        loc_req = loc_req[0]
        session = loc_req.session
        # Get recipient which is sender in the session
        recipient = models.User.get_by_username(loc_req.sender_username)
        if not recipient:
            error = dict(message=USER_NOT_FOUND, code='not_found')
            return api_utils.make_response(error, 404)
        session.complete = True
        session.put()
        return cls.handle_request(recipient, recipient.email, latlng, session)

    @classmethod
    def handle_email(cls, email, latlng):
        """Handles email parameter."""
        recipient = models.User.get_by_email(email)
        return cls.handle_request(recipient, email, latlng)

    @classmethod
    def handle_username(cls, username, latlng):
        """Handles username parameter."""
        recipient = models.User.get_by_username(username)
        if not recipient:
            error = dict(message=USER_NOT_FOUND, code='not_found')
            return api_utils.make_response(error, 404)
        return cls.handle_request(recipient, recipient.email, latlng)

    def post(self):
        args = reqparse.clean_args(api_args.NOTIFY_LOCATION_ARGS)
        if isinstance(args, flask.Response):
            return args

        username, email, key, latlng = (
            args['username'], args['email'], args['key'],
            args['latlng'])
        # Preference chain: key, email, username
        if key:
            return self.handle_key(key, latlng)
        elif email:
            return self.handle_email(email, latlng)
        elif username:
            return self.handle_username(username, latlng)

        error = dict(message=api_args.MISSING_EMAIL_USERNAME_REQ,
                     code='invalid_request')
        return api_utils.make_response(error, 400)


class UserProfileView(flask_restful.Resource):

    """Returns user profile details."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def get(self):  # pylint: disable=no-self-use
        return flask_restful.marshal(
            flask.request.user, api_fields.USER_FIELDS, envelope='data')


class UserActivityView(flask_restful.Resource):

    """Returns list of user activity."""
    method_decorators = [auth.eucaby_oauth.require_oauth('history')]

    @classmethod
    def _get_vector_data(cls, req_username, notif_username, offset, limit):
        username = flask.request.user.username
        # WARNING: This is not efficient as it loads all requests and
        #          notifications to memory and sorts them
        # Get requests sent or received by user
        requests = ndb_models.LocationRequest.query(
            req_username == username).fetch()
        req_resp = flask_restful.marshal(
            dict(data=requests), api_fields.REQUEST_LIST_FIELDS)
        # Get notifications sent or received by user
        notifications = ndb_models.LocationNotification.query(
            notif_username == username).fetch()
        notif_resp = flask_restful.marshal(
            dict(data=notifications), api_fields.NOTIFICATION_LIST_FIELDS)
        data = itertools.chain(req_resp['data'], notif_resp['data'])
        merged_data = sorted(data, key=lambda x: x['created_date'])
        return dict(data=merged_data[offset:offset+limit])

    @classmethod
    def get_outgoing_data(cls, offset, limit):
        """Returns data for outgoing activities."""
        return cls._get_vector_data(
            ndb_models.LocationRequest.sender_username,
            ndb_models.LocationNotification.sender_username, offset, limit)

    @classmethod
    def get_incoming_data(cls, offset, limit):
        """Returns data for request activities."""
        return cls._get_vector_data(
            ndb_models.LocationRequest.recipient_username,
            ndb_models.LocationNotification.recipient_username, offset, limit)

    @classmethod
    def get_request_data(cls, offset, limit):
        """Returns data for request activities."""
        username = flask.request.user.username
        req_class = ndb_models.LocationRequest
        requests = req_class.query(
            req_class.sender_username == username).fetch(
                limit, offset=offset)
        return flask_restful.marshal(
            dict(data=requests), api_fields.REQUEST_LIST_FIELDS)

    @classmethod
    def get_notification_data(cls, offset, limit):
        """Returns data for notification activities."""
        username = flask.request.user.username
        notif_class = ndb_models.LocationNotification
        notifications = notif_class.query(
            notif_class.sender_username == username).fetch(
                limit, offset=offset)
        return flask_restful.marshal(
            dict(data=notifications), api_fields.NOTIFICATION_LIST_FIELDS)

    @classmethod
    def handle_request(cls, act_type, offset, limit):
        """Handles request."""
        # Note: total number of requests and notifications is not very important
        if act_type == api_args.OUTGOING:
            resp = cls.get_outgoing_data(offset, limit)
        elif act_type == api_args.INCOMING:
            resp = cls.get_incoming_data(offset, limit)
        elif act_type == api_args.REQUEST:
            resp = cls.get_request_data(offset, limit)
        elif act_type == api_args.NOTIFICATION:
            resp = cls.get_notification_data(offset, limit)
        # Add pagination
        if resp:
            resp['paging'] = dict(next_offset=offset+limit, limit=limit)
            return resp

        error = dict(message=api_args.DEFAULT_ERROR, code='server_error')
        return api_utils.make_response(error, 500)

    def get(self):  # pylint: disable=no-self-use
        args = reqparse.clean_args(api_args.ACTIVITY_ARGS)
        if isinstance(args, flask.Response):
            return args
        limit = args['limit']
        if limit > 100:  # Limit can't exceed 100
            limit = 100
        return self.handle_request(args['type'], args['offset'], limit)


api.add_resource(OAuthToken, '/oauth/token')
api.add_resource(FriendsView, '/friends')
api.add_resource(RequestLocationView, '/location/request')
api.add_resource(NotifyLocationView, '/location/notify')
api.add_resource(UserProfileView, '/me')
api.add_resource(UserActivityView, '/history')
