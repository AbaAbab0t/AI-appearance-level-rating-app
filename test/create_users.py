import requests
import base64
import glob

register_url='http://127.0.0.1:5000/api/v1/auth/register'
login_url='http://127.0.0.1:5000/api/v1/auth/login'
def create_test_user(username,password):
    req=requests.post(register_url,json={'username':username,'password':password},headers={'Content-Type':'application/json'})
    print(req.text)

image_path=''

def login(username,password):
    req=requests.post(login_url,json={'username':username,'password':password},headers={'Content-Type':'application/json'})
    if req.status_code==200:
        print('login success')
        access_token=req.json().get('access_token')
        refresh_token=req.json().get('refresh_token')
    return access_token,refresh_token

def add_avatar(access_token,image_path):
    url='http://127.0.0.1:5000/api/v1/ai/avatar'
    headers={'Authorization':'Bearer '+access_token}
    # convert image to base64

    image=base64.b64encode(open(image_path,'rb').read())
    
    
    data={'image':image.decode()}
    req=requests.post(url,headers=headers,json=data)
    print(req.text)
 

if __name__ == '__main__':
    test_image='D:\\temp\\FaceRank\\resize_image\\4.567-1658.jpg'
    # for i in range(1,100):
    #     create_test_user('test'+str(i),'test'+str(i))
    images=glob.glob('D:\\works\\resize_image\\4.*.jpg')
    for i in range(1,100):
        access_token,refresh_token=login('test'+str(i),'test'+str(i))
        add_avatar(access_token,images[i])

    # access_token,refresh_token=login('test1','test1')
    # add_avatar(access_token,test_image)