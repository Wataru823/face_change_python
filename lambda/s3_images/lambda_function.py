"""lambdaで用いるモジュール

input用のS3に画像がputされたというイベントが発生したら、
元の画像と3つの描画された画像をoutput用のS3に保存する

"""

import io
import os

import urllib.parse
import boto3
from PIL import Image

OUTPUT_BUCKET = 'output用のバケット名'
emoji_type = 'blush' # 絵文字の種類を選ぶ grinning, heart_eyes, laughing, pleading_face

def lambda_handler(event, context):
    emoji_file_path = f'images/emoji/{emoji_type}.png' # 絵文字スタンプで使う{emoji_type}画像
    glass_file_path = 'images/glass/glass.png'

    client = Client(event)
    image = client.get_s3_image(client.image_path)
    emoji_image = client.get_s3_image(emoji_file_path)
    glass_image = client.get_s3_image(glass_file_path)

    for r in client.response['Contents']:
        if r['Key'] == client.image_path:
            output_emoji = image.copy()
            output_glass = image.copy()
            output_mozaiku = image.copy()

            for label in client.labels['FaceDetails']:
                draw_emoji(label, output_emoji, emoji_image)
                eye = Eye(label)
                eye.draw_glass(output_glass, glass_image)
                eye.draw_mozaiku(output_mozaiku)

            tmpkey = client.image_path.replace('/', '')
            input_upload_path = '/tmp/input-{}'.format(tmpkey)
            emoji_upload_path = '/tmp/emoji-{}'.format(tmpkey)
            glass_upload_path = '/tmp/glass-{}'.format(tmpkey)
            mozaiku_upload_path = '/tmp/mozaiku-{}'.format(tmpkey)
            image.save(input_upload_path)
            output_emoji.save(emoji_upload_path)
            output_glass.save(glass_upload_path)
            output_mozaiku.save(mozaiku_upload_path)

            image_file = os.path.basename(client.image_path) # 画像のファイル名
            s3_client = boto3.client('s3')
            s3_client.upload_file(input_upload_path, OUTPUT_BUCKET, 'input/'+image_file)
            s3_client.upload_file(emoji_upload_path, OUTPUT_BUCKET, f'output/emoji/{emoji_type}_'+image_file)
            s3_client.upload_file(glass_upload_path, OUTPUT_BUCKET, f'output/glass/glass_'+image_file)
            s3_client.upload_file(mozaiku_upload_path, OUTPUT_BUCKET, 'output/mozaiku/mozaiku_'+image_file)
            break

    return "Thanks"


def draw_emoji(label: dict, output_emoji: Image.Image, emoji_image: Image.Image):
    """画像に絵文字を描画する関数

    Args:
        label (dict): Rekognitionデータ
        output_emoji (Image.Image): 出力する画像
        emoji_image (Image.Image): 描画する際に用いる絵文字の画像

    """

    imgWidth, imgHeight = output_emoji.size
    box = label['BoundingBox']
    left = int(imgWidth * box['Left'])
    top = int(imgHeight * box['Top'])
    width = int(imgWidth * box['Width'])
    height = int(imgHeight * box['Height'])

    emoji_size = max(width, height)
    face_min = min(width, height)

    left -= int((emoji_size-face_min)/2)
    emoji_image = emoji_image.resize((emoji_size, emoji_size))
    output_emoji.paste(emoji_image, (left, top), emoji_image)

