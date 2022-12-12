import io

import boto3
from PIL import Image, ImageDraw

bucket_name = 's3のバケット名'
filename = 'face.jpg'

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

        box = l['BoundingBox'] # 目なら'Landmarks'を指定


        face_left = imgWidth * box['Left']
        face_top = imgHeight * box['Top']
        face_right = face_left + imgWidth * box['Width']
        face_bottom = face_top + imgHeight * box['Height']

        imcopy = image.copy() #もとの画像のコピーをとる
        imcut = imcopy.crop((face_left, face_top, face_right, face_bottom)) #顔の部分を切り取り
        mozaiku_size = 4
        gimg = imcut.resize([mozaiku_size, mozaiku_size]).resize(imcut.size) #顔の部分にモザイク処理
        image.paste(gimg, (int(face_left), int(face_top))) #もとの画像にモザイクをかけた画像をペースト

    image.save("out_mozaiku.jpg")
