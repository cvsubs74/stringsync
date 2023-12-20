from enum import Enum


class BaseBadge(Enum):
    def __init__(self, description, threshold, criteria, message, stats_info):
        self._value_ = description
        self.description = description
        self.threshold = threshold
        self.criteria = criteria
        self.message = message
        self.stats_info = stats_info

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if member.value == value:
                return member

    @property
    def value(self):
        return self._value_

    def format_stats_info(self, value):
        return self.stats_info.format(value=value)


class UserBadges(BaseBadge):
    FIRST_NOTE = (
        "First Note", 1,
        "Celebrate your start by uploading your first recording.",
        "You've taken the **first step** on a fantastic **musical journey**!",
        "You made your first recording!"
    )
    RISING_STAR = (
        "Rising Star", 3,
        "Shine bright with your emerging talent.",
        "Your **talent** is **shining** through, keep climbing to new **heights**!",
        "You've achieved the Rising Star badge by showcasing your talent!"
    )
    ROCKSTAR = (
        "Rockstar", 5,
        "Take center stage with your impressive skills.",
        "You're **rocking** the world with your **skills**!",
        "You've reached Rockstar status with your impressive skills!"
    )
    TWO_DAY_STREAK = (
        "2 Day Streak", 2,
        "Keep the rhythm! Practice for 2 consecutive days.",
        "You're building a **solid rhythm**, **two days** strong!",
        "You maintained a 2-day practice streak!"
    )
    THREE_DAY_STREAK = (
        "3 Day Streak", 3,
        "Harmonize your week with a 3-day practice streak.",
        "**Three days** in **harmony**, your **dedication** is music to our ears!",
        "You've kept up a 3-day practice streak!"
    )
    FIVE_DAY_STREAK = (
        "5 Day Streak", 5,
        "Show your dedication with a streak of practicing for 5 days.",
        "**Five** fantastic days of **dedication**! You're on a roll!",
        "You've impressively maintained a 5-day practice streak!"
    )
    SEVEN_DAY_STREAK = (
        "7 Day Streak", 7,
        "Demonstrate your commitment with a full week of practice.",
        "A **full week** of **commitment**! You're truly setting the stage.",
        "You've completed a commendable 7-day practice streak!"
    )
    TEN_DAY_STREAK = (
        "10 Day Streak", 10,
        "Set the bar high with a 10-day practice streak.",
        "**Ten days** of **excellence**! Your commitment is unmatched!",
        "You've achieved an incredible 10-day practice streak!"
    )
    WEEKLY_TRAILBLAZER = (
        "Trailblazer", 1,
        "Lead the pack by conquering the most recommended tracks in a week.",
        "You're **blazing a trail** with your **rapid progress**!",
        "You've knocked off the most recommended tracks this week, earning the Weekly Trailblazer badge!"
    )
    WEEKLY_MAX_PRACTICE_MINUTES = (
        "Practice Champ", 60,
        "Top the charts with the most practice minutes in a week.",
        "Your **practice efforts** are off the charts, truly **inspiring**!",
        "You practiced for **{value} minutes** this week, topping the charts!"
    )
    WEEKLY_MAX_RECORDING_MINUTES = (
        "Sound Sorcerer", 10,
        "Cast a spell by recording the most minutes in a week.",
        "You've **cast** a spellbinding **performance** with your **recordings**!",
        "You've recorded for **{value} minutes** this week as the **Sound Sorcerer**!"
    )
    WEEKLY_MAX_DAILY_PRACTICE_MINUTES = (
        "Practice Prodigy", 45,
        "Showcase your daily diligence in practice.",
        "Your **daily diligence** is the key to your **prodigious progress**!",
        "You're a **Practice Prodigy** with **{value} minutes** of practice on a single day!"
    )
    WEEKLY_MAX_RECORDINGS = (
        "Recording Kingpin", 5,
        "Rule the studio by making the most recordings in a week.",
        "You are **ruling the studio** with your **recordings** and a true **kingpin**!",
        "You made **{value} recordings** this week, earning you the **Recording Kingpin** badge!"
    )
    WEEKLY_MAX_SCORER = (
        "Melody Master", 40,
        "Hit the high score by earning the most points in a week.",
        "You are a **melody master**! Your **high scores** resonate with **excellence**.",
        "You've earned the **Melody Master** badge with a high score of **{value} points**!"
    )
    WEEKLY_MAX_TRACK_RECORDER = (
        "Track Titan", 3,
        "Be prolific! Record on the most number of different tracks.",
        "Your **versatility** shines as a **Track Titan**!",
        "Recording on **{value}** different **tracks** makes you a **Track Titan**!"
    )
    WEEKLY_MAX_BADGE_EARNER = (
        "Badge Baron", 3,
        "Be the ultimate achiever by earning a variety of badges.",
        "You are a **Baron of Badges**! Your collection showcases your diverse **talents**.",
        "You've earned **{value}** different **badges**, making you a true **Badge Baron**!"
    )
    MONTHLY_MAX_PRACTICE_MINUTES = (
        "Monthly Star", 250,
        "Be the monthly highlight with your practice minutes.",
        "Your **dedication** this month makes you a **Shining Star**!",
        "Your **{value} minutes** of practice this month have made you a **Monthly Star**!"
    )
    MONTHLY_MAX_RECORDING_MINUTES = (
        "Mic Champ", 30,
        "Be the champion of the mic with your monthly recordings.",
        "You are the **Champion of the Mic**! Your **recordings** set the standard.",
        "With **{value} minutes** of recordings this month, you're the undisputed **Mic Champ**!"
    )


