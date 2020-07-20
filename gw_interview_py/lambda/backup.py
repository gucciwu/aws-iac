import json


def lambda_handler(event, context):
    print('request: {}'.format(json.dumps(event)))
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': {"errCode": 0, "data": 'Backup succeeded!'}
    }
