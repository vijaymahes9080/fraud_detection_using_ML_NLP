import { useState, useEffect } from 'react';
import './App.css';

// Quick click-to-test presets for both Tamil and English (Wow Factor)
const TEMPLATE_PRESETS = {
  SMS: [
    { label: "Spam (English)", text: "Congratulations! You have won a £1,000 Walmart Gift Card. Click here to claim your prize now: http://walmart-winner.ru" },
    { label: "Spam (Tamil)", text: "வாழ்த்துகள்! உங்களுக்கு ரூ.50,000 ரொக்கப் பரிசு கிடைத்துள்ளது! உடனே பெற இந்த லிங்கை கிளிக் செய்க: http://scam-prize.ru" },
    { label: "Safe (English)", text: "Hey! Just wanted to check if you are still free to grab a quick coffee this afternoon around 3 PM? Let me know." },
    { label: "Safe (Tamil)", text: "அம்மா, நாம் இன்று மதியம் 1 மணிக்கு சாப்பிடுகிறோமா? எனக்கு சொல்லுங்கள்." }
  ],
  EMAIL: [
    { label: "Phishing (English)", text: "DEAR VALUED CUSTOMER: Your online banking access has been suspended due to unrecognized login attempts. Please confirm your identity immediately to prevent card locking: http://secure-chase-update.net/login" },
    { label: "Phishing (Tamil)", text: "அவசரம்! உங்கள் வங்கி கணக்கு தற்காலிகமாக முடக்கப்பட்டுள்ளது. உடனடியாக சரிபார்க்க கீழே உள்ள லிங்கை அழுத்தவும்: http://phish-bank.in" },
    { label: "Safe (English)", text: "Hi team, please find attached the slides for tomorrow's security alignment meeting. Review and suggest any updates by 5 PM. Thanks!" }
  ],
  CALL: [
    { label: "IRS Scam (English)", text: "This is officer Davis from the Tax Investigation Department. You have unpaid taxes and a warrant has been issued for your arrest. To avoid immediate police action, purchase $500 Apple gift cards and read the codes over the phone." },
    { label: "Fraud (Tamil)", text: "வணக்கம், நாங்கள் காவல் துறையிலிருந்து பேசுகிறோம். உங்கள் மீது வழக்கு பதிவு செய்யப்பட்டுள்ளது. கைது நடவடிக்கையை தவிர்க்க உடனடியாக ரூ.10,000 அபராதத்தை இந்த எண்ணிற்கு அனுப்பவும்." },
    { label: "Safe (English)", text: "Hello Vijay, this is Dr. Arul's clinic calling to confirm your annual health checkup appointment tomorrow at 10:30 AM. Please arrive 10 minutes early." }
  ],
  URL: [
    { label: "Phishing Link", text: "http://secure-login-chasebank-alert.com/signin" },
    { label: "Fake Lottery", text: "http://win-free-jackpot-claims-today.net" },
    { label: "Safe Documentation", text: "https://react.dev/reference/react" }
  ],
  SCAM: [
    { label: "Bitcoin Elite", text: "Make $5,000 every single day guaranteed with our AI automated crypto trader! Just deposit $100 today and watch your bank account grow. 100% risk free." },
    { label: "Job Offer", text: "Urgent hiring! Earn Rs.3000 to Rs.8000 daily working part-time from home. No experience needed. WhatsApp us immediately to start." }
  ]
};

const BACKEND_URL = "http://localhost:8000";

