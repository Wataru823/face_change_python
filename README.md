## AWS Rekognitionを用いて顔画像を処理
CC実験用

## AWS Rekognitionのアクセス許可をとる
LabRoleの許可ポリシーに
`AmazonRekognitionFullAccess`
`AmazonS3FullAccess`
を追加

LabRoleの許可ポリシーのところに行くには
Lambda > 適当な関数 > 設定 > 実行ロール > LabRole

s3のバケットにface.jpg (使用する顔画像) とimages/emojiフォルダの画像を入れておく
cloud9で実行するには、Pillowなどを適宜pipでinstallしたあと実行

顔の周りに四角を描画
```
python draw_bbox.py
```

顔の部分に絵文字をペースト
```
python draw_emoji.py
```
