// UI Translations dictionary for English, Hindi, Tamil, Telugu, Bengali, Kannada

export type SupportedLanguage = 'en' | 'hi' | 'ta' | 'te' | 'bn' | 'kn';

export interface UiStrings {
  // Navigation & Header
  investigate: string;
  stories: string;
  tagline: string;
  topBarLeft: string;
  topBarRight: string;

  // Hero Section
  heroQuote: string;
  heroAuthor: string;
  heroHeadline: string;
  heroSide: string;

  // Search
  searchPlaceholder: string;
  traceBtn: string;
  tracingBtn: string;

  // Translation Panel
  translateFullArticle: string;
  translateBtn: string;
  translatingBtn: string;
  viewOriginal: string;
  viewTranslation: string;
  translatedFrom: string;
  into: string;
  viewingOriginal: string;
  fromCache: string;

  // Article Cards
  by: string;
  readArticle: string;
  readMainSource: string;
  today: string;
  translatingCard: string;

  // Analysis Section
  analysisTitle: string;
  analyzingReport: string;
  summaryTitle: string;
  sourcesTitle: string;
  driftTitle: string;
  correctionsTitle: string;
  primarySource: string;
  derivativeSource: string;
  originalText: string;
  driftedText: string;
  shiftDetected: string;
  noDrift: string;
  noCorrections: string;
  confidenceScore: string;
  detectedDriftCount: string;
  severityLevel: string;
}

