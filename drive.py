"""Simple command-line sample for the Google Drive API.

Command-line application that retrieves the list of files in google drive.

Usage:
    $ python drive.py

You can also get help on all the command-line flags the program understands
by running:

    $ python drive.py --help

To get detailed log output run:

    $ python drive.py --logging_level=DEBUG
"""

__author__ = '''viky.nandha@gmail.com (Vignesh Nandha Kumar); 
                jeanbaptiste.bertrand@gmail.com (Jean-Baptiste Bertrand)
                sti.beshev@gmail.com'''

import gflags, httplib2, logging, os, pprint, sys, re, time, pytz

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError, flow_from_clientsecrets
from oauth2client.tools import run_flow
from tzlocal import get_localzone
from datetime import datetime


FLAGS = gflags.FLAGS

# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>

CLIENT_SECRETS = "client_secrets.json"

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

%s

with information from the APIs Console <https://code.google.com/apis/console>.

""" % os.path.join(os.path.dirname(__file__), CLIENT_SECRETS)

# Set up a Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/drive',
    message=MISSING_CLIENT_SECRETS_MESSAGE)


# The gflags module makes defining command-line options easy for
# applications. Run this program with the '--help' argument to see
# all the flags that it understands.
gflags.DEFINE_enum('logging_level', 'ERROR',
                   ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                   'Set the level of logging detail.')
gflags.DEFINE_string('destination', 'downloaded/', 'Destination folder location', short_name='d')
gflags.DEFINE_boolean('debug', False, 'Log folder contents as being fetched')
gflags.DEFINE_string('logfile', 'drive.log', 'Location of file to write the log')
gflags.DEFINE_string('drive_id', 'root', 'ID of the folder whose contents are to be fetched')
gflags.DEFINE_enum('export', 'OO', ['PDF', 'OO', 'MSO'], 'Export format. Export to PDF, OpenOffice, or MS Office format')



def export_type():

#Defining a "export_format" dictionary:
# *key = source mimeType of the Gdoc
# *value = a list of the target mimeType (index 0) + the target file extension (index 1)
#Values change according to the "export format" defined by the user.
#Maybe is there a cleaner way to do this?
    if FLAGS['export'].value == 'MSO':
        return {
        'application/vnd.google-apps.document': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx'),
        'application/vnd.google-apps.drawing': ('image/png', 'png'),
    #'application/vnd.google-apps.form': ('text/csv', 'csv'), : Can it be exported?
    #'application/vnd.google-apps.fusiontable' : Can it be exported?
        'application/vnd.google-apps.photo': ('image/png', 'png'),
        'application/vnd.google-apps.presentation': ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'pptx'),
        'application/vnd.google-apps.spreadsheet': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx')
        
        }
        
    elif FLAGS['export'].value == 'OO':
        return {
        'application/vnd.google-apps.document': ('application/vnd.oasis.opendocument.text', 'odt'),
        'application/vnd.google-apps.drawing': ('image/png', 'png'),
    #'application/vnd.google-apps.form': ('text/csv', 'pdf'),
    #'application/vnd.google-apps.fusiontable'
        'application/vnd.google-apps.photo': ('image/png', 'png'),
        'application/vnd.google-apps.presentation': ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'pptx'),
        'application/vnd.google-apps.spreadsheet': ('application/x-vnd.oasis.opendocument.spreadsheet', 'ods')
        
        }
        
    elif FLAGS['export'].value == 'PDF':
        return {
        'application/vnd.google-apps.document': ('application/pdf', 'pdf'),
        'application/vnd.google-apps.drawing': ('image/png', 'png'),
    #'application/vnd.google-apps.form': ('text/csv', 'csv'),
    #'application/vnd.google-apps.fusiontable' :
        'application/vnd.google-apps.photo': ('image/png', 'png'),
        'application/vnd.google-apps.presentation': ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'pdf'),
        'application/vnd.google-apps.spreadsheet': ('application/pdf', 'pdf')
        
        }
    

def open_logfile():
    
    #if not re.match('^/', FLAGS.logfile):
        #FLAGS.logfile = FLAGS.destination + FLAGS.logfile
    global LOG_FILE
    LOG_FILE = open(FLAGS.logfile, 'w+')

def log(log):
    LOG_FILE.write(str(log) + '\n')

def ensure_dir(directory):
    if not os.path.exists(directory):
        log("Creating directory: %s" % directory)
        os.makedirs(directory)

def is_google_doc(drive_file):
    return True if re.match('^application/vnd\.google-apps\..+', drive_file['mimeType']) else False

def is_file_modified(drive_file, local_file):
    
    if os.path.exists(local_file):
        
        local_file_time_from_epoch = os.path.getmtime(local_file)
        
        awear_server_file_time = pytz.utc.localize(datetime.strptime(drive_file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ'))
        awear_server_file_time = awear_server_file_time.astimezone(get_localzone())
        
        corect_server_time_from_epoch = datetime.timestamp(awear_server_file_time)  
        
        return corect_server_time_from_epoch > local_file_time_from_epoch
    
    else:
        return True

def get_folder_contents(service, http, folder, base_path='./', depth=0):
    
    if FLAGS.debug:
        log("\n" + ' ' * depth + "Getting contents of folder %s" % folder['title'])
    try:
        folder_contents = service.files().list(q="'%s' in parents" % folder['id']).execute()
    except:
        log("ERROR: Couldn't get contents of folder %s. Retrying..." % folder['title'])
        get_folder_contents(service, http, folder, base_path, depth)
        return
    folder_contents = folder_contents['items']
    dest_path = base_path + folder['title'].replace('/', '_') + '/'

    def is_file(item):
        return item['mimeType'] != 'application/vnd.google-apps.folder'

    def is_folder(item):
        return item['mimeType'] == 'application/vnd.google-apps.folder'

    if FLAGS.debug:
        for item in folder_contents:
            if is_folder(item):
                log(' ' * depth + "[] " + item['title'])
            else:
                log(' ' * depth + "-- " + item['title'])
        
    ensure_dir(dest_path)
    export_mimeType = export_type()
    for item in filter(is_file, folder_contents):
        #Check if it is a native Gdoc
        if is_google_doc(item):
            #Check if it is an exportable document
            if item['mimeType'] in export_mimeType.keys():
                
                extension = export_mimeType[item['mimeType']][1]
                full_path = dest_path + item['title'].replace('/', '_') + os.extsep + extension
            else:
                full_path = dest_path + item['title'].replace('/', '_')
        else:
            full_path = dest_path + item['title'].replace('/', '_')


        if is_file_modified(item, full_path):
            is_file_new = not os.path.exists(full_path)
            
            if download_file(service, item, dest_path):
                if is_file_new:
                    log("Created %s" % full_path)
                else:
                    log("Updated %s" % full_path)
            else:
                log("ERROR while saving %s" % full_path)

    for item in filter(is_folder, folder_contents):
        get_folder_contents(service, http, item, dest_path, depth+1)


def download_file(service, drive_file, dest_path):
    """Download a file's content.

