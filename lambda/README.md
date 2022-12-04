## lambdaでの設定

### import PIL
`import PIL` のために作成した、layer.zipを利用してレイヤーを設定する。
lambdaの関数で、ランタイムがpython3.9, アーキテクチャがx86_64であることを確認する。

参考の3つ目 (レイヤーを作成) のやり方で設定を進める。zipファイル作成までの手順は省略できるはず。
[[AWS Lambda] Pythonで外部モジュール(Pillow)を使う](https://qiita.com/Bashi50/items/1f72a93dbde23de55dda)


### その他
time outとなる場合は、実行時間上限を30秒に変更する。
[【AWS】Lambdaでtime out after 3.00 secondsが出たときの対処法](https://qiita.com/yokoyan/items/7a39a99996f2ade4af5b)
