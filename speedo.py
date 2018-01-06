from moviepy.editor import VideoFileClip, concatenate_videoclips
import youtube_dl
import pprint
import os
from datetime import datetime


# TODO: Ensure the video has subtitles (add a logger/hook?)
# TODO: Add some heuristic so the video changes closer to where the phrase is actually said (Maybe based off of # chars)
# https://github.com/rg3/youtube-dl/blob/master/README.md#embedding-youtube-dl
# https://zulko.github.io/moviepy/ref/videofx/moviepy.video.fx.all.speedx.html?highlight=speed

# A logger object for youtube-dl
class Logger(object):
    def warning(self, msg):
        if 'subtitles' in msg:
            print 'Error: ' + msg
            print 'Please choose a new video'
            print 'Quitting'
            exit(2)

    def error(self, msg):
        print 'error:' + msg

    def debug(self, msg):
        pass


# Formats strings in a consistent manner
def fmt(string):
    exclude = ['.', ':', ';', '!', ',', '?', '"']
    return ''.join(ch for ch in string if ch not in exclude).lower().replace('\n', ' ').strip()


video_url = 'https://www.youtube.com/watch?v=n5uujMb_hbo'
phrase = 'bellybutton'

phrase = fmt(phrase)
video_id = video_url[video_url.find('=') + 1:]
vid_extension = 'mp4'
video_name = video_id + '.' + vid_extension
subs_name = video_id + '.en.vtt'
output_name = "output.mp4"

# Downloads the video and subtitles
print 'Downloading video...'
ydl_opts = {'writesubtitles': True,
            'outtmpl': video_id + '.%(ext)s',
            'format_spec': vid_extension,
            'format': vid_extension,
            'logger': Logger()}

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([video_url])

print 'Finished downloading'

duration = VideoFileClip(video_name).duration

# Reads the subtitles into the string

with open(subs_name, 'r') as subs_file:
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

    # If the line has dialogue
    elif line != '\\n' and not line[0] in ['*', '[', '(']:
        subs[key] += line

# Formats all of the lines to remove noise
for key, val in subs.items():
    subs[key] = fmt(val)

pprint.pprint(subs)

# Creates an array of where the phrase occurs
instances = []
for time, line in subs.items():
    # Gets the indices of occurrences
    indices = []
    for i in range(len(line) - len(phrase) + 1):
        if line[i:i + len(phrase)] == phrase:
            indices += [i]

    # A rough heuristic to pin down how far into the phrase is said
    for i in indices:
        # The percentage of how far in the line the phrase occurs in
        pos = i / float(len(line))

        # The timestamp the phrase should occur at
        start, end = time
        time_pos = start + (end - start) * pos
        instances.append(round(time_pos, 1))

# Adds the start and end times of the video to create a complete range of how the video speeds up (examine for-loop)
instances += [0, duration]

# Sorts from first to last
instances.sort()

print instances

if len(instances) == 0:
    print 'The phrase did not occur'
    quit(2)

# https://zulko.github.io/moviepy/getting_started/compositing.html
speed_multiplier = 1.1  # An error may occur if this goes over 1.25
clip_arr = []
phrase_count = 0  # Number of times the phrase has been said so far
clip = VideoFileClip(video_name)

# Conjoins and speeds the clips
for i in range(len(instances) - 1):
    start, end = instances[i], instances[i + 1]
    clip_arr.append(clip.subclip(start, end).speedx(factor=speed_multiplier ** i))

# Combines and writes the video
final_clip = concatenate_videoclips(clip_arr)
final_clip.write_videofile(output_name, preset='superfast')

ans = raw_input('Would you like to delete the original files? (y/n)')
if ans == 'y':
    try:
        os.remove(video_name)
        os.remove(subs_name)
    except Exception as e:
        print e