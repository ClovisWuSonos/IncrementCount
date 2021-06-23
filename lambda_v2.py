# PRE-REQUISITE: if you need to run this script locally, install boto3 library on your machine
# pip3 install boto3
#
# Description: this script fetches an input jUnit xml file from a S3 bucket, parse it into a log-formatted string, 
# and upload the whole parsed string as a file to another S3 bucket. The parsed data contain testcase name, status(passed, 
# failure, skipped), build_number, service_version etc. Some fields are currently not available in the input file.
# A factory helper method is used to identify the test framework and file type of input file.
# The two methods: get_bucket_and_key and extract_key will be used after adding SNS/S3 trigger.
import boto3
import os
import xml.etree.ElementTree as ET
import urllib
import time


def get_bucket_and_key(event):
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    except Exception as e:
        print(e)

    return bucket, key


def extract_key(key):
    test_framework = ''
    filetype = ''
    filename = ''
    return test_framework, filetype, filename


def lambda_handler(event, context):

    #bucket, key = get_bucket_and_key(event) 
    #test_framework, filetype, filename = extract_key(key)
    bucket = 'grafana-integration'  
    key = 'TEST-com.sonos.services.functionaltests.v1.UserV1FunctionalTest.xml'

    test_framework = "junit"
    filetype = "xml"
    output_bucket = 'grafana-functional-tests-output-log'
    output_key = 'JUnit/TEST-com.sonos.services.functionaltests.v1.UserV1FunctionalTest_Parsed_Log.log'

    factory_helper(test_framework, filetype, bucket, key, output_bucket, output_key)


def factory_helper(test_framework, filetype, input_bucket, input_key, output_bucket, output_key):
    # Identify test framework and file type of input file, call corresponding method for parsing
    if (filetype == 'xml'):
        if (test_framework == 'junit'):
            parse_junit_report(input_bucket, input_key, output_bucket, output_key)
        elif (test_framework == 'allure'):
            print("No parsing logic for {} framework reports.".format(test_framework))
        else:
            print("No parsing logic for {} framework reports.".format(test_framework))
    elif (filetype == 'json'):
        print("No parsing logic for {} framework reports.".format(filetype))
    else:
        print("No parsing logic for {} formatted reports".format(filetype))


def parse_junit_report(input_bucket, input_key, output_bucket, output_key):

    s3 = boto3.client('s3')
    parsed_xml = ''
    string = ''

    try:
        obj = s3.get_object(Bucket=input_bucket, Key=input_key) #fetch input file from S3 bucket
        file_data = obj['Body'].read() #.decode('utf-8')
        parsed_xml = ET.fromstring(file_data)

        for element in parsed_xml.findall('testcase'):
            test_status = 'passed'
            message = 'na'
            failure_type = 'na'

            # Assume each testcase element has at most one child (i.e. test status).
            # If this test case has a child, then the test status is either failure or skipped. Otherwise, test status is passed.
            # Test status can be passed, failure, and skipped.
            children = element.getchildren();
            if (len(children) != 0):
                test_status = children[0].tag

                if (children[0].attrib.get("message") != None):
                    message = children[0].attrib["message"]
                
                if (children[0].attrib.get("type" != None)):
                    failure_type = children[0].attrib["type"]

            ts = time.time()
            line = "{} testcase={} classname={} time={} build_number={} service_version={} status={} message={} type={}\n".format(str(ts), element.attrib['name'], element.attrib['classname'], element.attrib['time'], 'na', 'na', test_status, message, failure_type)
            string += line #may need to optimize time complexity

        #upload file to another S3 bucket.
        s3.put_object(Bucket=output_bucket,Key=output_key, Body=string)

    except Exception as e:
        print(e)