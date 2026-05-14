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
  const [editMode, setEditMode] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [deleting, setDeleting] = useState(false)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renamingVal, setRenamingVal] = useState('')
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

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    setSelected(selected.size === clients.length ? new Set() : new Set(clients.map((c) => c.id)))
  }

  const exitEditMode = () => {
    setEditMode(false)
    setSelected(new Set())
  }

  const deleteSelected = async () => {
    if (selected.size === 0) return
    const names = clients.filter((c) => selected.has(c.id)).map((c) => c.client_code).join(', ')
    if (!confirm(`Delete ${selected.size} client(s)?\n${names}\n\nThis will remove all associated holdings and transactions.`)) return
    setDeleting(true)
    try {
      await Promise.all([...selected].map((id) => clientsApi.delete(id)))
      exitEditMode()
      load()
    } finally {
      setDeleting(false)
    }
  }

  const startRename = (e: React.MouseEvent, c: Client) => {
    e.stopPropagation()
    setRenamingId(c.id)
    setRenamingVal(c.client_code)
  }

  const saveRename = async (id: string) => {
    const val = renamingVal.trim()
    if (val && val !== clients.find((c) => c.id === id)?.client_code) {
      try {
        await clientsApi.update(id, { client_code: val })
        load()
      } catch (err: any) {
        alert(err.response?.data?.detail || 'Rename failed')
      }
    }
    setRenamingId(null)
  }

  const deleteSingle = async (e: React.MouseEvent, c: Client) => {
    e.stopPropagation()
    if (!confirm(`Delete client "${c.client_code}"?\n\nThis will remove all associated holdings and transactions.`)) return
    await clientsApi.delete(c.id)
    load()
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <h1 className="text-xl font-bold text-slate-800">PFIC §1291 Calculator</h1>
        <p className="text-xs text-slate-500">Excess Distribution — IRC §1291 / Form 8621 Part V</p>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-slate-800">Clients</h2>
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
                {clients.length > 0 && (
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
                  + New Client
                </button>
              </>
            )}
          </div>
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
          <>
            {editMode && (
              <div className="flex items-center gap-2 mb-3 px-1">
                <input
                  type="checkbox"
                  checked={selected.size === clients.length}
                  onChange={toggleAll}
                  className="w-4 h-4 accent-blue-600"
                />
                <span className="text-xs text-slate-500">Select all</span>
              </div>
            )}
            <div className="space-y-2">
              {clients.map((c) => (
                <div
                  key={c.id}
                  onClick={() => {
                    if (renamingId === c.id) return
                    editMode ? toggleSelect(c.id) : nav(`/clients/${c.id}`)
                  }}
                  className={`group bg-white rounded-xl border px-5 py-4 flex items-center gap-3 cursor-pointer transition-all
                    ${editMode && selected.has(c.id)
                      ? 'border-red-300 bg-red-50'
                      : 'border-slate-200 hover:border-blue-400 hover:shadow-sm'}`}
                >
                  {editMode && (
                    <input
                      type="checkbox"
                      checked={selected.has(c.id)}
                      onChange={() => toggleSelect(c.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-4 h-4 accent-blue-600 shrink-0"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    {renamingId === c.id ? (
                      <input
                        autoFocus
                        value={renamingVal}
                        onChange={(e) => setRenamingVal(e.target.value)}
                        onBlur={() => saveRename(c.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') saveRename(c.id)
                          if (e.key === 'Escape') setRenamingId(null)
                        }}
                        onClick={(e) => e.stopPropagation()}
                        className="border border-blue-400 rounded px-2 py-0.5 text-sm font-medium text-slate-800 w-full focus:outline-none focus:ring-2 focus:ring-blue-300"
                      />
                    ) : (
                      <p className="font-medium text-slate-800">{c.client_code}</p>
                    )}
                    {c.tax_year_start && <p className="text-xs text-slate-500">First year: {c.tax_year_start}</p>}
                  </div>
                  {editMode ? null : (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                      <button
                        onClick={(e) => startRename(e, c)}
                        className="text-slate-400 hover:text-blue-600 p-1 rounded"
                        title="Rename client"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                          <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                        </svg>
                      </button>
                      <button
                        onClick={(e) => deleteSingle(e, c)}
                        className="text-slate-400 hover:text-red-600 p-1 rounded"
                        title="Delete client"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 112 0v6a1 1 0 11-2 0V8z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
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
