import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os
import validators
import re
from ftplib import FTP

# TODO: find a better way to do this
try:
    from . import config
except (ImportError, SystemError):
    import config

import urllib3
urllib3.disable_warnings()


def truncate_path(path, max_len):
    pattern = re.compile(r"/?.*?/")

    for i in range(1, path.count("/")):
        new_path = pattern.sub(".../", path, i)
        if len(new_path) < max_len:
            return new_path
    return ".../" + path.rsplit("/", maxsplit=1)[1] if "/" in path else path


category_map = {

    # Application category
    'bcpio': 'application', 'bin': 'application', 'cdf': 'application',
    'csh': 'application', 'dll': 'application', 'doc': 'application',
    'dot': 'application', 'dvi': 'application', 'eml': 'application',
    'exe': 'application', 'hdf': 'application',
    'man': 'application', 'me': 'application', 'mht': 'application',
    'mhtml': 'application', 'mif': 'application', 'ms': 'application',
    'nc': 'application', 'nws': 'application', 'o': 'application',
    'obj': 'application', 'oda': 'application', 'p12': 'application',
    'p7c': 'application', 'pfx': 'application', 'tr': 'application',
    'ppa': 'application', 'pps': 'application', 'ppt': 'application',
    'ps': 'application', 'pwz': 'application', 'pyc': 'application',
    'pyo': 'application', 'ram': 'application', 'rdf': 'application',
    'roff': 'application', 'sh': 'application', 'so': 'application',
    'src': 'application', 'sv4cpio': 'application', 'sv4crc': 'application',
    't': 'application', 'tcl': 'application', 'tex': 'application',
    'texi': 'application', 'texinfo': 'application', 'ustar': 'application',
    'wiz': 'application', 'wsdl': 'application', 'xlb': 'application',
    'xls': 'application', 'xpdl': 'application', 'xsl': 'application',
    'torrent': 'application', 'rpm': 'application', 'deb': 'application',
    'atr': 'application', 'class': 'application', 'ttf': 'application',
    'img': 'application', 'msi': 'application', 'run': 'application',
    'drpm': 'application', 'udeb': 'application', 'patch': 'application',
    'nes': 'application', 'ebuild': 'application', 'scr': 'application',
    # Text category
    'java': 'text', 'cpp': 'text', 'rb': 'text',
    'bat': 'text', 'latex': 'text', 'xml': 'text',
    'etx': 'text', 'htm': 'text', 'c': 'text',
    'css': 'text', 'csv': 'text', 'html': 'text',
    'js': 'text', 'json': 'text', 'ksh': 'text',
    'pl': 'text', 'pot': 'application', 'py': 'text',
    'h': 'text', 'tsv': 'text', 'rtx': 'text',
    'sgm': 'text', 'sgml': 'text', 'txt': 'text',
    'vcf': 'text', 'pdf': 'text', 'epub': 'text',
    'srt': 'text', 'inc': 'text', 'php': 'text',
    'cbz': 'text', 'docx': 'text', 'mobi': 'text',
    'chm': 'text', 'xlsx': "text", 'djvu': 'text',
    'rtf': 'text', 'log': 'text', 'md': 'text',
    'dsc': 'text', 'info': 'text',
    # Video category
    '3g2': 'video', '3gp': 'video', 'asf': 'video',
    'asx': 'video', 'avi': 'video', 'flv': 'video',
    'swf': 'video', 'vob:': 'video', 'qt': 'video',
    'webm': 'video', 'mov': 'video', 'm1v': 'video',
    'm3u': 'video', 'm3u8': 'video', 'movie': 'video',
    'mp4': 'video', 'mpa': 'video', 'mpe': 'video',
    'mpeg': 'video', 'mpg': 'video', 'mkv': 'video',
    'wmv': 'video', 'm4s': 'video', 'ogv': 'video',
    'm4b': 'video', 'm4v': 'video', 'ts': 'video',

    # Audio category
    'wav': 'audio', 'snd': 'audio', 'mp2': 'audio',
    'aif': 'audio', 'iff': 'audio', 'm4a': 'audio',
    'mid': 'audio', 'midi': 'audio', 'mp3': 'audio',
    'wma': 'audio', 'ra': 'audio', 'aifc': 'audio',
    'aiff': 'audio', 'au': 'audio', 'flac': 'audio',
    'ogg': 'audio', 'oga': 'audio', 'mka': 'video',
    'ac3': 'audio',
    # Image category
    'bmp': 'image', 'gif': 'image', 'jpg': 'image',
    'xwd': 'image', 'tif': 'image', 'tiff': 'image',
    'png': 'image', 'pnm': 'image', 'ras': 'image',
    'ico': 'image', 'ief': 'image', 'pgm': 'image',
    'jpe': 'image', 'pbm': 'image', 'jpeg': 'image',
    'ppm': 'image', 'xpm': 'image', 'xbm': 'image',
    'rgb': 'image', 'svg': 'image', 'psd': 'image',
    'yuv': 'image', 'ai': 'image', 'eps': 'image',
    'bw': 'image', 'hdr': 'image',
    # Archive category
    'ar': 'archive', 'cpio': 'archive', 'shar': 'archive',
    'iso': 'archive', 'lbr': 'archive', 'mar': 'archive',
    'sbx': 'archive', 'bz2': 'archive', 'f': 'archive',
    'gz': 'archive', 'lz': 'archive', 'lzma': 'archive',
    'lzo': 'archive', 'rz': 'archive', 'sfark': 'archive',
    'sz': 'archive', 'z': 'archive', '7z': 'archive',
    's7z': 'archive', 'ace': 'archive', 'afa': 'archive',
    'alz': 'archive', 'apk': 'archive', 'arc': 'archive',
    'arj': 'archive', 'b1': 'archive', 'b6z': 'archive',
    'a': 'archive', 'bh': 'archive', 'cab': 'archive',
    'car': 'archive', 'cfs': 'archive', 'cpt': 'archive',
    'dar': 'archive', 'dd': 'archive', 'dgc': 'archive',
    'dmg': 'archive', 'ear': 'archive', 'gca': 'archive',
    'ha': 'archive', 'hki': 'archive', 'ice': 'archive',
    'jar': 'archive', 'kgb': 'archive', 'lzh': 'archive',
    'lha': 'archive', 'lzx': 'archive', 'pak': 'archive',
    'partimg': 'archive', 'paq6': 'archive', 'paq7': 'archive',
    'paq8': 'archive', 'pea': 'archive', 'pim': 'archive',
    'pit': 'archive', 'qda': 'archive', 'rar': 'archive',
    'rk': 'archive', 'sda': 'archive', 'sea': 'archive',
    'sen': 'archive', 'sfx': 'archive', 'shk': 'archive',
    'sit': 'archive', 'sitx': 'archive', 'sqx': 'archive',
    'tbz2': 'archive', 'tlz': 'archive', 'xz': 'archive',
    'txz': 'archive', 'uc': 'archive', 'uc0': 'archive',
    'uc2': 'archive', 'ucn': 'archive', 'ur2': 'archive',
    'ue2': 'archive', 'uca': 'archive', 'uha': 'archive',
    'war': 'archive', 'wim': 'archive', 'xar': 'archive',
    'xp3': 'archive', 'yz1': 'archive', 'zip': 'archive',
    'zipx': 'archive', 'zoo': 'archive', 'zpaq': 'archive',
    'zz': 'archive', 'xpi': 'archive', 'tgz': 'archive',
    'tbz': 'archive', 'tar': 'archive', 'bz': 'archive',
    'diz': 'archive',
}