Args:
service: Drive API service instance.
drive_file: Drive File instance.

Returns:
File's content if successful, None otherwise.
"""
        
    #Showing progress
    print(drive_file['title'] + " download in progress...")
    export_mimeType = export_type()    
    if is_google_doc(drive_file):
        
           
        if drive_file['mimeType'] in export_mimeType.keys():
            extension = export_mimeType[drive_file['mimeType']][1]
            file_location = dest_path + drive_file['title'].replace('/', '_') + os.extsep + extension
        #From the "export_mimeType" dictionary, retrieving data corresponding to the source mimeType:
            source_mimeType = drive_file['mimeType']
            dest_mimeType = export_mimeType[source_mimeType]
            
            #Retrieving the target mimeType (index 0) for putting it as a download url parameter
            download_url = drive_file.get('exportLinks')[dest_mimeType[0]]
        
        else:
                #if source mimeType is unknown, the google doc can't be exported
            print(drive_file['title'] + " can't be exported (" + drive_file['mimeType'] + " mimeType)")        
            return False
                
            
    else:
        
        file_location = dest_path + drive_file['title'].replace('/', '_')
    
        download_url = drive_file['downloadUrl']
        
    if download_url:
        try:
            resp, content = service._http.request(download_url)
        except httplib2.IncompleteRead:
            log('Error while reading file %s. Retrying...' % drive_file['title'].replace('/', '_'))
            download_file(service, drive_file, dest_path)
            return False

        if resp.status == 200:

            try:
                target = open(file_location, 'wb')
            except:
                log("Could not open file %s for writing. Please check permissions." % file_location)
                return False

            target.write(content)
            target.close()
            return True
        else:
            log('An error occurred: %s' % resp)
            return False
    else:
        # The file doesn't have any content stored on Drive.
        return False


def main(argv):
    # Let the gflags module process the command-line arguments
    try:
        argv = FLAGS(argv)
        
    except gflags.FlagsError as e:
        print('%s\\nUsage: %s ARGS\\n%s' % (e, argv[0], FLAGS))
        sys.exit(1)

    # Set the logging according to the command-line flag
    logging.getLogger().setLevel(getattr(logging, FLAGS.logging_level))

    # If the Credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    storage = Storage('drive.dat')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(FLOW, storage)

    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)

    service = build("drive", "v2", http=http)

    open_logfile()

    try:
        start_folder = service.files().get(fileId=FLAGS.drive_id).execute()
        get_folder_contents(service, http, start_folder, FLAGS.destination)
    except AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
               "the application to re-authorize")

if __name__ == '__main__':
    main(sys.argv)
