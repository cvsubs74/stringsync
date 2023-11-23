import enum


class ActivityType(enum.Enum):
    LOG_IN = ("Log In", "logged in", "🔓")
    LOG_OUT = ("Log Out", "logged out", "🔒")
    PLAY_TRACK = ("Play Track", "played a track", "▶️")
    UPLOAD_RECORDING = ("Upload Recording", "uploaded a recording", "🎤")
    REGISTER_TUTOR = ("Register Tutor", "registered a tutor", "👨‍🏫")
    REGISTER_SCHOOL = ("Register School", "registered a school", "🏫")
    POST_MESSAGE = ("Post Message", "posted a message", "✉️")
    CREATE_TRACK = ("Create Track", "has created a track", "🎵")
    CREATE_ASSIGNMENT = ("Create Assignment", "has created an assignment for you", "📝")
    REVIEW_SUBMISSION = ("Review Submission", "has reviewed your submissions", "🔍")

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if member.value == value:
                return member

    @property
    def value(self):
        return self._value_[0]

    @property
    def message(self):
        return self._value_[1]

    @property
    def icon(self):
        return self._value_[2]
