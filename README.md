# 日本環境向け AdAway 用 hosts :no_entry_sign:

![ホワイトリスト数](https://img.shields.io/badge/allow-48-brightgreen)
![ブロック数](https://img.shields.io/badge/block-13151-red)


---

AdAway 用の hosts ファイルです。  
詳細は以下を参照。

---
## hosts.txt
***従来のhostsファイルです***
```
https://raw.githubusercontent.com/lawnn/adaway-hosts/refs/heads/master/hosts.txt
```

## hosts_allow.txt
***ホワイトリストファイルです***
```
https://raw.githubusercontent.com/lawnn/adaway-hosts/refs/heads/master/hosts_allow.txt
```

## uBO-to-hosts.txt

***yuki氏豆腐氏のuBO用フィルターをhostsに変換してます。***
***余計なものまでブロックするので非推奨***
```
https://raw.githubusercontent.com/lawnn/adaway-hosts/refs/heads/master/uBO-to-hosts.txt
```


### 名前解決ができなくなった domain は随時削除しています。

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