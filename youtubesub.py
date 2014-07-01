# -*- coding: utf-8 -*-
"""
    Youtube Subtitle Downloader downloads subtitles from Youtube videos 
    (if those are present) and convert them to SRT format.

    Usage: youtubesub.py [-h] [-l] [--language LANGUAGE] [--filename FILENAME]
                         [--filetype {srt,xml}]
                         url

    positional arguments:
      url                   URL of the Youtube video

    optional arguments:
      -h, --help            show this help message and exit
      -l, --list            list all available languages
      --language LANGUAGE   the ISO language code
      --filename FILENAME   specify the name of subtitle
      --filetype {srt,xml}  specify the output type of subtitle

    Example:
    python youtubesub.py --filename subtitle --language en http://www.youtube.com/watch?v=5MgBikgcWnY

    :copyright: (c) 2014 by Nguyen Dang Minh (www.minhnd.com)
    :license: BSD, see LICENSE for more details.
"""

import urllib2
import urlparse
import argparse
import sys
import xml.etree.ElementTree as ET


class YoutubeSubDownloader():
    video_id = None
    subtitle = None
    languages = {}

    def __init__(self, url=None):
        self.video_id = self.extractVideoID(url)
        self.languages = self.getAvailableLanguages()
        if self.languages == {}:
            print "There's no subtitle"
            sys.exit()

    def extractVideoID(self, url=None):
        """
        Examples:
        - http://youtu.be/5MgBikgcWnY
        - http://www.youtube.com/watch?v=5MgBikgcWnY&feature=feed
        - http://www.youtube.com/embed/5MgBikgcWnY
        - http://www.youtube.com/v/5MgBikgcWnY?version=3&amp;hl=en_US
        """
        url_data = urlparse.urlparse(url)
        if url_data.hostname == 'youtu.be':
            return url_data.path[1:]
        if url_data.hostname in ('www.youtube.com', 'youtube.com'):
            if url_data.path == '/watch':
                query = urlparse.parse_qs(url_data.query)
                return query['v'][0]
            if url_data.path[:7] == '/embed/':
                return url_data.path.split('/')[2]
            if url_data.path[:3] == '/v/':
                return url_data.path.split('/')[2]
        return None

    def download(self, language, filename, filetype):
        """Download subtitle of the selected language"""
        if language not in self.languages.keys():
            print "Theres's no subtitle in this language"
            sys.exit()
        url = "http://www.youtube.com/api/timedtext?v={0}&lang={1}".format(self.video_id, language)
        self.subtitle = urllib2.urlopen(url)
        if filetype == "srt":
            self.writeSRTFile(filename)
        else:
            self.writeXMLFile(filename)

    def getAvailableLanguages(self):
        """Get all available languages of subtitle"""
        url = "http://www.youtube.com/api/timedtext?v=%s&type=list" % self.video_id
        xml = urllib2.urlopen(url)
        tree = ET.parse(xml)
        root = tree.getroot()
        languages = {}
        for child in root:
            languages[child.attrib["lang_code"]] = child.attrib["lang_translated"]
        return languages

    def list(self):
        """List all available languages of subtitle"""
        for key, value in self.languages.iteritems():
            print key, value

    def writeXMLFile(self, filename=None):
        with open(filename + ".xml", 'w') as f:
            for line in self.subtitle:
                f.write(line)

    def writeSRTFile(self, filename=None):
        tree = ET.parse(self.subtitle)
        root = tree.getroot()
        with open(filename + ".srt", 'w') as f:
            line = 1
            for child in root:
                f.write(self.printSRTLine(line, child.attrib["start"], child.attrib["dur"], child.text.encode('utf-8')))
                line += 1

    def formatSRTTime(self, secTime):
        """Convert a time in seconds (in Google's subtitle) to SRT time format"""
        sec, micro = str(secTime).split('.')
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        return "{:02}:{:02}:{:02},{}".format(h,m,s,micro)

    def printSRTLine(self, line, start, duration, text):
        """Print a subtitle in SRT format"""
        end = self.formatSRTTime(float(start) + float(duration))
        start = self.formatSRTTime(start)
        text = self.convertHTML(text)
        return "{}\n{} --> {}\n{}\n\n".format(line, start, end, text)

    def convertHTML(self, text):
        """A few HTML encodings replacements.
            &#39; to '
        """
        return text.replace('&#39;', "'")


def main():
    try:
        parser = argparse.ArgumentParser(description="Youtube Subtitle Downloader")
        parser.add_argument("url", help="URL of the Youtube video")
        parser.add_argument("-l", "--list", action="store_true", help="list all available languages")
        parser.add_argument("--language", default="en", help="the ISO language code")
        parser.add_argument("--filename", default="subtitle", help="specify the name of subtitle")
        parser.add_argument("--filetype", default="srt", choices=["srt", "xml"], help="specify the output type of subtitle")
        args = parser.parse_args()

        downloader = YoutubeSubDownloader(args.url)
        if args.list:
            print "Available languages:"
            f = downloader.list()
        downloader.download(args.language, args.filename, args.filetype)
    except Exception as e:
        print e


if __name__ == '__main__':
    main()
