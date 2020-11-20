# Mori

Mori 是一个用来检测 api 各种属性的脚本。

名字取自 _Mori Kokoro_ , 也就是 _毛利小五郎_ , 迷迷糊糊中完成的一个脚本

![mori.PNG](https://i.loli.net/2020/11/04/2rd9oFCMbUG7lLj.png)

## 主要功能

1. 检测 api 是否存在
2. 检测 api 是否包含指定的路径
3. 检测指定叶子节点的值(可选)

## TODO

- [x] 拆分文件,简化代码 -> 初步完成
- [x] 完善案例
- [ ] 添加 test
- [x] 兼容反反爬虫方法 [antispider参数](#参数说明)
- [x] 扩展 proxy 调用方法 [proxy参数](#参数说明)
- [x] 添加强校验模式
- [x] 添加发送邮件选项 [--email](#关于-configpy-文件)
- [x] 特化代理
- [x] 添加 traceback
- [x] 添加注释
- [ ] 对 --verbose 输出上色
- [x] 对代理进行校验 [strict_proxy参数](#参数说明)

![email.PNG](https://i.loli.net/2020/11/06/1uxYtDOUyAWdkEa.png)

## Installation

```shell
# installation
$ git@github.com:zxjlm/Mori.git
$ cd Mori
$ pip install -r requirements.txt

# use
$ python mori.py

# help
$ python mori.py --help
```

## Usage

```shell
usage: mori.py [-h] [--version] [--verbose] [--xls] [--show-all-site]
               [--json JSON_FILE] [--email] [--print-invaild]
               [--timeout TIMEOUT]

Mori Kokoro (Version v0.4)

optional arguments:
  -h, --help            show this help message and exit
  --version             Display version information and dependencies.
  --verbose, -v, -d, --debug
                        Display extra debugging information and metrics.
  --xls                 Create .xls File.(Microsoft Excel file format)
  --show-all-site       Show all infomations of the apis in files.
  --json JSON_FILE, -j JSON_FILE
                        Load data from a local JSON file.
  --email, -e           Send email to mailboxes in the file 'config.py'.
  --print-invaild       Output api(s) that was invalid.
  --timeout TIMEOUT     Time (in seconds) to wait for response to requests.
                        Default timeout is infinity. A longer timeout will be
                        more likely to get results from slow sites. On the
                        other hand, this may cause a long delay to gather all
                        results.
```

## 关于 apis.json 文件

所有的待搜索 api 都放在一个 json 文件中, 脚本会默认调用 apis.json 但是可以通过 **--json** 来指定另外的文件。

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

- name(str ) : 配置名, **唯一**
- url(str) : json 接口的 url
- base_url(str,optional) : 主页面的url,目的是方面报错之后查看
- data(dict,optional) : data 是 post 时提交的数据;  
  支持使用 _{{time}}_ 之类的伪参数，程序会对该类型的参数进行一次渲染
  - {{time}} : 13 位的 unix 时间戳
- header(dict,optional) :  
  默认的 header 中提供一个 UA,如果有需要补充的，如 Refer 等，可以自行规定
- regex(list,optional) :  
  遍历深度,如 [附录](#附录) 中的示例代码. $number$ 中的 number 是遇到列表时使用的索引值.
  - class->$0$->students->$1$->name : 最终将检索到 _Tio_
- proxy(str,optional) : 支持使用代理.调用方法如下：
  - 字符串的内容为代理池的接口地址,形如:_"http://proxy-api.com"_  
    返回代理(response.text)的格式,形如: _"http://\*.\*.\*.\*:\*"_
- strict_proxy(str,optional): 代理校验网站,仅在proxy有配置的情况下有效
  - 默认情况下，代理会通过百度( _"http://www.baidu.com"_ )进行可用性校验.校验的网站可以通过修改该参数改变.
  - 可以将值设为 _'skip'_ 跳过校验
- decrypt(str,optional) :  
  外装 json 解析函数,值为文件名(如:mori_decrypt),详见[关于 **加密的** json 的解析](#关于加密的-json-的解析)
- antispider(str,optional) :  
  外装 反爬虫 解决方案,使用方法同 decrypt,样例见 **mori_antispider.py**
- remark(str, optional) : 备注信息

### 补充说明

1. 没有特别规定 HTTP method，如果有 data，则默认是 POST 请求

## 关于 config.py 文件

该文件当且仅当使用 _email_ 参数时生效(也就是使用 **发送邮件** 功能时)

文件必须包含以下参数:

```shell
RECEIVERS = list # 接收人
MAIL_HOST = str  # stmp服务器
MAIL_USER = str # 发送人
MAIL_PASS = str # 密码
MAIL_SUBJECT = str # 邮件主题
MAIL_PORT = str # SSL时指定
```

## 关于加密的 json 的解析

有些网站返回的 json 数据可能是经过加密的，这里提供一个外装的 json 解析器( _class_ )。

该 class 继承自 _decrypt.py_ 的 **BaseDecrypt** ,所以自然就有了如下要求:

1. 必须包含 Decrypt 类
2. 必须放置于 **decrypt** 文件夹中
3. Decrypt 类必须包含 decrypt(str)函数

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
