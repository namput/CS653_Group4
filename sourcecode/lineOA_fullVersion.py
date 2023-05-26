    # -*- coding: utf-8 -*-
import boto3
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flask import Flask,request
import os
import json
import requests
#------------ end import zone -----------
s3 = boto3.resource('s3')
s3_bucket = s3.Bucket(name='bigdataprojectagri')
#obj = s3.Object('bigdataprojectagri','cleandata/GHG_Volumns/GHG_Volumns.csv')
#print(obj.get()['Body'].read())
app = Flask(__name__)

@app.route("/")                                                       
def hello():
    return "Hello World!"

#------------insert new code below --------
@app.route('/webhook' , methods = ['POST']) 
def webhook():
    payload = request.json
    print(payload)
    try :
        event_reply = payload['events'][0]['replyToken']
        print("==================send===============")
        sendtext(payload)
    except :
        None
    return '',200

def AHP(input):
    res = 0
    Matrix = [[1,0,0,0],
              [0,1,0,0],
              [0,0,1,0],
              [0,0,0,1]]
    province = s3.Object('bigdataprojectagri','cleandata/province/province.csv')
    province = province.get()['Body'].read()
    province = province.decode('UTF-8')
    province = np.array(province.split('\n')[1:])
    dict_province = {}
    for p in province :
        if len(p) > 10 : 
            temp = p.split(',')
            dict_province[temp[1]] = temp[2]
    temp = input.split('-')
    order = [int(temp[0]),int(temp[1]),int(temp[2])]
    pro = temp[3]
    proEng = dict_province[pro]
    Matrix[order[0]-1][order[1]-1] = 4
    Matrix[order[0]-1][order[2]-1] = 6
    Matrix[order[1]-1][order[2]-1] = 2
    for i in range(0,len(Matrix[3])-1) :
        Matrix[3][order[i]-1] = (1+i)*2
    for i in range(0,4) :
        for j in range(0,4) :
            if Matrix[i][j] == 0 :
                Matrix[i][j] = 1/Matrix[j][i]
    Matrix = np.array(Matrix)
    name = proEng+'_'+temp[0]+temp[1]+temp[2]
    name = name.replace(' ','_')
    copy_m=[]
    sumC = []
    weight = []
    for i in range(0,4) :
        sumC.append(sum(Matrix[:,i]))
    for i in range(0,len(Matrix)) :
        copy_m.append([x/sumC[i] for x in Matrix[:,i]])
    copy_m = np.array(copy_m).T
    weight = [sum(copy_m[i,:])/4 for i in range(0,len(copy_m))]
    Lamda = sum([sumC[i]*weight[i] for i in range(0,4)])
    CI = (Lamda-4)/3
    RI = 0.9
    CR = CI/RI
    print("===========================Stat Value===========================")  
    print("weight check = ",sum(weight)," (is 1) ")
    print("Lamda Max = ",Lamda)
    print("CI = ",CI)
    print("RI = ",RI)
    print("CR = ",CR)
    if CR <0.1 :
        print('\n',CR , "< 0.1 corect!!" )
    data = s3.Object('bigdataprojectagri','cleandata/fuzzy/fuzzy.csv')
    data = data.get()['Body'].read()
    data = data.decode('UTF-8')

    data = data.split('\n')
    clean = []
    for i in range(1,len(data)):
        temp = data[i].split(',')
        print(temp)    
        clean.append([temp[1],temp[2],temp[3],temp[4],temp[5],temp[6]])
        if temp[0] == '76':
            break
    data = np.array(clean)
    data = pd.DataFrame({
                'Province' : data[:,0],
                'Soybean' : data[:,1],
                'Palm' : data[:,2],
                'Coconut' : data[:,3],
                'Groundnut' : data[:,4],
                'Sunflower' : data[:,5]})
    agri = ['Soybean','Palm','Coconut','Groundnut','Sunflower']
    data['Soybean'] = data['Soybean'].astype(np.float64)
    data['Palm'] = data['Palm'].astype(np.float64)
    data['Coconut'] = data['Coconut'].astype(np.float64)
    data['Groundnut'] = data['Groundnut'].astype(np.float64)
    data['Sunflower'] = data['Sunflower'].astype(np.float64)

    data['Soybean'] = data['Soybean']*weight[2]
    data['Palm'] = data['Palm']*weight[2]
    data['Coconut'] = data['Coconut']*weight[2]
    data['Groundnut'] = data['Groundnut']*weight[2]   
    data['Sunflower'] = data['Sunflower']*weight[2]
    standard = [[2,2,1],
                [3,1,1],
                [3,1,3],
                [1,3,2],
                [2,2,2]]
    weight_agri = data.copy()
    for i in range(0,len(weight_agri)) :
        for j in range(1,6) :
            if weight_agri.iloc[i,j]!= 0 :
                weight_agri.iloc[i,j] = weight_agri.iloc[i,j]+standard[j-1][0]*weight[0]+standard[j-1][1]*weight[1]+standard[j-1][2]*weight[3]
    result = weight_agri[weight_agri['Province']==proEng].copy()
    result = result.drop(['Province'],axis=1).reset_index(drop=True)
    result = result.to_numpy()[0]
    t_df = pd.DataFrame({'product':agri,'weight':result})
    t_df = t_df.sort_values(['weight'])
    t_df = t_df[t_df['weight']!=0].reset_index(drop=True)
    temp_data = t_df.to_numpy()
    agri = temp_data[:,0]
    result = temp_data[:,1] 
    print("จังหวัด",pro,"ควรปลูก(ตามลำดับ)")
    for i in range(0,len(agri)) :
        print(agri[i], ':',result[i])
    return name,agri,result

