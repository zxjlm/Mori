# Mori

Mori 是一个用来检测 api 各种属性的脚本。

名字取自 _Mori Kokoro_ , 也就是毛利小五郎, 迷迷糊糊中完成的一个脚本。

## 主要功能

1. 检测 api 是否存在
2. 检测 api 是否包含指定的路径
3. 检测指定叶子节点的值(可选)

## TODO

- [ ] 拆分文件,简化代码
- [ ] 完善案例
- [ ] 添加 test

## Usage

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

## 关于 apis.json 文件

所有的待搜索 api 都放在一个 json 文件中。

画风如下。

```json
[
  {
    "name": "淘宝商品搜索建议",
    "url": "https://suggest.taobao.com/sug?code=utf-8&q=%E7%89%99%E8%86%8F",
    "regex": "result"
  },
  ...
]
```

### 参数说明

- name(str) : 尽量唯一
- url(str) : json 接口的 url
- data(dict,optional) : data 是 post 时提交的数据; 支持使用 _{{time}}_ 之类的伪参数，程序会对该类型的参数进行一次渲染
  - {{time}} : 13 位的 unix 时间戳
- header(dict,optional) : 默认的 header 中提供一个 UA,如果有需要补充的，如 Refer 等，可以自行规定
- regex(str,optional) : 遍历深度,如附录 1 中的示例代码. $number$ 中的 number 是遇到列表时使用的索引值.
  - class->$0$->students->$1$->name : 最终将检索到 _Tio_
- decrypt(str,optional) : 外装 json 解析函数,值为文件名(如:mori_decrypt),详见[关于 **加密的** json 的解析](<#关于加密的\ json\ 的解析>)

### 补充说明

1. 没有特别规定 HTTP method，如果有 data，则默认是 POST 请求

## 关于加密的 json 的解析

有些网站返回的 json 数据可能是经过加密的，这里提供一个外装的 json 解析器( _class_ )。

该 class 继承自 _decrypt.py_ 的 **BaseDecrypt** ,所以自然就有了如下要求:

1. 必须包含 Decrypt 类
2. Decrypt 类必须包含 decrypt(str)函数

## 附录

### 1. 示例代码

```json
{
  "class": [
    {
      "name": "A",
      "total": 64,
      "mid-term-examination": 2,
      "students": [
        {
          "number": "1",
          "name": "Ren",
          "sex": "F"
        },
        {
          "number": "2",
          "name": "Tio",
          "sex": "F"
        }
      ]
    }
  ]
}
```