colors = {
    "application": "bg-application",
    "text": "bg-text",
    "video": "bg-video",
    "image": "bg-image",
    "audio": "bg-audio",
    "archive": "bg-archive"
}


def get_color(category):
    return colors.get(category, None)


def get_category(extension):
    return category_map.get(extension, None)


def is_valid_url(url):
    if not url.endswith("/"):
        return False

    if not url.startswith(("http://", "https://", "ftp://")):
        return False

    return validators.url(url)


def has_extension(link):
    return len(os.path.splitext(link)[1]) > 0


def is_external_link(base_url, url: str):
    url = urljoin(base_url, url).strip()

    if base_url in url:
        return False
    return True


def is_od(url):
    if not url.endswith("/"):
        print("Url does not end with trailing /")
        return False

    try:
        if url.startswith("ftp://") and config.SUBMIT_FTP:
            ftp = FTP(urlparse(url).netloc)
            ftp.login()
            ftp.close()
            return True
        elif config.SUBMIT_HTTP:
            r = requests.get(url, timeout=30, allow_redirects=False, verify=False)
            if r.status_code != 200:
                # print("No redirects allowed!")
                return False
            soup = BeautifulSoup(r.text, "lxml")

            external_links = sum(1 if is_external_link(url, a.get("href")) else 0 for a in soup.find_all("a"))
            link_tags = len(list(soup.find_all("link")))
            script_tags = len(list(soup.find_all("script")))

            if external_links > 11:
                # print("Too many external links!")
                return False

            if link_tags > 5:
                # print("Too many link tags!")
                return False

            if script_tags > 7:
                # print("Too many script tags!")
                return False

            return True

    except Exception as e:
        # print(e)
        return False


def has_parent_dir(url):

    parsed_url = urlparse(url)

    if parsed_url.path == "/":
        return False

    parent_url = urljoin(url, "../")
    try:
        r = requests.get(parent_url, timeout=30, allow_redirects=False, verify=False)
        if r.status_code != 200:
            return False
        soup = BeautifulSoup(r.text, "lxml")

        for anchor in soup.find_all("a"):
            if anchor.get("href") and anchor.get("href").endswith("/") and urljoin(parent_url, anchor.get("href")) == url:
                # The parent page exists, and has a link to the child directory
                return is_od(parent_url)

    except:
        return False

    # Parent page exists, but does not have a link to the child directory
    return False


def get_top_directory(url):
    if url.startswith("ftp://"):
        return url

    while has_parent_dir(url):
        url = urljoin(url, "../")
    return url
