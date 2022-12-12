## lambda での設定

### import PIL

`import PIL` のために作成した、layer.zip を利用してレイヤーを設定する。
lambda の関数で、ランタイムが python3.9, アーキテクチャが x86_64 であることを確認する。

参考の 3 つ目 (レイヤーを作成) のやり方で設定を進める。zip ファイル作成までの手順は省略できるはず。
[[AWS Lambda] Python で外部モジュール(Pillow)を使う](https://qiita.com/Bashi50/items/1f72a93dbde23de55dda)

### その他

time out となる場合は、実行時間上限を 30 秒に変更する。
[【AWS】Lambda で time out after 3.00 seconds が出たときの対処法](https://qiita.com/yokoyan/items/7a39a99996f2ade4af5b)

S3 に画像をアップロードしたら自動で lambda 関数が実行されるようにするには、トリガーを設定する。(lambda_function.py のコードはトリガーに対応済み)
