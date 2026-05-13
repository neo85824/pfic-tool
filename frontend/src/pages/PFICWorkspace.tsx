import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { txnsApi, calcApi, holdingContextApi, exportUrl, type Holding, type Transaction, type CalculationDetail, type HoldingContext } from '../api'

type Step = 1 | 2 | 3 | 4 | 5

const STEP_LABELS = ['PFIC Info', 'Transactions', 'Parameters', 'Results', 'Export']

function fmt(v?: number | null) {
  if (v == null) return '—'
  return v.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

export default function PFICWorkspace() {
  const { holdingId } = useParams<{ holdingId: string }>()
  const nav = useNavigate()

  const [step, setStep] = useState<Step>(1)
  const [_holding, _setHolding] = useState<Holding | null>(null)
  const [context, setContext] = useState<HoldingContext | null>(null)
  const [txns, setTxns] = useState<Transaction[]>([])
  const [taxYear, setTaxYear] = useState<number>(() => {
    const stored = holdingId ? localStorage.getItem(`pfic_taxYear_${holdingId}`) : null
    return stored ? parseInt(stored) : new Date().getFullYear() - 1
  })
  const [calcResult, setCalcResult] = useState<CalculationDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [csvStatus, setCsvStatus] = useState('')
  const [showMethodology, setShowMethodology] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const updateTaxYear = (year: number) => {
    setTaxYear(year)
    if (holdingId) localStorage.setItem(`pfic_taxYear_${holdingId}`, String(year))
  }

  // Manual txn form
  const [txnForm, setTxnForm] = useState({ txn_date: '', txn_type: 'purchase', units: '', total_value_usd: '', notes: '' })

  useEffect(() => {
    if (!holdingId) return
    holdingContextApi.get(holdingId).then((r) => setContext(r.data)).catch(() => {})
    txnsApi.list(holdingId).then((r) => setTxns(r.data)).catch(() => {})
  }, [holdingId])

  const loadTxns = () => txnsApi.list(holdingId!).then((r) => setTxns(r.data))

  const addTxn = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await txnsApi.create(holdingId!, {
        txn_date: txnForm.txn_date,
        txn_type: txnForm.txn_type,
        units: txnForm.units ? parseFloat(txnForm.units) : undefined,
        total_value_usd: parseFloat(txnForm.total_value_usd),
        notes: txnForm.notes || undefined,
      })
      setTxnForm({ txn_date: '', txn_type: 'purchase', units: '', total_value_usd: '', notes: '' })
      await loadTxns()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add transaction')
    }
  }

  const deleteTxn = async (id: string) => {
    if (!window.confirm('Delete this transaction?')) return
    await txnsApi.delete(holdingId!, id)
    await loadTxns()
  }

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setCsvStatus('Uploading…')
    try {
      const res = await txnsApi.importCsv(holdingId!, file)
      const { imported, skipped, errors } = res.data
      setCsvStatus(`✓ Imported ${imported} rows${skipped ? `, ${skipped} skipped` : ''}${errors?.length ? ` — ${errors[0]}` : ''}`)
      await loadTxns()
    } catch (err: any) {
      setCsvStatus('Import failed: ' + (err.response?.data?.detail || err.message))
    }
    e.target.value = ''
  }

  const runCalc = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await calcApi.run(holdingId!, taxYear)
      setCalcResult(res.data)
      setStep(4)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Calculation failed')
    } finally {
      setLoading(false)
    }
  }

  const downloadExport = (type: 'pdf' | 'line16a' | 'excel') => {
    const token = localStorage.getItem('token')
    const url = exportUrl(holdingId!, taxYear, type)
    // Open with auth — use fetch + blob
    fetch('/api' + url.replace('/api', ''), { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.blob())
      .then((blob) => {
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = `Form8621_${type}_${taxYear}.${type === 'excel' ? 'xlsx' : 'pdf'}`
        a.click()
      })
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center gap-4">
        <button onClick={() => nav(-1)} className="text-slate-400 hover:text-slate-700 text-sm">←</button>
        <div className="flex-1">
          {context ? (
            <>
              <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">{context.client_code}</p>
              <h1 className="text-xl font-bold text-slate-800">{context.pfic_name}</h1>
            </>
          ) : (
            <h1 className="text-xl font-bold text-slate-800">PFIC Workspace</h1>
          )}
          <p className="text-xs text-slate-500">§1291 Excess Distribution · USD</p>
        </div>
        <button
          onClick={() => setShowMethodology(true)}
          className="ml-auto text-sm text-blue-600 border border-blue-200 bg-blue-50 hover:bg-blue-100 px-4 py-2 rounded-lg font-medium"
        >
          How we calculate ↗
        </button>
      </header>

      {/* Methodology modal */}
      {showMethodology && (
        <div className="fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowMethodology(false)} />
          <div className="relative ml-auto w-full max-w-2xl bg-white h-full overflow-y-auto shadow-2xl">
            <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-800">§1291 Excess Distribution — Calculation Methodology</h2>
                <p className="text-xs text-slate-400 mt-0.5">IRC §§1291–1298 · Form 8621 Part V</p>
              </div>
              <button onClick={() => setShowMethodology(false)} className="text-slate-400 hover:text-slate-700 text-xl leading-none">✕</button>
            </div>
            <div className="px-6 py-6 space-y-8 text-sm text-slate-700 leading-relaxed">

              {/* Overview */}
              <section>
                <h3 className="font-semibold text-slate-900 mb-2 text-base">Background &amp; Purpose</h3>
                <p className="mb-3">
                  A Passive Foreign Investment Company (PFIC) is any foreign corporation that meets either an income test (75% or more passive income) or an asset test (50% or more passive assets). U.S. persons who hold PFIC shares and receive distributions — or sell their shares at a gain — are subject to a punitive tax regime under IRC §1291.
                </p>
                <p className="mb-3">
                  The purpose of §1291 is to eliminate the tax deferral benefit that an investor would otherwise obtain by holding a foreign fund that accumulates income without distributing it. The law accomplishes this by treating large distributions as if they had been received ratably over the entire holding period, then taxing each portion at the highest applicable rate <em>for that year</em>, plus an interest charge to recover the time-value of the deferred tax.
                </p>
                <div className="bg-blue-50 border-l-4 border-blue-400 rounded-r-lg px-4 py-3 text-blue-800 text-xs">
                  <strong>Key point:</strong> The §1291 regime is the default method. It applies automatically unless the taxpayer has made a QEF election (§1295) or mark-to-market election (§1296) and maintained it consistently since the first year of PFIC ownership.
                </div>
              </section>

              {/* Step 1 */}
              <section>
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="bg-slate-800 text-white text-xs font-bold px-2 py-0.5 rounded">STEP 1</span>
                  <h3 className="font-semibold text-slate-900 text-base">Determining Whether a Distribution Is "Excess"</h3>
                </div>
                <p className="mb-3">
                  Not every distribution triggers the §1291 regime. The law first applies the <strong>125% test</strong>: a distribution is an <em>excess distribution</em> only to the extent it exceeds 125% of the average annual distribution received during the three years immediately preceding the distribution year (or, if shorter, the portion of the holding period prior to the distribution year).
                </p>
                <div className="bg-slate-50 rounded-lg p-4 mb-3 space-y-3">
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Prior-Year Average</p>
                    <p>Add up distributions received in the one, two, or three tax years before the current year (up to three years), then divide by the number of years the PFIC was held before the current year. If no prior distributions were received, the average is zero — meaning the entire current-year distribution is treated as excess.</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Threshold</p>
                    <p>Multiply the prior-year average by 1.25. Any current-year distribution above this threshold is the <strong>excess distribution</strong> subject to §1291. The portion at or below the threshold is taxed as ordinary income in the current year.</p>
                  </div>
                </div>
                <div className="bg-amber-50 border-l-4 border-amber-400 rounded-r-lg px-4 py-3 text-amber-800 text-xs">
                  <strong>Practical note:</strong> Missing even one year of prior distribution data will produce an incorrect prior-year average and therefore an incorrect excess amount. Ensure all prior distributions are entered before running the calculation.
                </div>
              </section>

              {/* Step 2 */}
              <section>
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="bg-slate-800 text-white text-xs font-bold px-2 py-0.5 rounded">STEP 2</span>
                  <h3 className="font-semibold text-slate-900 text-base">Allocating the Excess Across Purchase Lots</h3>
                </div>
                <p className="mb-3">
                  When the taxpayer acquired shares at different times (multiple purchase lots), the total excess distribution is allocated to each lot in proportion to the number of units each lot represents out of the total units held at the time of the distribution. Each lot is then treated independently for the remainder of the calculation, because each lot has its own acquisition date and therefore its own holding period.
                </p>
                <p>
                  Lots purchased in the same calendar year as the distribution are treated entirely as current-year ordinary income — their holding period does not extend into any prior PFIC year, so no deferred tax or interest arises from those lots.
                </p>
              </section>

              {/* Step 3 */}
              <section>
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="bg-slate-800 text-white text-xs font-bold px-2 py-0.5 rounded">STEP 3</span>
                  <h3 className="font-semibold text-slate-900 text-base">Spreading the Excess Ratably Over the Holding Period</h3>
                </div>
                <p className="mb-3">
                  For each lot, the allocated excess is spread over the holding period on a <strong>daily ratable basis</strong>. The holding period runs from the acquisition date up to (but not including) the date of distribution. The excess is divided by the total number of holding days to arrive at a daily amount, and each calendar year receives an amount equal to that daily rate multiplied by the number of days the lot was held during that year.
                </p>
                <p className="mb-3">
                  The result is a set of year-by-year amounts that together equal the full excess allocated to the lot. Each year's amount is then classified as one of three types:
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border border-slate-200 rounded-lg overflow-hidden">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Classification</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">When it applies</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Tax treatment</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      <tr>
                        <td className="px-3 py-2 font-medium text-green-700">Current Year</td>
                        <td className="px-3 py-2">Days in the tax year the distribution was received</td>
                        <td className="px-3 py-2">Ordinary income — included in gross income at current-year rates</td>
                      </tr>
                      <tr>
                        <td className="px-3 py-2 font-medium text-orange-700">Prior PFIC Year</td>
                        <td className="px-3 py-2">Days in prior years when the fund was already a PFIC (1987 or later)</td>
                        <td className="px-3 py-2">Subject to deferred tax at the historical maximum rate + §6621 interest</td>
                      </tr>
                      <tr>
                        <td className="px-3 py-2 font-medium text-slate-500">Pre-PFIC Year</td>
                        <td className="px-3 py-2">Days before 1987 (before the PFIC rules took effect)</td>
                        <td className="px-3 py-2">Ordinary income — taxed as current-year income with no interest charge</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Step 4 */}
              <section>
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="bg-slate-800 text-white text-xs font-bold px-2 py-0.5 rounded">STEP 4</span>
                  <h3 className="font-semibold text-slate-900 text-base">Applying the Historical Maximum Tax Rate</h3>
                </div>
                <p className="mb-3">
                  For each prior PFIC year, the allocated amount is taxed at the <strong>highest applicable individual income tax rate in effect for that year</strong>, regardless of the taxpayer's actual marginal rate. This rule ensures that no benefit is gained from the deferral regardless of the taxpayer's individual circumstances.
                </p>
                <div className="overflow-x-auto mb-3">
                  <table className="w-full text-xs border border-slate-200 rounded-lg overflow-hidden">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Tax Years</th>
                        <th className="px-3 py-2 text-right font-medium text-slate-600">Maximum Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {[
                        ['1987 – 1992', '28%'],
                        ['1993 – 2000', '39.6%'],
                        ['2001 – 2002', '39.1%'],
                        ['2003 – 2012', '35%'],
                        ['2013 – 2017', '39.6%'],
                        ['2018 – present', '37%'],
                      ].map(([yrs, rate]) => (
                        <tr key={yrs}>
                          <td className="px-3 py-2 text-slate-700">{yrs}</td>
                          <td className="px-3 py-2 text-right font-medium text-slate-800">{rate}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-slate-500">
                  The deferred tax for each prior year is computed independently. The sum of all prior-year deferred taxes is the "additional tax" reported on Form 8621, Line 16c.
                </p>
              </section>

              {/* Step 5 */}
              <section>
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="bg-slate-800 text-white text-xs font-bold px-2 py-0.5 rounded">STEP 5</span>
                  <h3 className="font-semibold text-slate-900 text-base">Computing the Interest Charge</h3>
                </div>
                <p className="mb-3">
                  In addition to the deferred tax, the taxpayer owes interest on each prior-year tax amount. This interest is calculated under §6621, using the IRS underpayment rate, which changes quarterly. It runs from the <strong>original filing deadline of the allocation year</strong> (i.e., the year to which the income was allocated) to the <strong>filing deadline of the current return year</strong>. Interest compounds daily under §6622.
                </p>
                <p className="mb-3">
                  The start date is the filing deadline of the year to which the income is attributed — typically April 15 of the following year — not the date of the actual distribution. This is a commonly misunderstood point: the interest clock starts from when the tax <em>would have been due</em> had the income been recognized in that year.
                </p>
                <div className="bg-slate-50 rounded-lg p-4 mb-3">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Special Filing Deadlines</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="pb-1.5 text-left font-medium text-slate-600">Allocation Year</th>
                          <th className="pb-1.5 text-left font-medium text-slate-600">Normal Deadline</th>
                          <th className="pb-1.5 text-left font-medium text-slate-600">Actual Deadline</th>
                          <th className="pb-1.5 text-left font-medium text-slate-600">Reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        <tr>
                          <td className="py-1.5 text-slate-700">2019</td>
                          <td className="py-1.5 text-slate-500">2020-04-15</td>
                          <td className="py-1.5 font-medium">2020-07-15</td>
                          <td className="py-1.5 text-slate-500">COVID-19 extension (Notice 2020-23)</td>
                        </tr>
                        <tr>
                          <td className="py-1.5 text-slate-700">2020</td>
                          <td className="py-1.5 text-slate-500">2021-04-15</td>
                          <td className="py-1.5 font-medium">2021-05-17</td>
                          <td className="py-1.5 text-slate-500">COVID-19 extension (Notice 2021-21)</td>
                        </tr>
                        <tr>
                          <td className="py-1.5 text-slate-700">2021</td>
                          <td className="py-1.5 text-slate-500">2022-04-15</td>
                          <td className="py-1.5 font-medium">2022-04-18</td>
                          <td className="py-1.5 text-slate-500">April 15 fell on Saturday; §7503 shifts to Monday</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
                <p className="text-xs text-slate-500">
                  The §6621 underpayment rate is set at the federal short-term rate plus 3 percentage points, adjusted each quarter. The system uses the official IRS Internal Revenue Bulletin rates for each quarter. The total interest for each prior year is reported on Form 8621, Line 16f.
                </p>
              </section>

              {/* Step 6 */}
              <section>
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="bg-slate-800 text-white text-xs font-bold px-2 py-0.5 rounded">STEP 6</span>
                  <h3 className="font-semibold text-slate-900 text-base">Lot Matching for Sales — FIFO Required</h3>
                </div>
                <p className="mb-3">
                  When a taxpayer disposes of PFIC shares, the IRS requires lots to be matched on a <strong>first-in, first-out (FIFO)</strong> basis. The oldest shares are deemed sold first. If only part of a lot is sold, the remaining units retain their original acquisition date — they are not treated as newly acquired. This matters significantly because the acquisition date determines how many calendar years fall within the holding period and therefore how much deferred tax and interest accumulates.
                </p>
                <p>
                  After a partial or full sale, subsequent distributions are calculated using only the units that remain. Sold units no longer participate in the ratable allocation.
                </p>
              </section>

              {/* Form 8621 */}
              <section>
                <h3 className="font-semibold text-slate-900 mb-3 text-base">Where These Amounts Appear on Form 8621</h3>
                <p className="mb-3">Form 8621, Part V is used to report excess distributions under §1291. The following lines correspond to the amounts computed in this tool:</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border border-slate-200 rounded-lg overflow-hidden">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-slate-600 w-20">Line</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">What It Represents</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Notes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      <tr>
                        <td className="px-3 py-2 font-medium text-slate-700">15e(1)</td>
                        <td className="px-3 py-2">Ordinary income</td>
                        <td className="px-3 py-2 text-slate-500">The non-excess portion of the distribution plus any current-year and pre-PFIC allocated amounts. Included in gross income at the taxpayer's current rate.</td>
                      </tr>
                      <tr>
                        <td className="px-3 py-2 font-medium text-slate-700">15e(2)</td>
                        <td className="px-3 py-2">Total excess distribution</td>
                        <td className="px-3 py-2 text-slate-500">The full amount that passed the 125% threshold test, across all lots.</td>
                      </tr>
                      <tr>
                        <td className="px-3 py-2 font-medium text-slate-700">16c</td>
                        <td className="px-3 py-2">Additional tax</td>
                        <td className="px-3 py-2 text-slate-500">Sum of deferred taxes computed for each prior PFIC year at the historical maximum rate. This is added directly to the tax liability — it does not offset deductions or credits.</td>
                      </tr>
                      <tr>
                        <td className="px-3 py-2 font-medium text-slate-700">16f</td>
                        <td className="px-3 py-2">§6621 interest</td>
                        <td className="px-3 py-2 text-slate-500">Daily-compounded underpayment interest on the deferred tax for each prior year. Also added directly to the tax liability.</td>
                      </tr>
                      <tr className="bg-slate-50 font-medium">
                        <td className="px-3 py-2 text-slate-800">16c + 16f</td>
                        <td className="px-3 py-2 text-slate-800">Total additional liability</td>
                        <td className="px-3 py-2 text-slate-500">The combined deferred tax and interest amount due with the current-year return. Shown as the grand total in the Results summary.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div className="mt-3 bg-amber-50 border-l-4 border-amber-400 rounded-r-lg px-4 py-3 text-amber-800 text-xs">
                  <strong>§6501(c)(8) — Statute of Limitations:</strong> The IRS statute of limitations on assessment does not begin to run for the PFIC-related items unless the taxpayer attaches a complete and accurate disclosure statement (the Line 16a attachment) to the timely filed return. Failure to attach this statement leaves the PFIC items open to IRS examination indefinitely.
                </div>
              </section>

              <section className="border-t border-slate-200 pt-5">
                <p className="text-xs text-slate-400">
                  Legal authority: IRC §§1291–1298 · Treas. Reg. §1.1291-1 · Form 8621 and Instructions (Rev. Jan. 2022) · Notice 2020-23 · Notice 2021-21 · Rev. Proc. 2022-38 (§6621 rates)
                </p>
              </section>

            </div>
          </div>
        </div>
      )}

      {/* Step nav */}
      <div className="bg-white border-b border-slate-200 px-6">
        <div className="max-w-4xl mx-auto flex">
          {STEP_LABELS.map((label, i) => {
            const s = (i + 1) as Step
            return (
              <button
                key={s}
                onClick={() => setStep(s)}
                className={`px-4 py-3 text-sm border-b-2 transition-colors ${
                  step === s
                    ? 'border-blue-600 text-blue-700 font-medium'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                {s}. {label}
              </button>
            )
          })}
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>}

        {/* Step 1 — Info */}
        {step === 1 && (
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="font-semibold text-slate-800 mb-4">Step 1: PFIC Information</h2>
            <div className="space-y-4 max-w-md">
              <div className="bg-slate-50 rounded-lg p-4 text-sm space-y-2">
                <p><span className="font-medium">Holding ID:</span> <span className="font-mono text-xs text-slate-500">{holdingId}</span></p>
                <p><span className="font-medium">Method:</span> §1291 Excess Distribution</p>
                <p><span className="font-medium">Currency:</span> USD (MVP)</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Tax Year to Calculate</label>
                <input
                  type="number"
                  value={taxYear}
                  onChange={(e) => updateTaxYear(parseInt(e.target.value))}
                  className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-32"
                />
              </div>
              <button
                onClick={() => setStep(2)}
                className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700"
              >
                Next: Transactions →
              </button>
            </div>
          </div>
        )}

        {/* Step 2 — Transactions */}
        {step === 2 && (
          <div className="space-y-6">
            {/* CSV Import */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="font-semibold text-slate-800 mb-1">CSV Import</h2>
              <p className="text-xs text-slate-500 mb-3">
                Columns: <code className="bg-slate-100 px-1 rounded">date, type, units, amount_usd, notes</code>
                &nbsp;· Types: purchase, sale, distribution, reinvestment
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => fileRef.current?.click()}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm px-4 py-2 rounded-lg"
                >
                  Upload CSV
                </button>
                <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleCsvUpload} />
                {csvStatus && <span className="text-sm text-slate-600">{csvStatus}</span>}
              </div>
            </div>

            {/* Manual entry */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="font-semibold text-slate-800 mb-4">Manual Entry</h2>
              <form onSubmit={addTxn} className="flex gap-2 flex-wrap items-end">
                <div>
                  <label className="block text-xs text-slate-600 mb-1">Date *</label>
                  <input type="date" value={txnForm.txn_date} onChange={(e) => setTxnForm({ ...txnForm, txn_date: e.target.value })}
                    className="border border-slate-300 rounded px-2 py-1.5 text-sm" required />
                </div>
                <div>
                  <label className="block text-xs text-slate-600 mb-1">Type *</label>
                  <select value={txnForm.txn_type} onChange={(e) => setTxnForm({ ...txnForm, txn_type: e.target.value })}
                    className="border border-slate-300 rounded px-2 py-1.5 text-sm">
                    {['purchase', 'sale', 'distribution', 'reinvestment', 'return_of_capital'].map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-600 mb-1">Units</label>
                  <input type="number" step="0.00000001" value={txnForm.units} onChange={(e) => setTxnForm({ ...txnForm, units: e.target.value })}
                    className="border border-slate-300 rounded px-2 py-1.5 text-sm w-24" placeholder="e.g. 100" />
                </div>
                <div>
                  <label className="block text-xs text-slate-600 mb-1">Amount USD *</label>
                  <input type="number" step="0.01" value={txnForm.total_value_usd} onChange={(e) => setTxnForm({ ...txnForm, total_value_usd: e.target.value })}
                    className="border border-slate-300 rounded px-2 py-1.5 text-sm w-28" placeholder="5000.00" required />
                </div>
                <div>
                  <label className="block text-xs text-slate-600 mb-1">Notes</label>
                  <input value={txnForm.notes} onChange={(e) => setTxnForm({ ...txnForm, notes: e.target.value })}
                    className="border border-slate-300 rounded px-2 py-1.5 text-sm w-32" />
                </div>
                <button type="submit" className="bg-blue-600 text-white text-sm px-3 py-1.5 rounded hover:bg-blue-700">Add</button>
              </form>
            </div>

            {/* Transaction list */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="font-semibold text-slate-800 mb-4">Transactions ({txns.length})</h2>
              {txns.length === 0 ? (
                <p className="text-slate-400 text-sm">No transactions yet.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left border-b border-slate-200">
                        <th className="pb-2 text-slate-500 font-medium">Date</th>
                        <th className="pb-2 text-slate-500 font-medium">Type</th>
                        <th className="pb-2 text-slate-500 font-medium text-right">Units</th>
                        <th className="pb-2 text-slate-500 font-medium text-right pr-8">Amount USD</th>
                        <th className="pb-2 text-slate-500 font-medium">Notes</th>
                        <th className="pb-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {txns.map((t) => (
                        <tr key={t.id} className="border-b border-slate-100 hover:bg-slate-50">
                          <td className="py-2 font-mono text-xs">{t.txn_date}</td>
                          <td className="py-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              t.txn_type === 'purchase' ? 'bg-green-100 text-green-700' :
                              t.txn_type === 'sale' ? 'bg-red-100 text-red-700' :
                              t.txn_type === 'distribution' ? 'bg-blue-100 text-blue-700' :
                              'bg-slate-100 text-slate-700'
                            }`}>{t.txn_type}</span>
                          </td>
                          <td className="py-2 text-right font-mono text-xs">{t.units ?? '—'}</td>
                          <td className="py-2 text-right font-mono pr-8">{fmt(t.total_value_usd)}</td>
                          <td className="py-2 text-slate-400 text-xs">{t.notes || '—'}</td>
                          <td className="py-2">
                            <button onClick={() => deleteTxn(t.id)} className="text-slate-300 hover:text-red-500 text-xs">✕</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <div className="mt-4 flex gap-3">
                <button onClick={() => setStep(3)} className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700">
                  Next: Parameters →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3 — Parameters */}
        {step === 3 && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 max-w-lg">
            <h2 className="font-semibold text-slate-800 mb-4">Step 3: Confirm Parameters</h2>
            <div className="space-y-3 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Tax year</span>
                <span className="font-medium">{taxYear}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Method</span>
                <span className="font-medium">§1291 Excess Distribution</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Tax rate</span>
                <span className="font-medium">Historical max rate per year (IRC §1291(c)(2))</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Transactions loaded</span>
                <span className="font-medium">{txns.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Interest</span>
                <span className="font-medium">§6622 daily compounding</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Lot matching</span>
                <span className="font-medium">FIFO (required by IRS)</span>
              </div>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800 mb-6">
              <strong>Before running:</strong> Ensure all transactions for tax year {taxYear} and prior years
              are loaded. Missing prior-year distributions will affect the 125% test.
            </div>
            <button
              onClick={runCalc}
              disabled={loading || txns.length === 0}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? '⏳ Calculating…' : '▶ Run Calculation'}
            </button>
            {txns.length === 0 && <p className="text-xs text-red-500 mt-2">Add transactions in Step 2 first.</p>}
          </div>
        )}

        {/* Step 4 — Results */}
        {step === 4 && calcResult && (() => {
          const fr = calcResult.full_result as any
          const yearBuckets: Record<string, any> = fr.year_buckets || {}

          // Merge year_results across all lots
          const merged: Record<string, any> = {}
          for (const dr of (fr.deferred_tax_results || [])) {
            for (const [yr, data] of Object.entries<any>(dr.year_results || {})) {
              if (!merged[yr]) {
                merged[yr] = { ...data, tax: parseFloat(data.tax || '0'), interest: parseFloat(data.interest || '0') }
              } else {
                merged[yr].tax += parseFloat(data.tax || '0')
                merged[yr].interest += parseFloat(data.interest || '0')
              }
            }
          }

          const sortedYears = Object.keys(yearBuckets).sort((a, b) => parseInt(a) - parseInt(b))
          const totalDays = sortedYears.reduce((s, yr) => s + yearBuckets[yr].days, 0)
          const excess = parseFloat(fr.excess_distribution || '0')
          const dailyRate = totalDays > 0 ? excess / totalDays : 0
          const firstYear = sortedYears[0] || ''
          const priorYears = sortedYears.filter(yr => merged[yr]?.classification === 'prior_pfic')
          const interestEnd = priorYears.length > 0 ? merged[priorYears[0]]?.interest_end?.slice(0, 10) : null

          return (
            <div className="space-y-5">
              {/* Warnings */}
              {calcResult.warnings?.length > 0 && (
                <div className="bg-amber-50 border border-amber-300 rounded-xl p-4">
                  <p className="font-semibold text-amber-800 mb-2">⚠ Warnings</p>
                  {calcResult.warnings.map((w, i) => <p key={i} className="text-sm text-amber-700">• {w}</p>)}
                </div>
              )}

              {/* §6501 banner */}
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
                <strong>§6501(c)(8):</strong> Download the Line 16a attachment in Step 5 and attach it to the filed return.
                Without this attachment, the IRS statute of limitations does not begin to run.
              </div>

              {/* 125% Test */}
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <h3 className="font-semibold text-slate-800 mb-3">
                  125% Test
                  <span className="ml-2 text-xs font-normal text-slate-400">[IRC §1291(b)(2)(A)]</span>
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { label: 'Current Distribution', value: parseFloat(fr.current_year_distribution || '0') },
                    { label: 'Prior 3-Year Average', value: parseFloat(fr.prior_3yr_average || '0') },
                    { label: 'Benchmark (×125%)', value: parseFloat(fr.prior_3yr_average || '0') * 1.25 },
                    { label: 'Excess Distribution', value: excess, highlight: true },
                  ].map(c => (
                    <div key={c.label} className={`rounded-lg border p-3 ${c.highlight ? 'border-orange-400 bg-orange-50' : 'border-slate-200 bg-slate-50'}`}>
                      <p className="text-xs text-slate-500 mb-1">{c.label}</p>
                      <p className={`font-bold text-sm ${c.highlight ? 'text-orange-700' : 'text-slate-800'}`}>{fmt(c.value)}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Excess Distribution by Lot */}
              {(fr.deferred_tax_results || []).length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                  <h3 className="font-semibold text-slate-800 mb-3">
                    Excess Distribution by Lot
                    <span className="ml-2 text-xs font-normal text-slate-400">[§1291(a)(1) proportional allocation]</span>
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b-2 border-slate-200 text-left bg-slate-50">
                          <th className="px-3 py-2 text-slate-500 font-medium">Lot</th>
                          <th className="px-3 py-2 text-slate-500 font-medium">Acquired</th>
                          <th className="px-3 py-2 text-slate-500 font-medium text-right">Units</th>
                          <th className="px-3 py-2 text-slate-500 font-medium text-right">Excess Share</th>
                          <th className="px-3 py-2 text-slate-500 font-medium text-right">Deferred Tax</th>
                          <th className="px-3 py-2 text-slate-500 font-medium text-right">Interest</th>
                          <th className="px-3 py-2 text-slate-500 font-medium text-right">Grand Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(fr.deferred_tax_results as any[]).map((dr, i) => (
                          <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                            <td className="px-3 py-2 font-medium text-slate-600">L{i + 1}</td>
                            <td className="px-3 py-2 font-mono text-xs">{dr.acquisition_date}</td>
                            <td className="px-3 py-2 text-right font-mono">{parseFloat(dr.units).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                            <td className="px-3 py-2 text-right font-mono">{fmt(parseFloat(dr.lot_excess))}</td>
                            <td className="px-3 py-2 text-right font-mono">{fmt(parseFloat(dr.total_deferred_tax))}</td>
                            <td className="px-3 py-2 text-right font-mono">{fmt(parseFloat(dr.total_interest))}</td>
                            <td className="px-3 py-2 text-right font-mono font-semibold">{fmt(parseFloat(dr.grand_total))}</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className="border-t-2 border-slate-300 bg-slate-100 font-bold">
                          <td className="px-3 py-2" colSpan={3}>Total</td>
                          <td className="px-3 py-2 text-right font-mono">{fmt(excess)}</td>
                          <td className="px-3 py-2 text-right font-mono">{fmt(calcResult.additional_tax)}</td>
                          <td className="px-3 py-2 text-right font-mono">{fmt(calcResult.total_interest)}</td>
                          <td className="px-3 py-2 text-right font-mono">{fmt(calcResult.grand_total)}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              )}

              {/* Step 1: Holding period */}
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <h3 className="font-semibold text-slate-800 mb-3">
                  Step 1 — Holding Period & Daily Rate
                  <span className="ml-2 text-xs font-normal text-slate-400">[§1291(a)(1)(A)]</span>
                </h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Period</p>
                    <p className="font-mono">{firstYear} → {fr.tax_year}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Total Days</p>
                    <p className="font-bold">{totalDays.toLocaleString()} days</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Daily Rate</p>
                    <p className="font-mono">${dailyRate.toFixed(5)}/day</p>
                  </div>
                </div>
              </div>

              {/* Step 2: Year-by-year allocation & tax */}
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <h3 className="font-semibold text-slate-800 mb-3">
                  Step 2 — Year-by-Year Allocation & Tax
                  <span className="ml-2 text-xs font-normal text-slate-400">[§1291(c)(2)]</span>
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b-2 border-slate-200 text-left bg-slate-50">
                        <th className="px-3 py-2 text-slate-500 font-medium">Year</th>
                        <th className="px-3 py-2 text-slate-500 font-medium text-right">Days</th>
                        <th className="px-3 py-2 text-slate-500 font-medium text-right">Allocated</th>
                        <th className="px-3 py-2 text-slate-500 font-medium text-right">Rate</th>
                        <th className="px-3 py-2 text-slate-500 font-medium text-right">Deferred Tax</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedYears.map(yr => {
                        const bkt = yearBuckets[yr]
                        const res = merged[yr]
                        const isCurrent = bkt.classification === 'current_year'
                        const tax = res?.tax ?? null
                        const rate = !isCurrent && tax != null && parseFloat(bkt.amount) > 0
                          ? (tax / parseFloat(bkt.amount) * 100).toFixed(1) + '%'
                          : '—'
                        return (
                          <tr key={yr} className={`border-b border-slate-100 ${isCurrent ? 'bg-slate-50' : 'hover:bg-slate-50'}`}>
                            <td className="px-3 py-2 font-medium">{yr}</td>
                            <td className="px-3 py-2 text-right text-slate-600">{bkt.days}</td>
                            <td className="px-3 py-2 text-right font-mono">{fmt(parseFloat(bkt.amount))}</td>
                            <td className="px-3 py-2 text-right font-medium">{rate}</td>
                            <td className="px-3 py-2 text-right font-mono">
                              {isCurrent
                                ? <span className="text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full">ordinary income</span>
                                : fmt(tax)
                              }
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 border-slate-300 bg-slate-100 font-bold">
                        <td className="px-3 py-2">Total</td>
                        <td className="px-3 py-2 text-right">{totalDays.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right font-mono">{fmt(excess)}</td>
                        <td></td>
                        <td className="px-3 py-2 text-right font-mono">{fmt(calcResult.additional_tax)}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* Step 3: Interest */}
              {priorYears.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                  <h3 className="font-semibold text-slate-800 mb-1">
                    Step 3 — §6621 Interest
                    <span className="ml-2 text-xs font-normal text-slate-400">[§6622 daily compound]</span>
                  </h3>
                  <p className="text-xs text-slate-500 mb-3">
                    Accrues from each year's filing deadline → {interestEnd} ({fr.tax_year} return due date)
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b-2 border-slate-200 text-left bg-slate-50">
                          <th className="px-3 py-2 text-slate-500 font-medium">Year</th>
                          <th className="px-3 py-2 text-slate-500 font-medium text-right">Tax</th>
                          <th className="px-3 py-2 text-slate-500 font-medium">Filing Deadline</th>
                          <th className="px-3 py-2 text-slate-500 font-medium text-right">Interest</th>
                        </tr>
                      </thead>
                      <tbody>
                        {priorYears.map(yr => {
                          const res = merged[yr]
                          const month = res?.interest_start?.slice(5, 7)
                          const isCovid = month && month !== '04'
                          return (
                            <tr key={yr} className="border-b border-slate-100 hover:bg-slate-50">
                              <td className="px-3 py-2 font-medium">{yr}</td>
                              <td className="px-3 py-2 text-right font-mono">{fmt(res?.tax)}</td>
                              <td className="px-3 py-2 font-mono text-xs">
                                {res?.interest_start?.slice(0, 10)}
                                {isCovid && <span className="ml-2 text-xs text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded font-semibold">⚠ COVID</span>}
                              </td>
                              <td className="px-3 py-2 text-right font-mono">{fmt(res?.interest)}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                      <tfoot>
                        <tr className="border-t-2 border-slate-300 bg-slate-100 font-bold">
                          <td className="px-3 py-2" colSpan={3}>Total Interest</td>
                          <td className="px-3 py-2 text-right font-mono">{fmt(calcResult.total_interest)}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              )}

              {/* Form 8621 Part V Summary */}
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <h3 className="font-semibold text-slate-800 mb-3">Form 8621 Part V — Summary</h3>
                <table className="w-full text-sm">
                  <tbody>
                    {[
                      { line: '15e(1)', desc: 'Ordinary income (Line 16b)', value: calcResult.ordinary_income },
                      { line: '15e(2)', desc: 'Excess distribution', value: calcResult.total_excess_dist },
                      { line: '16c',    desc: 'Additional tax', value: calcResult.additional_tax },
                      { line: '16f',    desc: '§6621 interest', value: calcResult.total_interest },
                    ].map(row => (
                      <tr key={row.line} className="border-b border-slate-100">
                        <td className="py-2 w-16 font-mono text-xs text-slate-400">{row.line}</td>
                        <td className="py-2 text-slate-700">{row.desc}</td>
                        <td className="py-2 text-right font-mono">{fmt(row.value)}</td>
                      </tr>
                    ))}
                    <tr className="bg-blue-50 border-t-2 border-blue-300">
                      <td className="py-3 font-mono text-xs font-bold text-blue-600">16c+f</td>
                      <td className="py-3 font-bold text-blue-800">Grand total additional liability</td>
                      <td className="py-3 text-right font-mono font-bold text-blue-800 text-base">{fmt(calcResult.grand_total)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-400">Engine: {calcResult.engine_version || 'dev'} · {calcResult.status}</p>
                <button onClick={() => setStep(5)} className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700">
                  Step 5: Export →
                </button>
              </div>
            </div>
          )
        })()}

        {step === 4 && !calcResult && (
          <div className="bg-white rounded-xl border border-slate-200 p-10 text-center">
            <p className="text-slate-500">No results yet. Go to Step 3 to run the calculation.</p>
            <button onClick={() => setStep(3)} className="mt-4 text-blue-600 text-sm hover:underline">← Step 3</button>
          </div>
        )}

        {/* Step 5 — Export */}
        {step === 5 && (
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="font-semibold text-slate-800 mb-1">Step 5: Export</h2>
            <p className="text-sm text-slate-500 mb-6">Download all documents needed for filing and audit.</p>

            {!calcResult && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-700 mb-4">
                No calculation results yet. Complete Step 3 first.
              </div>
            )}

            <div className="grid gap-4 md:grid-cols-3">
              {[
                {
                  type: 'pdf' as const,
                  title: 'Form 8621 Workpaper',
                  desc: 'Part V summary — all Form 8621 line numbers with computed values.',
                  icon: '📄',
                },
                {
                  type: 'line16a' as const,
                  title: 'Line 16a Attachment',
                  desc: 'Required daily allocation statement (§6501(c)(8)).',
                  icon: '📎',
                  required: true,
                },
                {
                  type: 'excel' as const,
                  title: 'Excel Workpapers',
                  desc: '3-sheet workbook: summary, year detail, daily allocation.',
                  icon: '📊',
                },
              ].map((item) => (
                <div key={item.type} className={`border rounded-xl p-5 ${item.required ? 'border-blue-400 bg-blue-50' : 'border-slate-200'}`}>
                  <div className="text-2xl mb-2">{item.icon}</div>
                  <h3 className="font-medium text-slate-800 mb-1">
                    {item.title}
                    {item.required && <span className="ml-2 text-xs text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded">Required</span>}
                  </h3>
                  <p className="text-xs text-slate-500 mb-4">{item.desc}</p>
                  <button
                    onClick={() => downloadExport(item.type)}
                    disabled={!calcResult}
                    className="w-full bg-slate-800 hover:bg-slate-900 text-white text-sm py-2 rounded-lg disabled:opacity-40"
                  >
                    Download
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
