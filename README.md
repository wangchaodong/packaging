# iOS Auto Packaging

iOS自动打包脚本

## 准备

* 脚本第一次执行之前 先检查依赖, packaging目录下终端执行 
* pip3 install -r requirements.txt

## 运行

``` shell
cd packaging
python3 packaging.py -s <scheme> -m <message> -ab <addBuildNumber> -pgy <pgy> -as <appstore>
```

## 配置

* configs.py 脚本的一些基本配置, 一些文件路径需要根据项目进行修改
* config.json 打包的相关配置, 运行脚本前先配置该文件的一些参数
* build目录是打包后的文件,建议加入到.gitignore

## 命令行参数

```
packaging.py -s <scheme> -m <message> -ab <addBuildNumber> -pgy <pgy> -as <appstore>
-h      help
-s      scheme: xcode project schemes
-m      message: app update message.
-ab     addBuildNumber: a boolean value, weather auto increase build number or not. yes will +1, no do nothing.
-pgy    pgy: a boolean value, weather upload ipa to pgy or not. 
-as    appstore: a boolean value, weather upload ipa to appstore or not.
```

## 命令行交互

* 输入 ("yes", "YES", "Yes", "y", "true", "True", "t", "1", "Y") 为 true
* 输入("no", "n", "false", "False", "FALSE", "f", "0", "0.0", "", "none", "[]", "{}", "N") 为 False


## 参考文档: 

* https://developer.apple.com/library/archive/technotes/tn2339/_index.html
* https://help.apple.com/asc/appsaltool/#/apdATD1E53-D1E1A1303-D1E53A1126
* https://www.pgyer.com/doc/view/api#uploadApp

## config.json

    "project_name": 项目名,
    "project_scheme_list": 需要打包的scheme,
    "project_scheme_index": project_scheme_list对应的index
    "apple_account_team_id": apple developer account teamID,
    "upload_pgy_enable": 是否上传pgy,
    "pgy_api_key": pgy_api_key,
    "upload_app_sotre_enable": 是否上传App Store,
    "upload_app_store_account_type" : 上传App Store账号类型 1 使用账号/密码, 2使用apikey/apiIssuer
    "apple_account_user":  apple 账号,
    "apple_account_password": apple 账号密码 ,
    "apple_account_apiKey": apple账号apiKey,
    "apple_account_apiIssuer": apple账号apiIssuer,
    "send_email_enable": 是否发送邮件,
    "email_receivers": 邮件收件人 list,
    "add_build_number_enable": 是否增加build number,
    "log_enable": 是否导出log,
    "provisioning_profiles": {
                bunddleId: mobileprovisioning
            },
    "distribution_method" : development, app-store, ad-hoc,


## xcodebuild 参数

```
xcodebuild -help

compileBitcode 参数类型：Bool
该参数告诉Xcode是否需要通过bitcode重新编译，需要与app中的Enable Bitcode配置一致。

destination 参数类型：String
该参数用来确认当前app是本地导出还是上传到Apple的服务器。可以填写的值为export、upload，默认值为export。

distributionBundleIdentifier 参数类型：String
该参数用来格式化包内可用目标的bundle identifier。

embedOnDemandResourcesAssetPacksInBundle参数类型：Bool
该参数在非app store的导出类型下有效。如果app使用了On Demand Resources功能，该选项为YES时，app将会加载所有的资源，可以在没有服务器支持下使用该app。如果没有配置onDemandResourcesAssetPacksBaseURL选项，则默认值为YES。

generateAppStoreInformation
参数类型：Bool
该参数在app store的导出类型下有效。在iTMSTransporter上传时判断是否生成App Store的相关信息。默认值为NO。

iCloudContainerEnvironment参数类型：String

manifest 参数类型：Dictionary
该参数在非app store的导出类型下有效。该参数用于web上安装测试应用包使用。该字典包含appURL、displayImageURL、fullSizeImageURL，如果使用了On Demand Resources，还需要配置assetPackManifestURL。

method 参数类型：String
该参数确定Xcode该如何导出应用包。可用的选项为：app-store、validation、ad-hoc、package、enterprise、development, 、developer-id和mac-application。默认值为development。

onDemandResourcesAssetPacksBaseURL 参数类型：String
该参数在非app store的导出类型下有效。如果app使用了On Demand Resources，并且embedOnDemandResourcesAssetPacksInBundle配置不是YES，则需要配置该字段。该配置确定app如何下载On Demand Resources资源。

provisioningProfiles 参数类型：Dictionary
该参数在手动配置签名下生效。指定包内所有可执行文件的描述文件。其中key为可执行文件对应的bundle identifier，value为描述文件的文件名或UUID。

signingCertificate 参数类型：String
该参数在手动配置签名下生效。可以配置为证书名称、SHA-1 Hash或者自动选择。其中自动选择允许Xcode自动选择最新可以使用的证书，可选值为：”iOS Developer”、”iOS Distribution”、”Developer ID Application”、”Apple Distribution”、”Mac Developer”和”Apple Development”。默认值和导出类型相关。

signingStyle 参数类型：String
该选项用来确定签名方式，可选值为manual和automatic。如果app配置为自动签名，打包前可以修改此配置，否则该配置会被忽略。

stripSwiftSymbols
参数类型：Bool 该参数用来确认是否需要对swift库进行裁剪。默认值为YES。

teamID 参数类型：String
该参数表明导出包使用的开发者ID。

thinning 参数类型：String
该参数在非app store的导出类型下有效。使用该参数可以打包出指定设备的精简包。可选项为（不精简）、（生成一个通用包和所有精简包）或者指定设备的标识符（如：”iPhone7, 1”）。默认值为。

uploadBitcode 参数类型：Bool
该参数在app store的导出类型下有效。用来配置导出的包是否包含bitcode。默认值为YES。

uploadSymbols 参数类型：Bool
该参数在app store的导出类型下有效。用来配置导出的包是否包含符号表。默认值为YES

```
