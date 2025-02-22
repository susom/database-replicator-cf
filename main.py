import base64
import logging
import json
from datetime import datetime

import time
from httplib2 import Http

from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials


def main(event, context):
    pubsub_message = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    credentials = GoogleCredentials.get_application_default()

    service = discovery.build('sqladmin', 'v1beta4', http=credentials.authorize(Http()), cache_discovery=False)

    try:
        # request = service.backupRuns().insert(
        #     project=pubsub_message['project'],
        #     instance=pubsub_message['instance']
        # )
        current = int(time.time())  # remove the decimals
        obj = {
            'exportContext': {
                'kind': 'sql#exportContext',
                'fileType': 'SQL',
                'uri': f"gs://ss-cord-prod-dumps/{current}.sql",
                'databases': ['postgres']
            }
        }
        request = service.instances().export(
            project=pubsub_message['project'],
            instance=pubsub_message['instance'],
            body=obj
        )
        response = request.execute()
    except HttpError as err:
        logging.error("Could NOT run backup. Reason: {}".format(err))
    else:
        logging.info("Backup task status: {}".format(response))