class TrackBadges(BaseBadge):
    FAST_LEARNER = (
        "Fast Learner", 1,
        "Master a new track quicker than the rest.",
        "You're a **quick learner**, mastering **tracks** at impressive speed!",
        "You mastered a new track in record time!"
    )
    SONG_BIRD = (
        "Song Bird", 3,
        "Consistently hit the right notes in your performances.",
        "Your **ability** to hit the **right notes** is simply **melodious**!",
        "Your pitch-perfect performance earned you the Song Bird badge!"
    )
    MAESTRO = (
        "Maestro", 5,
        "Demonstrate exceptional skill and control in your performances.",
        "Conduct your **performance** with the skill of a true **Maestro**!",
        "Your exceptional performance skills have earned you the Maestro badge!"
    )
    PERFECT_PITCH = (
        "Perfect Pitch", 2,
        "Display an excellent sense of pitch in your recordings.",
        "Your **pitch** is **perfect**, hitting **every note** just right!",
        "Your pitch-perfect recordings have earned you the Perfect Pitch badge!"
    )
    PERFECT_BEAT = (
        "Perfect Beat", 3,
        "Keep the rhythm and timing flawless in your performances.",
        "You've got the **beat**! Your sense of **rhythm** is unmatched.",
        "Your impeccable timing has earned you the Perfect Beat badge!"
    )
    MUSIC_WIZARD = (
        "Music Wizard", 4,
        "Blend creativity and skill to create magical performances.",
        "Like a **wizard**, you weave **magic** into your music!",
        "Your creative and skillful performances make you a Music Wizard!"
    )
    VIRTUOSO = (
        "Virtuoso", 5,
        "Reach the pinnacle of musical skill and artistry.",
        "Your **performances** reflect the skill of a true **Virtuoso**!",
        "Your artistry and skill have earned you the Virtuoso badge!"
    )
    PRACTICE_MAKES_PERFECT = (
        "Practice Makes Perfect", 10,
        "Demonstrate dedication and improvement through consistent practice.",
        "Your **dedication** to **practice** shows in your ever-improving performances!",
        "Your commitment to practice has rightfully earned you the Practice Makes Perfect badge!"
    )
