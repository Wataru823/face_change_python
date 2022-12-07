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
                glass = Eye(label, output_glass)
                glass.draw_glass(glass_image)
                mozaiku = Eye(label, output_mozaiku)
                mozaiku.draw_mozaiku()

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
        eye_left_left (float): 左目の左端. x座標
        eye_right_right (float): 右目の右端. x座標
        eye_top (float): 両目の上端. y座標
        eye_bottom (float): 両目の下端. y座標

    """

    def __init__(self, label: dict, output_img: Image.Image):
        """Rekognitionデータから目の情報を初期化

        Args:
            label (dict): Rekognitionのfaceデータ
            output_img (Image.Image): 描画する画像

        """

        self.output_img = output_img
        imgWidth, imgHeight = output_img.size
        landmarks = label['Landmarks']

        for landmark in landmarks:
            if landmark['Type'] == 'leftEyeUp':
                eye_left_top = int(landmark['Y'] * imgHeight)
            if landmark['Type'] == 'leftEyeDown':
                eye_left_bottom = int(landmark['Y'] * imgHeight)
            if landmark['Type'] == 'rightEyeUp':
                eye_right_top = int(landmark['Y'] * imgHeight)
            if landmark['Type'] == 'rightEyeDown':
                eye_right_bottom = int(landmark['Y'] * imgHeight)
            if landmark['Type'] == 'leftEyeLeft':
                self.eye_left_left = int(landmark['X'] * imgWidth)
            if landmark['Type'] == 'rightEyeRight':
                self.eye_right_right = int(landmark['X'] * imgWidth)

        self.eye_top = min(eye_left_top, eye_right_top)
        self.eye_bottom = max(eye_left_bottom, eye_right_bottom)

    def draw_mozaiku(self):
        """画像にモザイクを描画する関数
        """

        # モザイク範囲を少し広げる
        margin = (self.eye_bottom - self.eye_top) * 1
        self.eye_top -= margin
        self.eye_bottom += int(margin * 1.5)
        self.eye_left_left -= margin * 2
        self.eye_right_right += margin * 2

        imcopy = self.output_img.copy()
        imcut = imcopy.crop((self.eye_left_left, self.eye_top, self.eye_right_right, self.eye_bottom))
        mozaiku_size = 4
        gimg = imcut.resize([mozaiku_size, mozaiku_size]).resize(imcut.size)
        self.output_img.paste(gimg, (self.eye_left_left, self.eye_top))


    def draw_glass(self, glass_image: Image.Image):
        """画像にサングラスを描画する関数

        Args:
            glass_image (Image.Image): 描画する際に用いるサングラスの画像

        """

        glassWidth, glassHeight = glass_image.size

        # サングラスの範囲を少し広げる
        margin = (self.eye_bottom - self.eye_top) * 2
        self.eye_top -= margin
        self.eye_left_left -= margin * 2
        self.eye_right_right += margin * 2

        glass_width = (self.eye_right_right - self.eye_left_left)
        glass_height = int(glass_width * (glassHeight / glassWidth))

        glass_image = glass_image.resize((glass_width, glass_height))
        self.output_img.paste(glass_image, (self.eye_left_left, self.eye_top), glass_image)


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
        """clientで使う値を初期化

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