function App() {
  // Navigation & Form State
  const [activeTab, setActiveTab] = useState("scanner");
  const [selectedChannel, setSelectedChannel] = useState("SMS");
  const [scanInput, setScanInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  
  // Storage State
  const [historyLogs, setHistoryLogs] = useState([]);
  const [metricsData, setMetricsData] = useState(null);
  const [settingsData, setSettingsData] = useState(null);
  
  // Form Configurations
  const [cloudDbUri, setCloudDbUri] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [historyFilter, setHistoryFilter] = useState("ALL");
  const [toastMessage, setToastMessage] = useState("");

  // Continuous Learning Feedback State
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackCorrect, setFeedbackCorrect] = useState(null);
  const [selectedCorrectLabel, setSelectedCorrectLabel] = useState("");
  const [isFeedbackLoading, setIsFeedbackLoading] = useState(false);


  // Load metrics, history, and settings on mount
  useEffect(() => {
    fetchHistory();
    fetchMetrics();
    fetchSettings();
  }, []);

  // Fetch History Logs
  const fetchHistory = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/history?limit=50`);
      if (response.ok) {
        const data = await response.json();
        setHistoryLogs(data);
      }
    } catch (error) {
      console.error("Error fetching scan history:", error);
    }
  };

  // Fetch Metrics
  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/metrics`);
      if (response.ok) {
        const data = await response.json();
        setMetricsData(data);
      }
    } catch (error) {
      console.error("Error fetching system metrics:", error);
    }
  };

  // Fetch Settings
  const fetchSettings = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/settings`);
      if (response.ok) {
        const data = await response.json();
        setSettingsData(data);
      }
    } catch (error) {
      console.error("Error fetching database settings:", error);
    }
  };

  // Run Content Inference Scan
  const handleScan = async (e) => {
    if (e) e.preventDefault();
    if (!scanInput.trim()) return;

    setIsLoading(true);
    setScanResult(null);
    
    // Reset feedback state on new scan
    setFeedbackSubmitted(false);
    setFeedbackCorrect(null);
    setSelectedCorrectLabel("");
    setIsFeedbackLoading(false);


    // Payload matches backend expectations
    const payload = {
      channel: selectedChannel,
      content: scanInput
    };

    try {
      const response = await fetch(`${BACKEND_URL}/api/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        setScanResult(data);
        
        // Instant sync database entries and metrics counts
        fetchHistory();
        fetchMetrics();
      } else {
        const errorData = await response.json();
        showToast(`Scan Error: ${errorData.detail || "Server failed to process scan"}`);
      }
    } catch (error) {
      showToast("Cannot connect to backend server. Make sure FastAPI is running.");
      console.error("Scan API connection failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Save Settings
  const handleSaveSettings = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${BACKEND_URL}/api/settings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ cloud_db_uri: cloudDbUri })
      });

      if (response.ok) {
        showToast("Database settings updated successfully!");
        fetchSettings();
        fetchHistory();
        fetchMetrics();
      } else {
        showToast("Failed to update database settings.");
      }
    } catch (error) {
      showToast("Connection to settings API failed.");
    }
  };

  // Handle Feedback Submission
  const handleFeedback = async (isCorrect, correctedLabel = null) => {

    if (!scanResult || !scanResult.id) return;
    
    setIsFeedbackLoading(true);
    
    const label = isCorrect ? scanResult.prediction : correctedLabel;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          scan_id: scanResult.id,
          corrected_prediction: label
        })
      });
      
      if (response.ok) {
        setFeedbackSubmitted(true);
        setFeedbackCorrect(isCorrect);
        showToast(isCorrect ? "Thank you for confirming! Model reinforced." : "Correction submitted! Retraining model in real time...");
        
        // Update local results with calibrated output
        setScanResult(prev => ({
          ...prev,
          prediction: label,
          risk_score: label === "Safe" ? 5.0 : (label === "Promotional" ? 25.0 : 95.0)
        }));
        
        // Dynamic re-fetch of metrics and logs to update UI immediately
        setTimeout(() => {
          fetchHistory();
          fetchMetrics();
        }, 1000);
      } else {
        const errorData = await response.json();
        showToast(`Feedback Error: ${errorData.detail || "Submission failed"}`);
      }
    } catch (error) {
      showToast("Cannot connect to backend server for feedback.");
      console.error("Feedback failed:", error);
    } finally {
      setIsFeedbackLoading(false);
    }
  };

  // Helper: Truncate Text

  const truncateText = (text, maxLength = 80) => {
    if (!text) return "";
    return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
  };

  // Helper: Trigger custom popups
  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => {
      setToastMessage("");
    }, 4000);
  };

  // Dynamic Keyword Highlighter (Secure React DOM Rendering)
  const renderHighlightedText = (text, keywords) => {
    if (!text) return null;
    if (!keywords || keywords.length === 0) {
      return <span>{text}</span>;
    }
    
    // Clean and sort valid keywords (longest first to prevent sub-string overlap issues)
    const validKeywords = keywords
      .filter(kw => kw && kw.trim())
      .sort((a, b) => b.length - a.length);
      
    if (validKeywords.length === 0) {
      return <span>{text}</span>;
    }
    
    // Escape special regex characters in the keywords and build pattern
    const escapedKws = validKeywords.map(kw => kw.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'));
    const regex = new RegExp(`(${escapedKws.join('|')})`, 'gi');
    
    // Split the text. Capture groups keep matched keywords in the array
    const parts = text.split(regex);
    
    return (
      <div>
        {parts.map((part, index) => {
          // Check if segment matches a keyword (case-insensitive)
          const isKeyword = validKeywords.some(
            kw => kw.toLowerCase() === part.toLowerCase()
          );
          
          if (isKeyword) {
            return (
              <span key={index} className="highlight-word">
                {part}
              </span>
            );
          }
          return <span key={index}>{part}</span>;
        })}
      </div>
    );
  };


  // Dynamic Colors depending on threat assessment
  const getThreatClass = (pred) => {
    if (!pred) return "safe";
    const p = pred.toUpperCase();
    if (p === "SAFE") return "safe";
    if (p === "PROMOTIONAL") return "promo";
    if (p === "SPAM" || p === "SCAM" || p === "FRAUD" || p === "PHISHING") return "threat";
    return "warning";
  };

  const getThreatGaugeColor = (pred) => {
    const cls = getThreatClass(pred);
    if (cls === "safe") return "var(--color-safe)";
    if (cls === "promo") return "var(--color-promo)";
    if (cls === "threat") return "var(--color-danger)";
    return "var(--color-warning)";
  };

  return (
    <div className="app-container">
      
      {/* Toast Alert */}
      {toastMessage && (
        <div className="toast">
          🛡️ {toastMessage}
        </div>
      )}

      {/* Header Panel */}
      <header className="app-header">
        <div className="brand-section">
          <span className="brand-logo" role="img" aria-label="Shield">🛡️</span>
          <div>
            <h1 className="brand-title">ScamGuard Shield</h1>
            <div className="system-status">
              <span className="status-indicator pulse"></span>
              <span>Active: {settingsData?.db_mode || "SQLite Local DB"}</span>
            </div>
          </div>
        </div>

        {/* Tab Switcher */}
        <nav className="nav-tabs">
          <button 
            className={`tab-btn ${activeTab === 'scanner' ? 'active' : ''}`}
            onClick={() => setActiveTab('scanner')}
          >
            🔍 Universal Scanner
          </button>
          <button 
            className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('history');
              fetchHistory();
            }}
          >
            📋 Logs History
          </button>
          <button 
            className={`tab-btn ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('metrics');
              fetchMetrics();
            }}
          >
            📊 Analytics Console
          </button>
          <button 
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            ⚙️ DB Settings
          </button>
        </nav>
      </header>

      {/* Main Body */}
      <main className="dashboard-content">
        
        {/* Tab 1: Scanner Playgound */}
        {activeTab === "scanner" && (
          <div className="glass-panel">
            {/* Channel Cards Selector */}
            <div className="channel-grid">
              {[
                { id: "SMS", name: "SMS Messages", desc: "Short messaging scanner", icon: "💬" },
                { id: "EMAIL", name: "Email Client", desc: "Phishing body checker", icon: "📧" },
                { id: "CALL", name: "Voice Transcripts", desc: "Arrest/bank call scanner", icon: "📞" },
                { id: "URL", name: "Phishing Links", desc: "Lexical feature scanner", icon: "🔗" },
                { id: "SCAM", name: "Scam Alerts", desc: "Giveaways & Crypto scam", icon: "⚠️" }
              ].map((chan) => (
                <div 
                  key={chan.id}
                  className={`channel-card ${selectedChannel === chan.id ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedChannel(chan.id);
                    setScanInput("");
                    setScanResult(null);
                  }}
                >
                  <div className="channel-icon">{chan.icon}</div>
                  <div className="channel-name">{chan.name}</div>
                  <div className="channel-desc">{chan.desc}</div>
                </div>
              ))}
            </div>

            {/* Input and Result Panels */}
            <div className="scanner-workspace">
              {/* Form Input Block */}
              <div className="scan-form">
                <div className="input-label">
                  <span>ENTER {selectedChannel} CONTENT FOR SECURITY INSPECTION:</span>
                  <span className="lang-badge">Tamil & English Supported</span>
                </div>
                
                <div className="text-area-wrapper">
                  <textarea
                    className="scanner-textarea"
                    placeholder={
                      selectedChannel === "URL" 
                        ? "Enter URL to scan (e.g., http://suspicious-lottery-claims.com)" 
                        : `Paste ${selectedChannel.toLowerCase()} message text here to test safety...`
                    }
                    value={scanInput}
                    onChange={(e) => setScanInput(e.target.value)}
                  />
                  <div className="char-counter">{scanInput.length} chars</div>
                </div>

                <button 
                  className="scan-btn" 
                  disabled={isLoading || !scanInput.trim()}
                  onClick={handleScan}
                >
                  {isLoading ? (
                    <>⌛ Running Real-time AI Inference...</>
                  ) : (
                    <>⚡ Run Safety Scan</>
                  )}
                </button>

                {/* Click-to-load Presets */}
                <div className="templates-section">
                  <div className="templates-header">💡 QUICK PRESETS (CLICK TO TEST):</div>
                  <div className="templates-list">
                    {(TEMPLATE_PRESETS[selectedChannel] || []).map((preset, idx) => (
                      <span
                        key={idx}
                        className="template-chip"
                        onClick={() => setScanInput(preset.text)}
                        title={preset.text}
                      >
                        {preset.label}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Dynamic Threat Result Board */}
              <div className="results-card">
                {!scanResult && (
                  <div className="empty-results">
                    <span className="empty-icon">🛡️</span>
                    <h3>Awaiting Threat Scan</h3>
                    <p>Select a digital channel, enter the text content or paste a URL link, and trigger the security scanner to view high-fidelity AI metrics.</p>
                  </div>
                )}

                {scanResult && (
                  <>
                    <div className="result-main">
                      {/* Interactive Risk SVG Circular Meter */}
                      <div className="gauge-wrapper">
                        <svg className="gauge-svg">
                          <circle className="gauge-bg" cx="70" cy="70" r="60" />
                          <circle 
                            className="gauge-fill" 
                            cx="70" 
                            cy="70" 
                            r="60" 
                            stroke={getThreatGaugeColor(scanResult.prediction)}
                            strokeDasharray="376.99"
                            strokeDashoffset={376.99 - (376.99 * scanResult.risk_score) / 100}
                          />
                        </svg>
                        <div className="gauge-val">
                          <span className="gauge-percentage">{Math.round(scanResult.risk_score)}%</span>
                          <span className="gauge-lbl">Risk Score</span>
                        </div>
                      </div>

                      {/* Threat Level Badge */}
                      <div className={`diagnosis-banner ${getThreatClass(scanResult.prediction)}`}>
                        Threat Diagnosis: {scanResult.prediction}
                      </div>
                    </div>

                    {/* Class Probability Distribution */}
                    {scanResult.category_distribution && Object.keys(scanResult.category_distribution).length > 0 && (
                      <div className="dist-container">
                        <div className="highlight-title">🔍 CLASS PROBABILITY RATIO:</div>
                        {Object.entries(scanResult.category_distribution).map(([cat, val]) => (
                          <div className="dist-row" key={cat}>
                            <div className="dist-header">
                              <span>{cat}</span>
                              <span>{Math.round(val * 100)}%</span>
                            </div>
                            <div className="dist-bar-track">
                              <div 
                                className="dist-bar-fill" 
                                style={{ 
                                  width: `${val * 100}%`,
                                  backgroundColor: getThreatGaugeColor(cat) 
                                }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Word Highlights Block */}
                    {selectedChannel !== "URL" && (
                      <div className="highlight-panel">
                        <div className="highlight-title">
                          ⚠️ DETECTED RISKY KEYWORDS:
                        </div>
                        <div className="highlight-box">
                          {scanResult.suspicious_keywords && scanResult.suspicious_keywords.length > 0 ? (
                            renderHighlightedText(scanResult.input_content, scanResult.suspicious_keywords)
                          ) : (
                            <span className="safe-message">✅ Zero suspicious keywords flagged. Text linguistic properties match standard safe profile.</span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Active Feedback Loop for Continuous Learning */}
                    {isFeedbackLoading ? (
                      <div className="feedback-loading-card">
                        <div className="feedback-spinner"></div>
                        <span>🧠 ScamGuard Shield is retraining and hot-swapping the NLP classifier...</span>
                      </div>
                    ) : feedbackSubmitted ? (
                      <div className="feedback-success-card">
                        <span className="success-icon">✅</span>
                        <span>{feedbackCorrect ? "Reinforcement Locked: Model validated & strengthened." : `Retraining Complete: Model updated with '${selectedCorrectLabel}' classification label.`}</span>
                      </div>
                    ) : (
                      <div className="feedback-panel-interactive">
                        <div className="feedback-title">🤖 ACTIVE FEEDBACK LOOP & CONTINUOUS LEARNING:</div>
                        <div className="feedback-question">Is this threat diagnosis accurate?</div>
                        
                        {feedbackCorrect === null && (
                          <div className="feedback-buttons-row">
                            <button 
                              className="feedback-btn feedback-btn-yes" 
                              onClick={() => handleFeedback(true)}
                            >
                              👍 Yes, Correct
                            </button>
                            <button 
                              className="feedback-btn feedback-btn-no" 
                              onClick={() => setFeedbackCorrect(false)}
                            >
                              👎 No, Incorrect
                            </button>
                          </div>
                        )}
                        
                        {feedbackCorrect === false && (
                          <div className="feedback-correction-panel">
                            <div className="feedback-label-instruction">Select the correct classification category:</div>
                            <div className="feedback-label-grid">
                              {["Safe", "Spam", "Scam", "Fraud", "Phishing", "Promotional"]
                                .filter(label => {
                                  if (selectedChannel === "SMS") return ["Safe", "Spam", "Promotional"].includes(label);
                                  if (selectedChannel === "EMAIL") return ["Safe", "Spam", "Phishing", "Promotional"].includes(label);
                                  if (selectedChannel === "CALL") return ["Safe", "Fraud", "Scam"].includes(label);
                                  if (selectedChannel === "URL") return ["Safe", "Phishing"].includes(label);
                                  if (selectedChannel === "SCAM") return ["Safe", "Scam"].includes(label);
                                  return true;
                                })
                                .map((label) => (
                                  <span
                                    key={label}
                                    className={`feedback-label-chip ${selectedCorrectLabel === label ? 'active' : ''}`}
                                    onClick={() => setSelectedCorrectLabel(label)}
                                  >
                                    {label}
                                  </span>
                                ))}
                            </div>
                            <button
                              className="feedback-submit-btn"
                              disabled={!selectedCorrectLabel}
                              onClick={() => handleFeedback(false, selectedCorrectLabel)}
                            >
                              ⚡ Submit Correction & Train AI
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </>

                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Logs History */}
        {activeTab === "history" && (
          <div className="glass-panel">
            <div className="history-controls">
              <h2>🛡️ Real-Time Scan History Logs</h2>
              <div style={{ display: 'flex', gap: '12px' }}>
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search logs by keyword..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <select
                  className="filter-select"
                  value={historyFilter}
                  onChange={(e) => setHistoryFilter(e.target.value)}
                >
                  <option value="ALL">All Channels</option>
                  <option value="SMS">SMS</option>
                  <option value="EMAIL">Email</option>
                  <option value="CALL">Call</option>
                  <option value="URL">URL</option>
                  <option value="SCAM">Scam</option>
                </select>
              </div>
            </div>

            {/* Logs Table */}
            <div className="logs-table-wrapper">
              {historyLogs.length === 0 ? (
                <div className="empty-history">
                  <h3>No Scans Logged</h3>
                  <p>All scanned SMS, emails, voice call transcripts and URLs are automatically saved here for quick audit references.</p>
                </div>
              ) : (
                <table className="logs-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Channel</th>
                      <th>Content Scan (Hover for full text)</th>
                      <th>Prediction</th>
                      <th>Risk Score</th>
                      <th>Timestamp</th>
                      <th>Mode</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyLogs
                      .filter(log => {
                        const matchesChan = historyFilter === "ALL" || log.channel.toUpperCase() === historyFilter.toUpperCase();
                        const matchesQuery = !searchQuery || log.input_content.toLowerCase().includes(searchQuery.toLowerCase());
                        return matchesChan && matchesQuery;
                      })
                      .map((log) => (
                        <tr key={log.id}>
                          <td>#{log.id}</td>
                          <td>
                            <span className="badge badge-channel">
                              {log.channel.toUpperCase()}
                            </span>
                          </td>
                          <td title={log.input_content}>
                            <div className="content-preview">
                              {log.channel.toUpperCase() === "URL" ? (
                                <a href={log.input_content} target="_blank" rel="noreferrer">{log.input_content}</a>
                              ) : (
                                log.input_content
                              )}
                            </div>
                          </td>
                          <td>
                            <span className={`badge ${getThreatClass(log.prediction)}`}>
                              {log.prediction}
                            </span>
                          </td>
                          <td style={{ fontWeight: 'bold' }}>
                            {log.risk_score}%
                          </td>
                          <td className="time-stamp">
                            {new Date(log.timestamp).toLocaleString()}
                          </td>
                          <td>
                            <span style={{ fontSize: '11px', opacity: 0.6 }}>{log.db_mode}</span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Metrics Dashboard */}
        {activeTab === "metrics" && (
          <div className="glass-panel animate-fade">
            <h2 style={{ marginBottom: '24px' }}>📊 Real-time Security System Analytics</h2>
            
            {/* Metric Overview Widgets */}
            <div className="analytics-grid">
              <div className="metric-card total">
                <span className="metric-header">Total Scan Operations</span>
                <span className="metric-value">{metricsData?.total_scans || 0}</span>
                <span className="metric-sub">Across all communication endpoints</span>
              </div>
              <div className="metric-card threats">
                <span className="metric-header">Threat Scans Flagged</span>
                <span className="metric-value">{metricsData?.threat_count || 0}</span>
                <span className="metric-sub">Blocked malicious activities</span>
              </div>
              <div className="metric-card safe">
                <span className="metric-header">Safe Logs Validated</span>
                <span className="metric-value">{metricsData?.safe_count || 0}</span>
                <span className="metric-sub">Legitimate safe communications</span>
              </div>
              <div className="metric-card rate">
                <span className="metric-header">Overall Threat Ratio</span>
                <span className="metric-value">{metricsData?.threat_percentage || 0}%</span>
                <span className="metric-sub">System-wide threat density</span>
              </div>
            </div>

            {/* Category Breakdown Charts */}
            <div className="charts-wrapper">
              {/* Category Count Bar Chart */}
              <div className="chart-box">
                <h3 className="chart-title">Breakdown by Classification Category</h3>
                <div className="chart-visual-bars">
                  {metricsData?.category_counts && Object.keys(metricsData.category_counts).length > 0 ? (
                    Object.entries(metricsData.category_counts).map(([cat, count]) => {
                      const total = metricsData.total_scans || 1;
                      const percentage = (count / total) * 100;
                      return (
                        <div className="chart-bar-row" key={cat}>
                          <div className="chart-bar-lbl">{cat}</div>
                          <div className="chart-bar-track">
                            <div 
                              className={`chart-bar-fill ${getThreatClass(cat)}`}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <div className="chart-bar-val">{count}</div>
                        </div>
                      );
                    })
                  ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: '14px', textAlign: 'center', padding: '40px 0' }}>
                      Awaiting threat analytics data. Start scanning to plot metrics.
                    </div>
                  )}
                </div>
              </div>

              {/* Threat Ratio Gauge Box */}
              <div className="chart-box" style={{ justifyContent: 'center' }}>
                <h3 className="chart-title" style={{ textAlign: 'center' }}>Overall Threat Concentration</h3>
                <div className="ratio-widget">
                  <div className="gauge-wrapper" style={{ width: '160px', height: '160px' }}>
                    <svg className="gauge-svg">
                      <circle className="gauge-bg" cx="80" cy="80" r="70" strokeWidth="12" />
                      <circle 
                        className="gauge-fill" 
                        cx="80" 
                        cy="80" 
                        r="70" 
                        strokeWidth="12"
                        stroke="var(--color-danger)"
                        strokeDasharray="439.82"
                        strokeDashoffset={439.82 - (439.82 * (metricsData?.threat_percentage || 0)) / 100}
                      />
                    </svg>
                    <div className="gauge-val">
                      <span className="gauge-percentage" style={{ fontSize: '34px' }}>{metricsData?.threat_percentage || 0}%</span>
                      <span className="gauge-lbl" style={{ fontSize: '9px' }}>Threat Rate</span>
                    </div>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', textAlign: 'center', maxWidth: '300px', margin: '0 auto' }}>
                    Security logs indicate {metricsData?.threat_percentage || 0}% of scanned requests exhibit malicious scam or phishing characteristics.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Database Settings */}
        {activeTab === "settings" && (
          <div className="glass-panel">
            <h2 style={{ marginBottom: '24px' }}>⚙️ Database Router Control</h2>
            
            <form onSubmit={handleSaveSettings} className="settings-form">
              <div className="setting-row">
                <label>Database Storage Sync Status:</label>
                <div className="system-status" style={{ width: 'fit-content', background: 'rgba(255,255,255,0.02)', padding: '12px 20px', fontSize: '14px' }}>
                  <span className="status-indicator pulse"></span>
                  <span style={{ fontWeight: 'bold' }}>Routing Endpoint Mode: {settingsData?.db_mode || "SQLite Local DB"}</span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Currently, all scanning entries and logs are written securely to the server's local file storage. Configure a cloud URI failover below to run dynamic cloud syncs.
                </p>
              </div>

              <div className="setting-row">
                <label htmlFor="cloud-db-uri">Failover Cloud Connection String (PostgreSQL / MongoDB):</label>
                <div className="setting-input-group">
                  <input
                    type="password"
                    id="cloud-db-uri"
                    className="settings-input"
                    placeholder="postgresql://username:password@cloudhost:5432/dbname"
                    value={cloudDbUri}
                    onChange={(e) => setCloudDbUri(e.target.value)}
                  />
                  <button type="submit" className="settings-save-btn">
                    💾 Save & Sync Route
                  </button>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--accent-light)', marginTop: '2px' }}>
                  {settingsData?.cloud_db_uri_configured ? "✅ A cloud failover URI is currently configured and encrypted in the background server." : "⚠️ No cloud database is configured. Standard SQLite Local storage is active."}
                </span>
              </div>
            </form>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>ScamGuard Shield v1.0.0 — Live Security Console • Tamil and English NLP Classifiers Active</p>
      </footer>
    </div>
  );
}

export default App;
