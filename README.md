# Mori

Mori 是一个用来检测 api 各种属性的脚本。

主体的灵感来自于 [sherlock](https://github.com/sherlock-project/sherlock)

> 补充：
>
> sherlock 的功能 ：  
> Hunt down social media accounts by username across social networks  
> 也就是通过爬虫技术检测 username 是否存在于 Sherlock 记录中的社交网站

# 主要功能

1. 检测 api 是否存在
2. 检测 api 是否包含指定的路径
3. 检测指定叶子节点的值(可选)

# Usage

```shell
usage: mori [-h] [--version] [--verbose] [--csv] [--show-all-site]
               [--json JSON_FILE] [--print-invaild] [--timeout TIMEOUT]

Mori Kokoro (Version v0.1)

optional arguments:
  -h, --help            show this help message and exit
  --version             Display version information and dependencies.
  --verbose, -v, -d, --debug
                        Display extra debugging information and metrics.
  --csv                 Create Comma-Separated Values (CSV) File.
  --show-all-site       Show all infomations of the apis in files.
  --json JSON_FILE, -j JSON_FILE
                        Load data from a JSON file or an online, valid, JSON
                        file.
  --print-invaild       Output api(s) that was invalid.
  --timeout TIMEOUT     Time (in seconds) to wait for response to requests.
                        Default timeout is infinity. A longer timeout will be
                        more likely to get results from slow sites. On the
                        other hand, this may cause a long delay to gather all
                        results.
```

# 关于 apis.json 文件

所有的待搜索 api 都放在一个 json 文件中。

画风如下。

```json
[
  {
    "name": "淘宝商品搜索建议",
    "url": "https://suggest.taobao.com/sug?code=utf-8&q=%E7%89%99%E8%86%8F",
    "regex": "result"
  }
]
```
