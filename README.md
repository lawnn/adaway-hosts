# 日本環境向け AdAway 用 hosts :no_entry_sign:

![ホワイトリスト数](https://img.shields.io/badge/allow-48-brightgreen)
![ブロック数](https://img.shields.io/badge/block-13463-red)

## 注意
このhostsの定期更新は終了しました。  
今後は寄付いただいたタイミングでの更新とさせていただきます。
## Attention
The regular update of this hosts has ended.  
From now on, we will update it when we receive your donation.

---

AdAway 用の hosts ファイルです。  
詳細は以下を参照。

* [日本環境向け AdAway 用 hosts](https://logroid.blogspot.com/2021/05/adaway-hosts-for-japan.html)

名前解決ができなくなった domain は随時削除しています。  
要望・報告は issue or [blog](https://logroid.blogspot.com/2021/05/adaway-hosts-for-japan.html) のフォームにお願いします。

## Support this project

Ongoing maintenance of this project is made possible by the support of these wonderful backers.
* [Amazon Gift Card](https://www.amazon.co.jp/gp/product/B004N3APGO) Send to (logroid.dev@gmail.com)
* [GitHub Sponsors](https://github.com/sponsors/logroid)

Thank you!

このプロジェクトの継続的なメンテナンスは、支援者のサポートのおかげで可能になっています。
* [Amazon Gift Card](https://www.amazon.co.jp/gp/product/B004N3APGO) 送信先 (logroid.dev@gmail.com)
* [GitHub Sponsors](https://github.com/sponsors/logroid)

でご支援いただくことで、このプロジェクトをより良いものにすることができます。ありがとうございます！

---
* [@logroid](https://twitter.com/logroid)       

# remove_hosts.py
名前解決ができなくなった domain をこのコマンド一つで削除します(hosts.txtのみ) 

# android private DNS の設定方法       
下記noteをご覧ください     
※ 無料部分で大体のやり方は書いてます.        
[Pi-hole + nginx + android private dns(DoT) 家でも外出先でも広告カット](https://note.com/shiba_memo_note/n/ncb76466a5e55)        
        
# ubuntuを使い定期的にアップデート      
 - ssh接続ができるようにする       
 - レポジトリをクローンする   
 ```git clone git@github.com:lawnn/adaway-hosts.git hosts```
 - cronの設定例(毎月1日0時0分にアップデートする)
 ```
# your_name = usernameに置き換えてください
 00 00 01 * * /usr/bin/python3 /home/"your_name"/hosts/remove_hosts.py
 ```