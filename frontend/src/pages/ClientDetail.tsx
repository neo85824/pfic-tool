import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { clientsApi, holdingsApi, type Client, type Holding } from '../api'

export default function ClientDetail() {
  const { clientId } = useParams<{ clientId: string }>()
  const nav = useNavigate()
  const [client, setClient] = useState<Client | null>(null)
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ pfic_name: '', first_pfic_year: '', reference_id: '' })
  const [error, setError] = useState('')

  const load = async () => {
    const [c, h] = await Promise.all([
      clientsApi.get(clientId!),
      holdingsApi.list(clientId!),
    ])
    setClient(c.data)
    setHoldings(h.data)
  }

  useEffect(() => { load() }, [clientId])

  const createHolding = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await holdingsApi.create(clientId!, {
        pfic_name: form.pfic_name,
        currency: 'USD',
        method: '1291',
        first_pfic_year: form.first_pfic_year ? parseInt(form.first_pfic_year) : undefined,
        reference_id: form.reference_id || undefined,
      })
      setShowNew(false)
      setForm({ pfic_name: '', first_pfic_year: '', reference_id: '' })
      load()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create holding')
    }
  }

  if (!client) return <div className="p-8 text-slate-500">Loading…</div>

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center gap-4">
        <button onClick={() => nav('/')} className="text-slate-400 hover:text-slate-700 text-sm">← Dashboard</button>
        <div>
          <h1 className="text-xl font-bold text-slate-800">{client.client_code}</h1>
          {client.tax_year_start && <p className="text-xs text-slate-500">First year: {client.tax_year_start}</p>}
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-slate-800">PFIC Holdings</h2>
          <button
            onClick={() => setShowNew(true)}
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            + New PFIC
          </button>
        </div>

        {showNew && (
          <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
            <h3 className="font-medium text-slate-800 mb-4">New PFIC Holding</h3>
            <form onSubmit={createHolding} className="flex gap-3 flex-wrap items-end">
              <div>
                <label className="block text-xs text-slate-600 mb-1">PFIC Name *</label>
                <input
                  value={form.pfic_name}
                  onChange={(e) => setForm({ ...form, pfic_name: e.target.value })}
                  className="border border-slate-300 rounded px-3 py-1.5 text-sm w-56"
                  placeholder="e.g. Vanguard FTSE All-World"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-slate-600 mb-1">First PFIC Year</label>
                <input
                  type="number"
                  value={form.first_pfic_year}
                  onChange={(e) => setForm({ ...form, first_pfic_year: e.target.value })}
                  className="border border-slate-300 rounded px-3 py-1.5 text-sm w-28"
                  placeholder="e.g. 2018"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-600 mb-1">IRS Reference ID</label>
                <input
                  value={form.reference_id}
                  onChange={(e) => setForm({ ...form, reference_id: e.target.value })}
                  className="border border-slate-300 rounded px-3 py-1.5 text-sm w-36"
                  placeholder="optional"
                />
              </div>
              <p className="text-xs text-slate-400 self-center">Currency: USD (MVP)</p>
              <button type="submit" className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded hover:bg-blue-700">Create</button>
              <button type="button" onClick={() => setShowNew(false)} className="text-sm text-slate-500">Cancel</button>
            </form>
            {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
          </div>
        )}

        {holdings.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-10 text-center">
            <p className="text-slate-500">No PFIC holdings yet for this client.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {holdings.map((h) => (
              <div
                key={h.id}
                onClick={() => nav(`/holdings/${h.id}`)}
                className="bg-white rounded-xl border border-slate-200 px-5 py-4 flex items-center justify-between cursor-pointer hover:border-blue-400 hover:shadow-sm transition-all"
              >
                <div>
                  <p className="font-medium text-slate-800">{h.pfic_name}</p>
                  <p className="text-xs text-slate-500">
                    {h.currency} · §{h.method} · {h.first_pfic_year ? `First PFIC year: ${h.first_pfic_year}` : 'First PFIC year: not set'}
                  </p>
                </div>
                <span className="text-slate-400 text-lg">→</span>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
