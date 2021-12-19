# encoding:utf-8
import requests

AK = 'hKdbqx58D4I96l1DgWbjDcrA'
SK = 'EByffr5HRbhxrl7Cu9jc0AfPrFalNEnp'
# client_id 为官网获取的AK， client_secret 为官网获取的SK
host = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={AK}&client_secret={SK}".format(
    AK=AK, SK=SK)
print(host)
response = requests.get(host)
if response:
    print(response.json())
