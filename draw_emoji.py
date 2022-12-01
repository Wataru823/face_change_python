import io

import boto3
from PIL import Image, ImageDraw

bucket_name = 's3のバケット名'
filename = 'face.jpg' # s3に入れた顔画像のファイル名
emoji_file_path = './images/emoji/blush.png'

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
        right = left + imgWidth * box['Width']
        bottom = top + imgHeight * box['Height']

        width = imgWidth * box['Width']
        height = imgHeight * box['Height']

        emoji_size = max(int(width), int(height))
        face_min = min(int(width), int(height))

        print((left, top))
        left -= (emoji_size-face_min)/2
        pos = (int(left), int(top))
        print(pos)
        emoji_im = Image.open(emoji_file_path).resize((emoji_size, emoji_size))
        image.paste(emoji_im, pos, emoji_im)

    image.save("out_emoji.jpg", quality=95)
