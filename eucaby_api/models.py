"""SQL models for API service."""

import datetime
import flask
import flask_sqlalchemy
from sqlalchemy_utils.types import choice

from eucaby_api.utils import utils as api_utils
from eucaby_api.utils import date as utils_date

db = flask_sqlalchemy.SQLAlchemy(session_options=dict(expire_on_commit=False))

FACEBOOK = 'facebook'
EUCABY = 'eucaby'
EUCABY_SCOPES = ['profile', 'history', 'location']

SERVICE_TYPES = [
    (EUCABY, 'Eucaby'),
    (FACEBOOK, 'Facebook')
]


class User(db.Model):

    """User model.

    Notes:
        email can be empty because Facebook user might be authenticated with
        the phone number. "This field will not be returned if no valid email
        address is available."
        See: https://developers.facebook.com/docs/graph-api/reference/v2.2/user
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(50))
    email = db.Column(db.String(75))
    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_superuser = db.Column(db.Boolean, nullable=False, default=False)
    last_login = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now,
        onupdate=datetime.datetime.now)
    date_joined = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    # Timezone offset in minutes.
    #   Example: -420 timezone_offset is -7 timezone (US/Pacific)
    timezone_offset = db.Column(db.Integer)
    settings = db.relationship('UserSettings', uselist=False, backref='user')

    @classmethod
    def create(cls, **kwargs):
        """Creates user."""
        offset = api_utils.zone2offset(kwargs.get('timezone', 0))
        user = cls(
            username=kwargs['username'],
            first_name=kwargs.get('first_name', ''),
            last_name=kwargs.get('last_name', ''),
            email=kwargs.get('email', ''),
            gender=kwargs.get('gender'),
            timezone_offset=offset)
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def get_by_username(cls, username):
        """Returns user by username or None."""
        return cls.get_by(username=username)

    @classmethod
    def get_by_email(cls, email):
        """Returns user by email or None."""
        return cls.get_by(email=email)

    @classmethod
    def get_by(cls, **filter_params):
        """Returns user by filter parameters or None."""
        filter_params.update(dict(is_active=True))
        return cls.query.filter_by(**filter_params).first()

    @property
    def name(self):
        return u'{} {}'.format(self.first_name, self.last_name)

    def to_dict(self, timezone_offset=None):
        date_joined = utils_date.timezone_date(
            self.date_joined, timezone_offset)
        return dict(
            username=self.username, name=self.name, first_name=self.first_name,
            last_name=self.last_name, gender=self.gender, email=self.email,
            date_joined=date_joined)


class UserSettings(db.Model):

    """User settings model."""
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    # One to one relationship with User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    settings = db.Column(db.Text)  # Settings in json format

    @classmethod
    def get_or_create(cls, user_id, commit=False):
        """Returns user settings object or creates a new one."""
        obj = cls.query.filter_by(user_id=user_id).first()
        if not obj:
            obj = cls(user_id=user_id)
            # By default, the new object doesn't persist data
            if commit:
                db.session.add(obj)
                db.session.commit()
        return obj

    def update(self, params, commit=True):
        """Updates user settings."""
        if params is None:  # Only way to reset settings
            self.settings = None
        else:
            settings = self.to_dict()
            for k, v in params.items():
                settings[k] = v
            self.settings = flask.json.dumps(settings)
        if commit:
            db.session.add(self)
            db.session.commit()

    def to_dict(self):
        """Returns settings dictionary."""
        return self._json_loads(self.settings) or {}

    def __setattr__(self, key, value):
        """Override settings set attribute."""
        if key == 'settings' and value is not None:  # Can throw exception
            value = flask.json.loads(value) and value
        self.__dict__[key] = value

    @classmethod
    def _json_loads(cls, json_str):
        """Converts json string to dictionary."""
        try:
            return flask.json.loads(json_str)
        except (TypeError, ValueError) as e:
            return None


class Token(db.Model):

    """Bearer token for Facebook or Eucaby."""

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(choice.ChoiceType(SERVICE_TYPES), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User')

    access_token = db.Column(db.String(255), unique=True, nullable=False)
    refresh_token = db.Column(db.String(255), unique=True)
    created_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    updated_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now,
        onupdate=datetime.datetime.now)
    expires = db.Column(db.DateTime, nullable=False)
    scope = db.Column(db.Text)

    @classmethod
    def create_facebook_token(cls, user_id, access_token, expires_seconds):
        """Creates Facebook token."""
        # Note: It doesn't create user
        token = cls(
            service=FACEBOOK, user_id=user_id, access_token=access_token,
            expires=datetime.datetime.now() + datetime.timedelta(
                seconds=expires_seconds))
        db.session.add(token)
        db.session.commit()
        return token

    @classmethod
    def create_eucaby_token(cls, user_id, token):
        """Creates Eucaby token."""
        # Note: It doesn't create user
        token = cls(
            service=EUCABY, user_id=user_id,
            access_token=token['access_token'],
            refresh_token=token['refresh_token'],
            expires=datetime.datetime.now() + datetime.timedelta(
                seconds=token['expires_in']),
            scope=token['scope'])
        db.session.add(token)
        db.session.commit()
        return token

    def update_token(self, token):
        """Refreshes existing token. Doesn't update the refresh_token."""
        # Only Eucaby can be refreshed. Facebook has no way to do that
        self.access_token = token['access_token']
        self.expires = (datetime.datetime.now() +
                        datetime.timedelta(seconds=token['expires_in']))
        db.session.add(self)
        db.session.commit()

    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return []