class Eye:
    """目の情報を取得し、描画するクラス

    Attributes:
        boxes (list): 目,眉毛,鼻の位置などが含まれるデータ

    """

    def __init__(self, label: dict):
        """Rekognitionデータから目の情報を取得

        Args:
            label (dict): Rekognitionデータ

        """

        self.boxes = label['Landmarks'] # 目なら'Landmarks'を指定

        for box in self.boxes:
            if box['Type'] == 'leftEyeUp':
                self.eye_left_top = box['Y']
            if box['Type'] == 'leftEyeDown':
                self.eye_left_bottom = box['Y']
            if box['Type'] == 'rightEyeUp':
                self.eye_right_top = box['Y']
            if box['Type'] == 'rightEyeDown':
                self.eye_right_bottom = box['Y']
            if box['Type'] == 'leftEyeLeft':
                self.eye_left_left = box['X']
            if box['Type'] == 'rightEyeRight':
                self.eye_right_right = box['X']

    def draw_mozaiku(self, output_mozaiku: Image.Image):
        """画像にモザイクを描画する関数

        Args:
            output_mozaiku (Image.Image): 出力する画像

        """

        imgWidth, imgHeight = output_mozaiku.size

        eye_top = int(min(self.eye_left_top, self.eye_right_top) * imgHeight)
        eye_bottom = int(max(self.eye_left_bottom, self.eye_right_bottom) * imgWidth)
        eye_left_left = int(self.eye_left_left * imgWidth)
        eye_right_right = int(self.eye_right_right * imgWidth)

        # モザイク範囲を少し広げる
        margin = (eye_bottom - eye_top) * 1
        eye_top -= margin
        eye_bottom += int(margin * 1.5)
        eye_left_left -= margin * 2
        eye_right_right += margin * 2

        imcopy = output_mozaiku.copy()
        imcut = imcopy.crop((eye_left_left, eye_top, eye_right_right, eye_bottom))
        mozaiku_size = 4
        gimg = imcut.resize([mozaiku_size, mozaiku_size]).resize(imcut.size)
        output_mozaiku.paste(gimg, (eye_left_left, eye_top))


    def draw_glass(self, output_glass: Image.Image, glass_image: Image.Image):
        """画像にサングラスを描画する関数

        Args:
            output_glass (Image.Image): 出力する画像
            glass_image (Image.Image): 描画する際に用いるサングラスの画像

        """

        imgWidth, imgHeight = output_glass.size
        glassWidth, glassHeight = glass_image.size

        eye_top = int(min(self.eye_left_top, self.eye_right_top) * imgHeight)
        eye_bottom = int(max(self.eye_left_bottom, self.eye_right_bottom) * imgWidth)
        eye_left_left = int(self.eye_left_left * imgWidth)
        eye_right_right = int(self.eye_right_right * imgWidth)

        # サングラスの範囲を少し広げる
        margin = (eye_bottom - eye_top) * 2
        eye_top -= margin
        eye_left_left -= margin * 2
        eye_right_right += margin * 2

        glass_width = (eye_right_right - eye_left_left)
        glass_height = int(glass_width * (glassHeight / glassWidth))

        glass_image = glass_image.resize((glass_width, glass_height))
        output_glass.paste(glass_image, (eye_left_left, eye_top), glass_image)


class Client:
    """s3やRekognitionからデータを取得するクラス

    Attributes:
        input_bucket (str): input用のバケット名
        image_path (str): input用のバケットにputされた画像のパス
        response (dict): s3のデータ
        s3_resource : S3のリソース
        labels (dict): Rekognitionのfaceデータ

    """

    def __init__(self, event: dict):
        """clientで使う値を取得

        Args:
            event (dict): s3にinputされた際に発生するイベントデータ

        """

        self.input_bucket = event['Records'][0]['s3']['bucket']['name']
        self.image_path = urllib.parse.unquote_plus(
                            event['Records'][0]['s3']['object']['key'],
                            encoding='utf-8'
                            )

        session = boto3.session.Session()
        self.response = session.client('s3').list_objects_v2(Bucket=self.input_bucket)
        self.s3_resource = session.resource('s3')

        rekognition = session.client('rekognition')
        self.labels = rekognition.detect_faces(
                            Image={
                                "S3Object":
                                    {"Bucket": self.input_bucket,
                                    "Name": self.image_path}},
                            Attributes=['ALL']
                            )

    def get_s3_image(self, img_path: str) -> Image.Image:
        """s3から画像を取得する関数

        Args:
            img_path (str): 取得する画像ファイルの絶対パス

        Returns:
            Image.Image: 読み込んだ画像

        """

        s3_object = self.s3_resource.Object(self.input_bucket, img_path).get()
        stream = io.BytesIO(s3_object['Body'].read())
        img = Image.open(stream)
        return img
