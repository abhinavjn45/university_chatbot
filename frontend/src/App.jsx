import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, User, Database, Sparkles, Clock, CheckCircle2, 
  Activity, FileText, ChevronDown, ChevronUp, RefreshCw, 
  Lock, AlertTriangle, ShieldCheck, HelpCircle, GraduationCap,
  BookOpen, Calendar, DollarSign
} from 'lucide-react';

const QueryResultTable = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) return null;

  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState(null);
  const rowsPerPage = 5;

  const columns = Object.keys(data[0]);

  // Handle sorting
  const sortedData = React.useMemo(() => {
    let sortableItems = [...data];
    if (sortConfig !== null) {
      sortableItems.sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;
        if (aVal < bVal) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (aVal > bVal) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [data, sortConfig]);

  const requestSort = (key) => {
    let direction = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  // Handle pagination
  const indexOfLastRow = currentPage * rowsPerPage;
  const indexOfFirstRow = indexOfLastRow - rowsPerPage;
  const currentRows = sortedData.slice(indexOfFirstRow, indexOfLastRow);
  const totalPages = Math.ceil(data.length / rowsPerPage);

  // Export CSV function
  const downloadCSV = () => {
    const csvRows = [];
    csvRows.push(columns.join(',')); // Add headers

    for (const row of data) {
      const values = columns.map(col => {
        const val = row[col];
        const stringVal = val === null || val === undefined ? '' : String(val);
        // Escape quotes
        return `"${stringVal.replace(/"/g, '""')}"`;
      });
      csvRows.push(values.join(','));
    }

    const csvContent = "data:text/csv;charset=utf-8," + csvRows.join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `query_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="mt-3 border border-dark-800 rounded-xl bg-[#0b0c16]/80 overflow-hidden w-full max-w-full">
      {/* Table Title / Export Actions */}
      <div className="flex items-center justify-between px-3 py-2 bg-dark-900/40 border-b border-dark-800">
        <span className="text-[10px] font-bold text-dark-400 uppercase tracking-wider">
          Query Results ({data.length} records)
        </span>
        <button 
          onClick={downloadCSV}
          className="flex items-center gap-1 text-[10px] text-brand-300 hover:text-white bg-brand-950/40 hover:bg-brand-900/50 border border-brand-900/30 px-2 py-1 rounded transition-colors"
        >
          <FileText size={10} /> Export CSV
        </button>
      </div>

      {/* Main Table Container */}
      <div className="overflow-x-auto max-w-full">
        <table className="w-full text-left text-xs border-collapse font-sans">
          <thead>
            <tr className="border-b border-dark-800 text-dark-400 font-bold bg-[#0d0e1b]/60">
              {columns.map((col) => (
                <th 
                  key={col} 
                  onClick={() => requestSort(col)}
                  className="p-2.5 whitespace-nowrap cursor-pointer hover:text-white select-none transition-colors animate-fade-in"
                >
                  <div className="flex items-center gap-1">
                    {col}
                    {sortConfig?.key === col ? (
                      sortConfig.direction === 'ascending' ? ' ▲' : ' ▼'
                    ) : (
                      <span className="text-dark-600 text-[8px]"> ▼</span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-900 font-mono text-[11px] text-[#c2d4ff]">
            {currentRows.map((row, idx) => (
              <tr key={idx} className="hover:bg-dark-900/20 transition-colors">
                {columns.map((col) => (
                  <td key={col} className="p-2.5 max-w-[200px] truncate" title={String(row[col] ?? '')}>
                    {row[col] === null || row[col] === undefined ? '-' : String(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-3 py-2 border-t border-dark-800 bg-[#0d0e1b]/40 text-[10px]">
          <span className="text-dark-500 font-sans">
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="px-2 py-1 border border-dark-800 rounded bg-dark-950/50 text-dark-400 hover:text-white hover:border-dark-700 disabled:opacity-40 disabled:hover:text-dark-400 disabled:hover:border-dark-800 transition-colors"
            >
              Prev
            </button>
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="px-2 py-1 border border-dark-800 rounded bg-dark-950/50 text-dark-400 hover:text-white hover:border-dark-700 disabled:opacity-40 disabled:hover:text-dark-400 disabled:hover:border-dark-800 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const BACKEND_URL = 'http://127.0.0.1:8000';

function App() {
  // Authentication & Role State
  const [role, setRole] = useState('Super Admin');
  const [email, setEmail] = useState('');
  const [currentUser, setCurrentUser] = useState({ name: 'Demo Super Admin', role: 'Super Admin' });
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Chat & History State
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [sessionId, setSessionId] = useState(`session_${Math.random().toString(36).substring(7)}`);
  const [isLoading, setIsLoading] = useState(false);
  const [showConfigHelp, setShowConfigHelp] = useState(false);

  // Metrics Dashboard State
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'metrics'
  const [metrics, setMetrics] = useState({
    total_queries: 0,
    cache_hits: 0,
    failures: 0,
    accuracy_rate_percent: 0,
    cache_hit_rate_percent: 0,
    average_execution_speed_ms: 0,
    recent_queries: []
  });
  const [isRefreshingMetrics, setIsRefreshingMetrics] = useState(false);

  // Suggested Queries by Role
  const suggestedQueries = {
    'Student': [
      { text: "What is my CGPA?", query: "What is my CGPA?" },
      { text: "Show my attendance details", query: "Show my attendance details" },
      { text: "View my scholarships", query: "Show my scholarships details" },
      { text: "Show faculty salaries (Security Test)", query: "Show the salaries of all faculty members" }
    ],
    'Faculty': [
      { text: "Show Data Structures results", query: "Who are the toppers in Data Structures?" },
      { text: "Detained Students in Python?", query: "Which students are detained in Python Programming due to attendance?" },
      { text: "Show my course workloads", query: "What subjects are assigned to me and what is my workload?" },
      { text: "Show Student Fee Balances (Security Test)", query: "List all fee defaulters and pending balances" }
    ],
    'Department Admin': [
      { text: "Show fee defaulters", query: "Show fee defaulters from MCA course" },
      { text: "Who are the toppers in MCA?", query: "Who are the toppers in MCA?" },
      { text: "Operating Systems attendance", query: "What is the class attendance in Operating Systems?" },
      { text: "List recent notifications", query: "Show recent notifications for students" }
    ],
    'Super Admin': [
      { text: "Show all audit logs", query: "Show all audit logs" },
      { text: "Academic Fee Revenue", query: "Show total expected fee vs total paid fee across all courses" },
      { text: "Top students and attendance", query: "Show top 3 students by CGPA along with their attendance percentage" },
      { text: "Delete students table (Injection Test)", query: "DROP TABLE students" }
    ]
  };

  // Pre-configured email lists for ease of demo
  const demoEmails = {
    'Student': [
      { email: 'rahul.sharma1@student.edu', desc: 'Rahul Sharma (MCA, Top CGPA: 9.2)' },
      { email: 'amit.sen3@student.edu', desc: 'Amit Sen (MCA, Detained: <65% attendance)' },
      { email: 'sneha.reddy4@student.edu', desc: 'Sneha Reddy (B.Tech CSE, Top CGPA: 9.5)' },
      { email: 'rohan.malhotra5@student.edu', desc: 'Rohan Malhotra (B.Tech CSE, Fee Defaulter)' },
      { email: 'manish.gupta8@student.edu', desc: 'Manish Gupta (MBA, Detained & Defaulter)' }
    ],
    'Faculty': [
      { email: 'rajesh.kumar@university.edu', desc: 'Prof. Rajesh Kumar (MCA, Teaches DS/DBMS)' },
      { email: 'sunita.sharma@university.edu', desc: 'Prof. Sunita Sharma (MCA, Teaches Python)' },
      { email: 'amit.verma@university.edu', desc: 'Prof. Amit Verma (CSE, Teaches DAA)' }
    ]
  };

  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch metrics when entering the metrics tab
  useEffect(() => {
    if (activeTab === 'metrics') {
      fetchMetrics();
    }
  }, [activeTab]);

  // Initialize demo login settings
  useEffect(() => {
    if (role === 'Student') {
      setEmail(demoEmails['Student'][0].email);
    } else if (role === 'Faculty') {
      setEmail(demoEmails['Faculty'][0].email);
    } else {
      setEmail('');
    }
  }, [role]);

  // Mock login function connecting to API
  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setIsLoggingIn(true);
    setLoginError('');

    try {
      const response = await fetch(`${BACKEND_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: role,
          email: role === 'Student' || role === 'Faculty' ? email : `demo@${role.toLowerCase().replace(' ', '')}.com`
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to authenticate user.');
      }

      setCurrentUser(data);
      // Reset chat session upon login/role change
      setSessionId(`session_${Math.random().toString(36).substring(7)}`);
      setMessages([{
        sender: 'assistant',
        text: `Hello ${data.name}! I am your Conversational ERP Analytics Assistant. How can I help you today as a **${data.role}**?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        metadata: null
      }]);
    } catch (err) {
      setLoginError(err.message);
    } finally {
      setIsLoggingIn(false);
    }
  };

  // Fetch metrics data
  const fetchMetrics = async () => {
    setIsRefreshingMetrics(true);
    try {
      const response = await fetch(`${BACKEND_URL}/metrics`);
      const data = await response.json();
      if (response.ok) {
        setMetrics(data);
      }
    } catch (err) {
      console.error("Failed to fetch metrics", err);
    } finally {
      setIsRefreshingMetrics(false);
    }
  };

  // Submit Query to chatbot
  const handleSendMessage = async (queryText = null) => {
    const query = queryText || inputText;
    if (!query.trim() || isLoading) return;

    // Add user message to UI
    const userMsg = {
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);
    if (!queryText) setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          role: currentUser.role,
          student_id: currentUser.student_id || null,
          faculty_id: currentUser.faculty_id || null,
          user_email: currentUser.email || null,
          session_id: sessionId
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Internal server error processing query.');
      }

      const assistantMsg = {
        sender: 'assistant',
        text: data.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        metadata: {
          generated_sql: data.generated_sql,
          execution_time_ms: data.execution_time_ms,
          rows_returned: data.rows_returned,
          cache_hit: data.cache_hit,
          domain: data.domain,
          sql_valid: data.sql_valid,
          sql_error: data.sql_error,
          query_result: data.query_result
        }
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: `⚠️ Error: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        metadata: {
          sql_valid: false,
          sql_error: err.message,
          domain: 'unknown'
        }
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Message metadata subcomponent
  const MetadataPanel = ({ meta }) => {
    const [expanded, setExpanded] = useState(false);
    if (!meta) return null;

    const isSecurityBlocked = !meta.sql_valid || (meta.sql_error && meta.sql_error.includes('Security Validation Failed'));
    const isExecutionError = meta.sql_valid && meta.sql_error;

    return (
      <div className="mt-2 text-xs border border-dark-800 rounded bg-[#0e0f1b] overflow-hidden transition-all duration-300">
        <button 
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-between w-full px-3 py-1.5 text-dark-400 hover:bg-dark-900 transition-colors"
        >
          <span className="flex items-center gap-1.5 font-medium">
            <Database size={12} className="text-brand-400" />
            Execution Metadata
            {meta.cache_hit && (
              <span className="bg-emerald-950/80 text-emerald-400 border border-emerald-900/50 px-1.5 py-0.2 rounded text-[10px] font-bold tracking-wide">
                CACHE HIT
              </span>
            )}
            {isSecurityBlocked && (
              <span className="bg-red-950/80 text-red-400 border border-red-900/50 px-1.5 py-0.2 rounded text-[10px] font-bold tracking-wide">
                SECURITY BLOCKED
              </span>
            )}
          </span>
          <span className="flex items-center gap-2">
            <span className="text-[10px] text-dark-500 font-mono">
              Domain: <span className="text-brand-300">{meta.domain}</span> | Speed: {meta.execution_time_ms}ms
            </span>
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </span>
        </button>

        {expanded && (
          <div className="p-3 border-t border-dark-800 bg-[#07080f] font-mono text-[11px] space-y-2.5">
            {meta.generated_sql && (
              <div>
                <div className="text-dark-500 font-bold mb-1 text-[10px] uppercase tracking-wider">Generated SQL Query:</div>
                <pre className="p-2 border border-dark-800/80 rounded bg-[#0b0c16] text-[#c2d4ff] overflow-x-auto whitespace-pre-wrap select-all">
                  {meta.generated_sql}
                </pre>
              </div>
            )}

            {isSecurityBlocked && (
              <div className="p-2.5 border border-red-900/40 rounded bg-red-950/15 flex items-start gap-2">
                <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={14} />
                <div>
                  <div className="font-bold text-red-400 text-[10px] uppercase tracking-wider">Access Security Exception:</div>
                  <div className="text-red-300 mt-0.5">{meta.sql_error}</div>
                </div>
              </div>
            )}

            {isExecutionError && (
              <div className="p-2.5 border border-amber-900/40 rounded bg-amber-950/15 flex items-start gap-2">
                <AlertTriangle className="text-amber-500 shrink-0 mt-0.5" size={14} />
                <div>
                  <div className="font-bold text-amber-400 text-[10px] uppercase tracking-wider">Database Execution Error:</div>
                  <div className="text-amber-300 mt-0.5">{meta.sql_error}</div>
                </div>
              </div>
            )}

            {!meta.sql_error && meta.sql_valid && (
              <div className="grid grid-cols-2 gap-2 text-[10px] text-dark-400">
                <div className="p-2 border border-dark-900 rounded bg-dark-950/40">
                  <div className="font-semibold text-dark-500">ROWS RETURNED</div>
                  <div className="text-sm font-bold text-white mt-0.5">{meta.rows_returned}</div>
                </div>
                <div className="p-2 border border-dark-900 rounded bg-dark-950/40">
                  <div className="font-semibold text-dark-500">CACHE POLICY</div>
                  <div className="text-sm font-bold text-white mt-0.5">TTL: {meta.cache_hit ? 'Cached' : '1h Saved'}</div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col min-h-screen font-sans bg-[#0a0b12] text-white">
      {/* Top Header Bar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-dark-800 bg-[#121324]/80 backdrop-blur-md sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="grad-brand p-2.5 rounded-xl glow-brand">
            <Sparkles size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight m-0 bg-gradient-to-r from-white via-[#c2d4ff] to-brand-400 bg-clip-text text-transparent">
              University ERP Conversational Assistant
            </h1>
            <p className="text-xs text-dark-400 m-0">Secure Natural Language Analytics Interface</p>
          </div>
        </div>

        {/* Top Navbar Actions */}
        <div className="flex items-center gap-4">
          <div className="flex rounded-lg border border-dark-800 p-0.5 bg-dark-950/50">
            <button 
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-all ${activeTab === 'chat' ? 'grad-brand text-white' : 'text-dark-400 hover:text-white'}`}
            >
              Chat Room
            </button>
            <button 
              onClick={() => setActiveTab('metrics')}
              className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-all ${activeTab === 'metrics' ? 'grad-brand text-white' : 'text-dark-400 hover:text-white'}`}
            >
              Metrics Dashboard
            </button>
          </div>

          <button 
            onClick={() => setShowConfigHelp(!showConfigHelp)}
            className="flex items-center gap-1.5 text-xs text-brand-300 hover:text-white transition-colors bg-brand-950/40 border border-brand-900/50 px-3 py-1.5 rounded-lg"
          >
            <HelpCircle size={14} />
            Setup Tutorial
          </button>
        </div>
      </header>

      {/* API Configuration Guidance Panel */}
      {showConfigHelp && (
        <div className="mx-6 mt-4 p-4 border border-brand-900/40 rounded-xl bg-brand-950/20 text-xs animate-slide-up">
          <div className="flex items-center justify-between pb-2 border-b border-brand-950">
            <span className="font-bold text-brand-300 uppercase tracking-wide flex items-center gap-1.5">
              <Lock size={13} /> Setting Up Groq API Credentials
            </span>
            <button onClick={() => setShowConfigHelp(false)} className="text-dark-400 hover:text-white">✕</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
            <div>
              <p className="font-semibold text-[#e2e8f0]">1. Get API Key from Groq</p>
              <ol className="list-decimal pl-4 mt-1.5 space-y-1 text-dark-400">
                <li>Go to the <a href="https://console.groq.com/" target="_blank" rel="noopener noreferrer" className="underline text-brand-400 font-semibold hover:text-brand-300">Groq Developer Console</a></li>
                <li>Log in or create a free account</li>
                <li>Get your API key (Groq has a generous free tier for developers!)</li>
                <li>Go to <strong>API Keys</strong> and click <strong>Create API Key</strong></li>
              </ol>
            </div>
            <div>
              <p className="font-semibold text-[#e2e8f0]">2. Load key in the project config</p>
              <ol className="list-decimal pl-4 mt-1.5 space-y-1 text-dark-400">
                <li>Open the file <code className="text-[10px] text-white bg-dark-900 px-1 py-0.5 rounded">backend/.env</code> in your editor</li>
                <li>Replace <code className="text-brand-300">GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE</code> with your actual key</li>
                <li>Save the file and restart your FastAPI backend</li>
              </ol>
            </div>
          </div>
        </div>
      )}

      {/* Main Workspace split */}
      <div className="flex flex-1 overflow-hidden p-6 gap-6">
        
        {/* SIDEBAR: Controls & Role Selector */}
        <aside className="w-80 flex flex-col gap-6 shrink-0">
          
          {/* Active User Information Card */}
          <div className="glass-panel rounded-2xl p-5 flex flex-col gap-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-dark-400 flex items-center gap-2">
              <User size={13} className="text-brand-400" /> Current ERP Account
            </h2>
            
            <div className="flex items-center gap-3 bg-dark-950/40 p-3 rounded-xl border border-dark-900">
              <div className="h-10 w-10 rounded-lg grad-brand flex items-center justify-center font-bold text-white text-base">
                {currentUser.name.split(' ').map(n=>n[0]).join('')}
              </div>
              <div className="overflow-hidden">
                <div className="font-bold text-sm truncate text-white">{currentUser.name}</div>
                <div className="text-[10px] font-medium tracking-wide text-brand-400 flex items-center gap-1 mt-0.5">
                  <ShieldCheck size={11} /> {currentUser.role}
                </div>
              </div>
            </div>

            {currentUser.student_id && (
              <div className="text-[11px] grid grid-cols-2 gap-2 bg-[#0e101d] p-2.5 rounded-lg border border-dark-900/60 font-mono">
                <div>
                  <div className="text-dark-500 font-semibold">STUDENT ID</div>
                  <div className="text-[#c2d4ff] mt-0.5">{currentUser.student_id}</div>
                </div>
                <div>
                  <div className="text-dark-500 font-semibold">ENROLLMENT</div>
                  <div className="text-[#c2d4ff] mt-0.5">{currentUser.enrollment_no}</div>
                </div>
              </div>
            )}
          </div>

          {/* User Role Switching controls (Simulator) */}
          <div className="glass-panel rounded-2xl p-5 flex flex-col gap-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-dark-400 flex items-center gap-2">
              <Lock size={13} className="text-brand-400" /> ERP Access Simulator
            </h2>
            
            <form onSubmit={handleLogin} className="flex flex-col gap-3">
              <div>
                <label className="text-[10px] font-bold text-dark-400 uppercase tracking-wide">Select Demo Role</label>
                <select 
                  value={role} 
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg input-glass text-xs text-white focus:outline-none"
                >
                  <option value="Super Admin">Super Admin (All Tables)</option>
                  <option value="Department Admin">Department Admin (Academics/Fees)</option>
                  <option value="Faculty">Faculty (Class records only)</option>
                  <option value="Student">Student (Own records only)</option>
                </select>
              </div>

              {(role === 'Student' || role === 'Faculty') && (
                <div>
                  <label className="text-[10px] font-bold text-dark-400 uppercase tracking-wide">
                    Select Demo User Account
                  </label>
                  <select 
                    value={email} 
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg input-glass text-xs text-white focus:outline-none"
                  >
                    {demoEmails[role].map((item) => (
                      <option key={item.email} value={item.email}>{item.desc}</option>
                    ))}
                  </select>
                </div>
              )}

              {loginError && (
                <div className="text-[10px] text-red-400 bg-red-950/20 border border-red-900/30 p-2 rounded-lg mt-1">
                  {loginError}
                </div>
              )}

              <button 
                type="submit" 
                disabled={isLoggingIn}
                className="w-full mt-2 grad-brand hover:opacity-90 disabled:opacity-50 text-white font-semibold text-xs py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-all"
              >
                {isLoggingIn ? <RefreshCw size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                Apply Selected Role
              </button>
            </form>
          </div>

          {/* Quick Stats Summary */}
          <div className="glass-panel rounded-2xl p-5 flex flex-col gap-3.5 mt-auto">
            <h2 className="text-xs font-bold uppercase tracking-wider text-dark-400 flex items-center gap-2">
              <Activity size={13} className="text-brand-400" /> Active Security Policy
            </h2>
            <div className="space-y-2.5 text-[11px]">
              <div className="flex justify-between items-center py-1 border-b border-dark-900">
                <span className="text-dark-400">Rate Limiter</span>
                <span className="text-emerald-400 font-semibold uppercase tracking-wider text-[10px]">Active (10/min)</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-dark-900">
                <span className="text-dark-400">SQL Filter</span>
                <span className="text-emerald-400 font-semibold uppercase tracking-wider text-[10px]">Read-only Only</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-dark-400">Context Retention</span>
                <span className="text-brand-400 font-semibold uppercase tracking-wider text-[10px]">Last 10 turns</span>
              </div>
            </div>
          </div>

        </aside>

        {/* CENTER VIEWPORT: Chat Room OR Metrics */}
        <main className="flex-1 glass-panel rounded-3xl overflow-hidden flex flex-col border border-dark-800">
          
          {activeTab === 'chat' ? (
            /* TAB 1: Chat Room Component */
            <>
              {/* Message Feed container */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((msg, idx) => (
                  <div 
                    key={idx} 
                    className={`flex flex-col max-w-[85%] ${msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'} animate-fade-in`}
                  >
                    <div className="flex items-center gap-1.5 text-[10px] text-dark-400 mb-1 px-1">
                      {msg.sender === 'user' ? (
                        <>
                          <span>{msg.timestamp}</span>
                          <span className="font-bold text-brand-300">You</span>
                        </>
                      ) : (
                        <>
                          <span className="font-bold text-emerald-400">Assistant</span>
                          <span>{msg.timestamp}</span>
                        </>
                      )}
                    </div>
                    
                    <div className={`p-4 rounded-2xl text-sm leading-relaxed border ${msg.sender === 'user' ? 'bg-gradient-to-r from-brand-600 to-brand-700 text-white border-brand-500 rounded-tr-none' : 'bg-dark-900/50 text-[#e2e8f0] border-dark-800 rounded-tl-none shadow-lg'}`}>
                      {msg.text}
                    </div>

                    {msg.sender === 'assistant' && msg.metadata && msg.metadata.query_result && msg.metadata.query_result.length > 0 && (
                      <QueryResultTable data={msg.metadata.query_result} />
                    )}

                    {msg.sender === 'assistant' && msg.metadata && (
                      <div className="w-full">
                        <MetadataPanel meta={msg.metadata} />
                      </div>
                    )}
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex flex-col items-start max-w-[85%] animate-fade-in">
                    <div className="flex items-center gap-1.5 text-[10px] text-dark-400 mb-1 px-1">
                      <span className="font-bold text-emerald-400">Assistant</span>
                      <span className="text-brand-300">Generating query...</span>
                    </div>
                    <div className="p-4 rounded-2xl bg-dark-900/40 border border-dark-800 rounded-tl-none flex items-center gap-3">
                      <div className="flex gap-1">
                        <span className="h-2 w-2 rounded-full grad-brand animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="h-2 w-2 rounded-full grad-brand animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="h-2 w-2 rounded-full grad-brand animate-bounce" style={{ animationDelay: '300ms' }}></span>
                      </div>
                      <span className="text-xs text-dark-400 font-medium">Groq API compiling secure SQL...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input & Query Suggestions Area */}
              <div className="p-4 border-t border-dark-800 bg-[#0c0d17]/90 sticky bottom-0">
                {/* Suggestions Pills */}
                <div className="flex items-center gap-2 overflow-x-auto pb-3 scrollbar-hide text-xs">
                  <span className="text-dark-500 font-bold uppercase tracking-wider shrink-0 text-[10px]">Suggested:</span>
                  {suggestedQueries[currentUser.role]?.map((suggestion, idx) => (
                    <button 
                      key={idx}
                      onClick={() => handleSendMessage(suggestion.query)}
                      className="px-3 py-1.5 rounded-lg border border-dark-800 hover:border-brand-500/40 bg-dark-950/40 text-dark-300 hover:text-white shrink-0 transition-colors text-[11px]"
                    >
                      {suggestion.text}
                    </button>
                  ))}
                </div>

                {/* Input Text Form */}
                <form 
                  onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                  className="flex gap-2"
                >
                  <input 
                    type="text" 
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder={`Ask ERP questions in plain English as ${currentUser.role}...`}
                    className="flex-1 px-4 py-3 rounded-xl input-glass focus:outline-none text-sm placeholder-dark-500"
                    disabled={isLoading}
                  />
                  <button 
                    type="submit" 
                    disabled={!inputText.trim() || isLoading}
                    className="grad-brand hover:opacity-90 disabled:opacity-40 text-white p-3 rounded-xl flex items-center justify-center shrink-0 glow-brand transition-all"
                  >
                    <Send size={18} />
                  </button>
                </form>
              </div>
            </>
          ) : (
            /* TAB 2: Metrics Dashboard Component */
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-dark-800 pb-4">
                <div>
                  <h2 className="text-lg font-bold text-white">System Metrics Dashboard</h2>
                  <p className="text-xs text-dark-400">Cost, performance, and cache stats from active database queries.</p>
                </div>
                <button 
                  onClick={fetchMetrics}
                  disabled={isRefreshingMetrics}
                  className="flex items-center gap-1.5 text-xs text-brand-300 border border-brand-900/50 hover:bg-brand-950/20 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                >
                  <RefreshCw size={13} className={isRefreshingMetrics ? 'animate-spin' : ''} />
                  Reload Statistics
                </button>
              </div>

              {/* Statistics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card rounded-2xl p-4 border border-dark-800">
                  <div className="text-[10px] font-bold text-dark-400 uppercase tracking-wide">Total Queries</div>
                  <div className="text-2xl font-extrabold text-white mt-1">{metrics.total_queries}</div>
                  <div className="text-[10px] text-dark-500 mt-1 flex items-center gap-1">
                    <Database size={10} /> Active database logs
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-4 border border-dark-800">
                  <div className="text-[10px] font-bold text-dark-400 uppercase tracking-wide">Cache Hit Rate</div>
                  <div className="text-2xl font-extrabold text-emerald-400 mt-1">{metrics.cache_hit_rate_percent}%</div>
                  <div className="text-[10px] text-emerald-500 mt-1 flex items-center gap-1">
                    <CheckCircle2 size={10} /> Saved LLM/DB costs
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-4 border border-dark-800">
                  <div className="text-[10px] font-bold text-dark-400 uppercase tracking-wide">SQL Accuracy</div>
                  <div className="text-2xl font-extrabold text-brand-400 mt-1">{metrics.accuracy_rate_percent}%</div>
                  <div className="text-[10px] text-brand-500 mt-1 flex items-center gap-1">
                    <Activity size={10} /> Safe query execution
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-4 border border-dark-800">
                  <div className="text-[10px] font-bold text-dark-400 uppercase tracking-wide">Avg DB Speed (Uncached)</div>
                  <div className="text-2xl font-extrabold text-white mt-1">{metrics.average_execution_speed_ms}ms</div>
                  <div className="text-[10px] text-dark-500 mt-1 flex items-center gap-1">
                    <Clock size={10} /> Response Latency
                  </div>
                </div>
              </div>

              {/* Live Audit Log Table */}
              <div className="glass-card rounded-2xl border border-dark-800 overflow-hidden">
                <div className="px-4 py-3 bg-[#161726]/40 border-b border-dark-800 flex items-center justify-between">
                  <span className="font-bold text-xs uppercase tracking-wide text-dark-300">Live Audit Logs (Last 20 Runs)</span>
                  <span className="text-[10px] text-dark-500 font-mono">Real-time update</span>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-dark-800 text-dark-400 font-bold bg-[#0d0e1b]/40">
                        <th className="p-3">User Role</th>
                        <th className="p-3">Question</th>
                        <th className="p-3">Generated SQL</th>
                        <th className="p-3">Cache</th>
                        <th className="p-3">Latency</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-dark-900 font-mono">
                      {metrics.recent_queries.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="p-6 text-center text-dark-500">
                            No logs found in audit table. Run some questions in the Chat Room first!
                          </td>
                        </tr>
                      ) : (
                        metrics.recent_queries.map((q) => {
                          const isBlocked = q.response.includes('Query Blocked') || q.response.includes('Security Validation Failed');
                          return (
                            <tr key={q.log_id} className="hover:bg-dark-900/30 transition-colors">
                              <td className="p-3 whitespace-nowrap">
                                <span className="px-2 py-0.5 rounded bg-dark-950 text-brand-300 text-[10px] font-semibold border border-dark-800">
                                  {q.user_role}
                                </span>
                              </td>
                              <td className="p-3 max-w-[200px] truncate" title={q.question}>{q.question}</td>
                              <td className="p-3 max-w-[300px] truncate text-dark-400" title={q.generated_sql}>
                                {isBlocked ? (
                                  <span className="text-red-400 font-bold">[BLOCKED]</span>
                                ) : (
                                  q.generated_sql
                                )}
                              </td>
                              <td className="p-3">
                                {q.cache_hit ? (
                                  <span className="text-emerald-400 font-bold uppercase text-[9px] border border-emerald-950 px-1 py-0.2 rounded bg-emerald-950/20">HIT</span>
                                ) : (
                                  <span className="text-dark-500 uppercase text-[9px]">MISS</span>
                                )}
                              </td>
                              <td className="p-3 text-white font-semibold">{q.cache_hit ? '0ms' : `${q.execution_time_ms}ms`}</td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

        </main>
      </div>

      {/* Footer footer layout */}
      <footer className="px-6 py-4 border-t border-dark-800/80 bg-[#0a0b12] text-center text-xs text-dark-500">
        University ERP Conversational Assistant © 2026. Made with React, FastAPI, LangGraph, and Groq API.
      </footer>
    </div>
  );
}

export default App;