def pie_chart(name,data,label) :
    plt.pie(data,labels=label,autopct='%d%%')
    plt.savefig(name+".png")

def select_img(name):
    img={'imageFile':open(name+'.png','rb')}
    return img

def sendtext(payload):
    Reply_token = payload['events'][0]['replyToken']
    UserID = payload['events'][0]['source']['userId']
    Timestamp = payload['events'][0]['timestamp']
    lintNotifytoken = ''
    text = payload['events'][0]['message']['text']
    reply_url = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type':'application/json; charset=UTF-8',
        "Authorization": "Bearer " + lintNotifytoken}
    messages = ''
    token = ''
    s3_img = 'temp_img/'
    path_img = 'https://bigdataprojectagri.s3.amazonaws.com/temp_img/'
    data = {
        "to": token, 
        "mode": "active", 
        "replyToken": Reply_token, 
        "source": {"type": "user", "userId": UserID}, 
        "timestamp": Timestamp, 
        "type": "message"
    }
    if text == 'สอบถาม' :
        messages = [
        {
            "type":"text",
            "text":'เรียงลำดับว่าคุณให้ความสำคัญกับอะไรมากที่สุดเรียงจากมากไปน้อย \n1.ต้นทุนที่ต่ำ\n2.ราคาขายที่สูง \n3.ปริมาณผลผลิตที่มาก \nตัวอย่าง\nf:2-3-1-ลพบุรี\n(ชอบพืชที่ราคาขายสูงมากกว่าที่จะมีผลผลิตมากและต้นทุนที่ต่ำ อยู่จังหวัดลพบุรี)\n'
        },
      ]
    elif text[0:2]=='f:' :
        name,agri,result = AHP(text[2:])
        pie_chart(name,result,agri)
        name = name+'.png'
        print(name)
        s3_bucket.upload_file(Filename=name,Key='temp_img/'+name)
        messages = [{
             "type":"image",
             'previewImageUrl':path_img+name,
             'originalContentUrl':path_img+name
             }]
    else :
        messages = [{
             "type":"text",
             "text":'คำสั่งการทำงาน :\nสอบถาม\n'
             }]
    data['messages'] = messages
    r = requests.post(reply_url, headers=headers, data=json.dumps(data))
    print(r)


#------------ end edit zone  --------
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=int(os.environ.get('PORT','5000')))