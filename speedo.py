from moviepy.editor import VideoFileClip, concatenate_videoclips
import youtube_dl
import pprint
from datetime import datetime


# TODO: Ensure the video has subtitles (add a logger/hook?)
# TODO: Add some heuristic so the video changes closer to where the phrase is actually said (Maybe based off of # chars)
# https://github.com/rg3/youtube-dl/blob/master/README.md#embedding-youtube-dl
# https://zulko.github.io/moviepy/ref/videofx/moviepy.video.fx.all.speedx.html?highlight=speed


# Formats strings in a consistent manner
def fmt(string):
    exclude = ['.', ':', ';', '!', ',', '?']
    return ''.join(ch for ch in string if ch not in exclude).lower().replace('\n', ' ')


def dl_hook(d):
    print 'ASDFASDFASDF'
    print d['filename']


video_url = 'https://www.youtube.com/watch?v=79DijItQXMM'
phrase = 'You\'re welcome'
phrase = fmt(phrase)

# Downloads the video and subtitles
ydl_opts = {'writesubtitles': True,
            'outtmpl': 'video.%(ext)s',
            'format_spec': 'mp4',
            'format': 'mp4'}

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([video_url])

duration = VideoFileClip("video.mp4").duration

# Reads the subtitles into the string
with open('video.en.vtt', 'r') as subs_file:
    subs_str = subs_file.readlines()[4:]

# Splits the subtitles into a 2d array
subs = dict()
key = ''
for line in subs_str:
    if line[0].isdigit():
        # Extracts the timestamps
        start_time_str = line[0:line.find(' ')]
        end_time_str = line[line.find('>') + 2: line.find(' ', line.find('>') + 2)]

        # Converts them to milliseconds. Datetime is weird so you have to subtract the timestamp from a reference point
        # in order to extract the seconds passed
        base_time = datetime(1900, 1, 1)
        start_time = (datetime.strptime(start_time_str, '%H:%M:%S.%f') - base_time).total_seconds()
        end_time = (datetime.strptime(end_time_str, '%H:%M:%S.%f') - base_time).total_seconds()

        # Assigns the given start,end time as the current key to add the following lines to in the dict
        key = (start_time, end_time)
        subs[(start_time, end_time)] = ''
    elif line != '\\n':
        subs[key] += fmt(line)

pprint.pprint(subs)

# Creates an array of how often the phrase occurs in a given time span
# TODO: This only works for single words, fix for phrases
instances = []
for time, line in subs.items():
    # Gets the indices of occurrences
    # indices = [i for i, s in enumerate(line.split()) if s == phrase]
    indices = []
    for i in range(len(line) - len(phrase)):
        if line[i:i+len(phrase)] == phrase:
            indices += [i]

    # Adds the appropriate number of instances
    instances.append((time, len(indices)))

# Sorts from smallest to biggest
instances.sort(key=lambda tup: tup[0][0])

# Adds the beginning and end of the clip since they won't have subtitles
instances.insert(0, ((0, instances[0][0][0]), 0))
instances.insert(len(instances), ((instances[len(instances)-1][0][1], duration), 0))

print instances

# Conjoins and speeds the clips
# https://zulko.github.io/moviepy/getting_started/compositing.html
speed_multiplier = 1.1
clip_arr = []
phrase_count = 0  # Number of times the phrase has been said so far
clip = VideoFileClip("video.mp4")

for time_span, num_occur in instances:
    start, end = time_span
    phrase_count += num_occur
    clip_arr.append(clip.subclip(start, end).speedx(factor=speed_multiplier ** phrase_count))

# Combines and writes the video
final_clip = concatenate_videoclips(clip_arr)
final_clip.write_videofile("output.mp4", preset='ultrafast')
