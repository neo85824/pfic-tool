export type Lang = 'en' | 'zh'

export interface Section {
  id: string
  heading: string
  body: string
}

export interface FAQ {
  q: string
  a: string
}

export interface ManualContent {
  title: string
  subtitle: string
  backLabel: string
  toggleLabel: string
  tocLabel: string
  sections: Section[]
  faq: Section & { items: FAQ[] }
}

export const content: Record<Lang, ManualContent> = {
  en: {
    title: 'PFIC §1291 Calculator — User Manual',
    subtitle: 'Form 8621 Excess Distribution Method',
    backLabel: '← Back',
    toggleLabel: '繁體中文',
    tocLabel: 'Contents',
    sections: [
      {
        id: 'overview',
        heading: '1. Overview',
        body: `This tool computes U.S. tax liability for Passive Foreign Investment Companies (PFICs) under the Excess Distribution method (IRC §1291). It produces the figures needed to complete Form 8621 Part V and generates three export documents:

• Excel Workpaper — full calculation detail for CPA review
• PDF Workpaper — printable Form 8621 Part V summary
• Line 16a Attachment — required §6501(c)(8) statement

The calculation follows the IRS Form 8621 instructions and applies historical maximum marginal rates, §6621 underpayment interest rates (compounded daily per §6622), and §7503 filing deadline rules including COVID extensions (Notice 2020-23, Notice 2021-21).`,
      },
      {
        id: 'step1',
        heading: '2. Step 1 — Add a Client & PFIC Holding',
        body: `**Client**
A Client record represents one taxpayer. The Client Code is a short label you choose (e.g. "SMITH-2024"). It appears on all exported documents.

**PFIC Holding**
Each client can have one or more PFIC holdings. When creating a holding you supply:
• PFIC Name — the fund or company name (e.g. "Vanguard FTSE All-World")
• First PFIC Year — the first year the fund qualified as a PFIC (optional; used for pre-PFIC day classification)
• IRS Reference ID — optional; printed on exports

The holding stores all transactions (purchases and distributions) and links to all calculation runs.`,
      },
      {
        id: 'step2',
        heading: '3. Step 2 — Upload Transactions',
        body: `Transactions represent purchases and distributions for the holding. You can add them one by one or upload a CSV file.

**CSV Format**
Download the template from the Upload CSV panel. Required columns:
• date — YYYY-MM-DD (e.g. 2020-03-15)
• type — "buy" or "distribution"
• units — number of shares (required for buy; leave blank for distribution)
• total_value_usd — total USD amount of the transaction

**Tips**
• Buy transactions must have units. The engine tracks lots in FIFO order.
• Distribution transactions record the total cash received in the tax year.
• You can upload multiple times — new rows are appended, duplicates are not created.
• Use the Export CSV button to download the current transaction list and re-import it elsewhere.`,
      },
      {
        id: 'step3',
        heading: '4. Step 3 — Run the Calculation',
        body: `Select the tax year (the year you received the distribution) and click Run Calculation.

The engine performs the following steps:
1. Identifies all purchase lots held at year-end via FIFO.
2. Computes the prior 3-year average distribution to determine the 125% threshold (§1291(b)(2)(A)).
3. Splits the current-year distribution into non-excess (ordinary income) and excess portions.
4. Allocates the excess ratably across every day of each lot's holding period (§1291(a)(1)(A)).
5. Classifies each year as pre-PFIC, prior PFIC, or current year.
6. Applies the historical maximum marginal rate to each prior PFIC year's allocation.
7. Compounds §6621 interest daily from each year's filing deadline to the current return's due date.

Results are saved and can be re-opened at any time without re-running.`,
      },
      {
        id: 'step4',
        heading: '5. Step 4 — Read the Results',
        body: `The Results page has five sections:

**125% Test**
Shows the current distribution, prior 3-year average, and 125% benchmark. The excess distribution is any amount above the benchmark.

**Excess Distribution by Lot**
Each purchase lot's proportional share of the excess, with its deferred tax, §6621 interest, and grand total.

**Step 2 — Year-by-Year Allocation & Tax**
The excess is spread across each year of the holding period at a daily rate. Prior PFIC years show the historical rate (39.6% before 2018, 37% from 2018). Current-year and pre-PFIC years show "ordinary income" — no deferred tax.

**Step 3 — §6621 Interest**
Interest is charged on each prior PFIC year's deferred tax from that year's filing deadline to the current return's due date, compounded daily.

**Form 8621 Part V Summary**
• Line 15e(1) / 16b — non-excess ordinary income
• Line 15e(2) — excess distribution
• Line 16c — total additional §1291 tax
• Line 16f — total §6621 interest
• Grand total — sum of 16c + 16f (additional liability beyond regular tax)`,
      },
      {
        id: 'step5',
        heading: '6. Step 5 — Export',
        body: `Three export formats are available:

**Excel Workpaper (.xlsx)**
Five sheets mirroring the result page:
1. Summary — 125% Test + Form 8621 Part V summary
2. Lot Summary — per-lot excess, tax, interest
3. Year Allocation — year-by-year ratable allocation
4. Interest Detail — §6621 interest by year
5. Daily Allocation — full day-by-day breakdown

**PDF Workpaper**
A printable version of the same five sections. Attach to your working file.

**Line 16a Attachment**
The required §6501(c)(8) statement. Must be attached to the filed Form 8621. Failure to attach leaves the PFIC items open to IRS examination indefinitely.`,
      },
      {
        id: 'concepts',
        heading: '7. Key Tax Concepts',
        body: `**§1291 Excess Distribution**
A distribution is "excess" if it exceeds 125% of the average distributions received in the prior 3 years. The excess portion is not taxed at the current year's ordinary rate — instead it is allocated back across the entire holding period.

**Ratable Daily Allocation**
The excess is divided by the total number of holding-period days to get a daily rate. Each calendar year receives: days-in-that-year × daily-rate.

**Prior PFIC Years vs. Current Year**
• Prior PFIC years (1987 and later, before the distribution year) → deferred tax + §6621 interest
• Current year → ordinary income at the taxpayer's current rate (no interest)
• Pre-PFIC years (before 1987) → ordinary income (§1291 does not apply)

**Historical Maximum Marginal Rates**
The engine applies the top ordinary income rate in effect for each prior year:
• 1987–2017: 39.6% (post-TCJA rates apply only from 2018)
• 2018–present: 37%

**§6622 Daily Compound Interest**
Interest accrues from the filing deadline of the return for each prior year to the filing deadline of the current year's return. The rate changes quarterly (IRS §6621 underpayment rate). Compounding is daily.

**COVID Filing Extensions**
• 2019 return: deadline extended from 2020-04-15 → 2020-07-15 (Notice 2020-23)
• 2020 return: deadline extended from 2021-04-15 → 2021-05-17 (Notice 2021-21)
These extensions reduce the interest accrual period for those years. The engine applies them automatically.

**§6501(c)(8) Statute of Limitations**
If you fail to attach the Line 16a daily allocation statement to a filed Form 8621, the IRS can assess tax on those PFIC items at any time — the normal 3-year statute does not run. Always attach the Line 16a export.`,
      },
    ],
    faq: {
      id: 'faq',
      heading: '8. FAQ',
      body: '',
      items: [
        {
          q: 'What if I have no distributions in one or more of the prior 3 years?',
          a: 'The prior 3-year average is computed over only the years that had distributions, up to 3. If there were fewer than 3 prior distribution years, the engine divides by the actual number of years available. This matches the Form 8621 instructions.',
        },
        {
          q: 'The tool shows "ordinary income" for 2022 even though I owned the PFIC since 2015. Why?',
          a: 'The current tax year (the year you received the distribution) is always treated as ordinary income under §1291(a)(1)(C). Only prior PFIC years (1987 through the year before the distribution) bear deferred tax and §6621 interest.',
        },
        {
          q: 'Why does the interest look small compared to the deferred tax?',
          a: '§6621 interest is computed only on the deferred tax amount for each year — not on the full excess distribution. For example, a $37 deferred tax accruing interest for ~3 years at ~5% produces only about $6 of interest. Manual calculations that apply interest to the full distribution amount will be dramatically overstated.',
        },
        {
          q: 'Can I use this tool for dispositions (sales) instead of distributions?',
          a: 'The current version is designed for excess distributions only. Gains on disposition are also subject to §1291, but require a different calculation path. Disposition support may be added in a future version.',
        },
        {
          q: 'How do I handle multiple lots with different acquisition dates?',
          a: 'Enter each purchase as a separate "buy" transaction with its date and units. The engine tracks lots in FIFO order and allocates the excess proportionally across all lots held at year-end. The Lot Summary section in the results shows the breakdown per lot.',
        },
      ],
    },
  },

  zh: {
    title: 'PFIC §1291 計算工具 — 使用說明',
    subtitle: 'Form 8621 超額分配計算方式',
    backLabel: '← 返回',
    toggleLabel: 'English',
    tocLabel: '目錄',
    sections: [
      {
        id: 'overview',
        heading: '1. 概述',
        body: `本工具依據 IRC §1291（超額分配法）計算被動外國投資公司（PFIC）的美國稅務負擔，產出完成 Form 8621 Part V 所需的數據，並提供三種匯出文件：

• Excel 工作底稿 — 完整計算細節，供 CPA 審閱
• PDF 工作底稿 — 可列印的 Form 8621 Part V 摘要
• Line 16a 附件 — §6501(c)(8) 要求的法定附件

計算程序依照 IRS Form 8621 說明，使用歷史最高邊際稅率、§6621 罰息率（依 §6622 每日複利），並應用 §7503 申報截止日規則（含新冠疫情延期：Notice 2020-23、Notice 2021-21）。`,
      },
      {
        id: 'step1',
        heading: '2. 第一步 — 新增客戶與 PFIC 持有',
        body: `**客戶（Client）**
一個客戶記錄代表一位納稅人。客戶代碼（Client Code）是您自訂的簡短標籤（例如「SMITH-2024」），會顯示在所有匯出文件上。

**PFIC 持有（Holding）**
每位客戶可有一個或多個 PFIC 持有。建立持有時需填寫：
• PFIC 名稱 — 基金或公司名稱（例如「Vanguard FTSE All-World」）
• 首個 PFIC 年份 — 該基金首次被認定為 PFIC 的年度（選填；用於判斷前 PFIC 日期分類）
• IRS 參考編號 — 選填；會印在匯出文件上

持有記錄儲存所有交易（買入及分配）並連結所有計算結果。`,
      },
      {
        id: 'step2',
        heading: '3. 第二步 — 上傳交易記錄',
        body: `交易記錄代表該持有的買入及分配。可逐筆新增或上傳 CSV 檔案。

**CSV 格式**
請從「上傳 CSV」面板下載範本。必填欄位：
• date — 日期格式 YYYY-MM-DD（例如 2020-03-15）
• type — "buy"（買入）或 "distribution"（分配）
• units — 股數（買入時必填；分配時可留空）
• total_value_usd — 交易金額（美元）

**注意事項**
• 買入交易必須填入股數，引擎以先進先出（FIFO）順序追蹤每批次。
• 分配交易記錄該稅務年度收到的現金總額。
• 可多次上傳，新資料會被附加，不會產生重複記錄。
• 可使用「匯出 CSV」按鈕下載目前的交易清單，以便備份或移轉。`,
      },
      {
        id: 'step3',
        heading: '4. 第三步 — 執行計算',
        body: `選擇稅務年度（即收到分配的年度），然後點擊「執行計算」。

引擎執行以下步驟：
1. 透過 FIFO 識別年末持有的所有買入批次。
2. 計算前三年平均分配額，以確定 125% 基準（§1291(b)(2)(A)）。
3. 將當年度分配拆分為非超額部分（普通所得）及超額部分。
4. 依每日比例將超額部分分配至每批次持有期間的每一天（§1291(a)(1)(A)）。
5. 將每年分類為：前 PFIC 年（1987 年前）、先前 PFIC 年、或當年度。
6. 對每個先前 PFIC 年分配額套用歷史最高邊際稅率。
7. 從每年申報截止日起至當期申報截止日，每日複利計算 §6621 利息。

計算結果會儲存，可隨時重新查閱，無需重新計算。`,
      },
      {
        id: 'step4',
        heading: '5. 第四步 — 解讀結果',
        body: `結果頁面分為五個區塊：

**125% 測試**
顯示當年度分配額、前三年平均值及 125% 基準值。超出基準的部分即為超額分配。

**各批次超額分配明細**
每個買入批次在超額部分的比例分攤，及其遞延稅款、§6621 利息與總計金額。

**第二步 — 逐年分配與稅款**
超額部分以每日比例分配至持有期間每一年。先前 PFIC 年顯示歷史稅率（2018 年前 39.6%，2018 年起 37%）。當年度及前 PFIC 年顯示「普通所得」，無遞延稅款。

**第三步 — §6621 利息**
對每個先前 PFIC 年的遞延稅款，從該年申報截止日起至當期申報截止日，按每日複利計息。

**Form 8621 Part V 摘要**
• Line 15e(1) / 16b — 非超額普通所得
• Line 15e(2) — 超額分配
• Line 16c — §1291 額外稅款合計
• Line 16f — §6621 利息合計
• 總計 — 16c + 16f（超出一般申報的額外稅負）`,
      },
      {
        id: 'step5',
        heading: '6. 第五步 — 匯出文件',
        body: `提供三種匯出格式：

**Excel 工作底稿（.xlsx）**
五個工作表，與結果頁面一一對應：
1. 摘要 — 125% 測試 + Form 8621 Part V 摘要
2. 批次摘要 — 各批次超額、稅款、利息
3. 逐年分配 — 每日比例的逐年分配
4. 利息明細 — 各年度 §6621 利息
5. 每日分配 — 完整的逐日明細

**PDF 工作底稿**
上述五個區塊的可列印版本，附入工作文件備查。

**Line 16a 附件**
§6501(c)(8) 要求的法定申報附件，必須隨 Form 8621 一同申報。若未附上，IRS 可在任何時間評估 PFIC 相關稅款，正常三年追溯期限不適用。`,
      },
      {
        id: 'concepts',
        heading: '7. 重要稅務概念',
        body: `**§1291 超額分配**
若分配額超過前三年平均值的 125%，超出部分即為「超額分配」。超額部分不以當年度普通所得稅率課稅，而是回溯分配至整個持有期間。

**每日比例分配**
超額分配除以持有期間總天數，得到每日金額。每個日曆年分得：該年天數 × 每日金額。

**先前 PFIC 年 vs. 當年度**
• 先前 PFIC 年（1987 年及以後，早於分配年度）→ 遞延稅款 + §6621 利息
• 當年度 → 以納稅人當期稅率課徵普通所得（不計利息）
• 前 PFIC 年（1987 年前）→ 普通所得（§1291 不適用）

**歷史最高邊際稅率**
引擎對每個先前 PFIC 年套用當時的最高普通所得稅率：
• 1987–2017 年：39.6%（2018 年起 TCJA 才降低稅率）
• 2018 年至今：37%

**§6622 每日複利**
從各先前年度申報截止日至當期申報截止日，依 §6621 拖欠利率每日複利計算。利率每季調整。

**新冠疫情延期**
• 2019 年申報截止日：由 2020-04-15 延至 2020-07-15（Notice 2020-23）
• 2020 年申報截止日：由 2021-04-15 延至 2021-05-17（Notice 2021-21）
延期縮短了這兩年的利息計算期間，引擎自動處理。

**§6501(c)(8) 追溯期限**
若未隨 Form 8621 附上 Line 16a 每日比例分配說明書，IRS 可在任何時間對 PFIC 項目補稅，一般三年追溯期限不適用。請務必附上 Line 16a 匯出文件。`,
      },
    ],
    faq: {
      id: 'faq',
      heading: '8. 常見問題',
      body: '',
      items: [
        {
          q: '如果前三年中有一年或數年沒有分配記錄，應如何處理？',
          a: '前三年平均值僅計算有分配記錄的年份，最多三年。若有效年份不足三年，引擎以實際年份數為除數，與 Form 8621 說明一致。',
        },
        {
          q: '我從 2015 年起持有 PFIC，但 2022 年的分配顯示為「普通所得」，為什麼？',
          a: '依 §1291(a)(1)(C)，收到分配的當年度（當年度）永遠以普通所得處理。只有先前 PFIC 年（1987 年至分配年度前一年）才需計算遞延稅款與 §6621 利息。',
        },
        {
          q: '為何利息金額比遞延稅款小很多？',
          a: '§6621 利息僅計算在各年度的遞延稅款上，而非整個超額分配金額。例如 $37 的遞延稅款，約 3 年以 5% 利率計算，利息約只有 $6。若將利息計算套用於整個分配金額，結果將大幅高估。',
        },
        {
          q: '本工具可用於出售 PFIC 的資本利得計算嗎？',
          a: '目前版本僅支援超額分配計算。出售所得依 §1291 同樣需申報，但計算路徑不同。未來版本可能新增出售計算功能。',
        },
        {
          q: '持有多個不同買入日期的批次，如何處理？',
          a: '每筆買入以獨立交易記錄輸入，填入日期與股數。引擎以 FIFO 順序追蹤各批次，並按比例將超額分配至年末持有的所有批次。結果頁的「批次摘要」區塊顯示各批次明細。',
        },
      ],
    },
  },
}
