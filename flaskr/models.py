import enum
from datetime import date, datetime

from flask_login import UserMixin
from itsdangerous import TimedSerializer
from itsdangerous.exc import BadTimeSignature, SignatureExpired
from sqlalchemy.orm import defaultload
from timeago import format

from flaskr import app, db, login_manager


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# defining enum
class Role(enum.Enum):
    GENERAL = "general"
    HOST = "host"
    ADMIN = "admin"


class ComplainCategory(enum.Enum):
    CHEATER = "cheater"
    SCAMMER = "scammer"
    HARASSMENT = "harassment"
    OTHER = "other"


# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    verified_code = db.Column(db.String)
    is_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.Enum(Role), nullable=False)
    profile = db.relationship("Profile", backref="user", uselist=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(
        self, email: str, password: str, verified_code: str, role: str
    ) -> None:
        self.email = email
        self.password = password
        self.verified_code = verified_code
        self.role = role

    def get_joindate(self):
        return self.created_at.strftime("%B, %Y")

    def get_reset_token(self):
        # https://stackoverflow.com/questions/46486062/the-dumps-method-of-itsdangerous-throws-a-typeerror
        serializer = TimedSerializer(app.config["SECRET_KEY"], "confirmation")
        return serializer.dumps(self.id)

    @staticmethod
    def verify_reset_key(id: int, token: str, max_age=1800):
        # 1800 seconds means 30 minutes
        serializer = TimedSerializer(app.config["SECRET_KEY"], "confirmation")
        try:
            result = serializer.loads(token, max_age=max_age)
        except SignatureExpired:
            return {
                "is_authenticate": False,
                "message": "Token is expired! Please re-generate the token.",
            }
        except BadTimeSignature:
            return {"is_authenticate": False, "message": "Token is not valid."}
        if result != id:
            return {
                "is_authenticate": False,
                "message": "Token is not valid for this user.",
            }
        return {"is_authenticate": True, "message": "Password successfully changed."}


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(15), nullable=False)
    last_name = db.Column(db.String(15), nullable=False)
    date_of_birth = db.Column(db.DateTime, nullable=False)
    gender = db.Column(db.String, nullable=False)
    profile_photo = db.Column(
        db.String, default="/images/default/ProfilePhotos/default.png"
    )
    cover_photo = db.Column(
        db.String, default="/images/default/CoverPhotos/default.png"
    )
    rating = db.Column(db.Float, default=0.0)
    bio = db.Column(db.String(500))
    nid_number = db.Column(db.String(11))
    banned = db.relationship("AccountRestriction",
                             backref="profile", uselist=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    hosted_events = db.relationship("Event", backref="host")
    joined_events = db.Column(db.ARRAY(db.Integer), default=[])
    pending_events = db.Column(db.ARRAY(db.Integer), default=[])
    declines = db.relationship("Decline", backref="profile")
    pending_payments = db.relationship("PaymentPending", backref="profile")
    pending_req = db.relationship(
        "PromotionPending", backref="profile", uselist=False)
    notifications = db.relationship("Notification", backref="profile")
    message_sent = db.relationship("Message", backref="sender")
    complains = db.relationship("Complain", backref="complained_by")
    logs = db.relationship("Log", backref="profile")
    profile_bookmarks = db.Column(db.ARRAY(db.Integer), default=[])
    event_bookmarks = db.Column(db.ARRAY(db.Integer), default=[])
    social_links = db.relationship(
        "SocialConnection", backref="profile", uselist=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(
        self,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        gender: str,
        user_id: int,
    ) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.user_id = user_id

    def get_fullname(self):
        return f"{self.first_name} {self.last_name}"

    def unban(self):
        db.session.delete(self.banned)
        db.session.commit()

    def is_banned(self):
        if not self.banned:
            return False
        return True

    def total_unreaded_notifications(self):
        count = 0
        for i in range(len(self.notifications)):
            if not self.notifications[i].is_readed:
                count = count + 1
        return count

    def is_event_bookmarked(self, event_id: int):
        if self.event_bookmarks:
            for id in self.event_bookmarks:
                if id == event_id:
                    return True
        return False


class SocialConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    facebook = db.Column(db.String)
    twitter = db.Column(db.String)
    github = db.Column(db.String)
    linkedin = db.Column(db.String)
    website = db.Column(db.String)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(
        self,
        facebook: str,
        twitter: str,
        github: str,
        linkedin: str,
        website: str,
        profile_id: int,
    ) -> None:
        self.facebook = facebook
        self.twitter = twitter
        self.github = github
        self.linkedin = linkedin
        self.website = website
        self.profile_id = profile_id


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String, nullable=False)
    place_name = db.Column(db.String(100), nullable=False)
    event_time = db.Column(db.DateTime, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    night = db.Column(db.Integer, nullable=False)
    fee = db.Column(db.Integer, nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    members = db.Column(db.ARRAY(db.Integer), default=[])
    chat_room = db.relationship("Message", backref="event")
    plans = db.Column(db.ARRAY(db.String), default=[])
    photos = db.Column(db.ARRAY(db.String), default=[])
    cover_photo = db.Column(
        db.String, default="/images/default/CoverPhotos/event-default.png"
    )
    is_open = db.Column(db.Boolean, default=True)
    max_member = db.Column(db.Integer, nullable=False)
    pending_members = db.Column(db.ARRAY(db.Integer), default=[])
    pending_payments = db.relationship("PaymentPending", backref="event")
    hotel_name = db.Column(db.String(150))
    hotel_weblink = db.Column(db.String)
    declines = db.relationship("Decline", backref="event")
    logs = db.relationship("Log", backref="event")
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(
        self,
        title: str,
        description: str,
        place_name: str,
        event_time: datetime,
        day: int,
        night: int,
        fee: int,
        host_id: int,
        cover_photo: str,
        max_member: int,
        hotel_name: str,
        hotel_weblink: str,
        plans=[],
        photos=[],
    ) -> None:
        self.title = title
        self.description = description
        self.place_name = place_name
        self.event_time = event_time
        self.day = day
        self.night = night
        self.fee = fee
        self.host_id = host_id
        if cover_photo:
            self.cover_photo = cover_photo
        self.max_member = max_member
        if hotel_name:
            self.hotel_name = hotel_name
        if hotel_weblink:
            self.hotel_weblink = hotel_weblink
        self.plans = plans
        self.photos = photos

    def get_start_date_time_str(self):
        return self.event_time.strftime("%b %d, %Y at %H:%M GMT+6")

    def get_start_date(self):
        return self.event_time.strftime("%b %d, %Y")

    def get_start_time(self):
        return self.event_time.strftime("%I:%M %p")

    def event_status(self):
        if self.event_time < datetime.utcnow() or not self.is_open:
            return {
                "message": "Registration closed",
                "category": "danger",
                "status": False
            }
        return {
            "message": "Registration ongoing",
            "category": "primary",
            "status": True
        }

    def is_profile_going(self, profile_id: int) -> bool:
        return profile_id in self.members

    def is_profile_pending(self, profile_id: int) -> bool:
        for pending_payment in self.pending_payments:
            if pending_payment.profile.id == profile_id:
                return True
        return False

    def get_memebers(self) -> list:
        list_of_members = []
        for members_id in self.members:
            list_of_members.append(Profile.query.get(members_id))
        return list_of_members

    def add_memebers(self, profile_id: int):
        list_of_members = []
        for members_id in self.members:
            list_of_members.append(members_id)
        list_of_members.append(profile_id)
        self.members = list_of_members
        db.session.commit()

    def add_photo(self, file_path):
        list_of_photos = []
        for path in self.photos:
            list_of_photos.append(path)
        list_of_photos.append(file_path)
        self.photos = list_of_photos
        db.session.commit()

    def get_photos(self) -> list:
        list_of_photos = []
        for path in self.photos:
            list_of_photos.append(path)
        return list_of_photos


class Complain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)
    category = db.Column(db.Enum(ComplainCategory), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    complain_for = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(
        self,
        text: str,
        complain_category: ComplainCategory,
        complained_by: int,
        complain_for: int,
    ) -> None:
        self.text = text
        self.category = complain_category
        self.profile_id = complained_by
        self.complain_for = complain_for

    def get_complain_for(self):
        return Profile.query.get(self.complain_for)

    def get_days_ago(self):
        return format(self.created_at, datetime.utcnow())


class PaymentPending(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    trnx_id = db.Column(db.Integer, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(self, trnx_id: str, profile_id: int, event_id: int) -> None:
        self.trnx_id = trnx_id
        self.profile_id = profile_id
        self.event_id = event_id

    def approve(self):
        db.session.delete(self)
        db.session.commit()


class Decline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    message = db.Column(db.String, nullable=False)

    def __init__(self, message: str, profile_id: int, event_id: int) -> None:
        self.message = message
        self.profile_id = profile_id
        self.event_id = event_id


class PromotionPending(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(self, profile_id: int) -> None:
        self.profile_id = profile_id

    def approved(self):
        self.is_approved = True
        profile = Profile.query.get(self.profile_id)
        profile.user.role = Role.HOST
        db.session.delete(self)
        db.session.commit()


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(250), nullable=False)
    link = db.Column(db.String, nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    is_readed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(self, message: str, link: str, profile_id: int) -> None:
        self.message = message
        self.link = link
        self.profile_id = profile_id

    def mark_read(self):
        self.is_readed = True
        db.session.commit()

    def times_ago(self):
        return format(self.created_at, datetime.utcnow())


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_text = db.Column(db.String)
    message_photo = db.Column(db.String)
    sender_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(self, text: str, photo: str, profile_id: int, event_id: int) -> None:
        self.message_text = text
        self.message_photo = photo
        self.sender_id = profile_id
        self.event_id = event_id


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    activity = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(self, activity: str, profile_id: int, event_id: int) -> None:
        self.activity = activity
        self.profile_id = profile_id
        self.event_id = event_id


class AccountRestriction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expire_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String, nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(self, expire_date: datetime, reason: str, profile_id: int) -> None:
        self.expire_date = expire_date
        self.reason = reason
        self.profile_id = profile_id

    def days_left(self):
        return self.expire_date.strftime("%d %B, %Y")
