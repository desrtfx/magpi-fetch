#!/usr/bin/python3
# (c) 2017 by dark_skeleton / d-rez

from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import datetime
import yaml
import dropbox
import os
import sys
import argparse
import my_secrets

#----------------------------------------------
dropbox_token = my_secrets.dropbox_api_token
dropbox_path = my_secrets.dropbox_path

magpi_url = "https://www.raspberrypi.org/magpi/issues/"
# target_dir   = "/tmp" # not needed, we're not locally saving the file anymore
config_file = os.path.dirname(os.path.realpath(__file__)) + "/config.yaml"
log_file = os.path.dirname(os.path.realpath(__file__)) + "/magpi.log"
#----------------------------------------------

known_issues = {}

# Easy args support
parser = argparse.ArgumentParser(description='Process some args')
parser.add_argument('--log_file', action='store_true',
                    help="log to %s instead of stdout" % log_file)
parser.add_argument('--full', action='store_true',
                    help="Download all issues. Existing files will be redownladed with new name.")
parser.add_argument('--force', action='store_true',
                    help="Force overwrite existing issues. Includes '--full'.")
parser.add_argument('--debug', action='store_true')
args = parser.parse_args()

if args.log_file is True:
    # Redirect stdout to a file internally
    sys.stdout = open(log_file, 'a')
    print(datetime.now(), "\n", "-" * 80)

try:
    stream = open(config_file, 'r')
    known_issues = yaml.safe_load(stream)
    stream.close()
except:
    print("Could not load config file")
    # We don't really care if this fails

dbx = dropbox.Dropbox(dropbox_token)
print("Authed Dropbox as %s" % dbx.users_get_current_account())

# This doesn't work well in my case since Pocketbook also syncs and
# deletes deleted items

# print("Cleaning up old uploads...")
# old_ups = dbx.files_list_folder(dropbox_path).entries
#
# for old_issue in old_ups:
#   if old_issue.name in map((lambda x: x.split('/')[-1]), known_issues.values()):
#     print("  Deleting " + old_issue.name)
#     dbx.files_delete(old_issue.path_lower)


print("Loading list of MagPi issues...")
content = urlopen(magpi_url).read()
soup = BeautifulSoup(content, "html5lib")
issues = soup.select(".modal div.issue-wrap")

for issue in issues:
    title = str(issue.p.string)
    download_btn = issue.select_one("div a")
    if download_btn is None:
        continue
        # some issues have no download links
    download_link = download_btn.get("href")

    if args.debug:
        print("  Found %s: %s" % (title, download_link))

    if title not in known_issues.keys() or args.force or args.full:
        known_issues[title] = download_link
        filename = download_link.split('/')[-1]
        filepath = dropbox_path + "/" + filename

        # ----
        # This part is only useful if you want to save the file before uploading.
        # Asking Dropbox to fetch the URL is faster and easier and takes a couple
        # of seconds only. You can still use this if you want

        # print("    Downloading %s: %s" % (title, download_link))
        # binary = urlopen(download_link).read()

        # print("    Uploading..."
        # dbx.files_upload(binary, "%s/%s" % (dropbox_path, filename))
        # ----

        print("    Asking Dropbox to fetch %s to %s" %
              (download_link, filepath))
        if args.full:
            fdl = dbx.files.WriteMode('add', None)
        elif args.force:
            fdl = dbx.files.WriteMode('overwrite', None)
        res = dbx.files_save_url(filepath, download_link)
        print("      JobID: " + res.get_async_job_id())
        if args.debug:
            print(res)

print("All done!")

try:
    stream = open(config_file, 'w')
    yaml.safe_dump(known_issues, stream, default_flow_style=False)
    stream.close()
except:
    print("Could not save config file")
