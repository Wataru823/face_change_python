import io

import boto3
from PIL import Image, ImageDraw

bucket_name = 's3のバケット名'
filename = 'face.jpg' # s3に入れた顔画像のファイル名

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

    # ボックスの描画
    for l in labels['FaceDetails']:

        imgWidth, imgHeight = image.size
        draw = ImageDraw.Draw(image)

        box = l['BoundingBox']
        left = imgWidth * box['Left']
        top = imgHeight * box['Top']
        width = imgWidth * box['Width']
        height = imgHeight * box['Height']

        points = (
            (left,top),
            (left + width, top),
            (left + width, top + height),
            (left , top + height),
            (left, top)
        )
        draw.line(points, fill='#00d400', width=2)

    image.save("out_face.jpg")
