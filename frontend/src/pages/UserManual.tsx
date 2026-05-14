import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { content, type Lang } from '../i18n/manual'

export default function UserManual() {
  const nav = useNavigate()
  const [lang, setLang] = useState<Lang>('en')
  const t = content[lang]

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <button
          onClick={() => nav(-1)}
          className="text-slate-400 hover:text-slate-700 text-sm"
        >
          {t.backLabel}
        </button>
        <div className="text-center">
          <h1 className="text-base font-bold text-slate-800">{t.title}</h1>
          <p className="text-xs text-slate-500">{t.subtitle}</p>
        </div>
        <button
          onClick={() => setLang(lang === 'en' ? 'zh' : 'en')}
          className="text-sm text-blue-600 border border-blue-300 hover:bg-blue-50 px-3 py-1.5 rounded-lg transition-colors"
        >
          {t.toggleLabel}
        </button>
      </header>

      <div className="max-w-3xl mx-auto px-6 py-8 flex gap-8">
        {/* Table of Contents — sticky sidebar */}
        <aside className="hidden lg:block w-44 shrink-0">
          <div className="sticky top-24">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
              {t.tocLabel}
            </p>
            <nav className="space-y-1">
              {t.sections.map((s) => (
                <a
                  key={s.id}
                  href={`#${s.id}`}
                  className="block text-xs text-slate-500 hover:text-blue-600 py-0.5 leading-snug"
                >
                  {s.heading}
                </a>
              ))}
              <a
                href={`#${t.faq.id}`}
                className="block text-xs text-slate-500 hover:text-blue-600 py-0.5 leading-snug"
              >
                {t.faq.heading}
              </a>
            </nav>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 space-y-10">
          {t.sections.map((s) => (
            <section key={s.id} id={s.id}>
              <h2 className="text-lg font-bold text-slate-800 mb-3 pb-2 border-b border-slate-200">
                {s.heading}
              </h2>
              <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                {s.body.split(/(\*\*[^*]+\*\*)/).map((part, i) =>
                  part.startsWith('**') && part.endsWith('**') ? (
                    <strong key={i} className="font-semibold text-slate-800">
                      {part.slice(2, -2)}
                    </strong>
                  ) : (
                    <span key={i}>{part}</span>
                  )
                )}
              </div>
            </section>
          ))}

          {/* FAQ */}
          <section id={t.faq.id}>
            <h2 className="text-lg font-bold text-slate-800 mb-3 pb-2 border-b border-slate-200">
              {t.faq.heading}
            </h2>
            <div className="space-y-5">
              {t.faq.items.map((item, i) => (
                <div key={i} className="bg-white rounded-xl border border-slate-200 p-5">
                  <p className="font-semibold text-slate-800 text-sm mb-2">Q: {item.q}</p>
                  <p className="text-sm text-slate-600 leading-relaxed">{item.a}</p>
                </div>
              ))}
            </div>
          </section>

          <p className="text-xs text-slate-400 pt-4 border-t border-slate-200">
            {lang === 'en'
              ? 'This manual does not constitute tax advice. Verify all figures with a qualified tax professional before filing.'
              : '本說明文件不構成稅務建議。申報前請與合格稅務專業人員確認所有數據。'}
          </p>
        </main>
      </div>
    </div>
  )
}
