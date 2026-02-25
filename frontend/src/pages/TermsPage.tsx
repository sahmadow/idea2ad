import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function TermsPage() {
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
        <h1 className="text-3xl font-display font-bold">Terms of Service</h1>
        <p className="text-xs font-mono text-gray-500">Last updated: February 25, 2026</p>

        <div className="space-y-6 text-sm font-mono text-gray-300 leading-relaxed">
          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">1. Service Description</h2>
            <p>
              LaunchAd.io is an AI-powered ad creative generation platform operated by Journeylauncher LLC.
              The service analyzes product landing pages and generates ad creatives for social media advertising.
            </p>
            <p>
              Providing an email address for marketing communications is optional and separate from service usage.
              You may use the ad generation service regardless of whether you opt into marketing emails.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">2. Data Collection & Use</h2>
            <p>We collect the following personal data when you use our service:</p>
            <ul className="list-disc list-inside space-y-1 text-gray-400">
              <li>Email address (required to generate ads)</li>
              <li>Consent records (timestamp, IP address, consent choices)</li>
            </ul>
            <p>
              This data is used for: (a) service delivery, and (b) marketing communications (only with your
              separate, explicit consent). See our <a href="/privacy" className="text-brand-lime hover:underline">Privacy Policy</a> for full details.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">3. Marketing Communications</h2>
            <p>
              Marketing emails are sent only with your explicit opt-in consent. These may include product updates,
              feature announcements, and promotional offers from Journeylauncher LLC.
            </p>
            <p>
              You may unsubscribe at any time by clicking the unsubscribe link in any marketing email or
              by contacting us at <span className="text-brand-lime">privacy@launchad.io</span>.
              Every marketing email will contain an unsubscribe link.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">4. Data Retention</h2>
            <p>
              We retain your email address for as long as you maintain an active relationship with our service,
              or until you withdraw consent for marketing (whichever applies). Marketing data will be deleted
              within 30 days of consent withdrawal.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">5. Your Rights (GDPR Articles 15–22)</h2>
            <p>Under the General Data Protection Regulation, you have the right to:</p>
            <ul className="list-disc list-inside space-y-1 text-gray-400">
              <li>Access your personal data (Art. 15)</li>
              <li>Rectify inaccurate data (Art. 16)</li>
              <li>Erase your data / "right to be forgotten" (Art. 17)</li>
              <li>Restrict processing (Art. 18)</li>
              <li>Data portability (Art. 20)</li>
              <li>Object to processing (Art. 21)</li>
              <li>Withdraw consent at any time (Art. 7(3))</li>
              <li>Lodge a complaint with a supervisory authority</li>
            </ul>
            <p>
              To exercise any of these rights, contact us at{' '}
              <span className="text-brand-lime">privacy@launchad.io</span>.
              We will respond within 1 month.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">6. Security</h2>
            <p>
              We implement technical and organizational measures to protect your data, including encryption in
              transit (TLS 1.2+) and at rest. In the event of a data breach affecting your data, we will
              notify you in accordance with GDPR Articles 33 and 34.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">7. Age Restrictions</h2>
            <p>
              You must be at least 16 years old to use this service and provide consent for data processing.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">8. Governing Law</h2>
            <p>
              These terms are governed by the laws of the European Union and the applicable member state.
              You have the right to lodge complaints with your local data protection authority.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-display text-white">9. Contact</h2>
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
