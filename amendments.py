from enum import Enum


class Volume(Enum):
	VOLUME_1 = 1
	VOLUME_2 = 2
	VOLUME_3 = 3
	VOLUME_4 = 4

class Subscription(Enum):
	PLANNING = {Volume.VOLUME_1}
	INSTRUMENT = {Volume.VOLUME_2, Volume.VOLUME_3}
	VISUAL = {Volume.VOLUME_4}
