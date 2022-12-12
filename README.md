## AWS Rekognition を用いて顔画像を処理

CC 実験用

## AWS Rekognition のアクセス許可をとる

LabRole の許可ポリシーに
`AmazonRekognitionFullAccess`
`AmazonS3FullAccess`
を追加

LabRole の許可ポリシーのところに行くには
Lambda > 適当な関数 > 設定 > 実行ロール > LabRole

s3 のバケットに face.jpg (使用する顔画像) と images/emoji フォルダの画像を入れておく

(以降の設定は、lambda フォルダの README.md を参照)

### とりあえず実行したいなら

cloud9 で実行するには、Pillow などを適宜 pip で install したあと実行

顔の周りに四角を描画

```
python draw_bbox.py
```

顔の部分に絵文字をペースト

```
python draw_emoji.py
```
