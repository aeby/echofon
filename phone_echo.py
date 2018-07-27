import boto3
import decimal
import json
from boto3.dynamodb.conditions import Key

from twilio.twiml.voice_response import VoiceResponse


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('recording')

response = table.query(
    ProjectionExpression='phone, ts, recording',
    KeyConditionExpression=Key('phone').eq('+4146545546')
)

for i in response['Items']:
    print(json.dumps(i, cls=DecimalEncoder))


def echo_handler(event, ctx):
    operation = event['httpMethod']
    response = VoiceResponse()

    if operation == 'GET':
        # Check if we have a recording in the past 10s from the calling number
        if False:
            response.say('Playing your recorded message')
            response.play('https://api.twilio.com/cowbell.mp3')
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
        # Save recording url for calling number
        data = json.loads(event['body'])
        recording = data['RecordingUrl']
        caller = data['From']

        pass

    response.hangup()
    return str(response)
