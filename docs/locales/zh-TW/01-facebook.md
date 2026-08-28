---
episode: 1
destination: facebook_tw
locale: zh-TW
status: ready_from_live_canonical
account_status: blocked_identity_unverified
canonical_url: "https://agentivefinancelab.substack.com/p/mcp-and-skills-hit-their-limits-in"
prepared_at: 2026-08-28 Asia/Taipei
---

# Episode 1｜當金融工具愈來愈多，真正缺的是清楚的責任邊界

MCP 解決了工具接取的標準化，Skills 則把可重複的操作方式整理成流程。不過，當金融應用一路擴充到行情、基本面、總經資料、風險與內部資料時，新的問題不是「能不能呼叫 API」，而是：誰負責理解資料來源、誰做選擇、誰實際執行，以及失敗時誰能說清楚原因。

Agentive Finance Lab 的 Episode 1 用一條可執行的單一資料源流程，把責任拆開：

- **Data User（資料使用者）**負責需求與最後的資料源呼叫。
- **Data Consultant（資料顧問）**只根據同步到記憶體的目錄文件提供建議；這條 lite 流程沒有使用 LLM 生成答案。
- **YFinance Data Source（資料來源代理）**擁有端點規格與 `data_fetch` 執行邊界。
- **Plaza（中央協作目錄）**負責註冊、發現與 Pulse 交接，但不代理或合併供應商資料。

這次短片只示範已實作並於本機捕捉的 Data User → Plaza → Data Consultant → YFinance 流程，以及 `yfinance.ticker.history` 的直接呼叫。沒有加入 Alpha Vantage 或 FRED 的執行畫面，也不會把未捕捉的結果說成實測。

這個專案要證明的不是更多代理會帶來更好的報酬，而是金融資料流程能否做到責任清楚、來源可追溯、錯誤不被假資料或其他供應商悄悄掩蓋。

完整文章： https://agentivefinancelab.substack.com/p/mcp-and-skills-hit-their-limits-in

Demo 1： https://github.com/alvincho/agentive-finance-lab#demo-1-data-agent--single-source

想請教大家：如果金融資料呼叫失敗，你會要求系統在哪一層說明原因？在允許切換資料來源之前，又需要哪些證據？

---

Agentive Finance Lab 是教育用途的軟體示範，不提供投資建議、交易建議、資料授權，亦不保證資料來源的可用性、即時性、完整性或正確性。yfinance 與 Yahoo 無關；Yahoo Finance 資料僅供個人使用，並受相關條款限制。

發佈阻擋：尚未提供並驗證台灣 Facebook 專頁或帳號的精確身分，不得改用其他已登入帳號。
