from flask import Flask, request, abort

import json,urllib.request
import spacy
import os
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    StickerMessage

)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    StickerMessageContent,
    
)

app = Flask(__name__)

myT=os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
myC=os.getenv("LINE_CHANNEL_SECRET")
configuration = Configuration(access_token=myT)
handler = WebhookHandler(myC)

ansA=[]
city=''
nlp = spacy.load('zh_core_web_md')
url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=',os.getenv("YOUR_API"),'&format=JSON'
  

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

def myG(aa):
    ansA.clear()
    data = urllib.request.urlopen(url).read()
    output = json.loads(data)
    location=output['records']['location']
    for i in location:
        city = i['locationName']
        if city==aa:
            wx = i['weatherElement'][0]['time'][0]['parameter']['parameterName']
            maxtT = i['weatherElement'][4]['time'][0]['parameter']['parameterName']
            mintT = i['weatherElement'][2]['time'][0]['parameter']['parameterName']           
            ansA.append(city)
            ansA.append(wx)
            ansA.append(mintT)
            ansA.append(maxtT)
    return ansA   


@handler.add(MessageEvent, message=StickerMessageContent)
def handle_sticker_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[StickerMessage(
                    package_id=event.message.package_id,
                    sticker_id=event.message.sticker_id)
                ]
            )
        )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    getText=event.message.text
    statement1 = nlp("想查哪個城市?")
    statement2 = nlp('想查詢'+getText)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        print(statement1.similarity(statement2))
        if statement1.similarity(statement2) >= 0.50:
            for ent in statement2.ents:
                if ent.label_ == "GPE":
                    getText = ent.text
                    if getText=='台北' or getText=='臺北'or getText=='臺北市':
                        line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                        messages=[
                            #TextMessage(text='回傳:2023/11/16'),
                            TextMessage(text=str(myG('臺北市')))]                        
                        )
                    ) 
                    elif getText=='新北' or getText=='新北市':            
                        line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=str(myG('新北市')))]
                        )
                    )
  
                    elif getText=='台中' or getText=='臺中' or getText=='臺中市':
                        line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=str(myG('臺中市')))]
                        )
                    )

                    else:
                        line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text='1->臺北市.2->新北市.3->臺中市')]
                        )
                    )                
                if ent.label_ != "GPE":
                        line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text='-查無資料-')]
                        )
                    )

        else:
            line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=str(round(statement1.similarity(statement2), 2))+'相似度條件過低')]
                        )
                    )
            
if __name__ == "__main__":
    app.run(debug=True)
