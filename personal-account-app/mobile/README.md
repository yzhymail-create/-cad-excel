# 个人账本（安卓本地版）

面向老人使用的极简记账/存钱应用，**纯本地保存，不依赖网络**。当前原型提供：

- 存钱/记账两类操作
- 自动汇总余额
- 本地持久化（AsyncStorage）
- 大字号、少步骤的极简界面

## 本地运行

```bash
npm install
npm run android
```

## 生成 APK（本地构建）

```bash
npx expo prebuild --platform android
cd android
./gradlew assembleRelease
```

生成的 APK 位于：`android/app/build/outputs/apk/release/`。

## 云构建 APK（无电脑）

如果你没有电脑，可以使用 Expo EAS 云构建：

1. 注册 Expo 账号：https://expo.dev/signup
2. 在 Expo 个人设置中生成 **Access Token**
3. 在 GitHub 仓库设置中添加 `EXPO_TOKEN` Secret
4. 打开 GitHub Actions，手动运行 **Cloud Build Android APK** 工作流
5. 在 EAS 构建页面下载 APK

## UI 预览

仓库内提供静态预览图：`ui-preview.html`，用于确认极简布局与字体大小。

## 参考与借鉴（GitHub 开源项目）

- Cashew: https://github.com/jameskokoska/Cashew
- My Expenses: https://github.com/mtotschnig/MyExpenses
- Expenso: https://github.com/Spikeysanju/Expenso
- MoneyWallet: https://github.com/hkohan/moneywallet
