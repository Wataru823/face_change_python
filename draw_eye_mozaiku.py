"""
rekognition.detect_facesで読み取った情報の例をfacedetails.txtに入れた。
顔のモザイクではなく目のモザイクにする方法
例えば、facedetails.txt (labelsの中身)のLandmarksのtypeにeyeLeftやeyeRightがあるから
その位置から直線を決めて、顔の幅の値から目を隠す横幅を決める。
縦幅は顔の高さの割合で決めたりする
(pixelで指定すると画像の大きさに対応できないけどまあそれでもいい)
(コード書くとき参考にしたサイト) https://hacknote.jp/archives/45652/
"""
import io

import boto3
from PIL import Image, ImageDraw

bucket_name = 'バケット名'
filename = 'images/face.jpg' # 顔画像のpath

session = boto3.session.Session()

s3_client = session.client('s3')
res = s3_client.list_objects_v2(
    Bucket=bucket_name
)

rekognition = session.client('rekognition')

for r in res['Contents']:
    if r['Key'] != filename:
        print(r['Key'])
        continue

    labels = rekognition.detect_faces(
        Image={
            "S3Object":
                {"Bucket": bucket_name,
                "Name": filename}},
        Attributes=['ALL']
        )

    # S3から画像の読み込み
    s3_resource = session.resource('s3')
    s3_object = s3_resource.Object(bucket_name, filename).get()

    stream = io.BytesIO(s3_object['Body'].read())
    image = Image.open(stream)

    # ボックスの描画 labelsの中身はfacedetails.jsonを参照
    for l in labels['FaceDetails']:

        imgWidth, imgHeight = image.size
        draw = ImageDraw.Draw(image)

        boxes = l['Landmarks'] # 目なら'Landmarks'を指定

        for box in boxes:
            if box['Type'] == 'leftEyeUp':
                eye_left_top = imgHeight * box['Y']
            if box['Type'] == 'leftEyeDown':
                eye_left_bottom = imgHeight * box['Y']
            if box['Type'] == 'rightEyeUp':
                eye_right_top = imgHeight * box['Y']
            if box['Type'] == 'rightEyeDown':
                eye_right_bottom = imgHeight * box['Y']
            if box['Type'] == 'leftEyeLeft':
                eye_left_left = imgWidth * box['X']
            if box['Type'] == 'leftEyeRight':
                eye_left_right = imgWidth * box['X']
            if box['Type'] == 'rightEyeLeft':
                eye_right_left = imgWidth * box['X']
            if box['Type'] == 'rightEyeRight':
                eye_right_right = imgWidth * box['X']
        #高さの比較
        eye_top = min(eye_left_top, eye_right_top)
        eye_bottom = max(eye_left_bottom, eye_right_bottom)

        # モザイク範囲を少し広げる
        margin = (eye_bottom - eye_top) * 1
        eye_top -= margin
        eye_bottom += margin * 1.5
        eye_left_left -= margin * 2
        eye_right_right += margin * 2

        imcopy = image.copy() #もとの画像のコピーをとる
        imcut = imcopy.crop((eye_left_left, eye_top, eye_right_right, eye_bottom)) #目の部分を切り取り
        mozaiku_size = 4
        gimg = imcut.resize([mozaiku_size, mozaiku_size]).resize(imcut.size) #目の部分にモザイク処理
        image.paste(gimg, (int(eye_left_left), int(eye_top))) #もとの画像にモザイクをかけた画像をペースト

    image.save("out_eye_mozaiku.jpg")