export const UI_TRANSLATIONS: Record<SupportedLanguage, UiStrings> = {
  en: {
    investigate: "INVESTIGATE",
    stories: "STORIES",
    tagline: "SAME STORY. DIFFERENT REALITIES.",
    topBarLeft: "GLOBAL NEWS. DEEPER CONTEXT.",
    topBarRight: "FACTS TRAVEL FASTER THAN TRUTH.",

    heroQuote: '"In a world of information, context is everything."',
    heroAuthor: "— CHURNALIST",
    heroHeadline: "THE SAME STORY DOESN'T ALWAYS STAY THE SAME.",
    heroSide: "PEOPLE READ NEWS. WE READ BETWEEN THE LINES.",

    searchPlaceholder: "Enter URL of your news",
    traceBtn: "TRACE",
    tracingBtn: "TRACING...",

    translateFullArticle: "TRANSLATE FULL ARTICLE:",
    translateBtn: "TRANSLATE",
    translatingBtn: "TRANSLATING...",
    viewOriginal: "VIEW ORIGINAL",
    viewTranslation: "VIEW TRANSLATION",
    translatedFrom: "Translated from",
    into: "into",
    viewingOriginal: "Viewing Original",
    fromCache: "From Cache",

    by: "By",
    readArticle: "READ ARTICLE",
    readMainSource: "READ MAIN SOURCE",
    today: "TODAY",
    translatingCard: "TRANSLATING...",

    analysisTitle: "PROVENANCE & DRIFT INTELLIGENCE",
    analyzingReport: "ANALYZING STORY DRIFT WITH GROQ AI...",
    summaryTitle: "EXECUTIVE INTELLIGENCE SUMMARY",
    sourcesTitle: "SOURCE OVERLAP & CROSS-REFERENCING",
    driftTitle: "IDENTIFIED DRIFT SIGNALS",
    correctionsTitle: "CORRECTION TRAILS",
    primarySource: "PRIMARY SOURCE",
    derivativeSource: "DERIVATIVE SOURCE",
    originalText: "Original Text",
    driftedText: "Drifted Text",
    shiftDetected: "Shift Detected",
    noDrift: "No significant factual drift detected between sources.",
    noCorrections: "No post-publication corrections detected.",
    confidenceScore: "Confidence Score",
    detectedDriftCount: "Detected Drift Signals",
    severityLevel: "Severity"
  },

  kn: {
    investigate: "ತನಿಖೆ",
    stories: "ಸುದ್ದಿಗಳು",
    tagline: "ಒಂದೇ ಕಥೆ. ವಿಭಿನ್ನ ವಾಸ್ತವಗಳು.",
    topBarLeft: "ಜಾಗತಿಕ ಸುದ್ದಿ. ಆಳವಾದ ಸನ್ನಿವೇಶ.",
    topBarRight: "ಸತ್ಯಕ್ಕಿಂತ ವೇಗವಾಗಿ ಸಂಗತಿಗಳು ಚಲಿಸುತ್ತವೆ.",

    heroQuote: '"ಮಾಹಿತಿಯ ಜಗತ್ತಿನಲ್ಲಿ, ಸನ್ನಿವೇಶವೇ ಎಲ್ಲವೂ."',
    heroAuthor: "— ಚರ್ನಲಿಸ್ಟ್",
    heroHeadline: "ಒಂದೇ ಕಥೆ ಯಾವಾಗಲೂ ಒಂದೇ ರೀತಿ ಉಳಿಯುವುದಿಲ್ಲ.",
    heroSide: "ಜನರು ಸುದ್ದಿ ಓದುತ್ತಾರೆ. ನಾವು ಸಾಲುಗಳ ನಡುವಿನ ಅರ್ಥವನ್ನು ಓದುತ್ತೇವೆ.",

    searchPlaceholder: "ನಿಮ್ಮ ಸುದ್ದಿಯ URL ನಮೂದಿಸಿ",
    traceBtn: "ಟ್ರೇಸ್",
    tracingBtn: "ಟ್ರೇಸ್ ಮಾಡಲಾಗುತ್ತಿದೆ...",

    translateFullArticle: "ಪೂರ್ಣ ಲೇಖನವನ್ನು ಅನುವಾದಿಸಿ:",
    translateBtn: "ಅನುವಾದಿಸಿ",
    translatingBtn: "ಅನುವಾದಿಸಲಾಗುತ್ತಿದೆ...",
    viewOriginal: "ಮೂಲವನ್ನು ವೀಕ್ಷಿಸಿ",
    viewTranslation: "ಅನುವಾದವನ್ನು ವೀಕ್ಷಿಸಿ",
    translatedFrom: "ಇಂದ ಅನುವಾದಿಸಲಾಗಿದೆ",
    into: "ಗೆ",
    viewingOriginal: "ಮೂಲ ಪಠ್ಯವನ್ನು ವೀಕ್ಷಿಸಲಾಗುತ್ತಿದೆ",
    fromCache: "ಕ್ಯಾಶ್‌ನಿಂದ",

    by: "ಮೂಲಕ",
    readArticle: "ಲೇಖನ ಓದಿ",
    readMainSource: "ಮುಖ್ಯ ಮೂಲವನ್ನು ಓದಿ",
    today: "ಇಂದು",
    translatingCard: "ಅನುವಾದಿಸಲಾಗುತ್ತಿದೆ...",

    analysisTitle: "ಮೂಲ ಮತ್ತು ವಿಚಲನ ಬುದ್ಧಿಮತ್ತೆ",
    analyzingReport: "GROQ AI ಮೂಲಕ ಸುದ್ದಿಯ ವಿಚಲನ ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...",
    summaryTitle: "ಕಾರ್ಯನಿರ್ವಾಹಕ ಸಾರಾಂಶ",
    sourcesTitle: "ಮೂಲಗಳ ಹೋಲಿಕೆ ಮತ್ತು ಪರಿಶೀಲನೆ",
    driftTitle: "ಗುರುತಿಸಲಾದ ವಿಚಲನ ಸಂಕೇತಗಳು",
    correctionsTitle: "ತಿದ್ದುಪಡಿಗಳ ಇತಿಹಾಸ",
    primarySource: "ಪ್ರಾಥಮಿಕ ಮೂಲ",
    derivativeSource: "ಉತ್ಪನ್ನ ಮೂಲ",
    originalText: "ಮೂಲ ಪಠ್ಯ",
    driftedText: "ಬದಲಾದ ಪಠ್ಯ",
    shiftDetected: "ಬದಲಾವಣೆ ಗುರುತಿಸಲಾಗಿದೆ",
    noDrift: "ಮೂಲಗಳ ನಡುವೆ ಯಾವುದೇ ಪ್ರಮುಖ ವಿಚಲನ ಕಂಡುಬಂದಿಲ್ಲ.",
    noCorrections: "ಯಾವುದೇ ತಿದ್ದುಪಡಿಗಳು ಕಂಡುಬಂದಿಲ್ಲ.",
    confidenceScore: "ವಿಶ್ವಾಸಾರ್ಹತೆ ಸ್ಕೋರ್",
    detectedDriftCount: "ಗುರುತಿಸಲಾದ ವಿಚಲನಗಳು",
    severityLevel: "ತೀವ್ರತೆ"
  },

  hi: {
    investigate: "जांच",
    stories: "कहानियां",
    tagline: "वही कहानी। अलग वास्तविकताएं।",
    topBarLeft: "वैश्विक समाचार। गहरा संदर्भ।",
    topBarRight: "तथ्य सच से भी तेज यात्रा करते हैं।",

    heroQuote: '"सूचना की दुनिया में, संदर्भ ही सब कुछ है।"',
    heroAuthor: "— चर्नलिस्ट",
    heroHeadline: "वही कहानी हमेशा वैसी नहीं रहती।",
    heroSide: "लोग खबरें पढ़ते हैं। हम पंक्तियों के बीच पढ़ते हैं।",

    searchPlaceholder: "अपने समाचार का URL दर्ज करें",
    traceBtn: "ट्रेस करें",
    tracingBtn: "ट्रेस हो रहा है...",

    translateFullArticle: "पूरा लेख अनुवाद करें:",
    translateBtn: "अनुवाद करें",
    translatingBtn: "अनुवाद हो रहा है...",
    viewOriginal: "मूल देखें",
    viewTranslation: "अनुवाद देखें",
    translatedFrom: "से अनुवादित",
    into: "में",
    viewingOriginal: "मूल पाठ देख रहे हैं",
    fromCache: "कैश से",

    by: "द्वारा",
    readArticle: "लेख पढ़ें",
    readMainSource: "मुख्य स्रोत पढ़ें",
    today: "आज",
    translatingCard: "अनुवाद हो रहा है...",

    analysisTitle: "उत्पत्ति और विचलन विश्लेषण",
    analyzingReport: "GROQ AI से विचलन विश्लेषण किया जा रहा है...",
    summaryTitle: "कार्यकारी सारांश",
    sourcesTitle: "स्रोत ओवरलैप और क्रॉस-रेफरेंसिंग",
    driftTitle: "पहचाने गए विचलन संकेत",
    correctionsTitle: "संशोधन विवरण",
    primarySource: "प्राथमिक स्रोत",
    derivativeSource: "व्युत्पन्न स्रोत",
    originalText: "मूल पाठ",
    driftedText: "बदला हुआ पाठ",
    shiftDetected: "बदलाव पाया गया",
    noDrift: "स्रोतों के बीच कोई महत्वपूर्ण विचलन नहीं मिला।",
    noCorrections: "कोई संशोधन दर्ज नहीं किया गया।",
    confidenceScore: "विश्वसनीयता स्कोर",
    detectedDriftCount: "पहचाने गए विचलन",
    severityLevel: "गंभीरता"
  },

  ta: {
    investigate: "ஆராய்",
    stories: "செய்திகள்",
    tagline: "ஒரே கதை. வெவ்வேறு யதார்த்தங்கள்.",
    topBarLeft: "உலகளாவிய செய்தி. ஆழமான சூழல்.",
    topBarRight: "உண்மையை விட உண்மைகள் வேகமாகப் பயணிக்கின்றன.",

    heroQuote: '"தகவல் உலகில், சூழலே எல்லாமும்."',
    heroAuthor: "— சர்னலிஸ்ட்",
    heroHeadline: "ஒரே செய்தி எப்போதும் ஒரே மாதிரியாக இருப்பதில்லை.",
    heroSide: "மக்கள் செய்தி படிக்கிறார்கள். நாங்கள் வரிகளுக்கு இடையே படிக்கிறோம்.",

    searchPlaceholder: "செய்தியின் URL-ஐ உள்ளிடவும்",
    traceBtn: "கண்டறி",
    tracingBtn: "கண்டறியப்படுகிறது...",

    translateFullArticle: "முழு கட்டுரையை மொழிபெயர்க்கவும்:",
    translateBtn: "மொழிபெயர்",
    translatingBtn: "மொழிபெயர்க்கப்படுகிறது...",
    viewOriginal: "அசல் பார்க்க",
    viewTranslation: "மொழிபெயர்ப்பு பார்க்க",
    translatedFrom: "இருந்து மொழிபெயர்க்கப்பட்டது",
    into: "இல்",
    viewingOriginal: "அசல் உரையைப் பார்க்கிறீர்கள்",
    fromCache: "கேச் மூலம்",

    by: "வழங்கியவர்",
    readArticle: "கட்டுரையைப் படிக்க",
    readMainSource: "முக்கிய மூலத்தைப் படிக்க",
    today: "இன்று",
    translatingCard: "மொழிபெயர்க்கப்படுகிறது...",

    analysisTitle: "மூல மற்றும் மாற்றப் பகுப்பாய்வு",
    analyzingReport: "GROQ AI மூலம் பகுப்பாய்வு செய்யப்படுகிறது...",
    summaryTitle: "முக்கிய சுருக்கம்",
    sourcesTitle: "மூலங்களின் ஒப்பீடு",
    driftTitle: "கண்டறியப்பட்ட மாற்றங்கள்",
    correctionsTitle: "திருத்தங்களின் விவரம்",
    primarySource: "முதன்மை மூலம்",
    derivativeSource: "இரண்டாம் நிலை மூலம்",
    originalText: "அசல் உரை",
    driftedText: "மாற்றப்பட்ட உரை",
    shiftDetected: "மாற்றம் கண்டறியப்பட்டது",
    noDrift: "மூலங்களுக்கு இடையே பெரிய மாற்றங்கள் இல்லை.",
    noCorrections: "எந்த திருத்தங்களும் பதிவு செய்யப்படவில்லை.",
    confidenceScore: "நம்பகத்தன்மை மதிப்பீடு",
    detectedDriftCount: "கண்டறியப்பட்ட மாற்றங்கள்",
    severityLevel: "தீவிரம்"
  },

  te: {
    investigate: "పరిశోధన",
    stories: "వార్తలు",
    tagline: "ఒకే కథనం. విభిన్న వాస్తవాలు.",
    topBarLeft: "గ్లోబల్ న్యూస్. లోతైన సందర్భం.",
    topBarRight: "నిజం కంటే వాస్తవాలు వేగంగా ప్రయాణిస్తాయి.",

    heroQuote: '"సమాచార ప్రపంచంలో, సందర్భమే సర్వస్వం."',
    heroAuthor: "— చర్నలిస్ట్",
    heroHeadline: "ఒకే వార్త ఎల్లప్పుడూ ఒకేలా ఉండదు.",
    heroSide: "ప్రజలు వార్తలు చదువుతారు. మేము లోతైన అర్థాన్ని చదువుతాము.",

    searchPlaceholder: "మీ వార్త URL నమోదు చేయండి",
    traceBtn: "ట్రేస్ చేయండి",
    tracingBtn: "ట్రేస్ చేస్తోంది...",

    translateFullArticle: "పూర్తి కథనాన్ని అనువదించండి:",
    translateBtn: "అనువదించు",
    translatingBtn: "అనువదిస్తోంది...",
    viewOriginal: "అసలు చూడండి",
    viewTranslation: "అనువాదం చూడండి",
    translatedFrom: "నుండి అనువదించబడింది",
    into: "లోకి",
    viewingOriginal: "అసలు పాఠం చూస్తున్నారు",
    fromCache: "క్యాష్ నుండి",

    by: "ద్వారా",
    readArticle: "కథనాన్ని చదవండి",
    readMainSource: "ప్రధాన మూలాన్ని చదవండి",
    today: "ఈరోజు",
    translatingCard: "అనువదిస్తోంది...",

    analysisTitle: "మూల మరియు వ్యత్యాస విశ్లేషణ",
    analyzingReport: "GROQ AI తో వ్యత్యాస విశ్లేషణ జరుగుతోంది...",
    summaryTitle: "కార్యనిర్వాహక సారాంశం",
    sourcesTitle: "మూలాల సరిపోలిక",
    driftTitle: "గుర్తించిన వ్యత్యాసాలు",
    correctionsTitle: "సవరణల చరిత్ర",
    primarySource: "ప్రాథమిక మూలం",
    derivativeSource: "ద్వితీయ మూలం",
    originalText: "అసలు పాఠం",
    driftedText: "మారిన పాఠం",
    shiftDetected: "మార్పు గుర్తించబడింది",
    noDrift: "మూలాల మధ్య ఎటువంటి ముఖ్యమైన వ్యత్యాసాలు లేవు.",
    noCorrections: "ఎటువంటి సవరణలు లేవు.",
    confidenceScore: "విశ్వసనీయత స్కోర్",
    detectedDriftCount: "గుర్తించిన వ్యత్యాసాలు",
    severityLevel: "తీవ్రత"
  },

  bn: {
    investigate: "অনুসন্ধান",
    stories: "সংবাদ",
    tagline: "একই ঘটনা। ভিন্ন বাস্তবতা।",
    topBarLeft: "বিশ্ব সংবাদ। গভীর প্রেক্ষাপট।",
    topBarRight: "সত্যের চেয়ে তথ্য দ্রুত ছড়ায়।",

    heroQuote: '"তথ্যের দুনিয়ায়, প্রেক্ষাপটই আসল।"',
    heroAuthor: "— চার্নালিস্ট",
    heroHeadline: "একই খবর সবসময় এক থাকে না।",
    heroSide: "মানুষ খবর পড়ে। আমরা ভেতরের অর্থ খুঁজি।",

    searchPlaceholder: "আপনার সংবাদের URL লিখুন",
    traceBtn: "ট্রেস করুন",
    tracingBtn: "ট্রেস হচ্ছে...",

    translateFullArticle: "পুরো প্রতিবেদন অনুবাদ করুন:",
    translateBtn: "অনুবাদ করুন",
    translatingBtn: "অনুবাদ হচ্ছে...",
    viewOriginal: "আসল দেখুন",
    viewTranslation: "অনুবাদ দেখুন",
    translatedFrom: "থেকে অনূদিত",
    into: "তে",
    viewingOriginal: "আসল পাঠ্য দেখা হচ্ছে",
    fromCache: "ক্যাশে থেকে",

    by: "দ্বారా",
    readArticle: "প্রতিবেদন পড়ুন",
    readMainSource: "মূল উৎস পড়ুন",
    today: "আজ",
    translatingCard: "অনুবাদ হচ্ছে...",

    analysisTitle: "উৎস ও বিচ্যুতি বিশ্লেষণ",
    analyzingReport: "GROQ AI দিয়ে বিচ্যুতি বিশ্লেষণ করা হচ্ছে...",
    summaryTitle: "সারসংক্ষেপ",
    sourcesTitle: "উৎস যাচাই ও সমন্বয়",
    driftTitle: "শনাক্তকৃত পরিবর্তনসমূহ",
    correctionsTitle: "সংশোধন বিবরণ",
    primarySource: "প্রাথমিক উৎস",
    derivativeSource: "সহায়ক উৎস",
    originalText: "আসল পাঠ্য",
    driftedText: "পরিবর্তিত পাঠ্য",
    shiftDetected: "পরিবর্তন শনাক্ত",
    noDrift: "উৎসগুলির মধ্যে কোনো বড় পরিবর্তন পাওয়া যায়নি।",
    noCorrections: "কোনো সংশোধন পাওয়া যায়নি।",
    confidenceScore: "বিশ্বাসযোগ্যতা স্কোর",
    detectedDriftCount: "শনাক্তকৃত পরিবর্তন",
    severityLevel: "তীব্রতা"
  }
};

export function getUiStrings(lang: string): UiStrings {
  const code = (lang || 'en').toLowerCase() as SupportedLanguage;
  return UI_TRANSLATIONS[code] || UI_TRANSLATIONS.en;
}
