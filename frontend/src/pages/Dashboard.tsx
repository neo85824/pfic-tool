import { useState, useEffect } from 'react'
import { clientsApi, type Client } from '../api'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const [newCode, setNewCode] = useState('')
  const [newYear, setNewYear] = useState('')
  const [error, setError] = useState('')
  const nav = useNavigate()

  const load = () => clientsApi.list().then((r) => { setClients(r.data); setLoading(false) })

  useEffect(() => { load() }, [])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await clientsApi.create({ client_code: newCode, tax_year_start: newYear ? parseInt(newYear) : undefined })
      setShowNew(false)
      setNewCode('')
      setNewYear('')
      load()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create client')
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <h1 className="text-xl font-bold text-slate-800">PFIC Tool</h1>
        <p className="text-xs text-slate-500">§1291 Excess Distribution Calculator</p>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-slate-800">Clients</h2>
          <button
            onClick={() => setShowNew(true)}
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            + New Client
          </button>
        </div>

        {showNew && (
          <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
            <h3 className="font-medium text-slate-800 mb-4">New Client</h3>
            <form onSubmit={create} className="flex gap-3 flex-wrap items-end">
              <div>
                <label className="block text-xs text-slate-600 mb-1">Client Code *</label>
                <input
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value)}
                  className="border border-slate-300 rounded px-3 py-1.5 text-sm w-40"
                  placeholder="e.g. SMITH-2024"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-slate-600 mb-1">First Tax Year</label>
                <input
                  type="number"
                  value={newYear}
                  onChange={(e) => setNewYear(e.target.value)}
                  className="border border-slate-300 rounded px-3 py-1.5 text-sm w-28"
                  placeholder="e.g. 2020"
                />
              </div>
              <button type="submit" className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded hover:bg-blue-700">Create</button>
              <button type="button" onClick={() => setShowNew(false)} className="text-sm text-slate-500 hover:text-slate-800">Cancel</button>
            </form>
            {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
          </div>
        )}

        {loading ? (
          <p className="text-slate-500">Loading…</p>
        ) : clients.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-10 text-center">
            <p className="text-slate-500">No clients yet.</p>
            <p className="text-sm text-slate-400 mt-1">Add your first client to get started.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {clients.map((c) => (
              <div
                key={c.id}
                onClick={() => nav(`/clients/${c.id}`)}
                className="bg-white rounded-xl border border-slate-200 px-5 py-4 flex items-center justify-between cursor-pointer hover:border-blue-400 hover:shadow-sm transition-all"
              >
                <div>
                  <p className="font-medium text-slate-800">{c.client_code}</p>
                  {c.tax_year_start && <p className="text-xs text-slate-500">First year: {c.tax_year_start}</p>}
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
