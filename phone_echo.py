import time

import boto3
import decimal
import json
import os
from boto3.dynamodb.conditions import Key
from urllib.parse import parse_qs

from twilio.twiml.voice_response import VoiceResponse


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


dynamo_db = boto3.resource('dynamodb')
table = dynamo_db.Table(os.environ.get('RECORDING_TABLE'))


def echo_handler(event, ctx):
    operation = event['httpMethod']
    response = VoiceResponse()

    if operation == 'GET':
        # Check if we have a recording in the past 10s from the calling number
        phone = event['queryStringParameters']['From']
        rec_ts = int(time.time()) - 10
        result = table.query(
            ProjectionExpression='phone, ts, rec',
            KeyConditionExpression=Key('phone').eq(phone) & Key('ts').gte(rec_ts)
        )
        if len(result['Items']):
            response.say('Playing your recorded message')
            response.play(result['Items'][0]['rec'])
            response.say(
                'If you are able hear your own voice, the Caru phone is working correctly. '
                'If you hear this message but not your own voice then something is wrong with the audio settings. '
                'Please check the sensor logs in your dashboard.')
            response.hangup()
        else:
            # Record a new message
            response.say(
                'Hello. Welcome to the Caru phone testing service. After the beep please record the message. '
                'On your next call the message will be played back to you.')
            # This calls this URL with a POST request
            response.record(max_length=5)
    elif operation == 'POST':
        # Save recording url and timestamp for calling number
        data = parse_qs(event['body'])
        table.put_item(
            Item={
                'phone': data['From'][0],
                'ts': int(time.time()),
                'rec': data['RecordingUrl'][0]
            }
        )

    response.hangup()

    return {
        'statusCode': '200',
        'body': str(response),
        'headers': {
            'Content-Type': 'application/xml'
        }
    }
