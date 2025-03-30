import { useState, useEffect } from 'react';
import githubIcon from './assets/github-mark-white.png';
import './App.css';

function App() {
  // Form inputs state
  const [pat, setPat] = useState('');
  const [codeHost, setCodeHost] = useState('github');

  // Dates: default endDate today, startDate 7 days ago
  const today = new Date().toISOString().split('T')[0];
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0];
  const [startDate, setStartDate] = useState(sevenDaysAgo);
  const [endDate, setEndDate] = useState(today);

  // Accordion state for additional filters
  const [showFilters, setShowFilters] = useState(false);
  // Instead of hardcoding availableRepos, we now store it in state so it can be updated
  const [availableRepos, setAvailableRepos] = useState<string[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
  const [authorInput, setAuthorInput] = useState('');
  const [authors, setAuthors] = useState<string[]>([]);

  // Output state
  const [commitsOutput, setCommitsOutput] = useState('');
  const [dummyOutput, setDummyOutput] = useState('');
  const [progress, setProgress] = useState(0);
  const [isExecuting, setIsExecuting] = useState(false);

  // New state to control accordion visibility for PAT input
  const [showPATAccordion, setShowPATAccordion] = useState(false);
  // When authorized, we switch the PAT input to be masked
  const [isPATAuthorized, setIsPATAuthorized] = useState(false);

  // New state variables at the top of your App component:
  const [authProgress, setAuthProgress] = useState(0);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [authError, setAuthError] = useState(false);

  // Authorization state for GitHub
  const [isGithubAuthorized, setIsGithubAuthorized] = useState(false);
  const [sessionId, setSessionId] = useState(''); // New state to hold the session ID
  const isAuthorized = isGithubAuthorized || isPATAuthorized;

  // Handler for toggling filters accordion
  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };

  // Handler for selecting repos
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

  // Handler to add author from input
  const addAuthor = () => {
    if (authorInput && !authors.includes(authorInput)) {
      setAuthors([...authors, authorInput]);
      setAuthorInput('');
    }
  };

  // Handler for Recap button
  const handleRecap = async () => {
    setCommitsOutput('');
    setProgress(0);
    setIsExecuting(true);
  
    const progressInterval = setInterval(() => {
      setProgress((prev) => (prev < 95 ? prev + 1 : prev)); // Cap at 90%
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
    } catch (error) {
      console.error('Error fetching actions:', error);
      setCommitsOutput('Error retrieving actions.');
    } finally {
      clearInterval(progressInterval);
      setProgress(100); // Set to 100% when done
      setIsExecuting(false);
    }
  };

  // OAuth: retrieve session_id from external-signup
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    console.log("OAuth code from URL:", code);
    if (!code) return;
  
    const backendUrl = import.meta.env.VITE_AICORE_API; 
    const appName = import.meta.env.VITE_APP_NAME;
    const target = `${backendUrl}/external-signup?app=${appName}&accessToken=${code}&provider=GitHub`;
  
    fetch(target, { method: "GET" })
      .then((response) => response.json())
      .then((data) => {
        console.log("GitHub token response", data);
        setIsGithubAuthorized(true);
        // Save the session ID returned by the backend
        setSessionId(data.session_id);
      })
      .catch((error) => {
        console.error("Error processing GitHub login", error);
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

  // Handler for the PAT authorize button
  const handlePATAuthorize = async () => {
    const backendUrl = import.meta.env.VITE_AICORE_API;
    setAuthError(false);
    setAuthProgress(0);
    setIsAuthorizing(true);
  
    // Simulate progress bar increasing while waiting for the API call
    const progressInterval = setInterval(() => {
      setAuthProgress((prev) => (prev < 90 ? prev + 10 : prev));
    }, 300);
  
    try {
      const payload = {
        pat, // the PAT token to be stored in backend
        session_id: sessionId, // the session identifier (if already exists, or empty if not)
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
      // Update sessionId state so that repos fetch is triggered
      setSessionId(data.session_id);
  
      // Mask the PAT field by setting the flag to true
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
                    {/* Show progress bar when authorizing */}
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
              Authorized
            </button>
          )}
        </div>
        {/* Date Inputs */}
        <div className="form-group date-group">
          <div>
            <label>Start Date:</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div>
            <label>End Date:</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
        </div>

        {/* Accordion for Additional Filters */}
        <div className="accordion">
          <button onClick={toggleFilters}>
            {showFilters ? 'Hide Additional Filters' : 'Show Additional Filters'}
          </button>
          {showFilters && (
            <div className="accordion-content">
              {/* Repo Multi-Select */}
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
              {/* Authors Section */}
              <div className="authors-section">
                <div>
                  <label>Add Author:</label>
                  <input
                    type="text"
                    value={authorInput}
                    onChange={(e) => setAuthorInput(e.target.value)}
                    placeholder="Enter author name"
                  />
                  <button type="button" onClick={addAuthor}>
                    Add
                  </button>
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
          <progress value={progress} max="100"></progress>
          <textarea readOnly value={commitsOutput} rows={10} />
        </div>
        <div className="output-box">
          <h2>Dummy Output</h2>
          <progress value={progress} max="100"></progress>
          <textarea readOnly value={dummyOutput} rows={10} />
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