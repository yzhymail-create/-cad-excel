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

## UI 预览

仓库内提供静态预览图：`ui-preview.html`，用于确认极简布局与字体大小。

## 参考与借鉴（GitHub 开源项目）

- Cashew: https://github.com/jameskokoska/Cashew
- My Expenses: https://github.com/mtotschnig/MyExpenses
- Expenso: https://github.com/Spikeysanju/Expenso
- MoneyWallet: https://github.com/hkohan/moneywallet
