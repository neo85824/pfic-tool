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
  const [editMode, setEditMode] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [deleting, setDeleting] = useState(false)

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

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    setSelected(selected.size === holdings.length ? new Set() : new Set(holdings.map((h) => h.id)))
  }

  const exitEditMode = () => {
    setEditMode(false)
    setSelected(new Set())
  }

  const deleteSelected = async () => {
    if (selected.size === 0) return
    const names = holdings.filter((h) => selected.has(h.id)).map((h) => h.pfic_name).join(', ')
    if (!confirm(`Delete ${selected.size} holding(s)?\n${names}\n\nThis will remove all associated transactions and calculations.`)) return
    setDeleting(true)
    try {
      await Promise.all([...selected].map((id) => holdingsApi.delete(clientId!, id)))
      exitEditMode()
      load()
    } finally {
      setDeleting(false)
    }
  }

  const deleteSingle = async (e: React.MouseEvent, h: Holding) => {
    e.stopPropagation()
    if (!confirm(`Delete holding "${h.pfic_name}"?\n\nThis will remove all associated transactions and calculations.`)) return
    await holdingsApi.delete(clientId!, h.id)
    load()
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
          <div className="flex items-center gap-2">
            {editMode ? (
              <>
                <button
                  onClick={deleteSelected}
                  disabled={selected.size === 0 || deleting}
                  className="bg-red-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-40"
                >
                  {deleting ? 'Deleting…' : `Delete${selected.size > 0 ? ` (${selected.size})` : ''}`}
                </button>
                <button
                  onClick={exitEditMode}
                  className="text-sm text-slate-600 px-4 py-2 rounded-lg border border-slate-300 hover:bg-slate-100"
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                {holdings.length > 0 && (
                  <button
                    onClick={() => setEditMode(true)}
                    className="text-sm text-slate-600 px-3 py-2 rounded-lg border border-slate-300 hover:bg-slate-100"
                  >
                    Edit
                  </button>
                )}
                <button
                  onClick={() => setShowNew(true)}
                  className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  + New PFIC
                </button>
              </>
            )}
          </div>
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
          <>
            {editMode && (
              <div className="flex items-center gap-2 mb-3 px-1">
                <input
                  type="checkbox"
                  checked={selected.size === holdings.length}
                  onChange={toggleAll}
                  className="w-4 h-4 accent-blue-600"
                />
                <span className="text-xs text-slate-500">Select all</span>
              </div>
            )}
            <div className="space-y-2">
              {holdings.map((h) => (
                <div
                  key={h.id}
                  onClick={() => editMode ? toggleSelect(h.id) : nav(`/holdings/${h.id}`)}
                  className={`group bg-white rounded-xl border px-5 py-4 flex items-center gap-3 cursor-pointer transition-all
                    ${editMode && selected.has(h.id)
                      ? 'border-red-300 bg-red-50'
                      : 'border-slate-200 hover:border-blue-400 hover:shadow-sm'}`}
                >
                  {editMode && (
                    <input
                      type="checkbox"
                      checked={selected.has(h.id)}
                      onChange={() => toggleSelect(h.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-4 h-4 accent-blue-600 shrink-0"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-800">{h.pfic_name}</p>
                    <p className="text-xs text-slate-500">
                      {h.currency} · §{h.method} · {h.first_pfic_year ? `First PFIC year: ${h.first_pfic_year}` : 'First PFIC year: not set'}
                    </p>
                  </div>
                  {editMode ? null : (
                    <button
                      onClick={(e) => deleteSingle(e, h)}
                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 p-1 rounded transition-all"
                      title="Delete holding"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 112 0v6a1 1 0 11-2 0V8z" clipRule="evenodd" />
                      </svg>
                    </button>
                  )}
                  {!editMode && <span className="text-slate-400 text-lg">→</span>}
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
