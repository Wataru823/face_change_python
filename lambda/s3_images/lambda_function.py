import io

import urllib.parse
import boto3
from PIL import Image

print('Loading function')


def lambda_handler(event, context):
    input_bucket = event['Records'][0]['s3']['bucket']['name'] # inputの画像があるバケット名
    output_bucket = 'output-images-ikeda' # output用のバケット名
    image_dir = 'images/' # input画像のディレクトリ
    tmp_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8') # input画像のファイル名
    # tmp_key = 'images/face.jpg'
    key = tmp_key.replace(image_dir, '')
    print(tmp_key, key)
    image_path = image_dir + key  # s3に入れた顔画像のpath
    emoji_type = 'blush' # 絵文字の種類を選ぶ grinning, heart_eyes, laughing, pleading_face
    emoji_file_path = f'images/emoji/{emoji_type}.png' # 絵文字スタンプで使う{emoji_type}画像
    glass_file_path = 'images/glass/glass.png'

    session = boto3.session.Session()
    response = session.client('s3').list_objects_v2(Bucket=input_bucket)
    rekognition = session.client('rekognition')
    s3_resource = session.resource('s3')


    for r in response['Contents']:
        if r['Key'] == emoji_file_path:
            emoji_image = get_s3_image(s3_resource, input_bucket, emoji_file_path)
        if r['Key'] == emoji_file_path:
            glass_image = get_s3_image(s3_resource, input_bucket, glass_file_path)
            print("get emoji")

    for r in response['Contents']:
        if r['Key'] == image_path:
            print("find " + r['Key'])

            image = get_s3_image(s3_resource, input_bucket, image_path)
            output_emoji = image.copy()
            output_glass = image.copy()
            output_mozaiku = image.copy()
            labels = get_rekognition_labels(rekognition, input_bucket, image_path)

            for label in labels['FaceDetails']:
                draw_emoji(label, output_emoji, emoji_image)
                draw_glass(label, output_glass, glass_image)
                print(f"{emoji_type} done")
                draw_mozaiku(label, output_mozaiku)

            tmpkey = image_path.replace('/', '')
            input_upload_path = '/tmp/input-{}'.format(tmpkey)
            emoji_upload_path = '/tmp/emoji-{}'.format(tmpkey)
            glass_upload_path = '/tmp/glass-{}'.format(tmpkey)
            mozaiku_upload_path = '/tmp/mozaiku-{}'.format(tmpkey)
            image.save(input_upload_path)
            output_emoji.save(emoji_upload_path)
            output_glass.save(glass_upload_path)
            output_mozaiku.save(mozaiku_upload_path)
            s3_client = boto3.client('s3')
            s3_client.upload_file(input_upload_path, output_bucket, 'input/'+key)
            s3_client.upload_file(emoji_upload_path, output_bucket, f'output/emoji/{emoji_type}_'+key)
            s3_client.upload_file(glass_upload_path, output_bucket, f'output/glass/glass_'+key)
            s3_client.upload_file(mozaiku_upload_path, output_bucket, 'output/mozaiku/mozaiku_'+key)
            print('upload done')
            break

    return "Thanks"


def get_rekognition_labels(rekognition, input_bucket: str, image_path: str):
    labels = rekognition.detect_faces(
            Image={
                "S3Object":
                    {"Bucket": input_bucket,
                    "Name": image_path}},
            Attributes=['ALL']
            )
    return labels


def get_s3_image(s3_resource, input_bucket: str, image_path: str):
    # S3から画像の読み込み
    s3_object = s3_resource.Object(input_bucket, image_path).get()
    stream = io.BytesIO(s3_object['Body'].read())
    output_emoji = Image.open(stream)
    return output_emoji


def draw_emoji(label, output_emoji, emoji_image):
    imgWidth, imgHeight = output_emoji.size
    box = label['BoundingBox']
    left = imgWidth * box['Left']
    top = imgHeight * box['Top']
    width = imgWidth * box['Width']
    height = imgHeight * box['Height']

    emoji_size = max(int(width), int(height))
    face_min = min(int(width), int(height))

    left -= (emoji_size-face_min)/2
    pos = (int(left), int(top))
    emoji_image = emoji_image.resize((emoji_size, emoji_size))
    output_emoji.paste(emoji_image, pos, emoji_image)


def draw_mozaiku(label, output_mozaiku):
    imgWidth, imgHeight = output_mozaiku.size

    boxes = label['Landmarks'] # 目なら'Landmarks'を指定
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

    imcopy = output_mozaiku.copy() #もとの画像のコピーをとる
    imcut = imcopy.crop((eye_left_left, eye_top, eye_right_right, eye_bottom)) #目の部分を切り取り
    mozaiku_size = 4
    gimg = imcut.resize([mozaiku_size, mozaiku_size]).resize(imcut.size) #目の部分にモザイク処理
    output_mozaiku.paste(gimg, (int(eye_left_left), int(eye_top))) #もとの画像にモザイクをかけた画像をペースト
    print("mozaiku done")

def draw_glass(label, output_glass, glass_image):
    imgWidth, imgHeight = output_glass.size
    glassWidth, glassHeight = glass_image.size

    boxes = label['Landmarks'] # 目なら'Landmarks'を指定
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
        if box['Type'] == 'rightEyeRight':
            eye_right_right = imgWidth * box['X']

    #高さの比較
    eye_top = min(eye_left_top, eye_right_top)
    eye_bottom = max(eye_left_bottom, eye_right_bottom)

    # 範囲を少し広げる
    margin = (eye_bottom - eye_top) * 2
    eye_top -= margin
    eye_bottom += margin * 1.5
    eye_left_left -= margin * 2
    eye_right_right += margin * 2

    glass_width = int(eye_right_right - eye_left_left)
    glass_height = int(glass_width * (glassHeight / glassWidth))

    pos = (int(eye_left_left), int(eye_top))
    glass_image = glass_image.resize((glass_width, glass_height))
    output_glass.paste(glass_image, pos, glass_image)

    print("mozaiku done")
