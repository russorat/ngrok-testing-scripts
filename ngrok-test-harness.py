#!venv/bin/python

import argparse, time, codecs
from dotenv import dotenv_values
from os.path import expanduser
from datetime import datetime
import ngrok, requests, time, socket

def test_ip_restrictions(config):
    ip = requests.get('https://api.ipify.org').content.decode('utf8')
    print('Your public IP address is: {}'.format(ip))

    ng = ngrok.Client(config["NGROK_API_KEY"])

    print("Removing all IP Restrictions of type endpoints...")
    ipRestrictions = ng.ip_restrictions.list()
    for restriction in ipRestrictions.ip_restrictions:
        if restriction.type == "endpoints":
            ng.ip_restrictions.delete(id=restriction.id)
    print("All IP Restrictions of type endpoints removed!")

    test_site(200)
    
    print("Creating new IP Policy for testing...")
    newIPPolicy = ng.ip_policies.create(action="allow", description="created by test-ip-policy")
    print("New IP Policy created: {}".format(newIPPolicy.id))
    
    print("Creating new IP Restriciton for testing...")
    newIPRestriction = ng.ip_restrictions.create(type="endpoints",description="created by test-ip-policy",enforced=True,ip_policy_ids=[newIPPolicy.id])
    print("New IP Restriction created: {}".format(newIPRestriction.id))
    
    print("Testing access to unreliable.site...")
    startTime = time.perf_counter()
    test_site(403)
    stopTime = time.perf_counter()
    print(f"It took {stopTime - startTime:0.4f} seconds to apply the IP Restriction")

    print("Creating new IP Policy Rule to allow {} for testing...".format(ip))
    newIPPolicyRule = ng.ip_policy_rules.create(cidr=ip+"/32", ip_policy_id=newIPPolicy.id, description="me")
    print("New IP Policy Rule created: {}".format(newIPPolicyRule.id))

    print("Testing access to unreliable.site...")
    startTime = time.perf_counter()
    test_site(200)
    stopTime = time.perf_counter()
    print(f"It took {stopTime - startTime:0.4f} seconds to apply the IP Rule to allow")

    print("Cleaning Up...")
    ng.ip_policy_rules.delete(id=newIPPolicyRule.id)
    ng.ip_restrictions.delete(id=newIPRestriction.id)
    ng.ip_policies.delete(id=newIPPolicy.id)
    print("All clean!")

    test_site(200)

def test_site(expected):
    try:
        resp = requests.get('https://unreliable.site/status/200')
        if resp.status_code != expected:
            test_site(expected)
    except:
        test_site(expected)

def parseArguments():
    home = expanduser("~")
    parser = argparse.ArgumentParser(prog='ngrok-test-harness.py',
                                    description='A set of scripts for testing ngrok',
                                    epilog='Find me on GitHub: https://github.com/russorat')

    parser.add_argument('test_name', default="ip-restrictions", help='The name of the test to run.')
    
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    args = parseArguments()
    config = dotenv_values(".env")
    if not config["NGROK_API_KEY"]:
        print("No ngrok API key found. Try adding a .env file and defining NGROK_API_KEY.")
    else:
        if args.test_name == "ip-restrictions":
            test_ip_restrictions(config)
        else:
            print("I don't know about that test.")