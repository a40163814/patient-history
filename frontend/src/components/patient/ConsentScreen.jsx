import React, { useState } from 'react';
import { ShieldCheck, UserCheck, AlertCircle, ArrowRight, Check } from 'lucide-react';
import { submitConsent } from '../../services/api';

export default function ConsentScreen({ patient, onConsentApproved }) {
  const [accepted, setAccepted] = useState(false);
  const [isGuardian, setIsGuardian] = useState(false);
  const [guardianName, setGuardianName] = useState('');
  const [guardianRelation, setGuardianRelation] = useState('Parent');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const lang = patient.preferred_language || 'en';

  const texts = {
    en: {
      title: "Informed Patient Consent",
      subtitle: "Digital Personal Data Protection (DPDP Act 2023) Notice",
      q_what: "What We Collect:",
      a_what: "Your symptoms, pre-existing conditions, allergies, current medicines (Allopathic, Ayurvedic, Homeopathic), family history, vitals, and uploaded report photos.",
      q_why: "Why We Collect It:",
      a_why: "To organize a structured pre-intake case record so the consulting Ayush doctor can evaluate you efficiently.",
      q_who: "Who Sees It:",
      a_who: "Strictly your examining doctor and medical clinic staff. It is never sold or shared for marketing.",
      q_audio: "Audio & AI Processing:",
      a_audio: "Raw voice audio is processed in memory and NOT stored on our clinic servers. Audio data is transcribed in real-time by an external AI service provider.",
      guardian_toggle: "A caregiver, parent, or guardian is answering on behalf of the patient or minor",
      agree_label: "I have read and agree to the pre-OPD digital intake terms.",
      submit_btn: "Accept & Continue to Vitals"
    },
    hi: {
      title: "सूचित रोगी सहमति (Informed Consent)",
      subtitle: "डिजिटल व्यक्तिगत डेटा संरक्षण (DPDP अधिनियम 2023) सूचना",
      q_what: "हम क्या जानकारी लेते हैं:",
      a_what: "आपके वर्तमान लक्षण, पुरानी बीमारियां, एलर्जी, वर्तमान दवाएं (अंग्रेजी, काढ़ा, चूर्ण, होम्योपैथी), पारिवारिक इतिहास और जांच रिपोर्ट की तस्वीरें।",
      q_why: "हम यह जानकारी क्यों लेते हैं:",
      a_why: "डॉक्टर साहब के देखने से पहले आपकी केस शीट तैयार करने के लिए, जिससे परामर्श सटीक और तेज हो सके।",
      q_who: "यह कौन देखता है:",
      a_who: "केवल आपके जांचकर्ता आयुष डॉक्टर और क्लिनिक कर्मचारी। यह जानकारी पूरी तरह गोपनीय है।",
      q_audio: "ऑडियो और एआई प्रोसेसिंग:",
      a_audio: "आपकी आवाज का कच्चा ऑडियो हमारे सिस्टम पर स्टोर नहीं किया जाता। यह रीयल-टाइम में बाहरी एआई सेवा द्वारा प्रोसेस किया जाता है।",
      guardian_toggle: "मैं मरीज या बच्चे की ओर से उत्तर दे रहा/रही हूँ (अभिभावक / तीमारदार)",
      agree_label: "मैंने सभी शर्तें पढ़ ली हैं और मैं इस प्रक्रिया से सहमत हूँ।",
      submit_btn: "सहमति दें और आगे बढ़ें"
    },
    mr: {
      title: "माहिती संमती पत्र (Patient Consent)",
      subtitle: "डिजिटल वैयक्तिक डेटा संरक्षण (DPDP Act 2023) सूचना",
      q_what: "आम्ही कोणती माहिती गोळा करतो:",
      a_what: "तुमची लक्षणे, जुने आजार, अ‍ॅलर्जी, सुरू असलेली औषधे (काढा, चूर्ण, अ‍ॅलोपॅथिक), कौटुंबिक इतिहास आणि तपासणी रिपोर्ट.",
      q_why: "माहिती कशासाठी गोळा केली जाते:",
      a_why: "डॉक्टरांना तपासणीपूर्वी तुमची केस शीट तयार करून देण्यासाठी.",
      q_who: "ही माहिती कोणाला दिसते:",
      a_who: "फक्त तपासणारे आयुष डॉक्टर आणि दवाखाना कर्मचारी. इतर कोणाशीही शेअर केली जात नाही.",
      q_audio: "आवाज व एआय प्रोसेसिंग:",
      a_audio: "तुमचा आवाज आमच्या सिस्टीमवर सेव्ह केला जात नाही. तो सुरक्षितपणे एआय द्वारे ट्रान्सक्राइब होतो.",
      guardian_toggle: "पालक किंवा नातेवाईक रुग्णाच्या वतीने उत्तरे देत आहेत",
      agree_label: "मी सर्व अटी वाचल्या असून मी संमती देत आहे.",
      submit_btn: "संमती द्या आणि पुढे चला"
    }
  };

  const t = texts[lang] || texts.en;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!accepted) {
      setError('Please check the consent agreement to proceed');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await submitConsent({
        patient_token: patient.patient_token,
        consent_given: true,
        is_guardian_mode: isGuardian,
        guardian_name: isGuardian ? guardianName : null,
        guardian_relation: isGuardian ? guardianRelation : null,
        preferred_language: lang
      });
      onConsentApproved({
        is_guardian_mode: isGuardian,
        guardian_name: guardianName,
        guardian_relation: guardianRelation
      });
    } catch (err) {
      setError('Failed to record consent. Please retry.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="text-center space-y-1">
        <div className="inline-flex p-2.5 bg-emerald-100 text-emerald-800 rounded-full mb-2">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-800">{t.title}</h2>
        <p className="text-xs text-slate-500">{t.subtitle}</p>
      </div>

      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4 text-sm text-slate-700">
        <div className="space-y-1">
          <p className="font-semibold text-slate-900">{t.q_what}</p>
          <p className="text-xs text-slate-600 leading-relaxed">{t.a_what}</p>
        </div>

        <div className="space-y-1">
          <p className="font-semibold text-slate-900">{t.q_why}</p>
          <p className="text-xs text-slate-600 leading-relaxed">{t.a_why}</p>
        </div>

        <div className="space-y-1">
          <p className="font-semibold text-slate-900">{t.q_who}</p>
          <p className="text-xs text-slate-600 leading-relaxed">{t.a_who}</p>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
          <p className="font-semibold text-emerald-900 text-xs">{t.q_audio}</p>
          <p className="text-xs text-slate-600 leading-relaxed">{t.a_audio}</p>
        </div>

        {/* Guardian / Caregiver Mode Toggle */}
        <div className="pt-2 border-t border-slate-200">
          <label className="flex items-start space-x-3 cursor-pointer">
            <input
              type="checkbox"
              checked={isGuardian}
              onChange={(e) => setIsGuardian(e.target.checked)}
              className="w-5 h-5 mt-0.5 rounded text-emerald-700 focus:ring-emerald-600"
            />
            <span className="text-xs font-medium text-slate-800">
              {t.guardian_toggle}
            </span>
          </label>

          {isGuardian && (
            <div className="mt-3 grid grid-cols-2 gap-3 pl-8">
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">
                  Guardian / Caregiver Name
                </label>
                <input
                  type="text"
                  value={guardianName}
                  onChange={(e) => setGuardianName(e.target.value)}
                  placeholder="Full Name"
                  className="w-full px-3 py-2 text-xs rounded border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                  required={isGuardian}
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">
                  Relationship to Patient
                </label>
                <select
                  value={guardianRelation}
                  onChange={(e) => setGuardianRelation(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                >
                  <option value="Parent">Parent</option>
                  <option value="Child / Son / Daughter">Child (Son/Daughter)</option>
                  <option value="Spouse">Spouse</option>
                  <option value="Sibling">Sibling</option>
                  <option value="Caregiver">Caregiver / Attendant</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mandatory Acceptance Checkbox */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <label className="flex items-center space-x-3 cursor-pointer">
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
            className="w-6 h-6 rounded text-emerald-700 focus:ring-emerald-600"
          />
          <span className="text-sm font-semibold text-slate-900">
            {t.agree_label}
          </span>
        </label>

        {error && (
          <p className="text-xs text-red-600 font-medium bg-red-50 p-2 rounded">
            {error}
          </p>
        )}

        <button
          onClick={handleSubmit}
          disabled={!accepted || loading}
          className={`w-full py-3.5 rounded-lg font-semibold text-base shadow transition flex items-center justify-center space-x-2 min-h-touch ${
            accepted && !loading
              ? 'bg-emerald-700 hover:bg-emerald-800 text-white'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        >
          {loading ? (
            <span>Recording Consent...</span>
          ) : (
            <>
              <span>{t.submit_btn}</span>
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
