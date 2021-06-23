import boto3
import os
import xml.etree.ElementTree as ET
import urllib


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

    bucket = 'clovisbucketone'
    #key = 'junit/sfb_cloud/input.xml' #key: test_framework/team/filename', path: bucket/test_framework/team/filename'
    key = 'service-1/test-framework-1/input.xml'

    test_framework = "junit"
    team = "sfb_cloud"
    filename = "input.xml"
    filetype = "xml"

    output_bucket = 'clovisbucketzero'
    output_key = 'output.log'

    factory_helper(test_framework, filetype, bucket, key, output_bucket, output_key)



def factory_helper(test_framework, filetype, input_bucket, input_key, output_bucket, output_key):

    if (filetype == 'xml'):
        if (test_framework == 'junit'):
            parse_jUnit_report(input_bucket, input_key, output_bucket, output_key)
        else:
            print("No existing parsing logic for {} framework reports.".format(test_framework))

    else:
        print("No existing parsing logic for {} file format reports".format(filetype))



def factory_helper_2(test_framework, filetype, filename, bucket, key):

    if (filetype == 'xml'):
        if (test_framework == 'junit'):
            parse_jUnit_report(bucket, key)
        elif (test_framework == 'allure'):
            #parse allure report
            return
    elif (filetype == 'json'):
        #parse json report
        return
    elif (filetype == 'csv'):
        #parse CSV report
        return
    else:
        print("No parsing logic for {}".format(filetype))
        return



def parse_jUnit_report(input_bucket, input_key, output_bucket, output_key):

    s3 = boto3.client('s3')
    parsed_xml = ''
    string = ''

    try:
        obj = s3.get_object(Bucket=input_bucket, Key=input_key) #download file from S3 bucket
        file_data = obj['Body'].read() #.decode('utf-8')
        parsed_xml = ET.fromstring(file_data)

        for element in parsed_xml: 
            if (element.tag == "testcase"):
                testcase = element.attrib['name']
                classname = element.attrib['classname'] #class name is package name.
                time = element.attrib['time']
                build_number = 'na'
                service_version = 'na'
                test_status = 'na'
                message = 'na'
                failure_type = 'na'

                for child in element:
                    test_status = child.tag;
                    for attr in  child.attrib:
                        if (attr == 'message'):
                            message = child.attrib[attr]
                        elif (attr == 'type'):
                            failure_type = child.attrib[attr]
                        else:
                            print("Attribute {} not parsed in {} testcase status".format(attr, test_status))
                 
                if (test_status == 'na'):
                    test_status = 'passed'

                line = "testcase={} classname={} time={} build_number={} service_version={} status={} message={} type={} \n".format(testcase, classname, time, build_number, service_version, test_status, message, failure_type)
                string += line #bad time comlexity. how to optimize it.

        s3.put_object(Bucket=output_bucket,Key=output_key, Body=string) #upload file to another S3 bucket

    except Exception as e:
        print(e)
    

