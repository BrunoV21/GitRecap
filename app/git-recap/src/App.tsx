import { useState, useEffect } from 'react';
import githubIcon from './assets/github-mark-white.png';
import './App.css';
import ReactMarkdown from 'react-markdown';

function App() {
  // ... existing states ...
  const [pat, setPat] = useState('');
  const [codeHost, setCodeHost] = useState('github');

  // Date states
  const today = new Date().toISOString().split('T')[0];
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const [startDate, setStartDate] = useState(sevenDaysAgo);
  const [endDate, setEndDate] = useState(today);

  // Accordion and filter states
  const [showFilters, setShowFilters] = useState(false);
  const [availableRepos, setAvailableRepos] = useState<string[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
  const [authorInput, setAuthorInput] = useState('');
  const [authors, setAuthors] = useState<string[]>([]);

  // Output states
  const [commitsOutput, setCommitsOutput] = useState('');
  const [dummyOutput, setDummyOutput] = useState('');
  // Two separate progress states:
  const [progressActions, setProgressActions] = useState(0);
  const [progressWs, setProgressWs] = useState(0);
  const [isExecuting, setIsExecuting] = useState(false);

  // PAT accordion and authorization states
  const [showPATAccordion, setShowPATAccordion] = useState(false);
  const [isPATAuthorized, setIsPATAuthorized] = useState(false);
  const [authProgress, setAuthProgress] = useState(0);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [authError, setAuthError] = useState(false);  

  // Add a new state variable at the top with your other states
  const [oauthCodeProcessed, setOauthCodeProcessed] = useState(false);

  // Authorization states for GitHub/session
  const [isGithubAuthorized, setIsGithubAuthorized] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const isAuthorized = isGithubAuthorized || isPATAuthorized;

  // Handlers for toggling filters and selecting repos/authors
  const toggleFilters = () => setShowFilters(!showFilters);
  const handleRepoSelectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const options = event.target.options;
    const selected: string[] = [];
    for (let i = 0; i < options.length; i++) {
      if (options[i].selected) {
        selected.push(options[i].value);
      }
    }
    setSelectedRepos(selected);
  };
  const addAuthor = () => {
    if (authorInput && !authors.includes(authorInput)) {
      setAuthors([...authors, authorInput]);
      setAuthorInput('');
    }
  };

  // Handler for Recap button
  const handleRecap = async () => {
    setCommitsOutput('');
    setDummyOutput('');
    setProgressActions(0);
    setProgressWs(0);
    setIsExecuting(true);

    // Start progress for actions endpoint (cap at ~95%)
    const progressActionsInterval = setInterval(() => {
      setProgressActions((prev) => (prev < 95 ? prev + 1 : prev));
    }, 500);

    try {
      const backendUrl = import.meta.env.VITE_AICORE_API;
      const queryParams = new URLSearchParams({
        session_id: sessionId,
        start_date: startDate,
        end_date: endDate,
        ...(selectedRepos.length ? { repo_filter: selectedRepos.join(",") } : {}),
        ...(authors.length ? { authors: authors.join(",") } : {}),
      }).toString();

      const response = await fetch(`${backendUrl}/actions?${queryParams}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Request failed! Status: ${response.status}`);
      }

      const data = await response.json();
      setCommitsOutput(data.actions);

      // Actions progress is now complete:
      clearInterval(progressActionsInterval);
      setProgressActions(100);

      // --- Now open the websocket ---
      // Construct the websocket URL (assuming backend URL starts with http/https)
      const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/ws/${sessionId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connected.");
        // Send the actions output via the websocket
        ws.send(data.actions);
      };

      // Start a separate progress for websocket (simulate progress until <end> is received)
      const progressWsInterval = setInterval(() => {
        setProgressWs((prev) => (prev < 95 ? prev + 5 : prev));
      }, 500);

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data.toString()).chunk;
        if (message === "</end>") {
          // When <end> is received, complete progress and close
          clearInterval(progressWsInterval);
          setProgressWs(100);
          ws.close();
        } else {
          // Append received chunk to dummyOutput
          setDummyOutput((prev) => prev + message);
        }
      };

      ws.onerror = (event) => {
        console.error("WebSocket error:", event);
        clearInterval(progressWsInterval);
        setProgressWs(100);
      };
    } catch (error) {
      console.error('Error during recap:', error);
      setCommitsOutput('Error retrieving actions.');
    } finally {
      setIsExecuting(false);
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    
    if (!code) return;
    
    // Check if we've already processed this specific code
    const processedCode = sessionStorage.getItem('processedOAuthCode');
    if (processedCode === code) {
      console.log("This OAuth code was already processed");
      // Check if we have a stored session from this code
      const storedSession = sessionStorage.getItem('githubSessionId');
      if (storedSession) {
        console.log("Restoring session from storage:", storedSession);
        setIsGithubAuthorized(true);
        setSessionId(storedSession);
      }
      return;
    }
    
    // Store the code we're processing
    sessionStorage.setItem('processedOAuthCode', code);
    
    const backendUrl = import.meta.env.VITE_AICORE_API; 
    const appName = import.meta.env.VITE_APP_NAME;
    const target = `${backendUrl}/external-signup?app=${appName}&accessToken=${code}&provider=GitHub`;
    
    fetch(target, { method: "GET" })
      .then(response => response.json())
      .then(data => {
        console.log("GitHub token response", data);
        setIsGithubAuthorized(true);
        setSessionId(data.session_id);
        
        // Store the session ID in sessionStorage for future use
        sessionStorage.setItem('githubSessionId', data.session_id);
        
        // Clean up the URL after successful processing
        if (window.history.replaceState) {
          const newUrl = window.location.pathname + window.location.hash;
          window.history.replaceState(null, '', newUrl);
        }
      })
      .catch(error => {
        console.error("OAuth processing error:", error);
        // Only remove the stored code on error to allow retry
        sessionStorage.removeItem('processedOAuthCode');
      });
  }, []);

  // Fetch repos using session_id when it is available
  useEffect(() => {
    if (!sessionId) return;
    const backendUrl = import.meta.env.VITE_AICORE_API;
    fetch(`${backendUrl}/repos?session_id=${sessionId}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("Fetched repos:", data.repos);
        setAvailableRepos(data.repos);
      })
      .catch((error) => {
         console.error("Error fetching repos", error);
      });
  }, [sessionId]);

  const handleGithubLogin = () => {
    const GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID;
    const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI;
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=read:user`;
    window.location.href = githubAuthUrl;
  };

  // Toggle PAT accordion visibility
  const togglePATAccordion = () => {
    setShowPATAccordion((prev) => !prev);
  };

  // Handler for the PAT authorize button remains the same...
  const handlePATAuthorize = async () => {
    const backendUrl = import.meta.env.VITE_AICORE_API;
    setAuthError(false);
    setAuthProgress(0);
    setIsAuthorizing(true);
  
    const progressInterval = setInterval(() => {
      setAuthProgress((prev) => (prev < 90 ? prev + 10 : prev));
    }, 300);
  
    try {
      const payload = {
        pat,
        session_id: sessionId,
      };
  
      const response = await fetch(`${backendUrl}/pat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
  
      if (!response.ok) {
        throw new Error('PAT authorization failed.');
      }
  
      const data = await response.json();
      console.log("PAT stored for session:", data.session_id);
      setSessionId(data.session_id);
      setIsPATAuthorized(true);
    } catch (error) {
      console.error('Error authorizing PAT:', error);
      setAuthError(true);
      window.alert("PAT authorization failed. Please check your PAT and try again.");
    } finally {
      clearInterval(progressInterval);
      setAuthProgress(100);
      setIsAuthorizing(false);
    }
  };

  return (
    <div className="App">
      <h1>Git Recap</h1>
      <div className="form-container">
        <div className="github-signin-container">
          { !isAuthorized ? (
            <>
              <button className="github-signin-btn" onClick={handleGithubLogin}>
                <img src={githubIcon} alt="GitHub Icon" className="github-icon" />
                Sign in with GitHub
              </button>
              {/* PAT Accordion Section */}
              <div className="pat-accordion">
                <button className="accordion-toggle" onClick={togglePATAccordion}>
                  or authorize with a PAT
                </button>
                {showPATAccordion && (
                  <div className="accordion-content">
                    <div className="form-group pat-group">
                      <div>
                        <label>Personal Access Token (PAT):</label>
                        <input
                          type={isPATAuthorized ? "password" : "text"}
                          value={pat}
                          onChange={(e) => setPat(e.target.value)}
                          placeholder="Enter your PAT"
                          style={{ color: authError ? 'red' : '#fff' }}
                        />
                      </div>
                      <div>
                        <label>Code Host:</label>
                        <select value={codeHost} onChange={(e) => setCodeHost(e.target.value)}>
                          <option value="github">GitHub</option>
                          <option value="azure">Azure DevOps</option>
                          <option value="gitlab">GitLab</option>
                        </select>
                      </div>
                    </div>
                    {isAuthorizing && (
                      <progress value={authProgress} max="100" style={{ width: '100%' }}></progress>
                    )}
                    <button className="authorize-btn" onClick={handlePATAuthorize}>
                      Authorize
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <button className="authorized-btn" disabled>
              ✔ Authorized
            </button>
          )}
        </div>
        {/* Date Inputs */}
        <div className="form-group date-group">
          <div>
            <label>Start Date:</label>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div>
            <label>End Date:</label>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
        </div>
        {/* Accordion for Additional Filters */}
        <div className="accordion">
          <button onClick={toggleFilters}>
            {showFilters ? 'Hide Additional Filters' : 'Show Additional Filters'}
          </button>
          {showFilters && (
            <div className="accordion-content">
              <div>
                <label>Select Repositories:</label>
                <select multiple value={selectedRepos} onChange={handleRepoSelectChange}>
                  {availableRepos.map((repo) => (
                    <option key={repo} value={repo}>
                      {repo}
                    </option>
                  ))}
                </select>
              </div>
              <div className="authors-section">
                <div>
                  <label>Add Author:</label>
                  <input
                    type="text"
                    value={authorInput}
                    onChange={(e) => setAuthorInput(e.target.value)}
                    placeholder="Enter author name"
                  />
                  <button type="button" onClick={addAuthor}>Add</button>
                </div>
                {authors.length > 0 && (
                  <div className="form-group">
                    <label>Authors Added:</label>
                    <textarea readOnly value={authors.join(', ')} rows={2} />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      {/* Output Section */}
      <div className="output-section">
        <div className="output-box">
          <h2>Actions Log</h2>
          <progress value={progressActions} max="100"></progress>
          <textarea readOnly value={commitsOutput} rows={10} />
        </div>
        <div className="output-box">
          <h2>Summary</h2>
          <progress value={progressWs} max="100"></progress>
          <div className="markdown-output">
            <ReactMarkdown>{dummyOutput}</ReactMarkdown>
          </div>
        </div>
      </div>
      {/* Recap Button */}
      <div className="recap-button">
        <button onClick={handleRecap} disabled={isExecuting}>
          {isExecuting ? 'Processing...' : 'Recap'}
        </button>
      </div>
    </div>
  );
}

export default App;