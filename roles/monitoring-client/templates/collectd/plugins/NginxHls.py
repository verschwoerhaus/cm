#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, re, urllib, datetime, itertools, subprocess, collections, collectd
from glob import glob
from urlparse import urlparse

# TODO: read from plugin-config
# http-url to the nginx-rtmp-statsfile
rtmp_stat_urls = []
{% for id in range(0,(nginx_worker_processes | default('2'))) %}
rtmp_stat_urls.append('http://127.0.0.1:900{{ id }}/stats/rtmp')
{% endfor %}


# path to the access-log containing the hls-file-logs
hls_accesslog = '/var/log/nginx/access.log'

# list of hls-playlists
# this controls which hls-streams will be visible in the graphs
# autogenerated by globbing for /tmp/hls/*.m3u8
hls_playlists = glob('/tmp/hls/*.m3u8')

# configured target-size of a fragment
hls_fragment_size = 5 # seconds

# how log should viewers be counted as "live"
# viewer will seem to stay online for that number of seconds, even if they have already switched off
# setting it too low will wipe players out of the statistics which lag behind
# do not set lower then 2×hls_fragment_size seconds; good results can be achieved with 30-120 seconds
hls_fragment_window = 30 # seconds



##### helper methods #####
# see: http://stackoverflow.com/a/260433/1659732
def reversed_lines(file):
	"Generate the lines of file in reverse order."
	part = ''
	for block in reversed_blocks(file):
		for c in reversed(block):
			if c == '\n' and part:
				yield part[::-1]
				part = ''
			part += c
	if part: yield part[::-1]


def reversed_blocks(file, blocksize=4096):
	"Generate blocks of file's contents in reverse order."
	file.seek(0, os.SEEK_END)
	here = file.tell()
	while 0 < here:
		delta = min(blocksize, here)
		here -= delta
		#print "read block from {0} to {1}".format(here, here+delta)
		file.seek(here, os.SEEK_SET)
		yield file.read(delta)


# see: http://stackoverflow.com/a/4080021/1659732
def parse_logdate(datestr):
	"Parse a strictly formatted Date from a Common-Format-Logfile into a datetime-object (doing it manuall is faster then strptime)"

	month_abbreviations = {
		'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
		'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
		'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
	}

	year = int(datestr[7:11])
	month = month_abbreviations[datestr[3:6]]
	day = int(datestr[0:2])
	hour = int(datestr[12:14])
	minute = int(datestr[15:17])
	second = int(datestr[18:20])

	return datetime.datetime(year, month, day, hour, minute, second)


def filebasename(path):
	"Return the filename without extension from a given path"
	return os.path.splitext(os.path.basename(path))[0]

##### numbercrunching methods #####
def list_hls_streams():
	"List all configured hls-streams"
	# load list of known streams from the statefile
	known_hls_streams = load_streams_from_statefile('hls')

	# iterate over all configured playlists
	for playlist in hls_playlists:
		known_hls_streams[ urlparse(playlist).path ] = True

	# save list of known streams to statefile
	return save_streams_to_statefile('hls', known_hls_streams)


def count_hls_viewers():
	"Count the number of live-viewer for each configured and available hls-stream"
	# the hls-statistics algorithm works as folows
	# - read from the m3u8-playlist and find the fragment which was played hls_fragment_window-seconds ago
	#   fragment number hls_fragment_window / hls_fragment_size
	#
	# - read all lines from the access-log which concern the last hls_fragment_window×2 seconds
	#   the ×2 gives us a little buffer because not all fragments are exactly hls_fragment_size-seconds long
	#   and clocks may diverge
	#
	# - count the number of occurences of the fragment-filename in there relevant log-lines
	#   (as each client only loads each fragement once, this gives us a exact number of viewers that have
	#   been watching the stream hls_fragment_window-seconds ago

	# index of the fragemnt-name we're interested in (count from bottom to top in the m3u8-playlist)
	hls_fragment_threshold = hls_fragment_window / hls_fragment_size

	interesting_segments = {}
	for playlist in hls_playlists:
		# try to open the file
		try:
			with open(playlist) as f:
				# instanciate a generator that iterates lines in the file in inverse order
				lines_generator = reversed_lines(f)

				# wrap in an iterator that only passes non-empty- and non-comment-lines
				interesting_lines = itertools.ifilter(lambda line: line != "\n" and line[0] != '#', lines_generator)

				# wrap in an iterator that only passes the hls_fragment_threshold'th interested line
				last_interesting_lines = itertools.islice(interesting_lines, hls_fragment_threshold, hls_fragment_threshold+1)

				# fetch that single line and store it
				try:
					interesting_segments[ filebasename(playlist) ] = urlparse( last_interesting_lines.next().strip() ).path
				except StopIteration:
					# not enough segments in playlist for a useful analysis
					continue
		except IOError:
			# no, can't read it, ignore that file
			continue

	#print interesting_segments

	# regex to parse interesting parts of ngix access-log
	exp = '^([^ ]+) ([^ ]+) ([^ ]+) \[([^\]]+)\] "([A-Z]+) ([^ "]+) HTTP\/1.[01]" [0-9]{3}'

	# compare timestamp
	now = datetime.datetime.today()

	# viewer-count per stream
	viewer_counts = collections.Counter()

	# open the access-log
	with open(hls_accesslog) as f:
		# read through the lines backwards
		for line in reversed_lines(f):
			# parse line by line
			match = re.match(exp, line)
			if not match:
				break

			(ip, ident, username, tstamp, method, path) = match.groups()

			# parse date
			tstamp = parse_logdate(tstamp)

			# calculate number of seconds this record is old
			age = int((now - tstamp).total_seconds())

			#print path, tstamp, age

			# quit parsing when we reached the end of our window
			# to cater for frageements that5 are not exactly hls_fragment_size-seconds long,
			# we keep on reaading until we hit twice our window length. this gives us enough buffer
			if age > hls_fragment_window * 2:
				break

			# test the filename against all fragement-filenames we're intérested in
			for stream, segment in interesting_segments.iteritems():
				if segment == path:
					# and count one up for that stream
					viewer_counts[ urlparse(stream).path ] += 1

	return viewer_counts

def read(data=None):
	for stream, viewer in count_hls_viewers().items():
		vl = collectd.Values(plugin='hls', type='users', type_instance=stream, values=[viewer])
		vl.dispatch()

collectd.register_read(read);
