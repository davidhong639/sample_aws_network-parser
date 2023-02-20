import logging
import json
import boto3
import urllib.parse

from parse_log import parse_log

logging.basicConfig(
	level=logging.INFO,
    format='%(levelname)s - %(module)s:%(funcName)s - %(message)s'
)
log = logging.getLogger(__name__)

s3_client = boto3.client('s3')
glue_client = boto3.client('glue')

def lambda_handler(event, context):
    statusCode = 200
    body = []
    for record in event['Records']:
        try:
            record_s3 = record['s3']
            name_bucket = record_s3['bucket']['name']
            src_filename = urllib.parse.unquote_plus(record_s3['object']['key'], encoding='utf-8')
            
            log.info('getting s3 (bucket=%s, filename=%s)...' % (name_bucket, src_filename))
            response = s3_client.get_object(
                Bucket=name_bucket, Key=src_filename
            )


            log.info('parsing log (bucket=%s, filename=%s)...' % (name_bucket, src_filename))
            hostname, output_device, output_interface, output_trunk = parse_log(log, response['Body'])

            #   requires hostname and device data
            #   device can exist without interfaces and vlans
            if hostname and output_device:
                log.info('parsing successful, storing configuration (hostname=%s)' % hostname)

                #   write device data to csv
                tgt_fileDevice = 'output/device/{}/device.json'.format(hostname)
                s3_client.put_object(
                    Body=format_json(output_device),
                    Bucket=name_bucket,
                    Key=tgt_fileDevice
                )

                #   write interface data to csv
                tgt_fileInterface = 'output/interface/{}/interface.json'.format(hostname)
                s3_client.put_object(
                    Body=format_json(output_interface),
                    Bucket=name_bucket,
                    Key=tgt_fileInterface
                )

                #   write trunk data to csv
                tgt_fileTrunk = 'output/trunk/{}/trunk.json'.format(hostname)
                s3_client.put_object(
                    Body=format_json(output_trunk),
                    Bucket=name_bucket,
                    Key=tgt_fileTrunk
                )

                #   record which files have been created
                body.append({
                    'bucket': name_bucket,
                    'source': src_filename,
                    'target': [tgt_fileDevice, tgt_fileInterface, tgt_fileTrunk]
                })
        except Exception as e:
            log.error('there has been an error: %r' % e)
            statusCode = 400

    try:
        crawler_name = 'network_configuration'
        log.info('running crawler (crawler=%s)' % crawler_name)
    
        glue_client.start_crawler(Name=crawler_name)
    except Exception as e:
        log.error('failed to crawl output: %r' % e)

    return {
        'statusCode': statusCode,
        'body': body
    }


def format_json(data):
    #   by default, AWS Glue does not accept standard JSON formatting
    #       no list brackets outside data
    #       all data elements on a new line
    return json.dumps(data).replace('[', '').replace(']', '').replace('}, {', '},\n{')
