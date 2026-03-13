import { useState, useRef } from 'react';
import { api } from '../api';

type ScraperTab = 'import' | 'scrape';

export default function Scraper() {
  const [activeTab, setActiveTab] = useState<ScraperTab>('scrape');
  const [companyName, setCompanyName] = useState('');
  const [domain, setDomain] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [linkedinMaxEmployees, setLinkedinMaxEmployees] = useState(50);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [contacts, setContacts] = useState<any[]>([]);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleScrape = async () => {
    if (!companyName && !domain && !linkedinUrl) {
      setError('Enter company name, domain, or LinkedIn URL');
      return;
    }
    setLoading(true);
    setError('');
    setContacts([]);
    try {
      const res = await api.contacts.scrape({
        company_name: companyName || undefined,
        domain: domain || undefined,
        linkedin_url: linkedinUrl || undefined,
        linkedin_max_employees: linkedinUrl ? linkedinMaxEmployees : undefined,
      });
      setContacts(res.contacts);
    } catch (e: any) {
      setError(e.message || 'Scrape failed');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setError('');
    setContacts([]);
    try {
      const res = await api.contacts.importFile(file);
      setContacts(res.contacts);
    } catch (e: any) {
      setError(e.message || 'Import failed');
    } finally {
      setImporting(false);
      e.target.value = '';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 pb-12">
      <h1 className="text-2xl font-semibold text-deep-navy mb-8 pt-2">Contact Scraper</h1>

      {/* Segmented control */}
      <div className="inline-flex p-1 rounded-xl bg-pale-sky/60 mb-8">
        <button
          onClick={() => { setActiveTab('scrape'); setError(''); }}
          className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
            activeTab === 'scrape'
              ? 'bg-[#1a2f5a] text-white shadow-sm'
              : 'text-[#3d5c82] hover:bg-[#1e3a6e] hover:text-white'
          }`}
        >
          Scrape Website
        </button>
        <button
          onClick={() => { setActiveTab('import'); setError(''); }}
          className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
            activeTab === 'import'
              ? 'bg-[#1a2f5a] text-white shadow-sm'
              : 'text-[#3d5c82] hover:bg-[#1e3a6e] hover:text-white'
          }`}
        >
          Import Spreadsheet
        </button>
      </div>

      {activeTab === 'scrape' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-pale-sky">
            <div className="px-5 py-4 border-b border-pale-sky">
              <h2 className="text-[15px] font-semibold text-deep-navy">Scrape from Web</h2>
              <p className="text-[13px] text-slate-500 mt-0.5">
                Enter company name, domain, or LinkedIn URL
              </p>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Company name"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-pale-sky/30 text-deep-navy placeholder-slate-blue/70 text-[15px] border border-pale-sky/50 focus:ring-2 focus:ring-steel-blue/40 focus:ring-offset-0 focus:border-steel-blue transition-shadow"
                />
                <input
                  type="text"
                  placeholder="Domain (e.g. acme.com)"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-pale-sky/30 text-deep-navy placeholder-slate-blue/70 text-[15px] border border-pale-sky/50 focus:ring-2 focus:ring-steel-blue/40 focus:ring-offset-0 focus:border-steel-blue transition-shadow"
                />
              </div>
              <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
                <input
                  type="url"
                  placeholder="LinkedIn company URL"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  className="flex-1 w-full px-4 py-3 rounded-xl bg-pale-sky/30 text-deep-navy placeholder-slate-blue/70 text-[15px] border border-pale-sky/50 focus:ring-2 focus:ring-steel-blue/40 focus:ring-offset-0 focus:border-steel-blue transition-shadow"
                />
                <div className="flex items-center gap-2 shrink-0">
                  <label htmlFor="max-employees" className="text-[15px] text-slate-blue whitespace-nowrap">Max employees</label>
                  <input
                    id="max-employees"
                    type="number"
                    min={5}
                    max={100}
                    value={linkedinMaxEmployees}
                    onChange={(e) => setLinkedinMaxEmployees(parseInt(e.target.value, 10) || 50)}
                    className="w-20 px-3 py-2 rounded-lg bg-pale-sky/30 text-deep-navy text-[15px] text-right border border-pale-sky/50"
                  />
                </div>
              </div>
            </div>
            <div className="p-4 pt-0">
              <button
                onClick={handleScrape}
                disabled={loading || (!companyName && !domain && !linkedinUrl)}
                className="w-full py-3.5 rounded-xl bg-[#1a2f5a] hover:bg-[#1e3a6e] active:scale-[0.99] text-white text-[15px] font-semibold disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100 transition-all"
              >
                {loading ? 'Scraping...' : 'Start Scraping'}
              </button>
            </div>
          </div>
          {error && <p className="text-[#ff3b30] text-[13px] px-1 mt-2">{error}</p>}
        </div>
      )}

      {activeTab === 'import' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-pale-sky">
            <div className="px-5 py-4 border-b border-pale-sky">
              <h2 className="text-[15px] font-semibold text-deep-navy">Import from Spreadsheet</h2>
              <p className="text-[13px] text-slate-500 mt-0.5">
                CSV or Excel with name, email, title, company
              </p>
            </div>
            <div className="p-4">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx"
                onChange={handleImport}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={importing}
                className="w-full py-3.5 rounded-xl bg-[#1a2f5a] hover:bg-[#1e3a6e] active:scale-[0.99] text-white text-[15px] font-semibold disabled:opacity-50 transition-all"
              >
                {importing ? 'Importing...' : 'Import File'}
              </button>
            </div>
          </div>
          {error && <p className="text-[#ff3b30] text-[13px] px-1">{error}</p>}
        </div>
      )}

      {contacts.length > 0 && (
        <div className="mt-8 bg-white rounded-2xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-pale-sky">
          <div className="px-5 py-4 border-b border-pale-sky">
            <h2 className="text-[15px] font-semibold text-deep-navy">Discovered ({contacts.length})</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-[12px] text-slate-blue font-medium bg-pale-sky/40">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Company</th>
                  <th className="px-4 py-3">LinkedIn</th>
                  <th className="px-4 py-3">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {contacts.map((c) => (
                  <tr key={c.id} className="border-t border-pale-sky/50 hover:bg-pale-sky/20">
                    <td className="px-4 py-3 text-[14px] text-deep-navy">{c.name}</td>
                    <td className="px-4 py-3 text-[14px] text-steel-blue">{c.email}</td>
                    <td className="px-4 py-3 text-[14px] text-deep-navy">{c.title || '—'}</td>
                    <td className="px-4 py-3 text-[14px] text-deep-navy">{c.company || '—'}</td>
                    <td className="px-4 py-3">
                      {c.linkedin_url ? (
                        <a href={c.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-[14px] text-steel-blue hover:text-deep-navy">Profile</a>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-md text-[12px] font-medium ${
                          c.confidence === 'high'
                            ? 'bg-pale-sky/60 text-steel-blue'
                            : c.confidence === 'medium'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-pale-sky/40 text-slate-blue'
                        }`}
                      >
                        {c.confidence}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
