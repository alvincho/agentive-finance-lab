---
episode: 2
destination: facebook_tw
locale: zh-TW
status: prepared
canonical_url: null
canonical_link_policy: inject_verified_substack_url_at_delivery
prepared_at: 2026-08-29 Asia/Taipei
---

# Episode 2｜先把多代理金融實驗室跑起來，再談框架名詞

架構圖畫得再漂亮，都不能取代一個真的能啟動、能檢查、能看到失敗邊界的執行結果。

Agentive Finance Lab 的 Episode 2 先不急著解釋 Pit、Plaza、Pulse、Pulser 或 Persona，而是先完成最實際的操作路徑：

- 從 GitHub 複製公開儲存庫
- 建立 Python 3.11 以上的虛擬環境
- 用一個啟動指令開啟本機服務
- 透過 `/health` 檢查單一資料源網路
- 找到 Single Source、Multiple Sources 與 Real Data 三個 Demo

這次操作不需要 API 金鑰、資料庫、Node.js、模型帳號或外部代理服務。啟動指令是：

```bash
python demos/data-agent-network-demo/run.py --open
```

健康檢查會回報 Demo 1 已註冊 3 個參與者與 1 個 YFinance 資料來源。這裡的「健康」只表示本機縮減版網路已啟動，不代表上游資料一定可用，也不保證資料即時性、正確性或適合任何投資用途。

這個專案是從 FinMAS——原始完整金融多代理應用——縮減而來的可執行公開示範。保留的是 Data User（資料使用者）、Data Consultant（資料顧問）、Data Source（資料來源代理）與明確的互動邊界；移除的是分散式傳輸、帳號、驗證、計費、持久化記憶與模型路由等正式環境服務。

先有一個能重現的本機結果，下一集再來拆解為什麼依賴方向是 `demos → phemacast-lite → prompits-lite`，以及「Lite」為什麼代表範圍縮減，而不是把架構重寫。

執行說明：
https://github.com/alvincho/agentive-finance-lab#quick-start-clone-and-run-the-ui

正式發佈時，系統會自動附上已驗證的 Substack 原始文章網址。

想請教大家：你認為一個多代理開源專案要具備哪些證據，才算真的「可執行」？成功安裝、健康檢查、可見的參與者，還是至少一條完整請求流程？

---

Agentive Finance Lab 是教育用途的軟體示範，不提供投資建議、交易建議或資料授權，也不保證資料來源的可用性、即時性、完整性或正確性。即時資料仍受各供應商條款與限制規範。
