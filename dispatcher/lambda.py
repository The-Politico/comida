#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import os
import logging
import boto3
import json
from base64 import b64decode

ENCRYPTED_EXPECTED_TOKEN = os.environ['kmsEncryptedToken']
SNS_TOPIC = os.environ['snsTopic']
kms = boto3.client('kms')
expected_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']
sns_arn = kms.decrypt(CiphertextBlob=b64decode(SNS_TOPIC))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def validateToken(bot_event):
    """
    Token validation
    """
    msg = None
    try:
        token = bot_event['token']
    except KeyError:
        msg = 'Could not find request token, sorry.'
        return msg
    if token != expected_token:
        msg = 'Invalid request token'
    return msg


def lambda_handler(event, context):
    text = ''
    bot_event = event
    user = None
    # Comment out token validation since it is slow and not critical
    msg = validateToken(bot_event)
    if msg:
        logger.error(msg)
        return {'text': msg}

    # Publish a SNS topic message

    sns_client = boto3.client('sns')
    sns_client.publish(
        TopicArn=sns_arn,
        Message=json.dumps({'default': json.dumps(event)}),
        MessageStructure='json'
    )
    try:
        user = bot_event['user_name']
    except KeyError:
        pass
    if user:
        text += 'Hi %s, hungry huh?\n' % user
    text += 'Let me get you some food options, stay tuned.'
    response = {'response_type': 'in_channel'}
    response['text'] = text
    return response
