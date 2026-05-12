import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { holdingsApi, txnsApi, calcApi, exportUrl, type Holding, type Transaction, type CalculationDetail } from '../api'

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
  const [txns, setTxns] = useState<Transaction[]>([])
  const [taxYear, setTaxYear] = useState(new Date().getFullYear() - 1)
  const [calcResult, setCalcResult] = useState<CalculationDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [csvStatus, setCsvStatus] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  // Manual txn form
  const [txnForm, setTxnForm] = useState({ txn_date: '', txn_type: 'purchase', units: '', total_value_usd: '', notes: '' })

  useEffect(() => {
    holdingId && holdingsApi.list('').then().catch()
    // Fetch the holding itself — we get it from the client's holdings list
    // For simplicity, fetch transactions which confirms the holding exists
    txnsApi.list(holdingId!).then((r) => setTxns(r.data)).catch(() => {})
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
        <div>
          <h1 className="text-xl font-bold text-slate-800">PFIC Workspace</h1>
          <p className="text-xs text-slate-500">§1291 Excess Distribution · USD</p>
        </div>
      </header>

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
                  onChange={(e) => setTaxYear(parseInt(e.target.value))}
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
        {step === 4 && calcResult && (
          <div className="space-y-6">
            {/* Warnings */}
            {calcResult.warnings?.length > 0 && (
              <div className="bg-amber-50 border border-amber-300 rounded-xl p-4">
                <p className="font-semibold text-amber-800 mb-2">⚠ Warnings</p>
                {calcResult.warnings.map((w, i) => (
                  <p key={i} className="text-sm text-amber-700">• {w}</p>
                ))}
              </div>
            )}

            {/* §6501 reminder */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
              <strong>§6501(c)(8):</strong> Download the Line 16a attachment in Step 5 and attach it to the filed return.
              Without this attachment, the IRS statute of limitations does not begin to run.
            </div>

            {/* Summary cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Excess Distribution', value: calcResult.total_excess_dist },
                { label: 'Additional Tax', value: calcResult.additional_tax },
                { label: '§6621 Interest', value: calcResult.total_interest },
                { label: 'Grand Total', value: calcResult.grand_total, highlight: true },
              ].map((card) => (
                <div key={card.label} className={`rounded-xl border p-4 ${card.highlight ? 'border-blue-400 bg-blue-50' : 'border-slate-200 bg-white'}`}>
                  <p className="text-xs text-slate-500 mb-1">{card.label}</p>
                  <p className={`text-lg font-bold ${card.highlight ? 'text-blue-700' : 'text-slate-800'}`}>{fmt(card.value)}</p>
                </div>
              ))}
            </div>

            {/* Ordinary income */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <p className="text-sm font-medium text-slate-700">Ordinary Income (Line 16b)</p>
              <p className="text-2xl font-bold text-slate-800">{fmt(calcResult.ordinary_income)}</p>
              <p className="text-xs text-slate-400 mt-1">Pre-PFIC + current year amounts — taxed as ordinary income at your rate</p>
            </div>

            {/* Year detail */}
            {(calcResult.full_result as any)?.year_buckets && (
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <h3 className="font-semibold text-slate-800 mb-3">Year-by-Year Allocation</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left">
                      <th className="pb-2 text-slate-500 font-medium">Year</th>
                      <th className="pb-2 text-slate-500 font-medium text-right">Days</th>
                      <th className="pb-2 text-slate-500 font-medium text-right pr-8">Amount</th>
                      <th className="pb-2 text-slate-500 font-medium">Classification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries((calcResult.full_result as any).year_buckets as Record<string, any>)
                      .sort(([a], [b]) => parseInt(a) - parseInt(b))
                      .map(([yr, bkt]) => (
                        <tr key={yr} className="border-b border-slate-100">
                          <td className="py-1.5 font-medium">{yr}</td>
                          <td className="py-1.5 text-right text-slate-600">{bkt.days}</td>
                          <td className="py-1.5 text-right font-mono pr-8">{fmt(parseFloat(bkt.amount))}</td>
                          <td className="py-1.5">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              bkt.classification === 'prior_pfic' ? 'bg-orange-100 text-orange-700' :
                              bkt.classification === 'pre_pfic' ? 'bg-purple-100 text-purple-700' :
                              'bg-green-100 text-green-700'
                            }`}>{bkt.classification.replace('_', ' ')}</span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Engine version */}
            <p className="text-xs text-slate-400">
              Engine version: {calcResult.engine_version || 'dev'} · Status: {calcResult.status}
            </p>

            <button onClick={() => setStep(5)} className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700">
              Step 5: Export →
            </button>
          </div>
        )}

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
