import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function PrivacyPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-brand-dark text-white">
      <div className="border-b border-white/5 px-6 py-4">
        <div className="max-w-2xl mx-auto">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors font-mono"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-12 space-y-8">
        <h1 className="text-3xl font-display font-bold">Privacy Policy</h1>
        <p className="text-xs font-mono text-gray-500">Last updated: February 25, 2026</p>

        <div className="space-y-6 text-sm font-mono text-gray-300 leading-relaxed">
          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">Identity & Contact</h2>
            <p>
              Journeylauncher LLC ("we", "us", "our") operates LaunchAd.io.<br />
              Data protection contact: <span className="text-brand-lime">privacy@launchad.io</span>
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">Data We Collect</h2>
            <div className="bg-brand-gray border border-white/10 p-4 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Email address</span>
                <span className="text-gray-500">Required for service</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Consent records</span>
                <span className="text-gray-500">Timestamp, IP, choices</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Product URLs</span>
                <span className="text-gray-500">For ad generation</span>
              </div>
            </div>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">Purpose & Legal Basis</h2>
            <div className="bg-brand-gray border border-white/10 p-4 space-y-3">
              <div>
                <p className="text-xs text-white">Service delivery</p>
                <p className="text-xs text-gray-500">Legal basis: Contract performance (Art. 6(1)(b))</p>
              </div>
              <div>
                <p className="text-xs text-white">Marketing communications</p>
                <p className="text-xs text-gray-500">Legal basis: Consent (Art. 6(1)(a)) — only with explicit opt-in</p>
              </div>
              <div>
                <p className="text-xs text-white">Security & fraud prevention</p>
                <p className="text-xs text-gray-500">Legal basis: Legitimate interest (Art. 6(1)(f))</p>
              </div>
            </div>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">Data Recipients</h2>
            <p>Your data may be processed by the following categories of service providers:</p>
            <ul className="list-disc list-inside space-y-1 text-gray-400">
              <li>Cloud hosting provider (database and application hosting)</li>
              <li>Email service provider (for marketing communications, with consent)</li>
              <li>AI model providers (for ad creative generation — URLs only, not personal data)</li>
            </ul>
            <p>Data Processing Agreements are in place with all sub-processors.</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">Data Retention</h2>
            <div className="bg-brand-gray border border-white/10 p-4 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Email (service)</span>
                <span className="text-gray-500">Duration of active use</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Email (marketing)</span>
                <span className="text-gray-500">Until consent withdrawal + 30 days</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Consent records</span>
                <span className="text-gray-500">6 years (legal compliance)</span>
              </div>
            </div>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">International Transfers</h2>
            <p>
              Data is processed within the European Economic Area where possible.
              Where data is transferred outside the EEA, we rely on Standard Contractual Clauses
              or adequacy decisions as the transfer mechanism.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">Your Rights</h2>
            <p>Under GDPR, you have the right to:</p>
            <ul className="list-disc list-inside space-y-1 text-gray-400">
              <li>Access your personal data</li>
              <li>Rectify inaccurate data</li>
              <li>Erase your data ("right to be forgotten")</li>
              <li>Restrict processing</li>
              <li>Data portability (export in JSON/CSV)</li>
              <li>Object to processing</li>
              <li>Withdraw consent at any time</li>
              <li>Lodge a complaint with a supervisory authority</li>
            </ul>
            <p>
              Contact <span className="text-brand-lime">privacy@launchad.io</span> to exercise these rights.
              We will respond within 1 month per GDPR Article 12(3).
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">Automated Decision-Making</h2>
            <p>
              We use AI models to generate ad creatives. This processing does not involve automated
              decision-making that produces legal effects concerning you.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">Policy Updates</h2>
            <p>
              We may update this policy periodically. Material changes will be communicated via
              email (if you have opted in) or through a notice on our website.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">Contact</h2>
            <p>
              Journeylauncher LLC<br />
              Email: <span className="text-brand-lime">privacy@launchad.io</span>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
